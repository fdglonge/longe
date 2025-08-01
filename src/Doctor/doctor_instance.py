class Doctor:
    """Classe Doctor per Longeviva basata sul datamodel Firebase"""

    def __init__(self, data=None):
        if data:
            # Inizializza da dati Firebase
            self.id = data.get('id')
            self.name = data.get('name', '')
            self.surname = data.get('surname', '')
            self.email = data.get('email')
            self.google_email = data.get('googleEmail')
            self.phone_number = data.get('phoneNumber')
            self.specialty = data.get('specialty', 'Medicina Generale')
            self.city_of_work = data.get('cityOfWork', 'Roma')
            self.address = data.get('address')
            self.place_of_work = data.get('placeOfWork', '')
            self.organization = data.get('organization', '')
            self.hourly_fees = data.get('hourlyFees', 0)
            self.languages_spoken = data.get('languagesSpoken', ['Italiano'])
            self.area_of_interest = data.get('areaOfInterest', '')
            self.is_doctor = data.get('isDoctor', True)
            self.is_active = data.get('isActive', True)
            self.is_alive = data.get('isAlive', True)
            self.role = data.get('role', 'DOCTOR')
            self.fiscal_code = data.get('fiscalCode')
            self.license_number = data.get('licenseNumber')
            self.vat_number = data.get('vatNumber')
            self.sex = data.get('sex', '')
            self.birthdate = data.get('birthdate')
            self.profile_picture_url = data.get('profilePictureUrl')
            self.signup_request_id = data.get('signupRequestId')
            self.signup_approval_date = data.get('signupApprovalDate')
            self.issuer = data.get('issuer', '')
            self.qualification_validity = data.get('qualificationValidity')
            self.organization_period_validity = data.get('organizationPeriodValidity')
            self.required_password_change = data.get('requiredPasswordChange', False)
            self.created_at = data.get('createdAt')
        else:
            # Inizializza con valori di default
            self.id = None
            self.name = ""
            self.surname = ""
            self.email = None
            self.google_email = None
            self.phone_number = None
            self.specialty = "Medicina Generale"
            self.city_of_work = "Roma"
            self.address = None
            self.place_of_work = ""
            self.organization = ""
            self.hourly_fees = 0
            self.languages_spoken = ['Italiano']
            self.area_of_interest = ""
            self.is_doctor = True
            self.is_active = True
            self.is_alive = True
            self.role = "DOCTOR"
            self.fiscal_code = None
            self.license_number = None
            self.vat_number = None
            self.sex = ""
            self.birthdate = None
            self.profile_picture_url = None
            self.signup_request_id = None
            self.signup_approval_date = None
            self.issuer = ""
            self.qualification_validity = None
            self.organization_period_validity = None
            self.required_password_change = False
            self.created_at = None

    def get_name(self):
        return self.name

    def get_surname(self):
        return self.surname

    def get_full_name(self):
        if self.name and self.surname:
            return f"Dr. {self.name} {self.surname}"
        elif self.name:
            return f"Dr. {self.name}"
        else:
            return "Dottore"

    def get_specialization(self):
        return self.specialty

    def get_city(self):
        return self.city_of_work

    def get_years_of_experience(self):
        # Calcolo approssimativo basato su data creazione o valore di default
        if self.created_at:
            try:
                from datetime import datetime
                if hasattr(self.created_at, 'year'):
                    years = datetime.now().year - self.created_at.year
                    return max(1, years)
            except:
                pass
        return 10  # Valore di default

    def get_address(self):
        return self.address or f"Via Roma 123, {self.city_of_work}"

    def get_phone(self):
        return self.phone_number

    def get_email(self):
        return self.email or self.google_email

    def get_place_of_work(self):
        return self.place_of_work

    def get_organization(self):
        return self.organization

    def get_hourly_fees(self):
        return self.hourly_fees

    def get_languages_spoken(self):
        return self.languages_spoken

    def get_area_of_interest(self):
        return self.area_of_interest

    def get_profile_picture_url(self):
        return self.profile_picture_url

    def is_active_doctor(self):
        return self.is_active and self.is_alive and self.is_doctor

    def set_contact_info(self, phone=None, email=None, office_address=None):
        if phone: self.phone_number = phone
        if email: self.email = email
        if office_address: self.address = office_address

    def set_clinic_info(self, clinic_name=None):
        if clinic_name: self.place_of_work = clinic_name

    def to_dict(self):
        """Converte in formato per Firebase"""
        return {
            'name': self.name,
            'surname': self.surname,
            'email': self.email,
            'googleEmail': self.google_email,
            'phoneNumber': self.phone_number,
            'specialty': self.specialty,
            'cityOfWork': self.city_of_work,
            'address': self.address,
            'placeOfWork': self.place_of_work,
            'organization': self.organization,
            'hourlyFees': self.hourly_fees,
            'languagesSpoken': self.languages_spoken,
            'areaOfInterest': self.area_of_interest,
            'isDoctor': self.is_doctor,
            'isActive': self.is_active,
            'isAlive': self.is_alive,
            'role': self.role,
            'fiscalCode': self.fiscal_code,
            'licenseNumber': self.license_number,
            'vatNumber': self.vat_number,
            'sex': self.sex,
            'birthdate': self.birthdate,
            'profilePictureUrl': self.profile_picture_url,
            'signupRequestId': self.signup_request_id,
            'signupApprovalDate': self.signup_approval_date,
            'issuer': self.issuer,
            'qualificationValidity': self.qualification_validity,
            'organizationPeriodValidity': self.organization_period_validity,
            'requiredPasswordChange': self.required_password_change
        }


