
#Deprecated
from Patient.patient_instance import Patient
import random
from datetime import date, timedelta


def create_sample_patients():
    """
    Crea pazienti di esempio con storico medico e relazioni con i dottori
    """
    patients = []

    # Database di pazienti realistici
    patients_data = [
        {
            "name": "Marco", "surname": "Bianchi", "age": 35, "sex": "M",
            "height": 175, "weight": 80, "city": "Milano",
            "phone": "+39 333 1234567", "email": "marco.bianchi@email.com",
            "allergies": "Nessuna", "blood_type": "A+",
            "chronic_conditions": ["Ipertensione"],
            "current_purpose": "Controllo pressione arteriosa",
            "medical_history": [
                {"condition": "Ipertensione", "diagnosed": "2020-03-15", "doctor": "Dr. Ferrari"},
                {"condition": "Check-up generale", "date": "2023-12-10", "doctor": "Dr. Rossi"}
            ],
            "family_history": {
                "padre": ["Ipertensione", "Diabete tipo 2"],
                "madre": ["Osteoporosi"]
            }
        },

        {
            "name": "Sofia", "surname": "Rossi", "age": 28, "sex": "F",
            "height": 165, "weight": 58, "city": "Roma",
            "phone": "+39 340 9876543", "email": "sofia.rossi@email.com",
            "allergies": "Polline, Nichel", "blood_type": "B+",
            "chronic_conditions": [],
            "current_purpose": "Visita ginecologica di controllo",
            "medical_history": [
                {"condition": "Dermatite da contatto", "diagnosed": "2022-05-20", "doctor": "Dr. Romano"},
                {"condition": "Controllo ginecologico", "date": "2023-08-15", "doctor": "Dr. Grigi"}
            ],
            "family_history": {
                "madre": ["Endometriosi"],
                "nonna_materna": ["Tumore al seno"]
            }
        },

        {
            "name": "Giuseppe", "surname": "Verdi", "age": 72, "sex": "M",
            "height": 170, "weight": 75, "city": "Napoli",
            "phone": "+39 335 7654321", "email": "g.verdi@email.com",
            "allergies": "Penicillina", "blood_type": "O+",
            "chronic_conditions": ["Diabete tipo 2", "Artrite", "Ipertensione"],
            "current_purpose": "Controllo diabete e dolori articolari",
            "medical_history": [
                {"condition": "Diabete tipo 2", "diagnosed": "2015-11-30", "doctor": "Dr. Costa"},
                {"condition": "Artrite reumatoide", "diagnosed": "2018-07-22", "doctor": "Dr. Viola"},
                {"condition": "Ipertensione", "diagnosed": "2010-03-08", "doctor": "Dr. Bianchi"}
            ],
            "family_history": {
                "padre": ["Diabete tipo 2", "Infarto"],
                "fratello": ["Diabete tipo 1"]
            }
        },

        {
            "name": "Valentina", "surname": "Conti", "age": 24, "sex": "F",
            "height": 162, "weight": 55, "city": "Torino",
            "phone": "+39 338 1122334", "email": "valentina.conti@email.com",
            "allergies": "Nessuna", "blood_type": "AB+",
            "chronic_conditions": ["Emicrania"],
            "current_purpose": "Forti mal di testa ricorrenti",
            "medical_history": [
                {"condition": "Emicrania", "diagnosed": "2021-09-12", "doctor": "Dr. Neri"},
                {"condition": "Ansia", "date": "2023-01-20", "doctor": "Dr. Gialli"}
            ],
            "family_history": {
                "madre": ["Emicrania", "Depressione"],
                "sorella": ["Disturbi alimentari"]
            }
        },

        {
            "name": "Roberto", "surname": "Bruno", "age": 45, "sex": "M",
            "height": 178, "weight": 85, "city": "Bologna",
            "phone": "+39 347 5566778", "email": "roberto.bruno@email.com",
            "allergies": "Aspirina", "blood_type": "A-",
            "chronic_conditions": ["Colesterolo alto"],
            "current_purpose": "Dolore al petto durante sforzi",
            "medical_history": [
                {"condition": "Ipercolesterolemia", "diagnosed": "2019-04-15", "doctor": "Dr. Bianchi"},
                {"condition": "Controllo cardiologico", "date": "2023-11-08", "doctor": "Dr. Ferrari"}
            ],
            "family_history": {
                "padre": ["Infarto miocardico", "Bypass coronarico"],
                "nonno_paterno": ["Scompenso cardiaco"]
            }
        },

        {
            "name": "Chiara", "surname": "Russo", "age": 33, "sex": "F",
            "height": 168, "weight": 62, "city": "Palermo",
            "phone": "+39 339 8877665", "email": "chiara.russo@email.com",
            "allergies": "Lattosio", "blood_type": "O-",
            "chronic_conditions": ["Ipotiroidismo"],
            "current_purpose": "Stanchezza cronica e aumento di peso",
            "medical_history": [
                {"condition": "Ipotiroidismo", "diagnosed": "2020-08-30", "doctor": "Dr. Costa"},
                {"condition": "Intolleranza lattosio", "diagnosed": "2018-02-14", "doctor": "Dr. Rossi"}
            ],
            "family_history": {
                "madre": ["Ipotiroidismo", "Osteoporosi"],
                "zia_materna": ["Tiroidite di Hashimoto"]
            }
        },

        {
            "name": "Alessandro", "surname": "Ricci", "age": 19, "sex": "M",
            "height": 182, "weight": 70, "city": "Firenze",
            "phone": "+39 345 4433221", "email": "alessandro.ricci@email.com",
            "allergies": "Nessuna", "blood_type": "B-",
            "chronic_conditions": [],
            "current_purpose": "Acne severa sul viso",
            "medical_history": [
                {"condition": "Acne", "diagnosed": "2022-10-05", "doctor": "Dr. Romano"}
            ],
            "family_history": {
                "padre": ["Psoriasi"],
                "fratello": ["Dermatite atopica"]
            }
        },

        {
            "name": "Elena", "surname": "Marino", "age": 41, "sex": "F",
            "height": 160, "weight": 68, "city": "Venezia",
            "phone": "+39 342 9988776", "email": "elena.marino@email.com",
            "allergies": "Glutine", "blood_type": "A+",
            "chronic_conditions": ["Celiachia", "Osteopenia"],
            "current_purpose": "Dolori alle ossa e stanchezza",
            "medical_history": [
                {"condition": "Celiachia", "diagnosed": "2017-06-20", "doctor": "Dr. Rossi"},
                {"condition": "Osteopenia", "diagnosed": "2022-03-15", "doctor": "Dr. Viola"}
            ],
            "family_history": {
                "madre": ["Celiachia", "Osteoporosi"],
                "sorella": ["Malattia di Crohn"]
            }
        },

        {
            "name": "Francesco", "surname": "Galli", "age": 58, "sex": "M",
            "height": 173, "weight": 90, "city": "Genova",
            "phone": "+39 336 7766554", "email": "francesco.galli@email.com",
            "allergies": "Iodio", "blood_type": "AB-",
            "chronic_conditions": ["Obesità", "Diabete tipo 2", "Apnee notturne"],
            "current_purpose": "Difficoltà respiratorie durante il sonno",
            "medical_history": [
                {"condition": "Diabete tipo 2", "diagnosed": "2019-01-20", "doctor": "Dr. Costa"},
                {"condition": "Obesità", "diagnosed": "2016-09-10", "doctor": "Dr. Rossi"},
                {"condition": "Apnee ostruttive", "diagnosed": "2023-05-30", "doctor": "Dr. Neri"}
            ],
            "family_history": {
                "padre": ["Obesità", "Infarto"],
                "madre": ["Diabete tipo 2"]
            }
        },

        {
            "name": "Giulia", "surname": "Ferrari", "age": 31, "sex": "F",
            "height": 170, "weight": 65, "city": "Verona",
            "phone": "+39 348 5544332", "email": "giulia.ferrari@email.com",
            "allergies": "Nessuna", "blood_type": "O+",
            "chronic_conditions": [],
            "current_purpose": "Pianificazione gravidanza",
            "medical_history": [
                {"condition": "Controllo preconcezionale", "date": "2023-10-15", "doctor": "Dr. Grigi"}
            ],
            "family_history": {
                "madre": ["Diabete gestazionale"],
                "nonna_materna": ["Ipertensione gravidica"]
            }
        }
    ]

    # Crea oggetti Patient per ogni paziente
    for patient_data in patients_data:
        patient = Patient()

        # Dati anagrafici di base
        patient.set_name(patient_data["name"])
        patient.set_surname(patient_data["surname"])
        patient.set_age(patient_data["age"])
        patient.set_sex(patient_data["sex"])
        patient.set_height(patient_data["height"])
        patient.set_weight(patient_data["weight"])
        patient.set_city(patient_data["city"])

        # Contatti
        patient.set_contact_info(
            email=patient_data["email"],
            phone=patient_data["phone"]
        )

        # Informazioni mediche
        patient.set_allergies(patient_data["allergies"])
        patient.set_blood_type(patient_data["blood_type"])
        patient.set_purpose(patient_data["current_purpose"])

        # Condizioni croniche
        for condition in patient_data["chronic_conditions"]:
            patient.add_chronic_condition(condition)

        # Storia familiare
        for relation, conditions in patient_data["family_history"].items():
            patient.set_family_history(relation, conditions)

        # Storia medica
        for record in patient_data["medical_history"]:
            if "diagnosed" in record:
                patient.add_visit_to_history(
                    doctor=record["doctor"],
                    date=record["diagnosed"],
                    diagnosis=record["condition"]
                )
            else:
                patient.add_visit_to_history(
                    doctor=record["doctor"],
                    date=record["date"],
                    diagnosis=record["condition"]
                )

        # Aggiungi alcuni risultati di laboratorio casuali
        add_sample_lab_results(patient)

        # Imposta preferenze casuali
        set_random_preferences(patient)

        patients.append(patient)

    print(f"📋 Creati {len(patients)} pazienti di esempio con storico medico completo")
    return patients


