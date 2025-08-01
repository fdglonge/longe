# Test rapido - crea un file test_palermo.py
from src.Doctor.old.doctors_list import create_sample_doctors, get_doctors_by_city

doctors = create_sample_doctors()
palermo_doctors = get_doctors_by_city(doctors, "Palermo")

print(f"Medici a Palermo: {len(palermo_doctors)}")
for doc in palermo_doctors:
    print(f"- {doc.get_full_name()} - {doc.get_specialization()}")