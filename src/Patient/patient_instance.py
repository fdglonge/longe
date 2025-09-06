class Patient:
    """Classe Patient per Longeviva basata sul datamodel Firebase"""

    def __init__(self, data=None):
        if data:
            # Inizializza da dati Firebase
            self.id = data.get('id')
            self.name = data.get('name')
            self.surname = data.get('surname')
            self.email = data.get('email')
            self.sex = data.get('sex')
            self.height = data.get('height')
            self.weight = data.get('weight')
            self.fiscal_code = data.get('fiscalCode')
            self.birth_date = data.get('birthdate')
            self.allergies = data.get('allergies', [])
            self.lifestyle = data.get('lifeStyle', {
                'physicalActivityFrequency': '',
                'physicalActivityIntensity': '',
                'typeOfDiet': '',
                'alcoholFrequency': '',
                'hoursOfSleep': 0,
                'smokerFrequency': ''
            })
            self.additional_notes = data.get('additionalNotes', '')
            self.medical_history = data.get('medicalHistory', [])
            self.family_history = data.get('familyHistory', [])
            self.heart_rates = data.get('heartRates', [])
            self.body_temperatures = data.get('bodyTemperatures', [])
            self.blood_pressures = data.get('bloodPressures', [])
            self.created_at = data.get('createdAt')
        else:
            # Inizializza vuoto
            self.id = None
            self.name = None
            self.surname = None
            self.email = None
            self.sex = None
            self.height = None
            self.weight = None
            self.fiscal_code = None
            self.birth_date = None
            self.allergies = []
            self.lifestyle = {
                'physicalActivityFrequency': '',
                'physicalActivityIntensity': '',
                'typeOfDiet': '',
                'alcoholFrequency': '',
                'hoursOfSleep': 0,
                'smokerFrequency': ''
            }
            self.additional_notes = ''
            self.medical_history = []
            self.family_history = []
            self.heart_rates = []
            self.body_temperatures = []
            self.blood_pressures = []
            self.created_at = None

        # Campi aggiuntivi per conversazione
        self.purpose = None
        self.city = None
        self.contact_info = {}
        self.chronic_conditions = []

    # Metodi base
    def set_name(self, name):
        self.name = name

    def get_name(self):
        return self.name

    def set_surname(self, surname):
        self.surname = surname

    def get_surname(self):
        return self.surname

    def set_age(self, age):
        # Calcola birth_date se non esiste
        if not self.birth_date and age:
            from datetime import datetime
            birth_year = datetime.now().year - age
            self.birth_date = f"{birth_year}-01-01T00:00:00.000"

    def get_age(self):
        if self.birth_date:
            try:
                from datetime import datetime
                birth = datetime.strptime(self.birth_date.split('T')[0], '%Y-%m-%d')
                today = datetime.now()
                return today.year - birth.year - ((today.month, today.day) < (birth.month, birth.day))
            except:
                pass
        return None

    def set_sex(self, sex):
        self.sex = sex

    def get_sex(self):
        return self.sex

    def set_city(self, city):
        self.city = city

    def get_city(self):
        return self.city

    def set_purpose(self, purpose):
        self.purpose = purpose

    def get_purpose(self):
        return self.purpose

    def set_height(self, height):
        self.height = height

    def get_height(self):
        return self.height

    def set_weight(self, weight):
        self.weight = weight

    def get_weight(self):
        return self.weight

    def set_allergies(self, allergies):
        if isinstance(allergies, str):
            if allergies.lower() in ['nessuna', 'no', 'nessuno']:
                self.allergies = []
            else:
                self.allergies = [a.strip() for a in allergies.split(',')]
        else:
            self.allergies = allergies or []

    def get_allergies(self):
        """Restituisce le allergie come stringa"""
        if not self.allergies:
            return "Nessuna"

        # Handle different data formats
        allergy_strings = []
        for allergy in self.allergies:
            if isinstance(allergy, str):
                # Already a string
                allergy_strings.append(allergy)
            elif isinstance(allergy, dict):
                # Extract allergy name from dict structure
                # Common Firebase structures: {'name': 'allergy_name'} or {'allergy': 'name'}
                if 'name' in allergy:
                    allergy_strings.append(str(allergy['name']))
                elif 'allergy' in allergy:
                    allergy_strings.append(str(allergy['allergy']))
                elif 'allergen' in allergy:
                    allergy_strings.append(str(allergy['allergen']))
                else:
                    # Fallback: convert entire dict to string or take first value
                    values = [v for v in allergy.values() if isinstance(v, str)]
                    if values:
                        allergy_strings.append(values[0])
                    else:
                        allergy_strings.append(str(allergy))
            else:
                # Convert other types to string
                allergy_strings.append(str(allergy))

        return ", ".join(allergy_strings) if allergy_strings else "Nessuna"

    def set_contact_info(self, email=None, phone=None):
        if email:
            self.email = email
            self.contact_info['email'] = email
        if phone:
            self.contact_info['phone'] = phone

    def get_contact_info(self):
        info = self.contact_info.copy()
        if self.email:
            info['email'] = self.email
        return info

    def get_preferences(self):
        return {}

    def add_chronic_condition(self, condition):
        if condition not in self.chronic_conditions:
            self.chronic_conditions.append(condition)

    # Metodi per registrazione
    def set_birth_date(self, date):
        self.birth_date = date

    def get_birth_date(self):
        return self.birth_date

    def set_fiscal_code(self, fiscal_code):
        self.fiscal_code = fiscal_code

    def get_fiscal_code(self):
        return self.fiscal_code

    def set_additional_notes(self, notes):
        self.additional_notes = notes

    def get_additional_notes(self):
        return self.additional_notes

    def set_lifestyle(self, lifestyle):
        """Imposta i dati di lifestyle - VERSIONE CORRETTA"""
        if isinstance(lifestyle, dict):
            # ✅ CORREZIONE: Aggiorna il dizionario esistente invece di sostituirlo
            if not hasattr(self, 'lifestyle') or not self.lifestyle:
                self.lifestyle = {
                    'physicalActivityFrequency': '',
                    'physicalActivityIntensity': '',
                    'typeOfDiet': '',
                    'alcoholFrequency': '',
                    'hoursOfSleep': 0,
                    'smokerFrequency': ''
                }

            # Aggiorna solo i campi forniti
            for key, value in lifestyle.items():
                if key in self.lifestyle:
                    self.lifestyle[key] = value
                    print(f"🔧 DEBUG: Impostato {key} = {value}")

            print(f"🔧 DEBUG: Lifestyle finale: {self.lifestyle}")
        else:
            self.lifestyle = lifestyle

    def get_lifestyle(self):
        """Ottiene i dati di lifestyle"""
        return self.lifestyle

    def get_email(self):
        return self.email

    def get_phone(self):
        return self.contact_info.get('phone')

    def to_dict(self):
        """Converte in formato per Firebase - VERSIONE CORRETTA"""
        # ✅ ASSICURATI che lifestyle sia sempre presente e completo
        if not hasattr(self, 'lifestyle') or not self.lifestyle:
            self.lifestyle = {
                'physicalActivityFrequency': '',
                'physicalActivityIntensity': '',
                'typeOfDiet': '',
                'alcoholFrequency': '',
                'hoursOfSleep': 0,
                'smokerFrequency': ''
            }

        # ✅ VERIFICA che tutti i campi richiesti siano presenti
        required_lifestyle_fields = {
            'physicalActivityFrequency': '',
            'physicalActivityIntensity': '',
            'typeOfDiet': '',
            'alcoholFrequency': '',
            'hoursOfSleep': 0,
            'smokerFrequency': ''
        }

        for field, default_value in required_lifestyle_fields.items():
            if field not in self.lifestyle:
                self.lifestyle[field] = default_value

        result = {
            'name': self.name,
            'surname': self.surname,
            'email': self.email,
            'sex': self.sex,
            'height': self.height,
            'weight': self.weight,
            'fiscalCode': self.fiscal_code,
            'birthdate': self.birth_date,
            'allergies': self.allergies,
            'lifeStyle': self.lifestyle,  # ✅ IMPORTANTE: 'lifeStyle' (camelCase) per Firebase
            'additionalNotes': self.additional_notes,
            'medicalHistory': self.medical_history,
            'familyHistory': self.family_history,
            'heartRates': self.heart_rates,
            'bodyTemperatures': self.body_temperatures,
            'bloodPressures': self.blood_pressures
        }

        print(f"🔧 DEBUG to_dict: lifeStyle = {result['lifeStyle']}")
        return result

    # ✅ AGGIUNTO: Metodo helper per impostare singoli valori di lifestyle
    def set_lifestyle_field(self, field, value):
        """Imposta un singolo campo del lifestyle"""
        if not hasattr(self, 'lifestyle') or not self.lifestyle:
            self.lifestyle = {
                'physicalActivityFrequency': '',
                'physicalActivityIntensity': '',
                'typeOfDiet': '',
                'alcoholFrequency': '',
                'hoursOfSleep': 0,
                'smokerFrequency': ''
            }

        if field in self.lifestyle:
            self.lifestyle[field] = value
            print(f"🔧 DEBUG: Impostato lifestyle.{field} = {value}")
        else:
            print(f"⚠️ WARNING: Campo lifestyle '{field}' non riconosciuto")

    def set_smoking_frequency(self, frequency):
        self.set_lifestyle_field('smokerFrequency', frequency)

    def set_sleep_hours(self, hours):
        try:
            self.set_lifestyle_field('hoursOfSleep', float(hours))
        except:
            self.set_lifestyle_field('hoursOfSleep', 0)

    def set_physical_activity_frequency(self, frequency):
        self.set_lifestyle_field('physicalActivityFrequency', frequency)

    def set_physical_activity_intensity(self, intensity):
        self.set_lifestyle_field('physicalActivityIntensity', intensity)

    def set_alcohol_frequency(self, frequency):
        self.set_lifestyle_field('alcoholFrequency', frequency)

    def set_diet_type(self, diet_type):
        self.set_lifestyle_field('typeOfDiet', diet_type)

    def get_full_name(self):
        """Restituisce il nome completo del paziente"""
        if self.name and self.surname:
            return f"{self.name} {self.surname}"
        elif self.name:
            return self.name
        elif self.surname:
            return self.surname
        else:
            return "Nome non disponibile"

    def get_years_of_experience(self):
        """Metodo per compatibilità - non applicabile ai pazienti"""
        return 0

    def get_specialization(self):
        """Metodo per compatibilità - non applicabile ai pazienti"""
        return "Paziente"

    def get_address(self):
        """Restituisce l'indirizzo se disponibile"""
        if hasattr(self, 'address') and self.address:
            return self.address
        elif self.city:
            return self.city
        else:
            return "Indirizzo non disponibile"

    def get_phone_number(self):
        """Alias per get_phone()"""
        return self.get_phone()

    def __str__(self):
        """Rappresentazione stringa del paziente"""
        return f"Paziente: {self.get_full_name()}"

    def __repr__(self):
        """Rappresentazione per debug"""
        return f"Patient(name='{self.name}', surname='{self.surname}', email='{self.email}')"