def add_sample_lab_results(patient):
    """Aggiunge risultati di laboratorio di esempio"""
    lab_tests = [
        {"name": "Glicemia", "result": random.randint(80, 120), "range": "70-110", "unit": "mg/dL"},
        {"name": "Colesterolo totale", "result": random.randint(150, 250), "range": "<200", "unit": "mg/dL"},
        {"name": "HDL", "result": random.randint(35, 80), "range": ">40", "unit": "mg/dL"},
        {"name": "LDL", "result": random.randint(70, 180), "range": "<130", "unit": "mg/dL"},
        {"name": "Trigliceridi", "result": random.randint(50, 200), "range": "<150", "unit": "mg/dL"},
        {"name": "Emoglobina", "result": round(random.uniform(12.0, 16.0), 1), "range": "12-16", "unit": "g/dL"},
        {"name": "Globuli bianchi", "result": random.randint(4000, 11000), "range": "4000-11000", "unit": "/μL"},
        {"name": "Creatinina", "result": round(random.uniform(0.6, 1.2), 1), "range": "0.6-1.2", "unit": "mg/dL"}
    ]

    # Aggiungi 3-5 test casuali
    selected_tests = random.sample(lab_tests, random.randint(3, 5))

    for test in selected_tests:
        # Data casuale negli ultimi 6 mesi
        test_date = date.today() - timedelta(days=random.randint(1, 180))

        patient.add_lab_result(
            test_name=test["name"],
            result=f"{test['result']} {test['unit']}",
            reference_range=f"{test['range']} {test['unit']}",
            date=test_date.isoformat(),
            lab_name="Laboratorio Longeviva"
        )


