#Deprecated
from Doctor.doctor_instance import Doctor
import datetime
import random


def create_sample_doctors():
    """Crea e restituisce un elenco esteso di dottori realistici"""
    doctors = []

    # Database esteso di dottori con dati realistici
    doctors_data = [
        # CARDIOLOGIA
        {
            "name": "Laura", "surname": "Bianchi", "specialization": "Cardiologia", "experience": 12,
            "gender": "F", "age": 45, "city": "Milano", "region": "Lombardia",
            "subspecializations": ["Cardiologia Interventistica", "Elettrofisiologia"],
            "total_patients": 850, "success_rate": 94.5, "satisfaction": 4.7,
            "expertise": ["Angioplastica", "Ablazione cardiaca", "Ecocardiografia"],
            "conditions": ["Ipertensione", "Insufficienza cardiaca", "Aritmie", "Cardiopatia ischemica"],
            "consultation_fee": 120, "follow_up_fee": 80, "waiting_days": 7,
            "emergency": True, "home_visits": False, "telemedicine": True,
            "languages": ["Italiano", "Inglese"]
        },
        {
            "name": "Marco", "surname": "Ferrari", "specialization": "Cardiologia", "experience": 20,
            "gender": "M", "age": 55, "city": "Roma", "region": "Lazio",
            "subspecializations": ["Cardiochirurgia", "Emodinamica"],
            "total_patients": 1200, "success_rate": 96.8, "satisfaction": 4.9,
            "expertise": ["Bypass coronarico", "Valvuloplastica", "Cateterismo cardiaco"],
            "conditions": ["Stenosi valvolare", "Infarto miocardico", "Angina pectoris"],
            "consultation_fee": 150, "follow_up_fee": 100, "waiting_days": 14,
            "emergency": True, "home_visits": False, "telemedicine": False,
            "languages": ["Italiano", "Inglese", "Francese"]
        },

        # MEDICINA GENERALE
        {
            "name": "Mario", "surname": "Rossi", "specialization": "Medicina Generale", "experience": 18,
            "gender": "M", "age": 52, "city": "Milano", "region": "Lombardia",
            "subspecializations": ["Medicina Preventiva", "Geriatria"],
            "total_patients": 1200, "success_rate": 92.0, "satisfaction": 4.5,
            "expertise": ["Medicina preventiva", "Gestione cronicità", "Check-up completi"],
            "conditions": ["Diabete", "Ipertensione", "Controlli periodici", "Dislipidemia"],
            "consultation_fee": 80, "follow_up_fee": 60, "waiting_days": 3,
            "emergency": False, "home_visits": True, "telemedicine": True,
            "languages": ["Italiano"]
        },
        {
            "name": "Elena", "surname": "Conti", "specialization": "Medicina Generale", "experience": 15,
            "gender": "F", "age": 48, "city": "Torino", "region": "Piemonte",
            "subspecializations": ["Medicina Familiare", "Medicina dello Sport"],
            "total_patients": 980, "success_rate": 91.5, "satisfaction": 4.6,
            "expertise": ["Medicina familiare", "Vaccinazioni", "Certificazioni sportive"],
            "conditions": ["Malattie respiratorie", "Disturbi metabolici", "Medicina preventiva"],
            "consultation_fee": 75, "follow_up_fee": 55, "waiting_days": 2,
            "emergency": False, "home_visits": True, "telemedicine": True,
            "languages": ["Italiano", "Inglese"]
        },

        # DERMATOLOGIA
        {
            "name": "Giuseppe", "surname": "Verdi", "specialization": "Dermatologia", "experience": 9,
            "gender": "M", "age": 38, "city": "Napoli", "region": "Campania",
            "subspecializations": ["Dermatologia Oncologica", "Chirurgia Dermatologica"],
            "total_patients": 600, "success_rate": 96.2, "satisfaction": 4.8,
            "expertise": ["Chirurgia dermatologica", "Mappatura nei", "Laser terapia"],
            "conditions": ["Acne", "Dermatiti", "Nei e melanomi", "Psoriasi"],
            "consultation_fee": 100, "follow_up_fee": 70, "waiting_days": 10,
            "emergency": False, "home_visits": False, "telemedicine": False,
            "languages": ["Italiano", "Spagnolo"]
        },
        {
            "name": "Chiara", "surname": "Romano", "specialization": "Dermatologia", "experience": 14,
            "gender": "F", "age": 42, "city": "Bologna", "region": "Emilia-Romagna",
            "subspecializations": ["Dermatologia Pediatrica", "Tricologia"],
            "total_patients": 750, "success_rate": 94.8, "satisfaction": 4.7,
            "expertise": ["Dermatologia pediatrica", "Alopecia", "Medicina estetica"],
            "conditions": ["Dermatite atopica", "Alopecia", "Vitiligine", "Eczema"],
            "consultation_fee": 90, "follow_up_fee": 65, "waiting_days": 8,
            "emergency": False, "home_visits": False, "telemedicine": True,
            "languages": ["Italiano", "Inglese"]
        },

        # NEUROLOGIA
        {
            "name": "Anna", "surname": "Neri", "specialization": "Neurologia", "experience": 16,
            "gender": "F", "age": 50, "city": "Firenze", "region": "Toscana",
            "subspecializations": ["Neurologia Vascolare", "Cefalee"],
            "total_patients": 680, "success_rate": 93.5, "satisfaction": 4.6,
            "expertise": ["Ictus", "Emicrania", "Elettroencefalografia"],
            "conditions": ["Emicrania", "Epilessia", "Parkinson", "Sclerosi multipla"],
            "consultation_fee": 110, "follow_up_fee": 85, "waiting_days": 12,
            "emergency": True, "home_visits": False, "telemedicine": False,
            "languages": ["Italiano", "Inglese", "Tedesco"]
        },

        # PSICHIATRIA
        {
            "name": "Paolo", "surname": "Gialli", "specialization": "Psichiatria", "experience": 11,
            "gender": "M", "age": 43, "city": "Palermo", "region": "Sicilia",
            "subspecializations": ["Psichiatria dell'Adolescenza", "Disturbi dell'Umore"],
            "total_patients": 520, "success_rate": 89.5, "satisfaction": 4.4,
            "expertise": ["Terapia cognitivo-comportamentale", "Disturbi bipolari", "ADHD"],
            "conditions": ["Depressione", "Ansia", "Disturbi bipolari", "Disturbi alimentari"],
            "consultation_fee": 95, "follow_up_fee": 75, "waiting_days": 15,
            "emergency": False, "home_visits": False, "telemedicine": True,
            "languages": ["Italiano"]
        },

        # ORTOPEDIA
        {
            "name": "Giovanna", "surname": "Viola", "specialization": "Ortopedia", "experience": 13,
            "gender": "F", "age": 44, "city": "Venezia", "region": "Veneto",
            "subspecializations": ["Chirurgia della Mano", "Traumatologia Sportiva"],
            "total_patients": 890, "success_rate": 95.2, "satisfaction": 4.8,
            "expertise": ["Artroscopia", "Protesi articolari", "Chirurgia spinale"],
            "conditions": ["Fratture", "Artrosi", "Lesioni sportive", "Lombalgia"],
            "consultation_fee": 115, "follow_up_fee": 80, "waiting_days": 9,
            "emergency": True, "home_visits": False, "telemedicine": False,
            "languages": ["Italiano", "Inglese"]
        },

        # OCULISTICA
        {
            "name": "Marco", "surname": "Azzurri", "specialization": "Oculistica", "experience": 8,
            "gender": "M", "age": 36, "city": "Genova", "region": "Liguria",
            "subspecializations": ["Chirurgia Refrattiva", "Retina"],
            "total_patients": 450, "success_rate": 97.1, "satisfaction": 4.9,
            "expertise": ["Laser ad eccimeri", "Cataratta", "Glaucoma"],
            "conditions": ["Miopia", "Cataratta", "Glaucoma", "Retinopatia diabetica"],
            "consultation_fee": 105, "follow_up_fee": 70, "waiting_days": 6,
            "emergency": False, "home_visits": False, "telemedicine": False,
            "languages": ["Italiano", "Inglese"]
        },

        # ODONTOIATRIA
        {
            "name": "Francesca", "surname": "Marroni", "specialization": "Odontoiatria", "experience": 10,
            "gender": "F", "age": 39, "city": "Bari", "region": "Puglia",
            "subspecializations": ["Ortodonzia", "Implantologia"],
            "total_patients": 650, "success_rate": 96.8, "satisfaction": 4.7,
            "expertise": ["Apparecchi ortodontici", "Impianti dentali", "Endodonzia"],
            "conditions": ["Carie", "Malocclusioni", "Parodontite", "Edentulia"],
            "consultation_fee": 85, "follow_up_fee": 60, "waiting_days": 5,
            "emergency": True, "home_visits": False, "telemedicine": False,
            "languages": ["Italiano"]
        },

        # GINECOLOGIA
        {
            "name": "Luca", "surname": "Grigi", "specialization": "Ginecologia", "experience": 17,
            "gender": "M", "age": 51, "city": "Catania", "region": "Sicilia",
            "subspecializations": ["Ostetricia", "Oncologia Ginecologica"],
            "total_patients": 920, "success_rate": 94.9, "satisfaction": 4.6,
            "expertise": ["Gravidanza ad alto rischio", "Chirurgia laparoscopica", "Ecografia ostetrica"],
            "conditions": ["Gravidanza", "Fibromi uterini", "Endometriosi", "Menopausa"],
            "consultation_fee": 100, "follow_up_fee": 75, "waiting_days": 8,
            "emergency": True, "home_visits": False, "telemedicine": True,
            "languages": ["Italiano", "Inglese"]
        },

        # PEDIATRIA
        {
            "name": "Sofia", "surname": "Lilla", "specialization": "Pediatria", "experience": 19,
            "gender": "F", "age": 53, "city": "Verona", "region": "Veneto",
            "subspecializations": ["Neonatologia", "Allergologia Pediatrica"],
            "total_patients": 1100, "success_rate": 96.5, "satisfaction": 4.9,
            "expertise": ["Vaccinazioni", "Allergie pediatriche", "Sviluppo neuromotorio"],
            "conditions": ["Allergie alimentari", "Asma pediatrico", "Disturbi crescita", "Infezioni ricorrenti"],
            "consultation_fee": 90, "follow_up_fee": 65, "waiting_days": 4,
            "emergency": True, "home_visits": True, "telemedicine": True,
            "languages": ["Italiano", "Inglese"]
        },

        # MEDICI AGGIUNTIVI PER DIVERSE CITTÀ
        {
            "name": "Roberto", "surname": "Bruno", "specialization": "Cardiologia", "experience": 22,
            "gender": "M", "age": 58, "city": "Palermo", "region": "Sicilia",
            "subspecializations": ["Cardiologia Geriatrica"],
            "total_patients": 1350, "success_rate": 95.1, "satisfaction": 4.7,
            "expertise": ["Cardiologia geriatrica", "Scompenso cardiaco", "Ipertensione arteriosa"],
            "conditions": ["Scompenso cardiaco", "Fibrillazione atriale", "Cardiopatia ipertensiva"],
            "consultation_fee": 130, "follow_up_fee": 90, "waiting_days": 10,
            "emergency": True, "home_visits": True, "telemedicine": False,
            "languages": ["Italiano", "Francese"]
        },

        {
            "name": "Alessandra", "surname": "Costa", "specialization": "Medicina Generale", "experience": 25,
            "gender": "F", "age": 60, "city": "Cagliari", "region": "Sardegna",
            "subspecializations": ["Medicina Interna", "Diabetologia"],
            "total_patients": 1500, "success_rate": 93.8, "satisfaction": 4.8,
            "expertise": ["Diabetologia", "Medicina interna", "Terapia del dolore"],
            "conditions": ["Diabete mellito", "Tiroideopatie", "Malattie autoimmuni"],
            "consultation_fee": 85, "follow_up_fee": 65, "waiting_days": 2,
            "emergency": False, "home_visits": True, "telemedicine": True,
            "languages": ["Italiano", "Sardo"]
        },

        {
            "name": "Davide", "surname": "Mariani", "specialization": "Neurologia", "experience": 14,
            "gender": "M", "age": 46, "city": "Trieste", "region": "Friuli-Venezia Giulia",
            "subspecializations": ["Neurofisiologia", "Disturbi del Movimento"],
            "total_patients": 580, "success_rate": 92.7, "satisfaction": 4.5,
            "expertise": ["Elettromiografia", "Malattia di Parkinson", "Disturbi del sonno"],
            "conditions": ["Parkinson", "Tremore essenziale", "Neuropatie periferiche"],
            "consultation_fee": 115, "follow_up_fee": 85, "waiting_days": 11,
            "emergency": False, "home_visits": False, "telemedicine": True,
            "languages": ["Italiano", "Sloveno"]
        },

        {
            "name": "Valentina", "surname": "Ricci", "specialization": "Dermatologia", "experience": 7,
            "gender": "F", "age": 35, "city": "Padova", "region": "Veneto",
            "subspecializations": ["Dermatologia Estetica", "Laser Terapia"],
            "total_patients": 380, "success_rate": 95.8, "satisfaction": 4.6,
            "expertise": ["Medicina estetica", "Filler", "Botulino", "Peeling chimici"],
            "conditions": ["Acne", "Cicatrici", "Macchie cutanee", "Invecchiamento cutaneo"],
            "consultation_fee": 120, "follow_up_fee": 80, "waiting_days": 7,
            "emergency": False, "home_visits": False, "telemedicine": False,
            "languages": ["Italiano", "Inglese"]
        },

        {
            "name": "Antonio", "surname": "Esposito", "specialization": "Ortopedia", "experience": 18,
            "gender": "M", "age": 50, "city": "Napoli", "region": "Campania",
            "subspecializations": ["Chirurgia del Piede", "Protesica"],
            "total_patients": 1050, "success_rate": 94.3, "satisfaction": 4.4,
            "expertise": ["Protesi anca e ginocchio", "Chirurgia piede", "Artroscopia spalla"],
            "conditions": ["Coxartrosi", "Gonartrosi", "Alluce valgo", "Lesioni meniscali"],
            "consultation_fee": 110, "follow_up_fee": 80, "waiting_days": 12,
            "emergency": True, "home_visits": False, "telemedicine": False,
            "languages": ["Italiano"]
        }
    ]

    # Crea oggetti Doctor per ogni dottore nel database
    for doc_data in doctors_data:
        doctor = Doctor(
            name=doc_data["name"],
            surname=doc_data["surname"],
            specialization=doc_data["specialization"],
            experience_years=doc_data["experience"]
        )

        # Imposta informazioni personali
        doctor.set_personal_info(
            gender=doc_data["gender"],
            age=doc_data["age"],
            city=doc_data["city"],
            region=doc_data["region"]
        )

        # Aggiungi sottospezilaizzazioni
        for subspec in doc_data["subspecializations"]:
            doctor.add_subspecialization(subspec)

        # Imposta dati professionali
        doctor.set_professional_data(
            total_patients=doc_data["total_patients"],
            success_rate=doc_data["success_rate"],
            satisfaction=doc_data["satisfaction"]
        )

        # Aggiungi competenze specifiche
        for expertise in doc_data["expertise"]:
            doctor.add_expertise(expertise)

        # Aggiungi condizioni trattate
        for condition in doc_data["conditions"]:
            doctor.add_common_condition(condition)

        # Imposta tariffe
        doctor.set_fees(
            consultation=doc_data["consultation_fee"],
            follow_up=doc_data["follow_up_fee"]
        )

        # Imposta opzioni di servizio
        doctor.set_service_options(
            emergency=doc_data["emergency"],
            home_visits=doc_data["home_visits"],
            telemedicine=doc_data["telemedicine"]
        )

        # Imposta tempo di attesa
        doctor.set_waiting_time(doc_data["waiting_days"])

        # Aggiungi lingue
        for language in doc_data["languages"]:
            if language != "Italiano":  # Italiano è già default
                doctor.add_language(language)

        # Aggiungi informazioni di contatto
        email = f"{doc_data['name'].lower()}.{doc_data['surname'].lower()}@longeviva.it"
        doctor.set_contact_info(
            phone=f"+39 {random.randint(300, 399)} {random.randint(1000000, 9999999)}",
            email=email,
            office_address=f"Via della Salute {random.randint(1, 200)}, {doc_data['city']}",
            website="www.longeviva.it"
        )

        # Aggiungi alcune recensioni casuali
        for i in range(random.randint(5, 15)):
            rating = random.choices([3, 4, 5], weights=[10, 40, 50])[0]
            comments = [
                "Medico molto professionale",
                "Ottima esperienza",
                "Consigliato",
                "Molto competente",
                "Eccellente servizio",
                "Bravo dottore",
                "Tempi di attesa accettabili",
                "Staff cordiale",
                "Ambiente pulito e professionale"
            ]
            doctor.add_review(rating, random.choice(comments), f"Paziente {i + 1}")

        # Imposta range età tipico pazienti
        if doc_data["specialization"] == "Pediatria":
            doctor.typical_patient_age_range = "0-16"
        elif doc_data["specialization"] == "Ginecologia":
            doctor.typical_patient_age_range = "16-65"
        elif doc_data["specialization"] == "Geriatria":
            doctor.typical_patient_age_range = "65-100"
        else:
            doctor.typical_patient_age_range = "18-80"

        # Inizializza il calendario
        today = datetime.date.today()
        doctor.initialize_schedule(today.strftime('%Y-%m-%d'), days=30)

        doctors.append(doctor)

    print(
        f"Creati {len(doctors)} dottori specializzati in {len(set(d.specialization for d in doctors))} specializzazioni")
    return doctors

