# src/api/patient_routes.py
from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime
import traceback
import re
from typing import Dict, Any, Optional, List

from api.schemas.patient_schemas import (
    InserisciAnagraficaRequest,
    InserisciAnagraficaResponse,
    CompletaStoriaMedicaRequest,
    CompletaStoriaMedicaResponse,
    RiceviSommarioResponse,
    PatientSummaryInfo,
    SommarioCompleto
)
from dependencies import get_patient_handler
from Patient.patients_handler import PatientHandler

router = APIRouter()


# ============ DATA EXTRACTOR ============

class DataExtractor:
    MESI = {
        'gennaio': '01', 'febbraio': '02', 'marzo': '03', 'aprile': '04',
        'maggio': '05', 'giugno': '06', 'luglio': '07', 'agosto': '08',
        'settembre': '09', 'ottobre': '10', 'novembre': '11', 'dicembre': '12',
        'gen': '01', 'feb': '02', 'mar': '03', 'apr': '04',
        'mag': '05', 'giu': '06', 'lug': '07', 'ago': '08',
        'set': '09', 'ott': '10', 'nov': '11', 'dic': '12'
    }

    @staticmethod
    def extract_email(text: str) -> Optional[str]:
        pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        match = re.search(pattern, text)
        return match.group(0) if match else None

    @staticmethod
    def extract_birth_date(text: str) -> Optional[str]:
        text_lower = text.lower()

        # "28 gennaio 1990"
        for mese_nome, mese_num in DataExtractor.MESI.items():
            pattern = rf'\b(\d{{1,2}})\s+{mese_nome}\s+(\d{{4}})\b'
            match = re.search(pattern, text_lower)
            if match:
                giorno = match.group(1).zfill(2)
                anno = match.group(2)
                return f"{anno}-{mese_num}-{giorno}"

        # DD/MM/YYYY o DD-MM-YYYY
        pattern = r'\b(\d{1,2})[/-](\d{1,2})[/-](\d{4})\b'
        match = re.search(pattern, text)
        if match:
            giorno = match.group(1).zfill(2)
            mese = match.group(2).zfill(2)
            anno = match.group(3)
            return f"{anno}-{mese}-{giorno}"

        # YYYY-MM-DD
        pattern = r'\b(\d{4})-(\d{1,2})-(\d{1,2})\b'
        match = re.search(pattern, text)
        if match:
            return match.group(0)

        return None

    @staticmethod
    def extract_sex(text: str) -> Optional[str]:
        text_lower = text.lower()

        male_patterns = [r'\buomo\b', r'\bmaschio\b', r'\bsono un uomo\b', r'\bsono un\s', r'\bsesso maschile\b']
        for pattern in male_patterns:
            if re.search(pattern, text_lower):
                return 'M'

        female_patterns = [r'\bdonna\b', r'\bfemmina\b', r'\bsono una donna\b', r'\bsono una\s', r'\bsesso femminile\b',
                           r'\bnata\b']
        for pattern in female_patterns:
            if re.search(pattern, text_lower):
                return 'F'

        return None

    @staticmethod
    def extract_city(text: str, keyword: str) -> Optional[str]:
        """
        Migliora estrazione città evitando parole extra
        """
        # Pattern 1: "nato il 28 gennaio 1990 a Roma" -> prendi Roma
        pattern = rf'{keyword}(?:\s+il)?\s+(?:\d{{1,2}}\s+\w+\s+\d{{4}}\s+)?(?:a|in)\s+([A-ZÀ-Ù][a-zà-ù]+)'
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            city = match.group(1)
            # Filtra parole comuni non-città
            if city.lower() not in ['ma', 'il', 'la', 'un', 'una', 'e', 'di', 'da']:
                return city.title()

        # Pattern 2: "vivo a Milano" -> Milano
        pattern = rf'{keyword}\s+(?:a|in)\s+([A-ZÀ-Ù][a-zà-ù]+)'
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            city = match.group(1)
            if city.lower() not in ['ma', 'il', 'la', 'un', 'una', 'e', 'di', 'da']:
                return city.title()

        return None

    @staticmethod
    def extract_height(text: str) -> Optional[int]:
        text_lower = text.lower()

        # "1.75m" o "1,75m"
        pattern = r'(\d+)[.,](\d+)\s*(?:m|metri)(?!g)\b'
        match = re.search(pattern, text_lower)
        if match:
            return int(match.group(1)) * 100 + int(match.group(2))

        # "175cm" o "alto 175"
        pattern = r'(?:alto|altezza|misuro)[:\s]*(\d{2,3})\s*(?:cm|centimetri)?'
        match = re.search(pattern, text_lower)
        if match:
            return int(match.group(1))

        # "175 cm"
        pattern = r'\b(\d{2,3})\s*(?:cm|centimetri)\b'
        match = re.search(pattern, text_lower)
        if match:
            return int(match.group(1))

        return None

    @staticmethod
    def extract_weight(text: str) -> Optional[float]:
        text_lower = text.lower()

        patterns = [
            r'(?:peso|pesare|weight)[:\s]*(\d+(?:[.,]\d+)?)\s*(?:kg|chili)?',
            r'\bpeso\s+(\d+(?:[.,]\d+)?)\b',
            r'\b(\d+(?:[.,]\d+)?)\s*(?:kg|chili)\b'
        ]

        for pattern in patterns:
            match = re.search(pattern, text_lower)
            if match:
                peso_str = match.group(1).replace(',', '.')
                return float(peso_str)

        return None

    @staticmethod
    def extract_allergies(text: str) -> List[str]:
        text_lower = text.lower()

        # Pattern negativo
        if re.search(r'non ho allergie|nessuna allergia|senza allergie|non sono allergic', text_lower):
            return []

        # Pattern positivo: "allergico a pesce, glutine"
        pattern = r'allergi[coae]*\s+(?:a|al|alla|ai)?[:\s]*([a-zà-ù,\s]+?)(?:\.|$|;|\n|non\b|seguo\b|dormo\b|faccio\b)'
        match = re.search(pattern, text_lower)
        if match:
            allergie_str = match.group(1).strip()
            # Split su virgola o "e"
            allergies = [a.strip() for a in re.split(r',|\se\s', allergie_str) if a.strip() and len(a.strip()) > 2]
            return allergies

        return []

    @staticmethod
    def extract_lifestyle_field(text: str, field: str) -> Optional[Any]:
        text_lower = text.lower()

        if field == 'alcohol':
            if re.search(r'non bevo|mai\s+alcol|zero\s+alcol|non\s+consumo\s+alcol', text_lower):
                return 'mai'
            elif re.search(r'raramente\s+bevo|ogni\s+tanto', text_lower):
                return 'raramente'
            elif re.search(r'qualche\s+volta|occasionalmente', text_lower):
                return 'qualche volta'
            elif re.search(r'spesso|frequentemente', text_lower):
                return 'spesso'
            elif re.search(r'ogni\s+giorno|quotidianamente|tutti\s+i\s+giorni', text_lower):
                return 'quotidianamente'

        elif field == 'sleep':
            # "dormo 7 ore", "dormo circa 7-8 ore"
            pattern = r'dorm[oi]\s+(?:circa\s+)?(\d+)(?:-\d+)?\s*(?:ore|h)'
            match = re.search(pattern, text_lower)
            if match:
                return int(match.group(1))

        elif field == 'physical_activity_freq':
            if re.search(r'non\s+faccio|mai\s+sport|sedentari[oa]|non\s+pratico', text_lower):
                return 'mai'
            # "faccio sport 3 volte", "mi alleno 3 volte", "vado in palestra 3 volte"
            elif re.search(r'(?:faccio|pratico)?\s*(?:sport|attivit[aà]|palestra|alleno).*?(?:1|una|un)\s+volt[ea]',
                           text_lower):
                return '1-2 volte settimana'
            elif re.search(r'(?:faccio|pratico)?\s*(?:sport|attivit[aà]|palestra|alleno).*?(?:2|due)\s+volt[ea]',
                           text_lower):
                return '1-2 volte settimana'
            elif re.search(r'(?:faccio|pratico)?\s*(?:sport|attivit[aà]|palestra|alleno).*?(?:3|tre)\s+volt[ea]',
                           text_lower):
                return '3-4 volte settimana'
            elif re.search(r'(?:faccio|pratico)?\s*(?:sport|attivit[aà]|palestra|alleno).*?(?:4|quattro)\s+volt[ea]',
                           text_lower):
                return '3-4 volte settimana'
            elif re.search(
                    r'(?:faccio|pratico)?\s*(?:sport|attivit[aà]|palestra|alleno).*?(?:5|cinque|6|sei)\s+volt[ea]',
                    text_lower):
                return '5+ volte settimana'
            elif re.search(r'tutti\s+i\s+giorni|quotidianamente|ogni\s+giorno', text_lower):
                return 'quotidianamente'

        elif field == 'physical_activity_intensity':
            if re.search(r'(?:intensit[aà]\s+)?leggera|blanda|passeggia|camminat[ea]|tranquill[oa]', text_lower):
                return 'leggera'
            elif re.search(r'(?:intensit[aà]\s+)?moderata|media|normale', text_lower):
                return 'moderata'
            elif re.search(r'(?:intensit[aà]\s+)?intensa|pesante|vigorosa|intensiv[oa]|alta', text_lower):
                return 'intensa'

        elif field == 'smoker':
            if re.search(r'non\s+(?:sono\s+)?fumatore|non\s+fumo|mai\s+fumato|non\s+ho\s+mai', text_lower):
                return 'mai'
            elif re.search(r'ex\s+fumatore|ho\s+smesso|smesso\s+di\s+fumare', text_lower):
                return 'ex fumatore'
            elif re.search(r'occasionalmente|raramente\s+fumo|qualche\s+volta', text_lower):
                return 'occasionalmente'
            elif re.search(r'(?:sono\s+)?fumatore|fumo\s+regolarmente|fumo\s+tutti', text_lower):
                return 'regolarmente'

        elif field == 'diet':
            if re.search(r'dieta\s+vegana|vegan|sono\s+vegan', text_lower):
                return 'vegana'
            elif re.search(r'dieta\s+vegetariana|vegetarian[oa]|sono\s+vegetarian', text_lower):
                return 'vegetariana'
            elif re.search(r'dieta\s+mediterranea|mediterrane[oa]|stile\s+mediterraneo', text_lower):
                return 'mediterranea'
            elif re.search(r'dieta\s+onnivora|onnivoro|mangio\s+tutto|mangio\s+di\s+tutto', text_lower):
                return 'onnivora'

        return None

    @staticmethod
    def extract_doctor_preferences(text: str) -> Dict[str, int]:
        text_lower = text.lower()
        prefs = {'vicinanza': 3, 'specializzazione': 3, 'costo': 3, 'area_interesse': 3}

        high_keywords = ['molto\s+importante', 'fondamentale', 'essenziale', 'priorit[aà]', 'cruciale']
        medium_keywords = ['importante', 'preferibile', 'preferisco']
        low_keywords = ['non\s+(?:[eè]\s+)?importante', 'secondari[oa]', 'non\s+(?:[eè]\s+)?un\s+problema']

        fields_map = {
            'vicinanza': ['vicinanza', 'vicino', 'distanza', 'zona', 'geografica'],
            'specializzazione': ['specializzat[oa]', 'specializzazione', 'espert[oa]', 'competenz[ae]', 'preparat[oa]'],
            'costo': ['costo', 'prezzo', 'economic[oa]', 'budget', 'tariff[ae]'],
            'area_interesse': ['interesse', 'longevit[aà]', 'focus', 'area']
        }

        for field, keywords in fields_map.items():
            for keyword in keywords:
                if re.search(keyword, text_lower):
                    # Cerca contesto 100 char prima e dopo
                    idx = text_lower.find(re.search(keyword, text_lower).group())
                    context = text_lower[max(0, idx - 100):idx + 100]

                    # Check importanza
                    if any(re.search(h, context) for h in high_keywords):
                        prefs[field] = 5
                        break
                    elif any(re.search(m, context) for m in medium_keywords):
                        prefs[field] = 4
                        break
                    elif any(re.search(l, context) for l in low_keywords):
                        prefs[field] = 2
                        break

        return prefs


