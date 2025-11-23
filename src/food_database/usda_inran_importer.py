#!/usr/bin/env python3
"""
Longeviva Food Database - USDA/INRAN Data Importer
Task 3.1: Import automatizzato da fonti autorevoli
"""

import requests
import json
import csv
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import time
import os

from comprehensive_food_model import (
    ComprehensiveFood, NutritionalValues, Micronutrients,
    PortionInfo, FoodCategory, FoodSubcategory, AllergenType,
    QualityGrades, SeasonalAvailability
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class USDAFoodDataImporter:
    """Importatore dati USDA Food Data Central API"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or "YOUR_USDA_API_KEY"  # Registrati su https://fdc.nal.usda.gov/api-key-signup.html
        self.base_url = "https://api.nal.usda.gov/fdc/v1"
        self.session = requests.Session()

    def search_foods(self, query: str, page_size: int = 25) -> List[Dict]:
        """Cerca alimenti nel database USDA"""
        url = f"{self.base_url}/foods/search"
        params = {
            'api_key': self.api_key,
            'query': query,
            'pageSize': page_size,
            'dataType': ['Foundation', 'SR Legacy'],
            'sortBy': 'relevance'
        }

        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            return data.get('foods', [])
        except Exception as e:
            logger.error(f"USDA search failed for '{query}': {e}")
            return []

    def get_food_details(self, fdc_id: str) -> Optional[Dict]:
        """Ottieni dettagli completi alimento"""
        url = f"{self.base_url}/food/{fdc_id}"
        params = {
            'api_key': self.api_key,
            'format': 'full'
        }

        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"USDA detail fetch failed for {fdc_id}: {e}")
            return None

    def convert_usda_to_comprehensive_food(self, usda_data: Dict) -> Optional[ComprehensiveFood]:
        """Converte dati USDA in ComprehensiveFood"""
        try:
            name = usda_data.get('description', 'Unknown')

            # Estrai valori nutrizionali
            nutrients = {}
            for nutrient in usda_data.get('foodNutrients', []):
                nutrient_name = nutrient.get('nutrient', {}).get('name', '')
                nutrient_number = nutrient.get('nutrient', {}).get('number', '')
                value = nutrient.get('amount', 0)

                # Mappa nutrienti USDA ai nostri campi
                if nutrient_number == '208':  # Energy
                    nutrients['calories'] = value
                elif nutrient_number == '203':  # Protein
                    nutrients['proteins'] = value
                elif nutrient_number == '205':  # Carbohydrate
                    nutrients['carbohydrates'] = value
                elif nutrient_number == '204':  # Total fat
                    nutrients['fats'] = value
                elif nutrient_number == '291':  # Fiber
                    nutrients['fibers'] = value
                elif nutrient_number == '269':  # Sugars
                    nutrients['sugars'] = value
                elif nutrient_number == '606':  # Saturated fat
                    nutrients['saturated_fats'] = value
                elif nutrient_number == '307':  # Sodium
                    nutrients['sodium'] = value / 1000  # Convert mg to g
                elif nutrient_number == '255':  # Water
                    nutrients['water'] = value

                # Vitamine
                elif nutrient_number == '318':  # Vitamin A
                    nutrients['vitamin_a'] = value
                elif nutrient_number == '404':  # Thiamin
                    nutrients['vitamin_b1'] = value
                elif nutrient_number == '405':  # Riboflavin
                    nutrients['vitamin_b2'] = value
                elif nutrient_number == '406':  # Niacin
                    nutrients['vitamin_b3'] = value
                elif nutrient_number == '415':  # Vitamin B6
                    nutrients['vitamin_b6'] = value
                elif nutrient_number == '418':  # Vitamin B12
                    nutrients['vitamin_b12'] = value
                elif nutrient_number == '401':  # Vitamin C
                    nutrients['vitamin_c'] = value
                elif nutrient_number == '328':  # Vitamin D
                    nutrients['vitamin_d'] = value
                elif nutrient_number == '323':  # Vitamin E
                    nutrients['vitamin_e'] = value
                elif nutrient_number == '430':  # Vitamin K
                    nutrients['vitamin_k'] = value
                elif nutrient_number == '417':  # Folate
                    nutrients['folate'] = value

                # Minerali
                elif nutrient_number == '301':  # Calcium
                    nutrients['calcium'] = value
                elif nutrient_number == '303':  # Iron
                    nutrients['iron'] = value
                elif nutrient_number == '304':  # Magnesium
                    nutrients['magnesium'] = value
                elif nutrient_number == '305':  # Phosphorus
                    nutrients['phosphorus'] = value
                elif nutrient_number == '306':  # Potassium
                    nutrients['potassium'] = value
                elif nutrient_number == '309':  # Zinc
                    nutrients['zinc'] = value
                elif nutrient_number == '317':  # Selenium
                    nutrients['selenium'] = value

            # Crea oggetti nutrizionali
            nutritional_values = NutritionalValues(
                calories=nutrients.get('calories', 0),
                proteins=nutrients.get('proteins', 0),
                carbohydrates=nutrients.get('carbohydrates', 0),
                fats=nutrients.get('fats', 0),
                fibers=nutrients.get('fibers'),
                sugars=nutrients.get('sugars'),
                saturated_fats=nutrients.get('saturated_fats'),
                salt=nutrients.get('sodium'),  # Approximation
                water=nutrients.get('water')
            )

            micronutrients = Micronutrients(
                vitamin_a=nutrients.get('vitamin_a'),
                vitamin_b1_thiamine=nutrients.get('vitamin_b1'),
                vitamin_b2_riboflavin=nutrients.get('vitamin_b2'),
                vitamin_b3_niacin=nutrients.get('vitamin_b3'),
                vitamin_b6=nutrients.get('vitamin_b6'),
                vitamin_b12=nutrients.get('vitamin_b12'),
                vitamin_c=nutrients.get('vitamin_c'),
                vitamin_d=nutrients.get('vitamin_d'),
                vitamin_e=nutrients.get('vitamin_e'),
                vitamin_k=nutrients.get('vitamin_k'),
                folate=nutrients.get('folate'),
                calcium=nutrients.get('calcium'),
                iron=nutrients.get('iron'),
                magnesium=nutrients.get('magnesium'),
                phosphorus=nutrients.get('phosphorus'),
                potassium=nutrients.get('potassium'),
                sodium=nutrients.get('sodium', 0) * 1000,  # Convert back to mg
                zinc=nutrients.get('zinc'),
                selenium=nutrients.get('selenium')
            )

            # Determina categoria (semplificato)
            category = self._determine_category(name)

            food = ComprehensiveFood(
                name=name,
                description=usda_data.get('description'),
                category=category,
                nutritional_values=nutritional_values,
                micronutrients=micronutrients,
                portion_info=PortionInfo(100, "100g"),
                source="USDA",
                source_food_id=str(usda_data.get('fdcId')),
                verified=True
            )

            return food

        except Exception as e:
            logger.error(f"Failed to convert USDA data: {e}")
            return None

    def _determine_category(self, food_name: str) -> FoodCategory:
        """Determina categoria da nome alimento"""
        name_lower = food_name.lower()

        if any(word in name_lower for word in ['chicken', 'beef', 'pork', 'lamb', 'pollo', 'manzo']):
            return FoodCategory.CARNI
        elif any(word in name_lower for word in ['fish', 'salmon', 'tuna', 'cod', 'pesce', 'salmone']):
            return FoodCategory.PESCI
        elif any(word in name_lower for word in ['milk', 'cheese', 'yogurt', 'latte', 'formaggio']):
            return FoodCategory.LATTICINI
        elif any(word in name_lower for word in ['apple', 'banana', 'orange', 'mela', 'banana']):
            return FoodCategory.FRUTTA
        elif any(word in name_lower for word in ['spinach', 'carrot', 'tomato', 'spinaci', 'carote']):
            return FoodCategory.VERDURE
        elif any(word in name_lower for word in ['bread', 'pasta', 'rice', 'pane', 'riso']):
            return FoodCategory.CEREALI
        elif any(word in name_lower for word in ['beans', 'lentils', 'fagioli', 'lenticchie']):
            return FoodCategory.LEGUMI
        else:
            return FoodCategory.ALTRO


class INRANDataImporter:
    """Importatore dati INRAN (Istituto Nazionale di Ricerca per gli Alimenti e la Nutrizione)"""

    def __init__(self):
        # INRAN non ha API pubblica, usiamo dati CSV/JSON pre-elaborati
        self.inran_data_path = "data/inran_foods.csv"

    def load_inran_csv(self, file_path: str) -> List[ComprehensiveFood]:
        """Carica dati INRAN da CSV"""
        foods = []

        if not os.path.exists(file_path):
            logger.warning(f"INRAN CSV file not found: {file_path}")
            return foods

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    food = self._convert_inran_csv_row(row)
                    if food:
                        foods.append(food)

            logger.info(f"Loaded {len(foods)} foods from INRAN CSV")

        except Exception as e:
            logger.error(f"Failed to load INRAN CSV: {e}")

        return foods

    def _convert_inran_csv_row(self, row: Dict[str, str]) -> Optional[ComprehensiveFood]:
        """Converte riga CSV INRAN in ComprehensiveFood"""
        try:
            name = row.get('Nome', '')
            if not name:
                return None

            # Parse valori nutrizionali
            calories = float(row.get('Energia_kcal', 0))
            proteins = float(row.get('Proteine_g', 0))
            fats = float(row.get('Grassi_g', 0))
            carbs = float(row.get('Carboidrati_g', 0))

            nutritional_values = NutritionalValues(
                calories=calories,
                proteins=proteins,
                carbohydrates=carbs,
                fats=fats,
                fibers=float(row.get('Fibre_g', 0)) if row.get('Fibre_g') else None,
                water=float(row.get('Acqua_g', 0)) if row.get('Acqua_g') else None
            )

            # Micronutrienti (se disponibili)
            micronutrients = Micronutrients(
                calcium=float(row.get('Calcio_mg', 0)) if row.get('Calcio_mg') else None,
                iron=float(row.get('Ferro_mg', 0)) if row.get('Ferro_mg') else None,
                vitamin_c=float(row.get('VitaminaC_mg', 0)) if row.get('VitaminaC_mg') else None
            )

            food = ComprehensiveFood(
                name=name,
                description=row.get('Descrizione', ''),
                category=self._map_inran_category(row.get('Categoria', '')),
                nutritional_values=nutritional_values,
                micronutrients=micronutrients,
                source="INRAN",
                source_food_id=row.get('Codice', ''),
                verified=True
            )

            return food

        except Exception as e:
            logger.error(f"Failed to convert INRAN row: {e}")
            return None

    def _map_inran_category(self, inran_category: str) -> FoodCategory:
        """Mappa categoria INRAN a FoodCategory"""
        category_map = {
            'Cereali': FoodCategory.CEREALI,
            'Carni': FoodCategory.CARNI,
            'Pesci': FoodCategory.PESCI,
            'Latte e derivati': FoodCategory.LATTICINI,
            'Verdure': FoodCategory.VERDURE,
            'Frutta': FoodCategory.FRUTTA,
            'Legumi': FoodCategory.LEGUMI,
            'Grassi': FoodCategory.GRASSI_CONDIMENTI
        }
        return category_map.get(inran_category, FoodCategory.ALTRO)


class ComprehensiveFoodImporter:
    """Importatore unificato da multiple fonti"""

    def __init__(self, usda_api_key: Optional[str] = None):
        self.usda_importer = USDAFoodDataImporter(usda_api_key)
        self.inran_importer = INRANDataImporter()

    def import_italian_staples(self) -> List[ComprehensiveFood]:
        """Importa alimenti base italiani da USDA/INRAN"""
        italian_foods = [
            # Paste e cereali
            "pasta durum wheat", "risotto rice", "polenta corn",

            # Carni italiane
            "prosciutto", "pancetta", "bresaola",

            # Formaggi italiani
            "parmigiano reggiano", "mozzarella", "gorgonzola", "pecorino",

            # Verdure mediterranee
            "basil fresh", "tomato san marzano", "zucchini", "eggplant",
            "arugula", "radicchio",

            # Frutta italiana
            "lemon", "orange blood", "fig fresh", "grape",

            # Pesci mediterranei
            "sea bass", "sea bream", "anchovy", "tuna",

            # Oli e condimenti
            "olive oil extra virgin", "balsamic vinegar"
        ]

        all_foods = []

        for food_name in italian_foods:
            logger.info(f"Importing data for: {food_name}")

            # Cerca in USDA
            usda_results = self.usda_importer.search_foods(food_name, 3)

            for usda_food in usda_results[:1]:  # Prendi il primo risultato
                details = self.usda_importer.get_food_details(str(usda_food['fdcId']))
                if details:
                    comprehensive_food = self.usda_importer.convert_usda_to_comprehensive_food(details)
                    if comprehensive_food:
                        all_foods.append(comprehensive_food)
                        break

            # Rate limiting
            time.sleep(0.2)

        # Carica anche dati INRAN se disponibili
        inran_foods = self.inran_importer.load_inran_csv("data/inran_foods.csv")
        all_foods.extend(inran_foods)

        logger.info(f"Total imported foods: {len(all_foods)}")
        return all_foods

    def export_to_json(self, foods: List[ComprehensiveFood], filename: str):
        """Esporta alimenti in JSON"""
        data = {
            'export_date': datetime.now().isoformat(),
            'total_foods': len(foods),
            'foods': [food.to_firestore_document() for food in foods]
        }

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)

        logger.info(f"Exported {len(foods)} foods to {filename}")


def main():
    """Esecuzione principale importazione"""
    print("🌍 LONGEVIVA COMPREHENSIVE FOOD IMPORTER - Task 3.1")
    print("=" * 60)
    print("Importing from USDA Food Data Central and INRAN databases")

    # Inizializza importatore
    # NOTA: Sostituisci con la tua API key USDA
    usda_api_key = "YOUR_USDA_API_KEY_HERE"
    importer = ComprehensiveFoodImporter(usda_api_key)

    try:
        # Importa alimenti italiani
        print("\n1. Importing Italian staple foods...")
        foods = importer.import_italian_staples()

        print(f"✅ Imported {len(foods)} foods with comprehensive data")

        # Statistiche importazione
        categories = {}
        verified_count = 0
        with_micronutrients = 0

        for food in foods:
            cat = food.category.value
            categories[cat] = categories.get(cat, 0) + 1
            if food.verified:
                verified_count += 1
            if any(getattr(food.micronutrients, attr) for attr in dir(food.micronutrients) if not attr.startswith('_')):
                with_micronutrients += 1

        print(f"\n📊 Import Statistics:")
        print(f"   - Total foods: {len(foods)}")
        print(f"   - Verified sources: {verified_count}")
        print(f"   - With micronutrients: {with_micronutrients}")
        print(f"   - Categories:")
        for cat, count in categories.items():
            print(f"     * {cat}: {count}")

        # Esporta dati
        print("\n2. Exporting comprehensive food data...")
        importer.export_to_json(foods, "longeviva_comprehensive_foods.json")

        # Mostra esempio
        if foods:
            example = foods[0]
            print(f"\n🥗 Example: {example.name}")
            print(f"   Category: {example.category.value}")
            print(f"   Calories/100g: {example.nutritional_values.calories}")
            print(f"   Micronutrients: {bool(example.micronutrients.vitamin_c)}")
            print(f"   Source: {example.source}")

        print("\n🎉 Comprehensive food database import completed!")
        print("Ready for Firestore upload with full nutritional metadata")

    except Exception as e:
        logger.error(f"Import failed: {e}")
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()