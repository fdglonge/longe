# src/Patient/patient_extension.py
"""
Estensione della classe Patient esistente per supportare le nuove funzionalità di registrazione.
Aggiungi questi metodi alla tua classe Patient esistente.
"""


def extend_patient_class(PatientClass):
    """
    Estende una classe Patient esistente con i metodi necessari per la registrazione
    """

    # Metodi per il codice fiscale
    def get_fiscal_code(self):
        return getattr(self, 'fiscal_code', None)

    def set_fiscal_code(self, fiscal_code):
        self.fiscal_code = fiscal_code

    # Metodi per la data di nascita
    def get_birth_date(self):
        return getattr(self, 'birth_date', None)

    def set_birth_date(self, birth_date):
        self.birth_date = birth_date

    # Metodi per le note aggiuntive
    def get_additional_notes(self):
        return getattr(self, 'notes', '')

    def set_additional_notes(self, notes):
        self.notes = notes

    # Metodi per i dati lifestyle
    def get_lifestyle(self):
        return getattr(self, 'lifestyle', {})

    def set_lifestyle(self, lifestyle):
        self.lifestyle = lifestyle

    # Aggiungi i metodi alla classe
    PatientClass.get_fiscal_code = get_fiscal_code
    PatientClass.set_fiscal_code = set_fiscal_code
    PatientClass.get_birth_date = get_birth_date
    PatientClass.set_birth_date = set_birth_date
    PatientClass.get_additional_notes = get_additional_notes
    PatientClass.set_additional_notes = set_additional_notes
    PatientClass.get_lifestyle = get_lifestyle
    PatientClass.set_lifestyle = set_lifestyle

    return PatientClass


# Esempio di utilizzo:
"""
from Patient.patient_instance import Patient  # La tua classe esistente
from Patient.patient_extension import extend_patient_class

# Estendi la classe
Patient = extend_patient_class(Patient)

# Ora puoi usare i nuovi metodi
patient = Patient()
patient.set_fiscal_code("RSSMRA85M15H501Z")
patient.set_additional_notes("Note del paziente...")
"""


# Se vuoi creare una nuova classe Patient completa:
class ExtendedPatient:
    """
    Classe Patient estesa con tutti i metodi necessari per la registrazione
    """

    def __init__(self):
        # Dati base
        self.name = None
        self.surname = None
        self.age = None
        self.sex = None
        self.city = None
        self.purpose = None
        self.height = None
        self.weight = None
        self.allergies = None
        self.contact_info = {}
        self.chronic_conditions = []

        # Nuovi dati per registrazione
        self.fiscal_code = None
        self.birth_date = None
        self.notes = ""
        self.lifestyle = {}

    # Metodi esistenti
    def set_name(self, name):
        self.name = name

    def get_name(self):
        return self.name

    def set_surname(self, surname):
        self.surname = surname

    def get_surname(self):
        return self.surname

    def set_age(self, age):
        self.age = age

    def get_age(self):
        return self.age

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
        self.allergies = allergies

    def get_allergies(self):
        return self.allergies

    def set_contact_info(self, email=None, phone=None):
        if email:
            self.contact_info['email'] = email
        if phone:
            self.contact_info['phone'] = phone

    def get_contact_info(self):
        return self.contact_info

    def get_preferences(self):
        return {}

    def add_chronic_condition(self, condition):
        if condition not in self.chronic_conditions:
            self.chronic_conditions.append(condition)

    # Nuovi metodi per registrazione
    def get_fiscal_code(self):
        return self.fiscal_code

    def set_fiscal_code(self, fiscal_code):
        self.fiscal_code = fiscal_code

    def get_birth_date(self):
        return self.birth_date

    def set_birth_date(self, birth_date):
        self.birth_date = birth_date

    def get_additional_notes(self):
        return self.notes

    def set_additional_notes(self, notes):
        self.notes = notes

    def get_lifestyle(self):
        return self.lifestyle

    def set_lifestyle(self, lifestyle):
        self.lifestyle = lifestyle