# ============ ROUTES ============

@router.post("/inserisci_anagrafica", response_model=InserisciAnagraficaResponse)
async def inserisci_anagrafica(
        request: InserisciAnagraficaRequest,
        patient_handler: PatientHandler = Depends(get_patient_handler)
):
    try:
        extractor = DataExtractor()

        dati_estratti = {
            'email': extractor.extract_email(request.messaggio),
            'data_nascita': extractor.extract_birth_date(request.messaggio),
            'sesso': extractor.extract_sex(request.messaggio),
            'citta_nascita': (
                    extractor.extract_city(request.messaggio, 'nat[oa]') or
                    extractor.extract_city(request.messaggio, 'provengo')
            ),
            'citta_residenza': (
                    extractor.extract_city(request.messaggio, 'vivo') or
                    extractor.extract_city(request.messaggio, 'abito')
            ),
            'altezza': extractor.extract_height(request.messaggio),
            'peso': extractor.extract_weight(request.messaggio)
        }

        campi_obbligatori = {
            'email': 'Email',
            'data_nascita': 'Data di nascita',
            'sesso': 'Sesso',
            'citta_nascita': 'Città di nascita'
        }

        campi_mancanti = [
            nome for campo, nome in campi_obbligatori.items()
            if not dati_estratti.get(campo)
        ]

        is_complete = len(campi_mancanti) == 0
        message = "✅ Dati completi!" if is_complete else f"⚠️ Mancano: {', '.join(campi_mancanti)}"

        return InserisciAnagraficaResponse(
            success=True,
            message=message,
            dati_estratti=dati_estratti,
            is_complete=is_complete,
            campi_mancanti=campi_mancanti
        )

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/completa_storiamedica", response_model=CompletaStoriaMedicaResponse)
async def completa_storiamedica(
        request: CompletaStoriaMedicaRequest,
        patient_handler: PatientHandler = Depends(get_patient_handler)
):
    try:
        extractor = DataExtractor()

        allergie = extractor.extract_allergies(request.messaggio)

        lifestyle = {
            'frequenza_alcol': extractor.extract_lifestyle_field(request.messaggio, 'alcohol'),
            'ore_sonno': extractor.extract_lifestyle_field(request.messaggio, 'sleep'),
            'frequenza_attivita_fisica': extractor.extract_lifestyle_field(request.messaggio, 'physical_activity_freq'),
            'intensita_attivita_fisica': extractor.extract_lifestyle_field(request.messaggio, 'physical_activity_intensity'),
            'fumatore': extractor.extract_lifestyle_field(request.messaggio, 'smoker'),
            'tipo_dieta': extractor.extract_lifestyle_field(request.messaggio, 'diet')
        }

        scelta_medico = extractor.extract_doctor_preferences(request.messaggio)

        dati_estratti = {
            'allergie': allergie,
            'lifestyle': lifestyle,
            'obiettivi': {'testo_completo': request.messaggio[:500]},
            'motivo_visita': request.messaggio[:300],
            'scelta_medico': scelta_medico
        }

        campi_mancanti = [campo for campo, valore in lifestyle.items() if valore is None]
        is_complete = len(campi_mancanti) == 0
        message = "✅ Storia completa!" if is_complete else f"⚠️ Mancano: {', '.join(campi_mancanti)}"

        return CompletaStoriaMedicaResponse(
            success=True,
            message=message,
            dati_estratti=dati_estratti,
            is_complete=is_complete,
            campi_mancanti=campi_mancanti
        )

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ricevi_sommario/{email}", response_model=RiceviSommarioResponse)
async def ricevi_sommario(
        email: str,
        patient_handler: PatientHandler = Depends(get_patient_handler)
):
    try:
        patient = patient_handler.search_patient_by_email(email)

        if not patient:
            raise HTTPException(status_code=404, detail="Paziente non trovato")

        patient_info = PatientSummaryInfo(
            nome=patient.get_name(),
            cognome=patient.get_surname(),
            email=patient.get_email(),
            eta=patient.get_age() or 0,
            sesso=patient.get_sex()
        )

        anagrafica = {
            "nome": patient.get_name(),
            "cognome": patient.get_surname(),
            "email": patient.get_email(),
            "codice_fiscale": patient.get_fiscal_code(),
            "data_nascita": patient.get_birth_date(),
            "eta": patient.get_age(),
            "sesso": patient.get_sex(),
            "altezza": patient.get_height(),
            "peso": patient.get_weight()
        }

        sommario = SommarioCompleto(
            anagrafica=anagrafica,
            lifestyle=patient.get_lifestyle() or {},
            allergie=patient.allergies if hasattr(patient, 'allergies') else [],
            obiettivi={"testo_completo": patient.get_additional_notes() or ""},
            preferenze_medico={},
            sintesi_testuale=patient.get_additional_notes()
        )

        return RiceviSommarioResponse(
            success=True,
            patient=patient_info,
            sommario=sommario,
            generated_at=datetime.now().isoformat()
        )

    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))