# src/api/schemas/patient_schemas.py
from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict
from typing import List, Optional
from datetime import datetime


# ============ INSERISCI ANAGRAFICA ============

class DatiPersonali(BaseModel):
    nome: str = Field(..., min_length=1, max_length=100)
    cognome: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    data_nascita: str = Field(..., description="Formato: YYYY-MM-DD, DD/MM/YYYY o 'DD mese YYYY'")
    sesso: str = Field(..., pattern="^[MF]$")
    citta_nascita: str
    citta_residenza: str
    altezza: int = Field(..., gt=0, le=250, description="Altezza in cm")
    peso: float = Field(..., gt=0, le=500, description="Peso in kg")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "nome": "Mario",
                "cognome": "Rossi",
                "email": "mario.rossi@email.com",
                "data_nascita": "15 marzo 1990",
                "sesso": "M",
                "citta_nascita": "Roma",
                "citta_residenza": "Milano",
                "altezza": 175,
                "peso": 70.5
            }
        }
    )

    @field_validator('data_nascita')
    @classmethod
    def validate_data_nascita(cls, v: str) -> str:
        mesi_italiani = {
            'gennaio': '01', 'febbraio': '02', 'marzo': '03', 'aprile': '04',
            'maggio': '05', 'giugno': '06', 'luglio': '07', 'agosto': '08',
            'settembre': '09', 'ottobre': '10', 'novembre': '11', 'dicembre': '12'
        }

        v = v.strip()

        # Formato "28 gennaio 1999"
        parts = v.lower().split()
        if len(parts) == 3:
            try:
                giorno = parts[0]
                mese_nome = parts[1]
                anno = parts[2]

                if mese_nome in mesi_italiani:
                    mese_num = mesi_italiani[mese_nome]
                    data_normalizzata = f"{anno}-{mese_num}-{giorno.zfill(2)}"
                    datetime.strptime(data_normalizzata, '%Y-%m-%d')
                    return data_normalizzata
            except (ValueError, IndexError):
                pass

        # Formati standard
        for fmt in ['%d/%m/%Y', '%Y-%m-%d']:
            try:
                date_obj = datetime.strptime(v, fmt)
                return date_obj.strftime('%Y-%m-%d')
            except ValueError:
                continue

        raise ValueError('Data nascita deve essere in formato: DD/MM/YYYY, YYYY-MM-DD o "DD mese YYYY"')


class InserisciAnagraficaRequest(BaseModel):
    dati_personali: DatiPersonali


class InserisciAnagraficaResponse(BaseModel):
    success: bool
    message: str
    patient_id: str
    email: str
    password: str
    codice_fiscale: str


# ============ COMPLETA STORIA MEDICA ============

class LifestyleData(BaseModel):
    frequenza_alcol: str
    ore_sonno: int = Field(..., ge=0, le=24)
    frequenza_attivita_fisica: str
    intensita_attivita_fisica: str
    fumatore: str
    tipo_dieta: str

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "frequenza_alcol": "mai",
                "ore_sonno": 7,
                "frequenza_attivita_fisica": "3 volte a settimana",
                "intensita_attivita_fisica": "moderata",
                "fumatore": "no",
                "tipo_dieta": "mediterranea"
            }
        }
    )


class ObiettivoRisposta(BaseModel):
    domanda: str
    opzioni_disponibili: List[str]
    risposta: List[int] = Field(..., min_length=1)

    @field_validator('risposta')
    @classmethod
    def validate_risposta(cls, v: List[int], info) -> List[int]:
        opzioni = info.data.get('opzioni_disponibili', [])
        max_opzioni = len(opzioni)

        for num in v:
            if num < 1 or num > max_opzioni:
                raise ValueError(f'Risposta deve essere tra 1 e {max_opzioni}')

        return v


