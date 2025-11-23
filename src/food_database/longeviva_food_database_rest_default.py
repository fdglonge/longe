#!/usr/bin/env python3
"""
Longeviva Food Database - Populate Default Database
Aggiunge alimenti alla collection 'foods' esistente nel database (default)
"""

import json
import logging
import requests
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import google.auth
from google.auth.transport.requests import Request

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@dataclass
class Food:
    """Food model matching Longeviva Flutter implementation"""
    name: str
    calories: str
    weight: str
    proteins: str
    fats: str
    carbohydrates: str
    brand: Optional[str] = None

    @classmethod
    def from_values(cls, name: str, calories_per_100g: float, proteins_per_100g: float,
                    fats_per_100g: float, carbs_per_100g: float, weight_g: int = 100,
                    brand: Optional[str] = None) -> 'Food':
        """Create Food from numerical values"""
        return cls(
            name=name,
            calories=f"{int(calories_per_100g * weight_g / 100)}kcal",
            weight=f"{weight_g}g",
            proteins=f"{proteins_per_100g * weight_g / 100:.1f}g",
            fats=f"{fats_per_100g * weight_g / 100:.1f}g",
            carbohydrates=f"{carbs_per_100g * weight_g / 100:.1f}g",
            brand=brand
        )

    def to_firestore_fields(self) -> Dict[str, Any]:
        """Convert to Firestore REST API format"""
        fields = {
            'name': {'stringValue': self.name},
            'calories': {'stringValue': self.calories},
            'weight': {'stringValue': self.weight},
            'proteins': {'stringValue': self.proteins},
            'fats': {'stringValue': self.fats},
            'carbohydrates': {'stringValue': self.carbohydrates},
            'created_at': {'timestampValue': datetime.now().isoformat() + 'Z'},
            'updated_at': {'timestampValue': datetime.now().isoformat() + 'Z'}
        }
        if self.brand:
            fields['brand'] = {'stringValue': self.brand}
        return fields