def set_random_preferences(patient):
    """Imposta preferenze casuali per il paziente"""
    # Preferenza genere medico (30% hanno una preferenza)
    if random.random() < 0.3:
        preferred_gender = random.choice(["M", "F"])
        patient.set_preferences(doctor_gender=preferred_gender)

    # Distanza massima di viaggio (km)
    max_distance = random.choice([10, 20, 30, 50])
    patient.set_preferences(max_distance=max_distance)

    # Mezzo di trasporto
    transport = random.choice(["Auto", "Mezzi pubblici", "A piedi", "Taxi"])
    patient.set_preferences(transport=transport)

    # Livello di gravità del problema attuale
    severity = random.choice(["Basso", "Medio", "Alto"])
    urgency = random.choice(["Normale", "Urgente"])
    if severity == "Alto":
        urgency = random.choice(["Urgente", "Emergenza"])

    patient.set_case_details(severity=severity, urgency=urgency)


def get_patient_by_name(patients, name, surname):
    """Trova un paziente per nome e cognome"""
    for patient in patients:
        if (patient.get_name().lower() == name.lower() and
                patient.get_surname().lower() == surname.lower()):
            return patient
    return None


def get_patients_by_city(patients, city):
    """Restituisce tutti i pazienti di una città"""
    return [p for p in patients if p.get_city() and p.get_city().lower() == city.lower()]