class ObiettiviCompleti(BaseModel):
    motivo_scaricamento: ObiettivoRisposta
    obiettivi_principali: ObiettivoRisposta
    aspettative_percorso: ObiettivoRisposta

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "motivo_scaricamento": {
                    "domanda": "Perché hai scaricato Longeviva?",
                    "opzioni_disponibili": [
                        "1. Voglio migliorare il mio stile di vita con un supporto pratico e costante",
                        "2. Ho bisogno di un aiuto concreto per rimettermi in forma",
                        "3. Cerco un modo semplice per mangiare meglio e muovermi di più",
                        "4. Mi interessa la longevità e voglio prendermi cura della mia salute oggi",
                        "5. Mi ha incuriosito l'approccio innovativo con l'AI e la community"
                    ],
                    "risposta": [1, 3, 4]
                },
                "obiettivi_principali": {
                    "domanda": "Quali sono i tuoi obiettivi?",
                    "opzioni_disponibili": [
                        "1. Perdere peso in modo sano e sostenibile",
                        "2. Avere più energia durante la giornata",
                        "3. Migliorare la mia composizione corporea",
                        "4. Aumentare la mia consapevolezza alimentare",
                        "5. Vivere più a lungo e in salute",
                        "6. Sentirmi meglio fisicamente e mentalmente"
                    ],
                    "risposta": [1, 2, 6]
                },
                "aspettative_percorso": {
                    "domanda": "Cosa ti aspetti da questo percorso?",
                    "opzioni_disponibili": [
                        "1. Un percorso personalizzato e facile da seguire",
                        "2. Consigli pratici, non complicati",
                        "3. Sentirmi seguito/a da chi capisce le mie esigenze",
                        "4. Imparare abitudini che durino nel tempo",
                        "5. Un'esperienza motivante che mi tenga attivo/a e coinvolto/a"
                    ],
                    "risposta": [1, 3, 5]
                }
            }
        }
    )


class SceltaMedico(BaseModel):
    vicinanza: int = Field(..., ge=1, le=5)
    specializzazione: int = Field(..., ge=1, le=5)
    costo: int = Field(..., ge=1, le=5)
    area_interesse: int = Field(..., ge=1, le=5)


class CompletaStoriaMedicaRequest(BaseModel):
    email: EmailStr
    allergie: List[str] = []
    lifestyle: LifestyleData
    obiettivi: ObiettiviCompleti
    motivo_visita: str = Field(..., min_length=1)
    scelta_medico: SceltaMedico

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "mario.rossi@email.com",
                "allergie": ["pesce", "glutine", "lattosio"],
                "lifestyle": {
                    "frequenza_alcol": "mai",
                    "ore_sonno": 7,
                    "frequenza_attivita_fisica": "3 volte a settimana",
                    "intensita_attivita_fisica": "moderata",
                    "fumatore": "no",
                    "tipo_dieta": "mediterranea"
                },
                "obiettivi": {
                    "motivo_scaricamento": {
                        "domanda": "Perché hai scaricato Longeviva?",
                        "opzioni_disponibili": [
                            "1. Voglio migliorare il mio stile di vita con un supporto pratico e costante",
                            "2. Ho bisogno di un aiuto concreto per rimettermi in forma",
                            "3. Cerco un modo semplice per mangiare meglio e muovermi di più",
                            "4. Mi interessa la longevità e voglio prendermi cura della mia salute oggi",
                            "5. Mi ha incuriosito l'approccio innovativo con l'AI e la community"
                        ],
                        "risposta": [1, 3, 4]
                    },
                    "obiettivi_principali": {
                        "domanda": "Quali sono i tuoi obiettivi?",
                        "opzioni_disponibili": [
                            "1. Perdere peso in modo sano e sostenibile",
                            "2. Avere più energia durante la giornata",
                            "3. Migliorare la mia composizione corporea",
                            "4. Aumentare la mia consapevolezza alimentare",
                            "5. Vivere più a lungo e in salute",
                            "6. Sentirmi meglio fisicamente e mentalmente"
                        ],
                        "risposta": [1, 2, 6]
                    },
                    "aspettative_percorso": {
                        "domanda": "Cosa ti aspetti da questo percorso?",
                        "opzioni_disponibili": [
                            "1. Un percorso personalizzato e facile da seguire",
                            "2. Consigli pratici, non complicati",
                            "3. Sentirmi seguito/a da chi capisce le mie esigenze",
                            "4. Imparare abitudini che durino nel tempo",
                            "5. Un'esperienza motivante che mi tenga attivo/a e coinvolto/a"
                        ],
                        "risposta": [1, 3, 5]
                    }
                },
                "motivo_visita": "Voglio migliorare la mia salute generale e perdere peso",
                "scelta_medico": {
                    "vicinanza": 5,
                    "specializzazione": 4,
                    "costo": 3,
                    "area_interesse": 5
                }
            }
        }
    )


class CompletaStoriaMedicaResponse(BaseModel):
    success: bool
    message: str
    patient_id: str
    sommario_generato: bool = False


# ============ RICEVI SOMMARIO ============

class PatientSummaryInfo(BaseModel):
    nome: str
    cognome: str
    email: str
    eta: int
    sesso: str


class SommarioCompleto(BaseModel):
    anagrafica: dict
    lifestyle: dict
    allergie: List[str]
    obiettivi: dict
    preferenze_medico: dict
    sintesi_testuale: Optional[str] = None


class RiceviSommarioResponse(BaseModel):
    success: bool
    patient: PatientSummaryInfo
    sommario: SommarioCompleto
    generated_at: str