class LongevivaDefaultDatabasePopulator:
    """Populates foods collection in default database"""

    def __init__(self, project_id: str = "longeviva-web-app-dev"):
        self.project_id = project_id
        self.database_id = "(default)"
        self.access_token = None

    def get_access_token(self) -> str:
        """Get access token using Application Default Credentials"""
        try:
            credentials, project = google.auth.default(
                scopes=['https://www.googleapis.com/auth/datastore']
            )
            credentials.refresh(Request())
            self.access_token = credentials.token
            logger.info("Access token obtained successfully")
            return self.access_token
        except Exception as e:
            logger.error(f"Failed to get access token: {e}")
            raise

    def get_headers(self) -> Dict[str, str]:
        """Get HTTP headers with authorization"""
        if not self.access_token:
            self.get_access_token()

        return {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }

    def check_existing_foods(self, collection: str = "foods") -> Dict[str, Any]:
        """Check what's already in the foods collection"""
        try:
            list_url = f"https://firestore.googleapis.com/v1/projects/{self.project_id}/databases/{self.database_id}/documents/{collection}"

            response = requests.get(list_url, headers=self.get_headers())

            if response.status_code == 200:
                data = response.json()
                documents = data.get('documents', [])

                existing_foods = []
                for doc in documents:
                    fields = doc.get('fields', {})
                    if 'name' in fields and 'stringValue' in fields['name']:
                        existing_foods.append(fields['name']['stringValue'])

                logger.info(f"Found {len(existing_foods)} existing foods in collection")
                return {
                    "total_count": len(existing_foods),
                    "food_names": existing_foods,
                    "status": "SUCCESS"
                }
            else:
                logger.error(f"Failed to check existing foods: {response.status_code}")
                return {"status": "FAILED", "error": response.text}

        except Exception as e:
            logger.error(f"Failed to check existing foods: {e}")
            return {"status": "FAILED", "error": str(e)}

    def add_foods_to_collection(self, foods: List[Food], collection: str = "foods") -> bool:
        """Add new foods to existing collection"""
        try:
            # Check existing foods first
            existing_check = self.check_existing_foods(collection)
            if existing_check["status"] == "SUCCESS":
                existing_names = set(existing_check["food_names"])
                logger.info(f"Existing foods in collection: {len(existing_names)}")
            else:
                existing_names = set()

            # Filter new foods (avoid duplicates)
            new_foods = []
            for food in foods:
                if food.name not in existing_names:
                    new_foods.append(food)
                else:
                    logger.debug(f"Skipping duplicate: {food.name}")

            logger.info(f"Adding {len(new_foods)} new foods to collection '{collection}'")

            if len(new_foods) == 0:
                logger.info("No new foods to add - all foods already exist")
                return True

            # Base URL for collection
            collection_url = f"https://firestore.googleapis.com/v1/projects/{self.project_id}/databases/{self.database_id}/documents/{collection}"

            headers = self.get_headers()

            for i, food in enumerate(new_foods):
                # Create document
                doc_data = {
                    'fields': food.to_firestore_fields()
                }

                response = requests.post(collection_url, headers=headers, json=doc_data)

                if response.status_code not in [200, 201]:
                    logger.error(f"Failed to add food {i + 1} ({food.name}): {response.status_code}")
                    return False

                # Progress update every 10 foods
                if (i + 1) % 10 == 0:
                    logger.info(f"  Added {i + 1}/{len(new_foods)} new foods...")

            logger.info(f"✅ Successfully added {len(new_foods)} foods to default database")
            return True

        except Exception as e:
            logger.error(f"Failed to add foods: {e}")
            return False

    def verify_final_collection(self, collection: str = "foods") -> Dict[str, Any]:
        """Verify final state of collection"""
        try:
            list_url = f"https://firestore.googleapis.com/v1/projects/{self.project_id}/databases/{self.database_id}/documents/{collection}"

            response = requests.get(list_url, headers=self.get_headers())

            if response.status_code == 200:
                data = response.json()
                documents = data.get('documents', [])

                total_count = len(documents)

                # Get sample of latest foods
                sample_foods = []
                for doc in documents[-5:]:  # Last 5 documents
                    fields = doc.get('fields', {})
                    food_data = {}
                    for key, value in fields.items():
                        if 'stringValue' in value:
                            food_data[key] = value['stringValue']
                    sample_foods.append(food_data)

                return {
                    "database": self.database_id,
                    "collection": collection,
                    "total_count": total_count,
                    "sample_foods": sample_foods,
                    "status": "SUCCESS"
                }
            else:
                return {"status": "FAILED", "error": response.text}

        except Exception as e:
            return {"status": "FAILED", "error": str(e)}