def get_patients_by_condition(patients, condition):
    """Restituisce pazienti con una specifica condizione cronica"""
    result = []
    for patient in patients:
        if hasattr(patient, 'chronic_conditions'):
            if any(condition.lower() in cond.lower() for cond in patient.chronic_conditions):
                result.append(patient)
    return result


def get_patients_statistics(patients):
    """Restituisce statistiche sui pazienti"""
    if not patients:
        return {}

    # Statistiche di base
    total_patients = len(patients)
    avg_age = sum(p.get_age() for p in patients if p.get_age()) / total_patients

    # Distribuzione per genere
    gender_count = {"M": 0, "F": 0}
    for patient in patients:
        gender = patient.get_sex()
        if gender in gender_count:
            gender_count[gender] += 1

    # Città più comuni
    cities = {}
    for patient in patients:
        city = patient.get_city()
        if city:
            cities[city] = cities.get(city, 0) + 1

    # Condizioni più comuni
    conditions = {}
    for patient in patients:
        if hasattr(patient, 'chronic_conditions'):
            for condition in patient.chronic_conditions:
                conditions[condition] = conditions.get(condition, 0) + 1

    # Gruppi sanguigni
    blood_types = {}
    for patient in patients:
        if hasattr(patient, 'blood_type') and patient.blood_type:
            blood_types[patient.blood_type] = blood_types.get(patient.blood_type, 0) + 1

    return {
        "total_patients": total_patients,
        "average_age": round(avg_age, 1),
        "gender_distribution": gender_count,
        "top_cities": dict(sorted(cities.items(), key=lambda x: x[1], reverse=True)[:5]),
        "common_conditions": dict(sorted(conditions.items(), key=lambda x: x[1], reverse=True)[:5]),
        "blood_type_distribution": dict(sorted(blood_types.items())),
        "age_groups": categorize_by_age(patients)
    }


def categorize_by_age(patients):
    """Categorizza pazienti per fasce d'età"""
    age_groups = {
        "0-17": 0,  # Pediatria
        "18-30": 0,  # Giovani adulti
        "31-50": 0,  # Adulti
        "51-65": 0,  # Mezza età
        "66+": 0  # Anziani
    }

    for patient in patients:
        age = patient.get_age()
        if age:
            if age <= 17:
                age_groups["0-17"] += 1
            elif age <= 30:
                age_groups["18-30"] += 1
            elif age <= 50:
                age_groups["31-50"] += 1
            elif age <= 65:
                age_groups["51-65"] += 1
            else:
                age_groups["66+"] += 1

    return age_groups