def get_doctors_by_specialization(doctors, specialization):
    """Restituisce tutti i dottori con una determinata specializzazione"""
    return [doc for doc in doctors if doc.get_specialization() == specialization]

def get_doctors_by_city(doctors, city):
    """Restituisce tutti i dottori in una determinata città"""
    return [doc for doc in doctors if doc.get_city() and doc.get_city().lower() == city.lower()]

def get_doctor_by_name(doctors, name, surname):
    """Cerca un dottore per nome e cognome"""
    for doctor in doctors:
        if (doctor.get_name().lower() == name.lower() and
                doctor.get_surname().lower() == surname.lower()):
            return doctor
    return None

def get_best_doctor_for_purpose(doctors, purpose, patient_city=None, patient_preferences=None):
    """
    Trova il dottore più adatto con priorità geografica
    """
    purpose_lower = purpose.lower()

    print(f"🔍 DEBUG: Cercando medico per '{purpose}' a {patient_city}")

    # Mappa parole chiave a specializzazioni (migliorata)
    keyword_to_specialization = {
        # Neurologia - per mal di testa
        "mal di testa": "Neurologia", "emicrania": "Neurologia", "cefalea": "Neurologia",
        "testa": "Neurologia", "neurologico": "Neurologia", "nervi": "Neurologia",

        # Cardiologia
        "cuore": "Cardiologia", "cardiaco": "Cardiologia", "pressione": "Cardiologia",
        "petto": "Cardiologia", "dolori al petto": "Cardiologia",

        # Psichiatria - per problemi del sonno, stress
        "dormire": "Psichiatria", "sonno": "Psichiatria", "insonnia": "Psichiatria",
        "stress": "Psichiatria", "ansia": "Psichiatria", "depressione": "Psichiatria",

        # Ortopedia - per dolori articolari
        "articolari": "Ortopedia", "ossa": "Ortopedia", "frattura": "Ortopedia",
        "schiena": "Ortopedia", "ginocchio": "Ortopedia",

        # Medicina Generale - per problemi alimentazione
        "alimentazione": "Medicina Generale", "digestione": "Medicina Generale",
        "controllo": "Medicina Generale", "generale": "Medicina Generale",

        # Altri
        "pelle": "Dermatologia", "acne": "Dermatologia",
        "occhi": "Oculistica", "vista": "Oculistica",
        "denti": "Odontoiatria", "dente": "Odontoiatria",
        "ginecologico": "Ginecologia", "gravidanza": "Ginecologia",
        "bambino": "Pediatria", "bambina": "Pediatria"
    }

    # 1. Determina la specializzazione più adatta
    selected_specialization = "Medicina Generale"  # Default
    for keyword, specialization in keyword_to_specialization.items():
        if keyword in purpose_lower:
            selected_specialization = specialization
            print(f"📋 Keyword '{keyword}' → {specialization}")
            break

    print(f"🎯 Specializzazione selezionata: {selected_specialization}")

    # 2. STRATEGIA DI MATCHING A CASCATA

    # STEP 1: Cerca specialisti nella stessa città
    if patient_city:
        same_city_doctors = [d for d in doctors if d.get_city() and d.get_city().lower() == patient_city.lower()]
        same_city_specialists = [d for d in same_city_doctors if d.get_specialization() == selected_specialization]

        print(f"🏙️ Medici a {patient_city}: {len(same_city_doctors)}")
        print(f"🎯 Specialisti {selected_specialization} a {patient_city}: {len(same_city_specialists)}")

        if same_city_specialists:
            best = max(same_city_specialists, key=lambda d: d.get_experience_years())
            print(f"✅ TROVATO: {best.get_full_name()} - {selected_specialization} a {patient_city}")
            return best, selected_specialization

    # STEP 2: Se non trova specialisti in città, cerca medici generali in città
    if patient_city:
        same_city_general = [d for d in same_city_doctors if d.get_specialization() == "Medicina Generale"]
        if same_city_general:
            best = max(same_city_general, key=lambda d: d.get_experience_years())
            print(f"✅ FALLBACK: {best.get_full_name()} - Medicina Generale a {patient_city}")
            return best, "Medicina Generale"

    # STEP 3: Se non trova nemmeno medici generali, cerca il miglior psichiatra in città
    # (per problemi come mal di testa + disturbi del sonno)
    if patient_city and "testa" in purpose_lower and "dormire" in purpose_lower:
        same_city_psych = [d for d in same_city_doctors if d.get_specialization() == "Psichiatria"]
        if same_city_psych:
            best = max(same_city_psych, key=lambda d: d.get_experience_years())
            print(f"✅ ALTERNATIVA: {best.get_full_name()} - Psichiatria a {patient_city}")
            return best, "Psichiatria"

    # STEP 4: Cerca qualsiasi medico nella stessa città
    if patient_city and same_city_doctors:
        # Priorità: Cardiologia > Medicina Generale > Altri
        priority_specs = ["Cardiologia", "Medicina Generale", "Psichiatria", "Neurologia"]
        for spec in priority_specs:
            candidates = [d for d in same_city_doctors if d.get_specialization() == spec]
            if candidates:
                best = max(candidates, key=lambda d: d.get_experience_years())
                print(f"✅ SCELTA PRAGMATICA: {best.get_full_name()} - {spec} a {patient_city}")
                return best, spec

        # Se non trova nemmeno quelli, prendi il primo disponibile
        best = max(same_city_doctors, key=lambda d: d.get_experience_years())
        print(f"✅ ULTIMA RISORSA: {best.get_full_name()} - {best.get_specialization()} a {patient_city}")
        return best, best.get_specialization()

    # STEP 5: Solo come ultima risorsa, cerca fuori città
    all_specialists = [d for d in doctors if d.get_specialization() == selected_specialization]
    if all_specialists:
        best = max(all_specialists, key=lambda d: d.get_experience_years())
        print(f"⚠️ FUORI CITTÀ: {best.get_full_name()} - {selected_specialization} a {best.get_city()}")
        return best, selected_specialization

    # STEP 6: Fallback finale - qualsiasi medico generale
    general_doctors = [d for d in doctors if d.get_specialization() == "Medicina Generale"]
    if general_doctors:
        best = max(general_doctors, key=lambda d: d.get_experience_years())
        print(f"❌ FALLBACK FINALE: {best.get_full_name()} - Medicina Generale")
        return best, "Medicina Generale"

    print("❌ ERRORE: Nessun medico trovato!")
    return None, selected_specialization