def create_sample_doctors():
    """Crea medici di esempio con il formato corretto"""
    return [
        Doctor({
            'name': 'Mario',
            'surname': 'Rossi',
            'specialty': 'medicina generale',
            'cityOfWork': 'Roma',
            'address': 'Via del Corso 123, Roma',
            'phoneNumber': '06-12345678',
            'email': 'mario.rossi@clinic.it',
            'hourlyFees': 80,
            'isDoctor': True,
            'isActive': True,
            'isAlive': True,
            'role': 'DOCTOR',
            'languagesSpoken': ['Italiano'],
            'organization': 'Clinica Roma'
        }),
        Doctor({
            'name': 'Anna',
            'surname': 'Verdi',
            'specialty': 'cardiologia',
            'cityOfWork': 'Milano',
            'address': 'Via Brera 45, Milano',
            'phoneNumber': '02-87654321',
            'email': 'anna.verdi@cardio.it',
            'hourlyFees': 120,
            'isDoctor': True,
            'isActive': True,
            'isAlive': True,
            'role': 'DOCTOR',
            'languagesSpoken': ['Italiano', 'Inglese'],
            'organization': 'Ospedale San Raffaele'
        }),
        Doctor({
            'name': 'Luigi',
            'surname': 'Bianchi',
            'specialty': 'dermatologia',
            'cityOfWork': 'Napoli',
            'address': 'Via Toledo 78, Napoli',
            'phoneNumber': '081-45678901',
            'email': 'luigi.bianchi@derma.it',
            'hourlyFees': 90,
            'isDoctor': True,
            'isActive': True,
            'isAlive': True,
            'role': 'DOCTOR',
            'languagesSpoken': ['Italiano'],
            'organization': 'Studio Dermatologico Napoli'
        }),
        Doctor({
            'name': 'Sara',
            'surname': 'Neri',
            'specialty': 'neurologia',
            'cityOfWork': 'Torino',
            'address': 'Via Po 234, Torino',
            'phoneNumber': '011-23456789',
            'email': 'sara.neri@neuro.it',
            'hourlyFees': 110,
            'isDoctor': True,
            'isActive': True,
            'isAlive': True,
            'role': 'DOCTOR',
            'languagesSpoken': ['Italiano', 'Francese'],
            'organization': 'Neurologia Torino'
        }),
        Doctor({
            'name': 'Marco',
            'surname': 'Ferrari',
            'specialty': 'ortopedia',
            'cityOfWork': 'Firenze',
            'address': 'Via Uffizi 12, Firenze',
            'phoneNumber': '055-34567890',
            'email': 'marco.ferrari@ortho.it',
            'hourlyFees': 100,
            'isDoctor': True,
            'isActive': True,
            'isAlive': True,
            'role': 'DOCTOR',
            'languagesSpoken': ['Italiano'],
            'organization': 'Centro Ortopedico Firenze'
        })
    ]