def create_patient_doctor_relationships(patients, doctors):
    """
    Crea relazioni realistiche tra pazienti e dottori basate su:
    - Prossimità geografica
    - Specializzazione necessaria
    - Storia medica del paziente
    """
    relationships = []

    for patient in patients:
        # Trova medici nella stessa città del paziente
        same_city_doctors = [d for d in doctors if d.get_city() == patient.get_city()]

        # Trova il medico di base (Medicina Generale)
        general_doctors = [d for d in same_city_doctors if d.get_specialization() == "Medicina Generale"]
        if general_doctors:
            primary_doctor = random.choice(general_doctors)
            relationships.append({
                "patient": patient,
                "doctor": primary_doctor,
                "relationship_type": "Medico di base",
                "since": "2020-01-01",
                "visits_count": random.randint(3, 10)
            })

            # Aggiungi il paziente al medico
            primary_doctor.add_patient(patient)

        # Trova specialisti per le condizioni croniche del paziente
        if hasattr(patient, 'chronic_conditions'):
            for condition in patient.chronic_conditions:
                specialist_type = map_condition_to_specialization(condition)
                if specialist_type:
                    specialists = [d for d in doctors if d.get_specialization() == specialist_type]
                    if specialists:
                        # Preferisci specialisti nella stessa città
                        same_city_specialists = [d for d in specialists if d.get_city() == patient.get_city()]
                        if same_city_specialists:
                            specialist = random.choice(same_city_specialists)
                        else:
                            specialist = random.choice(specialists)

                        relationships.append({
                            "patient": patient,
                            "doctor": specialist,
                            "relationship_type": f"Specialista per {condition}",
                            "since": "2021-06-01",
                            "visits_count": random.randint(2, 6)
                        })

                        specialist.add_patient(patient)

        # Per pazienti con problemi attuali, trova specialista appropriato
        if patient.get_purpose():
            from Doctor.doctors_list import get_best_doctor_for_purpose
            recommended_doctor, _ = get_best_doctor_for_purpose(
                doctors,
                patient.get_purpose(),
                patient.get_city()
            )

            if recommended_doctor and recommended_doctor not in [r["doctor"] for r in relationships if
                                                                 r["patient"] == patient]:
                relationships.append({
                    "patient": patient,
                    "doctor": recommended_doctor,
                    "relationship_type": "Consulto attuale",
                    "since": "2024-01-01",
                    "visits_count": 1
                })

                recommended_doctor.add_patient(patient)

    print(f"🔗 Create {len(relationships)} relazioni paziente-medico")
    return relationships


def map_condition_to_specialization(condition):
    """Mappa una condizione medica alla specializzazione appropriata"""
    condition_map = {
        "Ipertensione": "Cardiologia",
        "Diabete tipo 2": "Medicina Generale",  # O Endocrinologia
        "Diabete tipo 1": "Medicina Generale",
        "Artrite": "Ortopedia",
        "Emicrania": "Neurologia",
        "Depressione": "Psichiatria",
        "Ansia": "Psichiatria",
        "Colesterolo alto": "Cardiologia",
        "Ipotiroidismo": "Medicina Generale",  # O Endocrinologia
        "Celiachia": "Medicina Generale",
        "Obesità": "Medicina Generale",
        "Apnee notturne": "Neurologia",
        "Osteopenia": "Ortopedia",
        "Endometriosi": "Ginecologia"
    }

    return condition_map.get(condition)


def generate_sample_medical_records(patient, doctor, relationship_data):
    """Genera cartelle cliniche di esempio per una relazione paziente-medico"""
    records = []
    visits_count = relationship_data["visits_count"]

    for i in range(visits_count):
        # Data casuale basata sulla relazione
        days_ago = random.randint(30, 365 * 2)  # Ultimi 2 anni
        visit_date = (date.today() - timedelta(days=days_ago)).isoformat()

        # Tipo di visita
        visit_types = ["Visita di controllo", "Prima visita", "Visita urgente", "Follow-up"]
        visit_type = random.choice(visit_types)

        # Contenuto basato sulla specializzazione
        content = generate_visit_content(doctor.get_specialization(), patient)

        record = patient.add_medical_record(
            doctor=doctor.get_full_name(),
            date=visit_date,
            record_type=visit_type,
            content=content
        )

        records.append(record)

    return records


