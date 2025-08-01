# Deprecated
class Doctor:
    def __init__(self, name=None, surname=None, specialization=None, experience_years=None):
        # Dati base
        self.name = name
        self.surname = surname
        self.specialization = specialization
        self.experience_years = experience_years
        self.patients = []

        # Nuovi dati demografici e professionali
        self.gender = None  # M/F
        self.age = None
        self.city = None
        self.region = None
        self.languages_spoken = ["Italiano"]
        self.medical_license_number = None
        self.university = None
        self.graduation_year = None

        # Informazioni professionali avanzate
        self.subspecializations = []  # Sottospezilaizzazioni
        self.certifications = []  # Certificazioni aggiuntive
        self.research_interests = []  # Interessi di ricerca
        self.publications_count = 0
        self.awards = []

        # Esperienza e competenze
        self.total_patients_treated = 0
        self.years_in_current_position = 0
        self.previous_positions = []
        self.specific_expertise = []  # Competenze specifiche
        self.case_success_rate = 0.0  # Percentuale di successo
        self.patient_satisfaction_score = 0.0  # Punteggio soddisfazione (1-5)

        # Contatti
        self.phone = None
        self.email = None
        self.office_address = None
        self.website = None
        self.social_media = {}

        # Struttura e affiliazioni
        self.hospital_affiliations = []
        self.clinic_name = None
        self.department = None
        self.position_title = None  # Primario, Dirigente, Aiuto, etc.
        self.insurance_accepted = []

        # Orari e disponibilità
        self.schedule = {}
        self.working_hours = {
            "lunedì": {"start": "09:00", "end": "18:00"},
            "martedì": {"start": "09:00", "end": "18:00"},
            "mercoledì": {"start": "09:00", "end": "18:00"},
            "giovedì": {"start": "09:00", "end": "18:00"},
            "venerdì": {"start": "09:00", "end": "18:00"},
            "sabato": {"start": "09:00", "end": "13:00"},
            "domenica": None
        }

        # Costi e servizi
        self.consultation_fee = None
        self.follow_up_fee = None
        self.emergency_availability = False
        self.home_visits = False
        self.telemedicine = False

        # Dati di matching paziente
        self.typical_patient_age_range = None  # es. "20-65"
        self.gender_preference = None  # Se specializzato per un genere
        self.common_conditions_treated = []
        self.complex_cases_handled = []
        self.waiting_time_days = 0  # Giorni di attesa media

        # Valutazioni e feedback
        self.reviews = []
        self.avg_rating = 0.0
        self.total_reviews = 0

    # SETTER BASE
    def set_name(self, name):
        self.name = name

    def set_surname(self, surname):
        self.surname = surname

    def set_specialization(self, specialization):
        self.specialization = specialization

    def set_experience_years(self, years):
        self.experience_years = years

    def set_contact_info(self, phone=None, email=None, office_address=None, website=None):
        if phone:
            self.phone = phone
        if email:
            self.email = email
        if office_address:
            self.office_address = office_address
        if website:
            self.website = website

    # SETTER AVANZATI
    def set_personal_info(self, gender=None, age=None, city=None, region=None):
        if gender and gender.upper() in ['M', 'F']:
            self.gender = gender.upper()
        if age:
            self.age = age
        if city:
            self.city = city.title()
        if region:
            self.region = region.title()

    def set_education(self, university=None, graduation_year=None, license_number=None):
        if university:
            self.university = university
        if graduation_year:
            self.graduation_year = graduation_year
        if license_number:
            self.medical_license_number = license_number

    def add_subspecialization(self, subspecialization):
        if subspecialization and subspecialization not in self.subspecializations:
            self.subspecializations.append(subspecialization)

    def add_certification(self, certification, year_obtained=None):
        cert_info = {
            "name": certification,
            "year": year_obtained
        }
        self.certifications.append(cert_info)

    def add_language(self, language):
        if language and language not in self.languages_spoken:
            self.languages_spoken.append(language)

    def set_professional_data(self, total_patients=None, success_rate=None, satisfaction=None):
        if total_patients:
            self.total_patients_treated = total_patients
        if success_rate:
            self.case_success_rate = success_rate
        if satisfaction:
            self.patient_satisfaction_score = satisfaction

    def add_hospital_affiliation(self, hospital_name, department=None, position=None):
        affiliation = {
            "hospital": hospital_name,
            "department": department,
            "position": position
        }
        self.hospital_affiliations.append(affiliation)

    def set_clinic_info(self, clinic_name=None, department=None, position_title=None):
        if clinic_name:
            self.clinic_name = clinic_name
        if department:
            self.department = department
        if position_title:
            self.position_title = position_title

    def add_expertise(self, expertise_area):
        if expertise_area and expertise_area not in self.specific_expertise:
            self.specific_expertise.append(expertise_area)

    def add_common_condition(self, condition):
        if condition and condition not in self.common_conditions_treated:
            self.common_conditions_treated.append(condition)

    def set_fees(self, consultation=None, follow_up=None):
        if consultation:
            self.consultation_fee = consultation
        if follow_up:
            self.follow_up_fee = follow_up

    def set_service_options(self, emergency=None, home_visits=None, telemedicine=None):
        if emergency is not None:
            self.emergency_availability = emergency
        if home_visits is not None:
            self.home_visits = home_visits
        if telemedicine is not None:
            self.telemedicine = telemedicine

    def add_insurance(self, insurance_name):
        if insurance_name and insurance_name not in self.insurance_accepted:
            self.insurance_accepted.append(insurance_name)

    def set_waiting_time(self, days):
        self.waiting_time_days = days

    def add_review(self, rating, comment=None, patient_name=None, date=None):
        review = {
            "rating": rating,
            "comment": comment,
            "patient": patient_name,
            "date": date or self._get_current_date()
        }
        self.reviews.append(review)
        self._update_avg_rating()

    # GETTER
    def get_name(self):
        return self.name

    def get_surname(self):
        return self.surname

    def get_full_name(self):
        title = "Dott."
        if self.gender == "F":
            title = "Dott.ssa"
        return f"{title} {self.name} {self.surname}"

    def get_specialization(self):
        return self.specialization

    def get_experience_years(self):
        return self.experience_years

    def get_city(self):
        return self.city

    def get_contact_info(self):
        return {
            "phone": self.phone,
            "email": self.email,
            "office_address": self.office_address,
            "website": self.website
        }

    def get_professional_summary(self):
        subspecs = ", ".join(self.subspecializations) if self.subspecializations else "Nessuna"
        languages = ", ".join(self.languages_spoken)

        return {
            "specialization": self.specialization,
            "subspecializations": subspecs,
            "experience_years": self.experience_years,
            "total_patients": self.total_patients_treated,
            "success_rate": f"{self.case_success_rate}%",
            "satisfaction_score": f"{self.patient_satisfaction_score}/5.0",
            "languages": languages,
            "city": self.city,
            "waiting_time": f"{self.waiting_time_days} giorni"
        }

    def get_ratings_summary(self):
        return {
            "average_rating": self.avg_rating,
            "total_reviews": len(self.reviews),
            "latest_reviews": self.reviews[-3:] if self.reviews else []
        }

    def get_doctor_info(self):
        """Informazioni complete del medico"""
        subspecs = ", ".join(self.subspecializations) if self.subspecializations else "Nessuna"
        languages = ", ".join(self.languages_spoken)
        expertise = ", ".join(self.specific_expertise) if self.specific_expertise else "Generale"

        return f"""
╔══════════════════════════════════════════════════════════════╗
║                    PROFILO MEDICO                            ║
╠══════════════════════════════════════════════════════════════╣
║ {self.get_full_name()}                                       
║ Specializzazione: {self.specialization}                     
║ Sottospezilaizzazioni: {subspecs}                          
║ Esperienza: {self.experience_years} anni                    
║ Città: {self.city}                                          
║ Pazienti trattati: {self.total_patients_treated}            
║ Tasso di successo: {self.case_success_rate}%                
║ Soddisfazione: {self.patient_satisfaction_score}/5.0        
║                                                              ║
║ COMPETENZE SPECIFICHE                                        ║
║ Aree di expertise: {expertise}                              
║ Condizioni comuni: {', '.join(self.common_conditions_treated[:3]) if self.common_conditions_treated else 'Varie'}
║                                                              ║
║ CONTATTI E SERVIZI                                           ║
║ Telefono: {self.phone}                                      
║ Email: {self.email}                                         
║ Indirizzo: {self.office_address}                            
║ Emergenze: {'Sì' if self.emergency_availability else 'No'}  
║ Visite domiciliari: {'Sì' if self.home_visits else 'No'}    
║ Telemedicina: {'Sì' if self.telemedicine else 'No'}         
║                                                              ║
║ TARIFFE                                                      ║
║ Visita: {self.consultation_fee or 'Da concordare'}€         
║ Controllo: {self.follow_up_fee or 'Da concordare'}€         
║ Attesa media: {self.waiting_time_days} giorni               
║                                                              ║
║ VALUTAZIONI                                                  ║
║ Rating medio: {self.avg_rating}/5.0 ({len(self.reviews)} recensioni)
║ Lingue parlate: {languages}                                 
╚══════════════════════════════════════════════════════════════╝
"""

    def get_patients(self):
        return self.patients

    def get_compatibility_score_with_patient(self, patient):
        """Calcola compatibilità con un paziente specifico"""
        score = 0

        # Vicinanza geografica (peso alto)
        if patient.get_city() == self.city:
            score += 25
        elif patient.get_city() and self.city:
            # Se sono nella stessa regione ma città diverse
            score += 10

        # Esperienza generale
        if self.experience_years >= 15:
            score += 15
        elif self.experience_years >= 10:
            score += 10
        elif self.experience_years >= 5:
            score += 5

        # Specializzazione appropriata per il problema
        purpose = patient.get_purpose()
        if purpose and self.specialization:
            if any(keyword in purpose.lower() for keyword in self._get_specialization_keywords()):
                score += 20

        # Competenze specifiche per condizioni croniche del paziente
        patient_conditions = patient.chronic_conditions if hasattr(patient, 'chronic_conditions') else []
        for condition in patient_conditions:
            if condition.lower() in [c.lower() for c in self.common_conditions_treated]:
                score += 15

        # Esperienza con pazienti simili
        patient_age = patient.get_age()
        if patient_age and self.typical_patient_age_range:
            try:
                min_age, max_age = map(int, self.typical_patient_age_range.split("-"))
                if min_age <= patient_age <= max_age:
                    score += 10
            except:
                pass

        # Preferenze del paziente
        if hasattr(patient, 'preferred_doctor_gender') and patient.preferred_doctor_gender:
            if self.gender == patient.preferred_doctor_gender:
                score += 10

        # Servizi richiesti
        if hasattr(patient, 'urgency'):
            if patient.urgency == "Emergenza" and self.emergency_availability:
                score += 20
            elif patient.urgency == "Urgente" and self.waiting_time_days <= 3:
                score += 15

        # Soddisfazione e recensioni
        if self.patient_satisfaction_score >= 4.5:
            score += 10
        elif self.patient_satisfaction_score >= 4.0:
            score += 5

        # Lingue
        if hasattr(patient, 'preferred_language') and patient.preferred_language:
            if patient.preferred_language in self.languages_spoken:
                score += 5

        return min(score, 100)  # Massimo 100 punti

    def _get_specialization_keywords(self):
        """Restituisce parole chiave associate alla specializzazione"""
        keyword_map = {
            "Cardiologia": ["cuore", "cardiaco", "pressione", "ipertensione", "tachicardia"],
            "Dermatologia": ["pelle", "acne", "dermatite", "macchie", "nei"],
            "Neurologia": ["testa", "emicrania", "neurologico", "nervi", "cervello"],
            "Psichiatria": ["depressione", "ansia", "stress", "psicologico", "mentale"],
            "Ortopedia": ["ossa", "frattura", "articolazioni", "schiena", "ginocchio"],
            "Oculistica": ["occhi", "vista", "visione", "oculare"],
            "Odontoiatria": ["denti", "dente", "dentale", "gengive"],
            "Ginecologia": ["ginecologico", "mestruazioni", "gravidanza", "utero"],
            "Pediatria": ["bambino", "bambina", "pediatrico", "infantile"],
            "Medicina Generale": ["generale", "controllo", "check-up", "visita"]
        }
        return keyword_map.get(self.specialization, [])

    # METODI GESTIONE CALENDARIO (rimangono gli stessi del codice originale)
    def initialize_schedule(self, start_date, days=30, slot_duration=30):
        """Inizializza il calendario per un numero di giorni"""
        import datetime

        if isinstance(start_date, str):
            start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d').date()

        for day in range(days):
            current_date = start_date + datetime.timedelta(days=day)
            weekday = ["lunedì", "martedì", "mercoledì", "giovedì", "venerdì", "sabato", "domenica"][
                current_date.weekday()]

            if self.working_hours.get(weekday) is None:
                continue

            work_start = datetime.datetime.strptime(self.working_hours[weekday]["start"], "%H:%M").time()
            work_end = datetime.datetime.strptime(self.working_hours[weekday]["end"], "%H:%M").time()

            start_dt = datetime.datetime.combine(current_date, work_start)
            end_dt = datetime.datetime.combine(current_date, work_end)

            date_str = current_date.strftime('%Y-%m-%d')
            self.schedule[date_str] = []

            current_slot = start_dt
            while current_slot < end_dt:
                self.schedule[date_str].append({
                    "ora": current_slot.strftime('%H:%M'),
                    "disponibile": True
                })
                current_slot += datetime.timedelta(minutes=slot_duration)

    def get_available_slots(self, date):
        """Restituisce gli slot disponibili per una data specifica"""
        if date not in self.schedule:
            return []
        return [slot for slot in self.schedule[date] if slot["disponibile"]]

    def get_next_available_dates(self, count=3):
        """Restituisce le prossime date disponibili"""
        available_dates = []

        for date, slots in sorted(self.schedule.items()):
            available_slots = [slot for slot in slots if slot["disponibile"]]
            if available_slots:
                available_dates.append(date)
                if len(available_dates) >= count:
                    break

        return available_dates

    def book_appointment(self, date, time, patient=None):
        """Prenota un appuntamento"""
        if date not in self.schedule:
            return False, "Data non disponibile"

        for slot in self.schedule[date]:
            if slot["ora"] == time:
                if slot["disponibile"]:
                    slot["disponibile"] = False
                    slot["paziente"] = patient.get_full_name() if patient else "Paziente non specificato"

                    if patient:
                        patient.add_appointment(self, date, time)

                    return True, f"Appuntamento prenotato per il {date} alle {time}"
                else:
                    return False, f"Lo slot delle {time} non è disponibile"

        return False, "Orario non trovato"

    # METODI GESTIONE PAZIENTI
    def add_patient(self, patient):
        if patient not in self.patients:
            self.patients.append(patient)
            self.total_patients_treated += 1

    def get_patient_statistics(self):
        """Statistiche sui pazienti"""
        if not self.patients:
            return {}

        ages = [p.get_age() for p in self.patients if p.get_age()]
        avg_age = sum(ages) / len(ages) if ages else 0

        gender_count = {"M": 0, "F": 0}
        for patient in self.patients:
            gender = patient.get_sex()
            if gender in gender_count:
                gender_count[gender] += 1

        return {
            "total_patients": len(self.patients),
            "average_age": round(avg_age, 1),
            "gender_distribution": gender_count,
            "most_common_conditions": self._get_most_common_conditions()
        }

    def _get_most_common_conditions(self):
        """Trova le condizioni più comuni tra i pazienti"""
        conditions = {}
        for patient in self.patients:
            if hasattr(patient, 'chronic_conditions'):
                for condition in patient.chronic_conditions:
                    conditions[condition] = conditions.get(condition, 0) + 1

        return sorted(conditions.items(), key=lambda x: x[1], reverse=True)[:5]

    def _update_avg_rating(self):
        """Aggiorna il rating medio"""
        if self.reviews:
            total_rating = sum(review["rating"] for review in self.reviews)
            self.avg_rating = round(total_rating / len(self.reviews), 1)
        else:
            self.avg_rating = 0.0

    def _get_current_date(self):
        """Data corrente"""
        from datetime import date
        return date.today().isoformat()

    def load_sample_data(self, doctor_type="general"):
        """Carica dati di esempio per testing"""
        if doctor_type == "cardiologist":
            self.set_name("Laura")
            self.set_surname("Bianchi")
            self.set_specialization("Cardiologia")
            self.set_experience_years(12)
            self.set_personal_info(gender="F", age=45, city="Milano", region="Lombardia")
            self.add_subspecialization("Cardiologia Interventistica")
            self.add_subspecialization("Elettrofisiologia")
            self.set_professional_data(total_patients=850, success_rate=94.5, satisfaction=4.7)
            self.add_expertise("Angioplastica")
            self.add_expertise("Ablazione cardiaca")
            self.add_common_condition("Ipertensione")
            self.add_common_condition("Insufficienza cardiaca")
            self.add_common_condition("Aritmie")
            self.set_fees(consultation=120, follow_up=80)
            self.set_service_options(emergency=True, home_visits=False, telemedicine=True)
            self.set_waiting_time(7)

        elif doctor_type == "general":
            self.set_name("Mario")
            self.set_surname("Rossi")
            self.set_specialization("Medicina Generale")
            self.set_experience_years(18)
            self.set_personal_info(gender="M", age=52, city="Roma", region="Lazio")
            self.set_professional_data(total_patients=1200, success_rate=92.0, satisfaction=4.5)
            self.add_expertise("Medicina preventiva")
            self.add_expertise("Gestione cronicità")
            self.add_common_condition("Diabete")
            self.add_common_condition("Ipertensione")
            self.add_common_condition("Controlli periodici")
            self.set_fees(consultation=80, follow_up=60)
            self.set_service_options(emergency=False, home_visits=True, telemedicine=True)
            self.set_waiting_time(3)

        elif doctor_type == "dermatologist":
            self.set_name("Giuseppe")
            self.set_surname("Verdi")
            self.set_specialization("Dermatologia")
            self.set_experience_years(9)
            self.set_personal_info(gender="M", age=38, city="Napoli", region="Campania")
            self.add_subspecialization("Dermatologia Oncologica")
            self.set_professional_data(total_patients=600, success_rate=96.2, satisfaction=4.8)
            self.add_expertise("Chirurgia dermatologica")
            self.add_expertise("Mappatura nei")
            self.add_common_condition("Acne")
            self.add_common_condition("Dermatiti")
            self.add_common_condition("Nei e melanomi")
            self.set_fees(consultation=100, follow_up=70)
            self.set_service_options(emergency=False, home_visits=False, telemedicine=False)
            self.set_waiting_time(10)

        # Aggiungi contatti base
        email = f"{self.name.lower()}.{self.surname.lower()}@longeviva.it"
        self.set_contact_info(
            phone="+39 123 456 7890",
            email=email,
            office_address=f"Via della Salute 123, {self.city}",
            website="www.longeviva.it"
        )

        # Aggiungi alcune recensioni di esempio
        self.add_review(5, "Medico eccellente, molto professionale", "Paziente A")
        self.add_review(4, "Bravo medico, tempi di attesa accettabili", "Paziente B")
        self.add_review(5, "Altamente raccomandato", "Paziente C")