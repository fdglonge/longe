#!/usr/bin/env python3
"""
Longeviva Food Database Populator
Populates Firebase with comprehensive food nutritional data for meal planning system
"""

import json
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime

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
    # Future extension field
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

    def to_dict(self) -> Dict[str, Any]:
        """Convert to Firebase document format"""
        data = {
            'name': self.name,
            'calories': self.calories,
            'weight': self.weight,
            'proteins': self.proteins,
            'fats': self.fats,
            'carbohydrates': self.carbohydrates,
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        }
        if self.brand:
            data['brand'] = self.brand
        return data


class LongevivaFoodDatabase:
    """Firebase food database manager"""

    def __init__(self, project_id: str = "longeviva-web-app-dev",
                 database_id: str = "longeviva-web-app-dev-sviluppo"):
        self.project_id = project_id
        self.database_id = database_id
        self.db = None

    def initialize_firebase(self, credentials_path: Optional[str] = None):
        """Initialize Firebase connection"""
        try:
            if not firebase_admin._apps:
                if credentials_path and os.path.exists(credentials_path):
                    # Use service account key if provided and exists
                    cred = credentials.Certificate(credentials_path)
                    firebase_admin.initialize_app(cred, {
                        'projectId': self.project_id
                    })
                    logger.info(f"Using service account credentials: {credentials_path}")
                else:
                    # Use Application Default Credentials (gcloud auth)
                    firebase_admin.initialize_app(options={
                        'projectId': self.project_id
                    })
                    logger.info("Using Application Default Credentials (gcloud)")

            self.db = firestore.client(database=self.database_id)
            logger.info(f"Firebase initialized for project: {self.project_id}, database: {self.database_id}")

        except Exception as e:
            logger.error(f"Firebase initialization failed: {e}")
            logger.error("Try: gcloud auth application-default login")
            raise

    def get_comprehensive_food_dataset(self) -> List[Food]:
        """Generate comprehensive food dataset for meal planning"""
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

    def populate_database(self, foods: List[Food], collection_name: str = "foods") -> bool:
        """Populate Firebase with food data"""
        try:
            if not self.db:
                raise Exception("Firebase not initialized")

            collection_ref = self.db.collection(collection_name)

            # Clear existing data (optional)
            # docs = collection_ref.get()
            # for doc in docs:
            #     doc.reference.delete()

            batch_size = 500  # Firestore batch limit
            batch = self.db.batch()
            batch_count = 0

            for i, food in enumerate(foods):
                doc_ref = collection_ref.document()
                batch.set(doc_ref, food.to_dict())
                batch_count += 1

                # Commit batch when limit reached
                if batch_count >= batch_size:
                    batch.commit()
                    batch = self.db.batch()
                    batch_count = 0
                    logger.info(f"Committed batch, processed {i + 1} foods")

            # Commit remaining items
            if batch_count > 0:
                batch.commit()

            logger.info(f"Successfully populated database with {len(foods)} food items")
            return True

        except Exception as e:
            logger.error(f"Database population failed: {e}")
            return False

    def verify_data(self, collection_name: str = "foods") -> Dict[str, Any]:
        """Verify populated data"""
        try:
            collection_ref = self.db.collection(collection_name)
            docs = collection_ref.limit(5).get()

            stats = {
                "total_count": len(collection_ref.get()),
                "sample_foods": [doc.to_dict() for doc in docs],
                "verification_status": "SUCCESS"
            }

            logger.info(f"Verification complete: {stats['total_count']} foods in database")
            return stats

        except Exception as e:
            logger.error(f"Verification failed: {e}")
            return {"verification_status": "FAILED", "error": str(e)}


def main():
    """Main execution function"""
    # Initialize database manager
    food_db = LongevivaFoodDatabase()

    try:
        # Initialize Firebase (adjust credentials path as needed)
        food_db.initialize_firebase()

        # Generate comprehensive food dataset
        foods = food_db.get_comprehensive_food_dataset()

        # Populate database
        success = food_db.populate_database(foods)

        if success:
            # Verify data
            verification = food_db.verify_data()
            print(f"Database population completed successfully!")
            print(f"Total foods added: {verification.get('total_count', 'Unknown')}")

            # Display sample data
            print("\nSample foods:")
            for food in verification.get('sample_foods', [])[:3]:
                print(f"- {food.get('name')}: {food.get('calories')} "
                      f"(P: {food.get('proteins')}, F: {food.get('fats')}, C: {food.get('carbohydrates')})")
        else:
            print("Database population failed!")

    except Exception as e:
        logger.error(f"Execution failed: {e}")
        print(f"Error: {e}")


if __name__ == "__main__":
    main()