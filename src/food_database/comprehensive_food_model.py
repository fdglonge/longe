#!/usr/bin/env python3
"""
Longeviva Food Database - Task 3.1: Modello Dati Alimento Completo
Implementa il modello dati completo per alimenti con tutti i metadati nutrizionali
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from enum import Enum
import json


class AllergenType(Enum):
    """Allergeni comuni secondo regolamento UE"""
    GLUTINE = "glutine"
    CROSTACEI = "crostacei"
    UOVA = "uova"
    PESCE = "pesce"
    ARACHIDI = "arachidi"
    SOIA = "soia"
    LATTE = "latte"
    FRUTTA_GUSCIO = "frutta_guscio"
    SEDANO = "sedano"
    SENAPE = "senape"
    SESAMO = "sesamo"
    SOLFITI = "solfiti"
    LUPINI = "lupini"
    MOLLUSCHI = "molluschi"


class FoodCategory(Enum):
    """Categorie principali alimenti"""
    CEREALI = "cereali"
    VERDURE = "verdure"
    FRUTTA = "frutta"
    LATTICINI = "latticini"
    CARNI = "carni"
    PESCI = "pesci"
    LEGUMI = "legumi"
    GRASSI_CONDIMENTI = "grassi_condimenti"
    DOLCI = "dolci"
    BEVANDE = "bevande"
    SPEZIE_AROMI = "spezie_aromi"
    ALTRO = "altro"


class FoodSubcategory(Enum):
    """Sottocategorie specifiche"""
    # Cereali
    PASTA = "pasta"
    RISO = "riso"
    PANE = "pane"
    CEREALI_COLAZIONE = "cereali_colazione"
    FARINE = "farine"

    # Verdure
    FOGLIE_VERDI = "foglie_verdi"
    RADICI_TUBERI = "radici_tuberi"
    FRUTTI_ORTAGGI = "frutti_ortaggi"
    BULBI = "bulbi"
    FUNGHI = "funghi"

    # Frutta
    AGRUMI = "agrumi"
    FRUTTI_BOSCO = "frutti_bosco"
    FRUTTA_ESOTICA = "frutta_esotica"
    FRUTTA_SECCA = "frutta_secca"

    # Carni
    CARNI_ROSSE = "carni_rosse"
    CARNI_BIANCHE = "carni_bianche"
    SALUMI = "salumi"

    # Pesci
    PESCE_MAGRO = "pesce_magro"
    PESCE_GRASSO = "pesce_grasso"
    FRUTTI_MARE = "frutti_mare"

    # Latticini
    LATTE = "latte"
    YOGURT = "yogurt"
    FORMAGGI_FRESCHI = "formaggi_freschi"
    FORMAGGI_STAGIONATI = "formaggi_stagionati"


@dataclass
class NutritionalValues:
    """Valori nutrizionali per 100g di prodotto"""
    # Macronutrienti (g)
    calories: float  # kcal
    proteins: float  # g
    carbohydrates: float  # g
    fats: float  # g
    fibers: Optional[float] = None  # g
    sugars: Optional[float] = None  # g
    saturated_fats: Optional[float] = None  # g
    salt: Optional[float] = None  # g
    water: Optional[float] = None  # g
    alcohol: Optional[float] = None  # g


@dataclass
class Micronutrients:
    """Micronutrienti per 100g"""
    # Vitamine (mg o μg)
    vitamin_a: Optional[float] = None  # μg
    vitamin_b1_thiamine: Optional[float] = None  # mg
    vitamin_b2_riboflavin: Optional[float] = None  # mg
    vitamin_b3_niacin: Optional[float] = None  # mg
    vitamin_b6: Optional[float] = None  # mg
    vitamin_b12: Optional[float] = None  # μg
    vitamin_c: Optional[float] = None  # mg
    vitamin_d: Optional[float] = None  # μg
    vitamin_e: Optional[float] = None  # mg
    vitamin_k: Optional[float] = None  # μg
    folate: Optional[float] = None  # μg

    # Minerali (mg o μg)
    calcium: Optional[float] = None  # mg
    iron: Optional[float] = None  # mg
    magnesium: Optional[float] = None  # mg
    phosphorus: Optional[float] = None  # mg
    potassium: Optional[float] = None  # mg
    sodium: Optional[float] = None  # mg
    zinc: Optional[float] = None  # mg
    selenium: Optional[float] = None  # μg
    iodine: Optional[float] = None  # μg


@dataclass
class PortionInfo:
    """Informazioni sulle porzioni"""
    standard_portion: float  # g
    portion_description: str  # es: "1 mela media", "1 fetta"
    household_measures: Dict[str, float] = field(default_factory=dict)  # es: {"cucchiaio": 15, "tazza": 240}


@dataclass
class SeasonalAvailability:
    """Disponibilità stagionale"""
    peak_months: List[int] = field(default_factory=list)  # 1-12
    available_months: List[int] = field(default_factory=list)  # 1-12
    origin_region: Optional[str] = None


@dataclass
class QualityGrades:
    """Indici di qualità nutrizionale"""
    glycemic_index: Optional[int] = None  # 0-100
    glycemic_load: Optional[float] = None
    inflammatory_index: Optional[float] = None  # DII score
    antioxidant_capacity: Optional[float] = None  # ORAC units
    protein_quality_score: Optional[float] = None  # PDCAAS


@dataclass
class ComprehensiveFood:
    """Modello dati completo alimento Longeviva Task 3.1"""

    # Identificazione base
    id: Optional[str] = None
    name: str = ""
    description: Optional[str] = None
    brand: Optional[str] = None

    # Categorizzazione
    category: FoodCategory = FoodCategory.ALTRO
    subcategory: Optional[FoodSubcategory] = None
    food_group: Optional[str] = None  # Gruppo personalizzato

    # Valori nutrizionali
    nutritional_values: NutritionalValues = field(default_factory=lambda: NutritionalValues(0, 0, 0, 0))
    micronutrients: Micronutrients = field(default_factory=Micronutrients)

    # Allergeni e intolleranze
    allergens: List[AllergenType] = field(default_factory=list)
    contains_traces: List[AllergenType] = field(default_factory=list)

    # Porzioni e utilizzo
    portion_info: PortionInfo = field(default_factory=lambda: PortionInfo(100, "100g"))
    seasonal_info: Optional[SeasonalAvailability] = None

    # Qualità nutrizionale
    quality_grades: QualityGrades = field(default_factory=QualityGrades)

    # Metadati
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    source: Optional[str] = None  # USDA, INRAN, etc.
    source_food_id: Optional[str] = None
    verified: bool = False

    # Varianti e preparazioni
    preparation_methods: List[str] = field(default_factory=list)  # ["crudo", "cotto", "al vapore"]
    preservation_methods: List[str] = field(default_factory=list)  # ["fresco", "congelato", "inscatolato"]

    # Sostenibilità e origine
    origin_country: Optional[str] = None
    organic: bool = False
    carbon_footprint: Optional[float] = None  # kg CO2 eq/kg

    @classmethod
    def from_basic_food(cls, name: str, calories: float, proteins: float,
                        fats: float, carbs: float, weight: int = 100,
                        brand: Optional[str] = None) -> 'ComprehensiveFood':
        """Crea da valori base (compatibilità retroattiva)"""
        nutritional_values = NutritionalValues(
            calories=calories * weight / 100,
            proteins=proteins * weight / 100,
            carbohydrates=carbs * weight / 100,
            fats=fats * weight / 100
        )

        portion_info = PortionInfo(
            standard_portion=weight,
            portion_description=f"{weight}g"
        )

        return cls(
            name=name,
            brand=brand,
            nutritional_values=nutritional_values,
            portion_info=portion_info
        )

    def to_firestore_document(self) -> Dict[str, Any]:
        """Converte in documento Firestore"""
        doc = {
            'name': self.name,
            'description': self.description,
            'brand': self.brand,
            'category': self.category.value,
            'subcategory': self.subcategory.value if self.subcategory else None,
            'food_group': self.food_group,

            # Valori nutrizionali (formato stringa per compatibilità Flutter)
            'calories': f"{self.nutritional_values.calories:.1f}kcal",
            'proteins': f"{self.nutritional_values.proteins:.1f}g",
            'carbohydrates': f"{self.nutritional_values.carbohydrates:.1f}g",
            'fats': f"{self.nutritional_values.fats:.1f}g",
            'weight': f"{self.portion_info.standard_portion:.0f}g",

            # Valori nutrizionali estesi (numerico per calcoli)
            'nutrition_per_100g': {
                'calories': self.nutritional_values.calories * 100 / self.portion_info.standard_portion,
                'proteins': self.nutritional_values.proteins * 100 / self.portion_info.standard_portion,
                'carbohydrates': self.nutritional_values.carbohydrates * 100 / self.portion_info.standard_portion,
                'fats': self.nutritional_values.fats * 100 / self.portion_info.standard_portion,
                'fibers': self.nutritional_values.fibers,
                'sugars': self.nutritional_values.sugars,
                'saturated_fats': self.nutritional_values.saturated_fats,
                'salt': self.nutritional_values.salt,
                'water': self.nutritional_values.water
            },

            # Micronutrienti
            'micronutrients': {
                # Vitamine
                'vitamins': {
                    'vitamin_a': self.micronutrients.vitamin_a,
                    'vitamin_b1': self.micronutrients.vitamin_b1_thiamine,
                    'vitamin_b2': self.micronutrients.vitamin_b2_riboflavin,
                    'vitamin_b3': self.micronutrients.vitamin_b3_niacin,
                    'vitamin_b6': self.micronutrients.vitamin_b6,
                    'vitamin_b12': self.micronutrients.vitamin_b12,
                    'vitamin_c': self.micronutrients.vitamin_c,
                    'vitamin_d': self.micronutrients.vitamin_d,
                    'vitamin_e': self.micronutrients.vitamin_e,
                    'vitamin_k': self.micronutrients.vitamin_k,
                    'folate': self.micronutrients.folate
                },
                # Minerali
                'minerals': {
                    'calcium': self.micronutrients.calcium,
                    'iron': self.micronutrients.iron,
                    'magnesium': self.micronutrients.magnesium,
                    'phosphorus': self.micronutrients.phosphorus,
                    'potassium': self.micronutrients.potassium,
                    'sodium': self.micronutrients.sodium,
                    'zinc': self.micronutrients.zinc,
                    'selenium': self.micronutrients.selenium,
                    'iodine': self.micronutrients.iodine
                }
            },

            # Allergeni
            'allergens': [allergen.value for allergen in self.allergens],
            'contains_traces': [allergen.value for allergen in self.contains_traces],

            # Porzioni
            'portion_info': {
                'standard_portion': self.portion_info.standard_portion,
                'description': self.portion_info.portion_description,
                'household_measures': self.portion_info.household_measures
            },

            # Qualità
            'quality_grades': {
                'glycemic_index': self.quality_grades.glycemic_index,
                'glycemic_load': self.quality_grades.glycemic_load,
                'inflammatory_index': self.quality_grades.inflammatory_index,
                'antioxidant_capacity': self.quality_grades.antioxidant_capacity,
                'protein_quality_score': self.quality_grades.protein_quality_score
            },

            # Stagionalità
            'seasonal_info': {
                'peak_months': self.seasonal_info.peak_months if self.seasonal_info else [],
                'available_months': self.seasonal_info.available_months if self.seasonal_info else [],
                'origin_region': self.seasonal_info.origin_region if self.seasonal_info else None
            } if self.seasonal_info else None,

            # Metadati
            'preparation_methods': self.preparation_methods,
            'preservation_methods': self.preservation_methods,
            'origin_country': self.origin_country,
            'organic': self.organic,
            'carbon_footprint': self.carbon_footprint,
            'verified': self.verified,
            'source': self.source,
            'source_food_id': self.source_food_id,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }

        # Rimuovi campi None per ottimizzare spazio
        return {k: v for k, v in doc.items() if v is not None}

    def to_firestore_fields(self) -> Dict[str, Any]:
        """Converte in formato REST API Firestore"""
        doc = self.to_firestore_document()

        def convert_value(value):
            """Converte valore in formato Firestore REST API"""
            if value is None:
                return {'nullValue': None}
            elif isinstance(value, bool):
                return {'booleanValue': value}
            elif isinstance(value, int):
                return {'integerValue': str(value)}
            elif isinstance(value, float):
                return {'doubleValue': value}
            elif isinstance(value, str):
                return {'stringValue': value}
            elif isinstance(value, list):
                return {'arrayValue': {'values': [convert_value(item) for item in value]}}
            elif isinstance(value, dict):
                return {'mapValue': {'fields': {k: convert_value(v) for k, v in value.items() if v is not None}}}
            elif isinstance(value, datetime):
                return {'timestampValue': value.isoformat() + 'Z'}
            else:
                return {'stringValue': str(value)}

        return {key: convert_value(value) for key, value in doc.items() if value is not None}


def create_comprehensive_food_database() -> List[ComprehensiveFood]:
    """Crea database completo con metadati nutrizionali"""
    foods = []

    # ESEMPIO: Pollo petto con dati completi
    pollo_petto = ComprehensiveFood(
        name="Pollo (petto senza pelle)",
        description="Petto di pollo domestico senza pelle, crudo",
        category=FoodCategory.CARNI,
        subcategory=FoodSubcategory.CARNI_BIANCHE,
        nutritional_values=NutritionalValues(
            calories=165,
            proteins=31.0,
            carbohydrates=0.0,
            fats=3.6,
            saturated_fats=1.0,
            fibers=0.0,
            sugars=0.0,
            salt=0.07,
            water=73.2
        ),
        micronutrients=Micronutrients(
            vitamin_b3_niacin=14.8,
            vitamin_b6=0.6,
            vitamin_b12=0.3,
            phosphorus=220,
            selenium=27.6,
            potassium=256,
            sodium=74
        ),
        allergens=[],
        portion_info=PortionInfo(
            standard_portion=100,
            portion_description="1 petto di pollo medio (150g)",
            household_measures={"petto medio": 150, "fetta": 25}
        ),
        quality_grades=QualityGrades(
            protein_quality_score=1.0,  # Proteine complete
            inflammatory_index=-2.5  # Anti-infiammatorio
        ),
        preparation_methods=["crudo", "grigliato", "al forno", "bollito"],
        source="INRAN",
        verified=True,
        organic=False
    )
    foods.append(pollo_petto)

    # ESEMPIO: Spinaci con dati completi
    spinaci = ComprehensiveFood(
        name="Spinaci freschi",
        description="Spinaci baby freschi crudi",
        category=FoodCategory.VERDURE,
        subcategory=FoodSubcategory.FOGLIE_VERDI,
        nutritional_values=NutritionalValues(
            calories=23,
            proteins=2.9,
            carbohydrates=3.6,
            fats=0.4,
            fibers=2.2,
            sugars=0.4,
            salt=0.02,
            water=91.4
        ),
        micronutrients=Micronutrients(
            vitamin_a=469,  # μg
            vitamin_c=28.1,
            vitamin_k=483,
            folate=194,
            iron=2.7,
            calcium=99,
            magnesium=79,
            potassium=558,
            sodium=79
        ),
        allergens=[],
        portion_info=PortionInfo(
            standard_portion=100,
            portion_description="1 porzione di contorno (80g)",
            household_measures={"tazza": 30, "manciata": 25}
        ),
        seasonal_info=SeasonalAvailability(
            peak_months=[10, 11, 12, 1, 2, 3],
            available_months=list(range(1, 13)),  # Tutto l'anno
            origin_region="Italia"
        ),
        quality_grades=QualityGrades(
            glycemic_index=15,  # Molto basso
            antioxidant_capacity=1515,  # ORAC
            inflammatory_index=-3.2  # Fortemente anti-infiammatorio
        ),
        preparation_methods=["crudo", "saltato", "bollito", "al vapore"],
        preservation_methods=["fresco", "surgelato"],
        source="USDA",
        verified=True,
        carbon_footprint=0.2  # kg CO2 eq/kg
    )
    foods.append(spinaci)

    # ESEMPIO: Pasta integrale
    pasta_integrale = ComprehensiveFood(
        name="Pasta di grano duro integrale",
        description="Pasta secca integrale di grano duro",
        brand="Barilla",
        category=FoodCategory.CEREALI,
        subcategory=FoodSubcategory.PASTA,
        nutritional_values=NutritionalValues(
            calories=348,
            proteins=13.4,
            carbohydrates=66.2,
            fats=2.9,
            fibers=9.2,
            sugars=3.2,
            saturated_fats=0.6,
            salt=0.01
        ),
        micronutrients=Micronutrients(
            vitamin_b1_thiamine=0.4,
            vitamin_b3_niacin=5.9,
            vitamin_e=1.4,
            iron=3.6,
            magnesium=143,
            phosphorus=258,
            potassium=312,
            zinc=2.9
        ),
        allergens=[AllergenType.GLUTINE],
        contains_traces=[AllergenType.UOVA, AllergenType.SOIA],
        portion_info=PortionInfo(
            standard_portion=80,
            portion_description="1 porzione standard pasta (80g)",
            household_measures={"porzione": 80, "piatto abbondante": 100}
        ),
        quality_grades=QualityGrades(
            glycemic_index=50,  # Medio-basso
            glycemic_load=25.0,
            protein_quality_score=0.7
        ),
        preparation_methods=["bollita", "al dente"],
        source="Barilla",
        verified=True,
        carbon_footprint=1.1
    )
    foods.append(pasta_integrale)

    # Aggiungi altri alimenti con dati semplificati ma struttura completa
    additional_foods = [
        # Frutta
        ComprehensiveFood.from_basic_food("Mela Gala", 52, 0.3, 0.2, 13.8),
        ComprehensiveFood.from_basic_food("Banana", 89, 1.1, 0.3, 22.8),

        # Latticini
        ComprehensiveFood.from_basic_food("Parmigiano Reggiano 24 mesi", 392, 35.8, 26.0, 0.0),

        # Legumi
        ComprehensiveFood.from_basic_food("Lenticchie rosse secche", 353, 25.8, 1.9, 51.1),

        # Pesci
        ComprehensiveFood.from_basic_food("Salmone atlantico", 208, 25.4, 12.4, 0.0)
    ]

    # Assegna categorie ai cibi aggiuntivi
    additional_foods[0].category = FoodCategory.FRUTTA
    additional_foods[0].seasonal_info = SeasonalAvailability(peak_months=[9, 10, 11],
                                                             available_months=list(range(1, 13)))

    additional_foods[1].category = FoodCategory.FRUTTA
    additional_foods[1].quality_grades.glycemic_index = 51

    additional_foods[2].category = FoodCategory.LATTICINI
    additional_foods[2].subcategory = FoodSubcategory.FORMAGGI_STAGIONATI
    additional_foods[2].allergens = [AllergenType.LATTE]

    additional_foods[3].category = FoodCategory.LEGUMI
    additional_foods[3].quality_grades.protein_quality_score = 0.8

    additional_foods[4].category = FoodCategory.PESCI
    additional_foods[4].subcategory = FoodSubcategory.PESCE_GRASSO
    additional_foods[4].micronutrients.vitamin_d = 11.0
    additional_foods[4].micronutrients.vitamin_b12 = 3.2

    foods.extend(additional_foods)

    return foods


# Test del modello
if __name__ == "__main__":
    foods = create_comprehensive_food_database()

    print("🥗 LONGEVIVA COMPREHENSIVE FOOD MODEL - Task 3.1")
    print("=" * 55)
    print(f"Generated {len(foods)} foods with complete nutritional data")

    # Mostra esempio di conversione Firestore
    example_food = foods[0]  # Pollo petto
    firestore_doc = example_food.to_firestore_document()

    print(f"\n📊 Example: {example_food.name}")
    print(f"Category: {example_food.category.value}")
    print(f"Proteins per 100g: {firestore_doc['nutrition_per_100g']['proteins']:.1f}g")
    print(f"Micronutrients: {len([v for v in firestore_doc['micronutrients']['vitamins'].values() if v])} vitamins")
    print(f"Quality verified: {example_food.verified}")