def get_comprehensive_food_dataset() -> List[Food]:
    """Generate comprehensive food dataset"""
    foods = []

    # PROTEINE / CARNI
    protein_foods = [
        # Carni rosse
        Food.from_values("Manzo (filetto)", 250, 26.0, 15.0, 0.0, brand="Generico"),
        Food.from_values("Manzo (macinato magro)", 215, 26.1, 11.0, 0.0, brand="Generico"),
        Food.from_values("Vitello (scaloppina)", 196, 31.9, 7.56, 0.0, brand="Generico"),
        Food.from_values("Agnello (costoletta)", 294, 25.6, 20.9, 0.0, brand="Generico"),
        Food.from_values("Maiale (lonza)", 242, 27.3, 14.2, 0.0, brand="Generico"),

        # Carni bianche
        Food.from_values("Pollo (petto)", 165, 31.0, 3.6, 0.0, brand="Generico"),
        Food.from_values("Pollo (coscia)", 209, 26.0, 10.9, 0.0, brand="Generico"),
        Food.from_values("Tacchino (petto)", 135, 30.1, 1.66, 0.0, brand="Generico"),
        Food.from_values("Anatra (petto)", 201, 23.5, 11.2, 0.0, brand="Generico"),
        Food.from_values("Coniglio", 173, 33.0, 3.5, 0.0, brand="Generico"),

        # Pesci
        Food.from_values("Salmone atlantico", 208, 25.4, 12.4, 0.0, brand="Generico"),
        Food.from_values("Tonno fresco", 144, 23.3, 4.9, 0.0, brand="Generico"),
        Food.from_values("Branzino", 118, 23.2, 2.5, 0.0, brand="Generico"),
        Food.from_values("Orata", 115, 20.7, 3.8, 0.0, brand="Generico"),
        Food.from_values("Merluzzo", 82, 17.8, 0.7, 0.0, brand="Generico"),
        Food.from_values("Sogliola", 86, 16.9, 2.1, 0.0, brand="Generico"),
        Food.from_values("Gamberi", 85, 20.1, 1.4, 0.0, brand="Generico"),
        Food.from_values("Polpo", 82, 14.9, 1.4, 2.2, brand="Generico"),
        Food.from_values("Calamari", 92, 15.6, 1.4, 3.1, brand="Generico"),

        # Uova e latticini proteici
        Food.from_values("Uovo intero", 155, 13.0, 11.0, 1.1, 50, brand="Generico"),
        Food.from_values("Albume d'uovo", 52, 11.1, 0.2, 0.7, 100, brand="Generico"),
        Food.from_values("Ricotta vaccina", 146, 8.8, 10.9, 4.3, brand="Generico"),
        Food.from_values("Mozzarella", 280, 18.7, 22.4, 2.2, brand="Generico"),
        Food.from_values("Parmigiano Reggiano", 392, 35.8, 26.0, 0.0, brand="Generico"),
        Food.from_values("Gorgonzola", 330, 19.4, 27.0, 0.0, brand="Generico"),
    ]

    # CARBOIDRATI
    carb_foods = [
        # Cereali e paste
        Food.from_values("Riso Basmati", 365, 8.1, 0.6, 78.0, brand="Generico"),
        Food.from_values("Riso integrale", 362, 7.2, 1.8, 72.9, brand="Generico"),
        Food.from_values("Pasta di grano duro", 353, 13.0, 1.4, 70.9, brand="Barilla"),
        Food.from_values("Pasta integrale", 348, 13.4, 2.9, 66.2, brand="Barilla"),
        Food.from_values("Quinoa", 368, 14.1, 6.1, 64.2, brand="Generico"),
        Food.from_values("Avena", 389, 16.9, 6.9, 66.3, brand="Generico"),
        Food.from_values("Orzo perlato", 354, 10.4, 1.2, 70.5, brand="Generico"),
        Food.from_values("Farro", 340, 15.1, 2.5, 67.1, brand="Generico"),

        # Pane
        Food.from_values("Pane integrale", 247, 13.2, 4.2, 41.0, brand="Generico"),
        Food.from_values("Pane bianco", 275, 8.1, 3.2, 50.6, brand="Generico"),
        Food.from_values("Pane di segale", 259, 8.5, 3.3, 48.3, brand="Generico"),
        Food.from_values("Fette biscottate integrali", 407, 13.0, 6.0, 72.0, brand="Mulino Bianco"),

        # Tuberi e patate
        Food.from_values("Patate", 77, 2.1, 0.1, 17.5, brand="Generico"),
        Food.from_values("Patate dolci", 86, 1.6, 0.1, 20.1, brand="Generico"),
        Food.from_values("Patate al vapore", 86, 1.9, 0.1, 20.0, brand="Generico"),

        # Legumi
        Food.from_values("Lenticchie secche", 353, 25.8, 1.9, 51.1, brand="Generico"),
        Food.from_values("Ceci secchi", 316, 20.9, 6.3, 46.9, brand="Generico"),
        Food.from_values("Fagioli cannellini", 279, 17.5, 2.0, 45.5, brand="Generico"),
        Food.from_values("Fagioli borlotti", 289, 20.2, 2.0, 45.5, brand="Generico"),
        Food.from_values("Piselli secchi", 317, 21.7, 2.0, 48.2, brand="Generico"),
    ]

    # VERDURE E ORTAGGI
    vegetable_foods = [
        # Verdure a foglia verde
        Food.from_values("Spinaci", 23, 2.9, 0.4, 3.6, brand="Generico"),
        Food.from_values("Lattuga", 15, 1.4, 0.2, 2.9, brand="Generico"),
        Food.from_values("Rucola", 25, 2.6, 0.7, 3.7, brand="Generico"),
        Food.from_values("Cavolo nero", 35, 2.9, 0.6, 5.4, brand="Generico"),
        Food.from_values("Bietole", 19, 1.8, 0.2, 3.7, brand="Generico"),

        # Ortaggi colorati
        Food.from_values("Pomodori", 18, 0.9, 0.2, 3.9, brand="Generico"),
        Food.from_values("Peperoni rossi", 31, 1.0, 0.3, 6.0, brand="Generico"),
        Food.from_values("Zucchine", 17, 1.2, 0.3, 3.1, brand="Generico"),
        Food.from_values("Melanzane", 25, 1.0, 0.2, 5.9, brand="Generico"),
        Food.from_values("Carote", 41, 0.9, 0.2, 9.6, brand="Generico"),
        Food.from_values("Broccoli", 25, 3.0, 0.4, 5.0, brand="Generico"),
        Food.from_values("Cavolfiore", 25, 1.9, 0.3, 4.9, brand="Generico"),
        Food.from_values("Cetrioli", 15, 0.7, 0.1, 3.6, brand="Generico"),
        Food.from_values("Finocchi", 23, 1.2, 0.2, 5.1, brand="Generico"),

        # Funghi
        Food.from_values("Champignon", 22, 3.1, 0.3, 3.3, brand="Generico"),
        Food.from_values("Porcini", 26, 3.9, 0.7, 1.1, brand="Generico"),
    ]

    # FRUTTA
    fruit_foods = [
        # Frutta fresca comune
        Food.from_values("Mela", 52, 0.3, 0.2, 13.8, brand="Generico"),
        Food.from_values("Banana", 89, 1.1, 0.3, 22.8, brand="Generico"),
        Food.from_values("Arancia", 47, 0.9, 0.1, 11.8, brand="Generico"),
        Food.from_values("Pera", 57, 0.4, 0.1, 15.2, brand="Generico"),
        Food.from_values("Kiwi", 61, 1.1, 0.5, 14.7, brand="Generico"),
        Food.from_values("Fragole", 32, 0.7, 0.3, 7.7, brand="Generico"),
        Food.from_values("Uva", 69, 0.7, 0.2, 17.2, brand="Generico"),
        Food.from_values("Pesche", 39, 0.9, 0.3, 9.5, brand="Generico"),
        Food.from_values("Albicocche", 48, 1.4, 0.4, 11.1, brand="Generico"),
        Food.from_values("Prugne", 46, 0.7, 0.3, 11.4, brand="Generico"),

        # Frutta esotica
        Food.from_values("Ananas", 50, 0.5, 0.1, 13.1, brand="Generico"),
        Food.from_values("Mango", 60, 0.8, 0.4, 15.0, brand="Generico"),
        Food.from_values("Avocado", 160, 2.0, 14.7, 8.5, brand="Generico"),

        # Frutti di bosco
        Food.from_values("Mirtilli", 57, 0.7, 0.3, 14.5, brand="Generico"),
        Food.from_values("Lamponi", 52, 1.2, 0.7, 11.9, brand="Generico"),
    ]

    # GRASSI E CONDIMENTI
    fat_foods = [
        # Oli
        Food.from_values("Olio extravergine oliva", 884, 0.0, 100.0, 0.0, brand="Monini"),
        Food.from_values("Olio di semi di girasole", 884, 0.0, 100.0, 0.0, brand="Generico"),
        Food.from_values("Olio di cocco", 862, 0.0, 100.0, 0.0, brand="Generico"),

        # Frutta secca
        Food.from_values("Mandorle", 579, 21.2, 49.9, 21.6, brand="Generico"),
        Food.from_values("Noci", 654, 15.2, 65.2, 13.7, brand="Generico"),
        Food.from_values("Nocciole", 628, 15.0, 60.8, 16.7, brand="Generico"),
        Food.from_values("Pistacchi", 557, 20.2, 45.3, 28.0, brand="Generico"),
        Food.from_values("Arachidi", 567, 25.8, 49.2, 16.1, brand="Generico"),

        # Semi
        Food.from_values("Semi di girasole", 584, 20.8, 51.5, 20.0, brand="Generico"),
        Food.from_values("Semi di zucca", 559, 30.2, 49.0, 10.7, brand="Generico"),
        Food.from_values("Semi di chia", 486, 16.5, 30.7, 42.1, brand="Generico"),
        Food.from_values("Semi di lino", 534, 18.3, 42.2, 28.9, brand="Generico"),
    ]

    # LATTICINI
    dairy_foods = [
        Food.from_values("Latte intero", 61, 3.2, 3.6, 4.9, brand="Parmalat"),
        Food.from_values("Latte scremato", 36, 3.6, 0.4, 5.0, brand="Parmalat"),
        Food.from_values("Yogurt greco", 59, 10.0, 0.4, 4.0, brand="Fage"),
        Food.from_values("Yogurt intero", 61, 3.5, 3.9, 4.3, brand="Danone"),
        Food.from_values("Kefir", 41, 3.0, 1.0, 4.0, brand="Generico"),
    ]

    # BEVANDE E ALTERNATIVE
    beverage_foods = [
        Food.from_values("Latte di mandorla", 13, 0.4, 1.1, 0.3, brand="Alpro"),
        Food.from_values("Latte di avena", 42, 3.0, 1.5, 6.6, brand="Oatly"),
        Food.from_values("Latte di soia", 33, 2.9, 1.8, 0.8, brand="Alpro"),
        Food.from_values("Acqua", 0, 0.0, 0.0, 0.0, brand="Generico"),
        Food.from_values("Tè verde", 1, 0.2, 0.0, 0.0, brand="Generico"),
        Food.from_values("Caffè espresso", 2, 0.1, 0.0, 0.0, 10, brand="Generico"),
    ]

    # Combine all food categories
    foods.extend(protein_foods)
    foods.extend(carb_foods)
    foods.extend(vegetable_foods)
    foods.extend(fruit_foods)
    foods.extend(fat_foods)
    foods.extend(dairy_foods)
    foods.extend(beverage_foods)

    logger.info(f"Generated {len(foods)} food items for database")
    return foods