def generate_visit_content(specialization, patient):
    """Genera contenuto realistico per una visita medica"""
    base_content = f"Paziente: {patient.get_full_name()}, {patient.get_age()} anni\n"

    if specialization == "Medicina Generale":
        content = base_content + """
Anamnesi: Controllo periodico di routine
Esame obiettivo: Condizioni generali buone
Parametri vitali: PA 120/80 mmHg, FC 72 bpm
Peso: {}kg, Altezza: {}cm, BMI: {:.1f}
Terapia: Continua terapia in corso
Controllo: 6 mesi
        """.format(
            patient.get_weight() or "?",
            patient.get_height() or "?",
            patient.get_bmi() or 0
        )

    elif specialization == "Cardiologia":
        content = base_content + """
Anamnesi: Controllo cardiologico
ECG: Ritmo sinusale regolare
Ecocardiogramma: Funzione sistolica conservata
PA: 130/85 mmHg
Raccomandazioni: Dieta iposodica, attività fisica moderata
Prossimo controllo: 6 mesi
        """

    elif specialization == "Dermatologia":
        content = base_content + """
Anamnesi: Controllo dermatologico
Esame obiettivo: Cute e annessi nella norma
Dermatoscopia: Nevi stabili
Raccomandazioni: Protezione solare, autoesame
Controllo: 12 mesi
        """

    else:
        content = base_content + f"""
Anamnesi: Visita specialistica {specialization.lower()}
Esame obiettivo: Nella norma per la specialità
Diagnosi: In fase di valutazione
Terapia: Da definire
Controllo: Da programmare
        """

    return content.strip()


def export_patients_summary(patients, filename="patients_summary.txt"):
    """Esporta un riassunto dei pazienti in un file"""
    stats = get_patients_statistics(patients)

    with open(filename, 'w', encoding='utf-8') as f:
        f.write("RIASSUNTO PAZIENTI LONGEVIVA\n")
        f.write("=" * 50 + "\n\n")

        f.write(f"Totale pazienti: {stats['total_patients']}\n")
        f.write(f"Età media: {stats['average_age']} anni\n")
        f.write(
            f"Distribuzione genere: M={stats['gender_distribution']['M']}, F={stats['gender_distribution']['F']}\n\n")

        f.write("PAZIENTI PER CITTÀ:\n")
        for city, count in stats['top_cities'].items():
            f.write(f"  {city}: {count} pazienti\n")
        f.write("\n")

        f.write("CONDIZIONI PIÙ COMUNI:\n")
        for condition, count in stats['common_conditions'].items():
            f.write(f"  {condition}: {count} pazienti\n")
        f.write("\n")

        f.write("DETTAGLIO PAZIENTI:\n")
        f.write("-" * 30 + "\n")

        for patient in patients:
            f.write(f"\n{patient.get_full_name()}\n")
            f.write(f"  Età: {patient.get_age()}, Sesso: {patient.get_sex()}\n")
            f.write(f"  Città: {patient.get_city()}\n")
            f.write(f"  Problema attuale: {patient.get_purpose()}\n")

            if hasattr(patient, 'chronic_conditions') and patient.chronic_conditions:
                f.write(f"  Condizioni croniche: {', '.join(patient.chronic_conditions)}\n")

            if patient.get_allergies() and patient.get_allergies() != "Nessuna":
                f.write(f"  Allergie: {patient.get_allergies()}\n")

            f.write("  " + "-" * 25 + "\n")

    print(f"📄 Riassunto pazienti esportato in: {filename}")


# Funzione di test
def test_sample_patients():
    """Testa la creazione dei pazienti di esempio"""
    print("🧪 Test creazione pazienti di esempio...")

    patients = create_sample_patients()

    print(f"✅ Creati {len(patients)} pazienti")

    # Test alcune funzionalità
    stats = get_patients_statistics(patients)
    print(f"📊 Statistiche: {stats['total_patients']} pazienti, età media {stats['average_age']} anni")

    # Test ricerca per città
    milan_patients = get_patients_by_city(patients, "Milano")
    print(f"🏙️ Pazienti a Milano: {len(milan_patients)}")

    # Test ricerca per condizione
    diabetes_patients = get_patients_by_condition(patients, "Diabete")
    print(f"💊 Pazienti con diabete: {len(diabetes_patients)}")

    print("✅ Test completati con successo!")

    return patients


if __name__ == "__main__":
    test_sample_patients()