def find_doctors_near_patient(doctors, patient_city, specialization=None, max_results=5):
    """
    Trova medici vicini al paziente, con possibilità di filtrare per specializzazione
    """
    if not patient_city:
        return doctors[:max_results] if not specialization else get_doctors_by_specialization(doctors, specialization)[
                                                                :max_results]

    # Prima priorità: stessa città
    same_city = get_doctors_by_city(doctors, patient_city)
    if specialization:
        same_city = [d for d in same_city if d.get_specialization() == specialization]

    if len(same_city) >= max_results:
        return same_city[:max_results]

    # Seconda priorità: stessa regione (simulazione)
    region_doctors = []
    patient_region = get_region_by_city(patient_city)
    if patient_region:
        region_doctors = [d for d in doctors if
                          hasattr(d, 'region') and d.region == patient_region and d not in same_city]
        if specialization:
            region_doctors = [d for d in region_doctors if d.get_specialization() == specialization]

    # Combina risultati
    result = same_city + region_doctors
    return result[:max_results]

def get_region_by_city(city):
    """
    Mappa semplificata città -> regione
    In un'implementazione reale, si userebbe un database geografico
    """
    city_region_map = {
        "milano": "Lombardia", "roma": "Lazio", "napoli": "Campania",
        "torino": "Piemonte", "palermo": "Sicilia", "genova": "Liguria",
        "bologna": "Emilia-Romagna", "firenze": "Toscana", "bari": "Puglia",
        "catania": "Sicilia", "venezia": "Veneto", "verona": "Veneto",
        "padova": "Veneto", "trieste": "Friuli-Venezia Giulia",
        "cagliari": "Sardegna"
    }
    return city_region_map.get(city.lower())

