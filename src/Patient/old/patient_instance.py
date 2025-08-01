
#Deprecated
class Patient:
    def __init__(self):
        # Dati anagrafici base
        self.name = None
        self.surname = None
        self.age = None
        self.sex = None
        self.height = None  # in cm
        self.weight = None  # in kg
        self.allergies = None
        self.bmi = None
        self.purpose = None

        # Nuovi dati demografici
        self.city = None
        self.address = None
        self.birth_date = None
        self.fiscal_code = None
        self.emergency_contact = None
        self.emergency_phone = None

        # Contatti
        self.phone = None
        self.email = None

        # Dati medici avanzati
        self.blood_type = None
        self.chronic_conditions = []
        self.current_medications = []
        self.family_medical_history = {}
        self.insurance_info = None
        self.preferred_language = "Italiano"

        # Storico visite e trattamenti
        self.visit_history = []  # Lista di appuntamenti passati
        self.upcoming_appointments = []  # Appuntamenti futuri
        self.medical_records = []  # Cartelle cliniche
        self.lab_results = []  # Risultati laboratorio

        # Preferenze
        self.preferred_doctor_gender = None  # M/F/Nessuna preferenza
        self.transportation_method = None  # Auto, pubblico, piedi
        self.max_travel_distance = None  # km massimi di viaggio

        # Dati per matching con medici
        self.severity_level = None  # Basso, Medio, Alto
        self.urgency = None  # Normale, Urgente, Emergenza
        self.previous_similar_cases = []

    # SETTER BASE
    def set_name(self, name):
        self.name = name.title() if name else None

    def set_surname(self, surname):
        self.surname = surname.title() if surname else None

    def set_age(self, age):
        try:
            self.age = int(age)
        except (ValueError, TypeError):
            print("Errore: età non valida")

    def set_sex(self, sex):
        if sex and sex.upper() in ['M', 'F']:
            self.sex = sex.upper()

    def set_height(self, height):
        try:
            cleaned_height_str = str(height).replace(',', '.')
            height_value = float(cleaned_height_str)

            if height_value > 3:
                self.height = height_value
            else:
                self.height = height_value * 100
        except (ValueError, TypeError):
            print("Errore: altezza non valida")

    def set_weight(self, weight):
        try:
            cleaned_weight_str = str(weight).replace(',', '.')
            self.weight = float(cleaned_weight_str)
        except (ValueError, TypeError):
            print("Errore: peso non valido")

    def set_allergies(self, allergies):
        if isinstance(allergies, str):
            self.allergies = allergies if allergies.lower() != "nessuna" else None
        else:
            self.allergies = allergies

    def set_purpose(self, purpose):
        self.purpose = purpose

    # SETTER AVANZATI
    def set_city(self, city):
        self.city = city.title() if city else None

    def set_address(self, address):
        self.address = address

    def set_birth_date(self, birth_date):
        self.birth_date = birth_date

    def set_fiscal_code(self, fiscal_code):
        self.fiscal_code = fiscal_code.upper() if fiscal_code else None

    def set_emergency_contact(self, name, phone):
        self.emergency_contact = name
        self.emergency_phone = phone

    def set_contact_info(self, email=None, phone=None):
        if email:
            self.email = email.lower()
        if phone:
            self.phone = phone

    def set_blood_type(self, blood_type):
        valid_types = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']
        if blood_type and blood_type.upper() in valid_types:
            self.blood_type = blood_type.upper()

    def add_chronic_condition(self, condition):
        if condition and condition not in self.chronic_conditions:
            self.chronic_conditions.append(condition)

    def add_medication(self, medication, dosage=None, frequency=None):
        med_info = {
            "name": medication,
            "dosage": dosage,
            "frequency": frequency,
            "start_date": None
        }
        self.current_medications.append(med_info)

    def set_family_history(self, relation, conditions):
        """relation: padre, madre, fratello, sorella, nonno, nonna, etc."""
        self.family_medical_history[relation] = conditions

    def set_preferences(self, doctor_gender=None, max_distance=None, transport=None):
        if doctor_gender:
            self.preferred_doctor_gender = doctor_gender
        if max_distance:
            self.max_travel_distance = max_distance
        if transport:
            self.transportation_method = transport

    def set_case_details(self, severity=None, urgency=None):
        """severity: Basso, Medio, Alto / urgency: Normale, Urgente, Emergenza"""
        if severity:
            self.severity_level = severity
        if urgency:
            self.urgency = urgency

    # METODI GESTIONE APPUNTAMENTI E STORICO
    def add_appointment(self, doctor, date, time, notes=None):
        """Aggiunge un appuntamento futuro"""
        appointment = {
            "doctor": doctor,
            "date": date,
            "time": time,
            "notes": notes,
            "status": "scheduled",
            "created_at": self._get_current_timestamp()
        }
        self.upcoming_appointments.append(appointment)
        return appointment

    def add_visit_to_history(self, doctor, date, diagnosis=None, treatment=None, notes=None):
        """Aggiunge una visita allo storico"""
        visit = {
            "doctor": doctor,
            "date": date,
            "diagnosis": diagnosis,
            "treatment": treatment,
            "notes": notes,
            "satisfaction_rating": None
        }
        self.visit_history.append(visit)
        return visit

    def add_medical_record(self, doctor, date, record_type, content):
        """Aggiunge una cartella clinica"""
        record = {
            "doctor": doctor,
            "date": date,
            "type": record_type,  # visita, esame, prescrizione, etc.
            "content": content,
            "id": len(self.medical_records) + 1
        }
        self.medical_records.append(record)
        return record

    def add_lab_result(self, test_name, result, reference_range, date, lab_name=None):
        """Aggiunge risultato di laboratorio"""
        lab_result = {
            "test_name": test_name,
            "result": result,
            "reference_range": reference_range,
            "date": date,
            "lab_name": lab_name,
            "status": "normal" if self._is_in_range(result, reference_range) else "abnormal"
        }
        self.lab_results.append(lab_result)
        return lab_result

    # GETTER
    def get_name(self):
        return self.name

    def get_surname(self):
        return self.surname

    def get_full_name(self):
        if self.name and self.surname:
            return f"{self.name} {self.surname}"
        return "Paziente senza nome"

    def get_age(self):
        return self.age

    def get_sex(self):
        return self.sex

    def get_height(self):
        return self.height

    def get_weight(self):
        return self.weight

    def get_allergies(self):
        return self.allergies

    def get_purpose(self):
        return self.purpose

    def get_city(self):
        return self.city

    def get_address(self):
        return self.address

    def get_contact_info(self):
        return {
            "email": self.email,
            "phone": self.phone
        }

    def get_emergency_contact(self):
        return {
            "name": self.emergency_contact,
            "phone": self.emergency_phone
        }

    def get_medical_info(self):
        return {
            "blood_type": self.blood_type,
            "chronic_conditions": self.chronic_conditions,
            "current_medications": self.current_medications,
            "allergies": self.allergies
        }

    def get_upcoming_appointments(self):
        return self.upcoming_appointments

    def get_visit_history(self):
        return self.visit_history

    def get_bmi(self):
        return self.calculate_bmi()

    def get_preferences(self):
        return {
            "preferred_doctor_gender": self.preferred_doctor_gender,
            "max_travel_distance": self.max_travel_distance,
            "transportation_method": self.transportation_method
        }

    # METODI DI CALCOLO E UTILITÀ
    def calculate_bmi(self):
        if self.height is None or self.weight is None:
            return None

        height_in_meters = self.height / 100

        if height_in_meters <= 0 or self.weight <= 0:
            return None

        bmi = self.weight / (height_in_meters ** 2)
        return round(bmi, 2)

    def get_bmi_category(self):
        bmi = self.get_bmi()
        if not bmi:
            return "Non calcolabile"

        if bmi < 18.5:
            return "Sottopeso"
        elif 18.5 <= bmi < 25:
            return "Normopeso"
        elif 25 <= bmi < 30:
            return "Sovrappeso"
        else:
            return "Obesità"

    def calculate_age_from_birth_date(self):
        """Calcola l'età dalla data di nascita"""
        if not self.birth_date:
            return None

        from datetime import date
        try:
            if isinstance(self.birth_date, str):
                birth = date.fromisoformat(self.birth_date)
            else:
                birth = self.birth_date

            today = date.today()
            age = today.year - birth.year - ((today.month, today.day) < (birth.month, birth.day))
            return age
        except:
            return None

    def get_risk_factors(self):
        """Restituisce fattori di rischio basati sui dati del paziente"""
        risk_factors = []

        bmi = self.get_bmi()
        if bmi:
            if bmi >= 30:
                risk_factors.append("Obesità")
            elif bmi >= 25:
                risk_factors.append("Sovrappeso")

        if self.age and self.age >= 65:
            risk_factors.append("Età avanzata")

        if self.chronic_conditions:
            risk_factors.extend([f"Condizione cronica: {cond}" for cond in self.chronic_conditions])

        if self.family_medical_history:
            risk_factors.append("Storia familiare di patologie")

        return risk_factors

    def get_compatibility_score_with_doctor(self, doctor):
        """Calcola un punteggio di compatibilità con un medico"""
        score = 0

        # Preferenza di genere del medico
        if self.preferred_doctor_gender and hasattr(doctor, 'gender'):
            if doctor.gender == self.preferred_doctor_gender:
                score += 10

        # Esperienza del medico con casi simili
        if hasattr(doctor, 'specialization_experience'):
            for condition in self.chronic_conditions:
                if condition.lower() in [spec.lower() for spec in doctor.specialization_experience]:
                    score += 15

        # Vicinanza geografica
        if self.city and hasattr(doctor, 'city'):
            if doctor.city == self.city:
                score += 20

        # Esperienza generale
        if hasattr(doctor, 'experience_years'):
            if doctor.experience_years >= 10:
                score += 5

        return score

    def get_profile_summary(self):
        """Restituisce un riassunto completo del profilo"""
        bmi_value = self.get_bmi()
        bmi_category = self.get_bmi_category()

        summary = f"""
╔══════════════════════════════════════════════════════════════╗
║                      PROFILO PAZIENTE                       ║
╠══════════════════════════════════════════════════════════════╣
║ DATI ANAGRAFICI                                              ║
║ Nome: {self.name} {self.surname}                                     
║ Età: {self.age} anni                                         
║ Sesso: {self.sex}                                            
║ Città: {self.city}                                           
║ Codice Fiscale: {self.fiscal_code or 'Non inserito'}        
║                                                              ║
║ DATI FISICI                                                  ║
║ Altezza: {self.height} cm                                    
║ Peso: {self.weight} kg                                       
║ BMI: {bmi_value} ({bmi_category})                            
║ Gruppo sanguigno: {self.blood_type or 'Non specificato'}    
║                                                              ║
║ CONTATTI                                                     ║
║ Telefono: {self.phone or 'Non inserito'}                    
║ Email: {self.email or 'Non inserita'}                       
║ Contatto emergenza: {self.emergency_contact or 'Non inserito'} 
║                                                              ║
║ INFORMAZIONI MEDICHE                                         ║
║ Allergie: {self.allergies or 'Nessuna'}                     
║ Condizioni croniche: {', '.join(self.chronic_conditions) if self.chronic_conditions else 'Nessuna'}
║ Motivo visita: {self.purpose or 'Non specificato'}          
║ Livello gravità: {self.severity_level or 'Non valutato'}    
║ Urgenza: {self.urgency or 'Normale'}                        
║                                                              ║
║ PREFERENZE                                                   ║
║ Genere medico: {self.preferred_doctor_gender or 'Nessuna preferenza'}
║ Distanza max: {self.max_travel_distance or 'Non specificata'} km
║ Trasporto: {self.transportation_method or 'Non specificato'}
╚══════════════════════════════════════════════════════════════╝
"""
        return summary

    def get_basic_info_dict(self):
        """Restituisce le informazioni base come dizionario per l'LLM"""
        return {
            "name": self.name,
            "surname": self.surname,
            "age": self.age,
            "sex": self.sex,
            "height": self.height,
            "weight": self.weight,
            "city": self.city,
            "phone": self.phone,
            "email": self.email,
            "allergies": self.allergies,
            "purpose": self.purpose,
            "chronic_conditions": self.chronic_conditions,
            "blood_type": self.blood_type
        }

    # --- Utils ---
    def _get_current_timestamp(self):
        from datetime import datetime
        return datetime.now().isoformat()

    def _is_in_range(self, value, reference_range):
        """Verifica se un valore è nel range di riferimento"""
        if not reference_range:
            return True

        try:
            # Esempio: "10-20" o "< 5" o "> 100"
            if "-" in reference_range:
                min_val, max_val = map(float, reference_range.split("-"))
                return min_val <= float(value) <= max_val
            elif "<" in reference_range:
                max_val = float(reference_range.replace("<", "").strip())
                return float(value) < max_val
            elif ">" in reference_range:
                min_val = float(reference_range.replace(">", "").strip())
                return float(value) > min_val
        except:
            pass

        return True

    def load_sample_data(self, patient_type="standard"):
        """Carica dati di esempio per testing"""
        if patient_type == "standard":
            self.set_name("Marco")
            self.set_surname("Bianchi")
            self.set_age(35)
            self.set_sex("M")
            self.set_height(175)
            self.set_weight(80)
            self.set_city("Milano")
            self.set_contact_info(email="marco.bianchi@email.com", phone="+39 333 1234567")
            self.set_allergies("Nessuna")
            self.set_blood_type("A+")
            self.add_chronic_condition("Ipertensione")
            self.set_purpose("Controllo pressione arteriosa")

        elif patient_type == "elderly":
            self.set_name("Giuseppe")
            self.set_surname("Verdi")
            self.set_age(72)
            self.set_sex("M")
            self.set_height(170)
            self.set_weight(75)
            self.set_city("Roma")
            self.set_contact_info(email="g.verdi@email.com", phone="+39 335 7654321")
            self.set_allergies("Penicillina")
            self.set_blood_type("O+")
            self.add_chronic_condition("Diabete tipo 2")
            self.add_chronic_condition("Artrite")
            self.set_purpose("Controllo diabete e dolori articolari")

        elif patient_type == "young":
            self.set_name("Sofia")
            self.set_surname("Rossi")
            self.set_age(24)
            self.set_sex("F")
            self.set_height(165)
            self.set_weight(58)
            self.set_city("Napoli")
            self.set_contact_info(email="sofia.rossi@email.com", phone="+39 340 9876543")
            self.set_allergies("Nessuna")
            self.set_blood_type("B+")
            self.set_purpose("Visita ginecologica di controllo")