def main():
    """Main execution"""
    print("🚀 LONGEVIVA FOOD DATABASE - POPULATE DEFAULT")
    print("=" * 50)
    print("Adding foods to existing 'foods' collection in (default) database")

    # Initialize populator
    populator = LongevivaDefaultDatabasePopulator()

    try:
        # Check existing foods
        print("\n1. Checking existing foods collection...")
        existing_check = populator.check_existing_foods()

        if existing_check["status"] == "SUCCESS":
            print(f"✅ Found existing collection with {existing_check['total_count']} foods")
        else:
            print("⚠️  Could not check existing foods, proceeding anyway...")

        # Generate food data
        print("\n2. Generating comprehensive food dataset...")
        foods = get_comprehensive_food_dataset()

        # Add foods to collection
        print(f"\n3. Adding {len(foods)} foods to default database...")
        success = populator.add_foods_to_collection(foods)

        if not success:
            print("❌ Failed to add foods to collection")
            return False

        # Verify final collection
        print("\n4. Verifying final collection state...")
        verification = populator.verify_final_collection()

        if verification["status"] == "SUCCESS":
            print("\n🎉 FOODS ADDED TO DEFAULT DATABASE!")
            print(f"✅ Database: {verification['database']}")
            print(f"✅ Collection: {verification['collection']}")
            print(f"✅ Total foods now: {verification['total_count']}")

            print("\n📊 Recent foods added:")
            for food in verification.get('sample_foods', [])[-3:]:
                print(f"  - {food.get('name', 'N/A')}: {food.get('calories', 'N/A')} "
                      f"(P: {food.get('proteins', 'N/A')}, F: {food.get('fats', 'N/A')}, C: {food.get('carbohydrates', 'N/A')})")
        else:
            print(f"⚠️  Verification issues: {verification.get('error', 'Unknown')}")

        return True

    except Exception as e:
        logger.error(f"Execution failed: {e}")
        print(f"❌ Error: {e}")
        return False


if __name__ == "__main__":
    main()