def get_doctors_statistics(doctors):
    """
    Restituisce statistiche sui dottori nel database
    """
    if not doctors:
        return {}

    specializations = {}
    cities = {}
    avg_experience = 0

    for doctor in doctors:
        # Conta specializzazioni
        spec = doctor.get_specialization()
        specializations[spec] = specializations.get(spec, 0) + 1

        # Conta città
        city = doctor.get_city()
        if city:
            cities[city] = cities.get(city, 0) + 1

        # Somma esperienza
        if doctor.get_experience_years():
            avg_experience += doctor.get_experience_years()

    avg_experience = avg_experience / len(doctors) if doctors else 0

    return {
        "total_doctors": len(doctors),
        "specializations": dict(sorted(specializations.items(), key=lambda x: x[1], reverse=True)),
        "cities": dict(sorted(cities.items(), key=lambda x: x[1], reverse=True)),
        "average_experience": round(avg_experience, 1),
        "most_common_specialization": max(specializations.items(), key=lambda x: x[1])[0] if specializations else None
    }

def search_doctors_by_criteria(doctors, criteria):
    """
    Cerca medici in base a criteri multipli
    criteria: {
        'specialization': str,
        'city': str,
        'min_experience': int,
        'max_waiting_days': int,
        'languages': list,
        'services': list (emergency, home_visits, telemedicine)
    }
    """
    filtered_doctors = doctors[:]

    if criteria.get('specialization'):
        filtered_doctors = [d for d in filtered_doctors if d.get_specialization() == criteria['specialization']]

    if criteria.get('city'):
        filtered_doctors = [d for d in filtered_doctors if
                            d.get_city() and d.get_city().lower() == criteria['city'].lower()]

    if criteria.get('min_experience'):
        filtered_doctors = [d for d in filtered_doctors if
                            d.get_experience_years() and d.get_experience_years() >= criteria['min_experience']]

    if criteria.get('max_waiting_days'):
        filtered_doctors = [d for d in filtered_doctors if
                            hasattr(d, 'waiting_time_days') and d.waiting_time_days <= criteria['max_waiting_days']]

    if criteria.get('languages'):
        for language in criteria['languages']:
            filtered_doctors = [d for d in filtered_doctors if
                                hasattr(d, 'languages_spoken') and language in d.languages_spoken]

    if criteria.get('services'):
        for service in criteria['services']:
            if service == 'emergency':
                filtered_doctors = [d for d in filtered_doctors if
                                    hasattr(d, 'emergency_availability') and d.emergency_availability]
            elif service == 'home_visits':
                filtered_doctors = [d for d in filtered_doctors if hasattr(d, 'home_visits') and d.home_visits]
            elif service == 'telemedicine':
                filtered_doctors = [d for d in filtered_doctors if hasattr(d, 'telemedicine') and d.telemedicine]

    return filtered_doctors