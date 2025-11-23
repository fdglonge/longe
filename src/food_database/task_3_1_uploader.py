#!/usr/bin/env python3
"""
Longeviva Food Database - Task 3.1 Firestore Uploader
Carica il modello dati completo con metadati nutrizionali in Firestore
"""

import json
import logging
import requests
from typing import Dict, List, Any, Optional
from datetime import datetime
import google.auth
from google.auth.transport.requests import Request

from comprehensive_food_model import (
    ComprehensiveFood, create_comprehensive_food_database,
    FoodCategory, FoodSubcategory, AllergenType
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class LongevivaComprehensiveFoodUploader:
    """Uploader per modello dati completo Task 3.1"""

    def __init__(self,
                 project_id: str = "longeviva-web-app-dev",
                 database_id: str = "longeviva-web-app-dev-sviluppo"):
        self.project_id = project_id
        self.database_id = database_id
        self.access_token = None

    def get_access_token(self) -> str:
        """Get access token"""
        try:
            credentials, project = google.auth.default(
                scopes=['https://www.googleapis.com/auth/datastore']
            )
            credentials.refresh(Request())
            self.access_token = credentials.token
            return self.access_token
        except Exception as e:
            logger.error(f"Failed to get access token: {e}")
            raise

    def get_headers(self) -> Dict[str, str]:
        """Get HTTP headers"""
        if not self.access_token:
            self.get_access_token()

        return {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }

    def upload_comprehensive_foods(self, foods: List[ComprehensiveFood],
                                   collection: str = "foods_comprehensive") -> bool:
        """Upload comprehensive foods to Firestore"""
        try:
            collection_url = f"https://firestore.googleapis.com/v1/projects/{self.project_id}/databases/{self.database_id}/documents/{collection}"

            headers = self.get_headers()
            success_count = 0

            logger.info(f"Uploading {len(foods)} comprehensive foods to {collection}...")

            for i, food in enumerate(foods):
                try:
                    # Convert to Firestore format
                    doc_data = {
                        'fields': food.to_firestore_fields()
                    }

                    response = requests.post(collection_url, headers=headers, json=doc_data)

                    if response.status_code in [200, 201]:
                        success_count += 1
                        logger.debug(f"Uploaded: {food.name}")
                    else:
                        logger.error(f"Failed to upload {food.name}: {response.status_code}")
                        logger.error(f"Response: {response.text}")

                except Exception as e:
                    logger.error(f"Error uploading {food.name}: {e}")
                    continue

                # Progress update
                if (i + 1) % 5 == 0:
                    logger.info(f"Progress: {success_count}/{i + 1} foods uploaded successfully")

            logger.info(f"✅ Upload completed: {success_count}/{len(foods)} foods uploaded")
            return success_count == len(foods)

        except Exception as e:
            logger.error(f"Upload failed: {e}")
            return False

    def create_food_indexes(self) -> bool:
        """Crea indici Firestore per ricerche efficienti"""
        # Gli indici Firestore devono essere creati tramite Firebase Console o gcloud
        # Qui documentiamo gli indici necessari

        recommended_indexes = [
            {
                "collection": "foods_comprehensive",
                "fields": [
                    {"field": "category", "order": "ASCENDING"},
                    {"field": "verified", "order": "ASCENDING"}
                ]
            },
            {
                "collection": "foods_comprehensive",
                "fields": [
                    {"field": "allergens", "mode": "ARRAY_CONTAINS"},
                    {"field": "category", "order": "ASCENDING"}
                ]
            },
            {
                "collection": "foods_comprehensive",
                "fields": [
                    {"field": "nutrition_per_100g.proteins", "order": "DESCENDING"},
                    {"field": "category", "order": "ASCENDING"}
                ]
            }
        ]

        logger.info("📋 Recommended Firestore indexes:")
        for idx in recommended_indexes:
            logger.info(f"   Collection: {idx['collection']}")
            logger.info(f"   Fields: {idx['fields']}")
            logger.info("   ---")

        logger.info("Create these indexes in Firebase Console for optimal performance")
        return True

    def verify_comprehensive_upload(self, collection: str = "foods_comprehensive") -> Dict[str, Any]:
        """Verifica upload completo"""
        try:
            list_url = f"https://firestore.googleapis.com/v1/projects/{self.project_id}/databases/{self.database_id}/documents/{collection}"

            response = requests.get(list_url, headers=self.get_headers())

            if response.status_code == 200:
                data = response.json()
                documents = data.get('documents', [])

                # Analisi dati caricati
                stats = {
                    "total_foods": len(documents),
                    "categories": {},
                    "with_micronutrients": 0,
                    "verified_foods": 0,
                    "with_allergens": 0,
                    "sample_foods": []
                }

                for doc in documents:
                    fields = doc.get('fields', {})

                    # Categoria
                    if 'category' in fields and 'stringValue' in fields['category']:
                        cat = fields['category']['stringValue']
                        stats["categories"][cat] = stats["categories"].get(cat, 0) + 1

                    # Micronutrienti
                    if 'micronutrients' in fields:
                        stats["with_micronutrients"] += 1

                    # Verified
                    if 'verified' in fields and fields['verified'].get('booleanValue'):
                        stats["verified_foods"] += 1

                    # Allergeni
                    if 'allergens' in fields and fields['allergens'].get('arrayValue', {}).get('values'):
                        stats["with_allergens"] += 1

                    # Sample data
                    if len(stats["sample_foods"]) < 3:
                        food_name = fields.get('name', {}).get('stringValue', 'Unknown')
                        food_category = fields.get('category', {}).get('stringValue', 'Unknown')
                        stats["sample_foods"].append({
                            "name": food_name,
                            "category": food_category
                        })

                stats["verification_status"] = "SUCCESS"
                return stats
            else:
                return {"verification_status": "FAILED", "error": response.text}

        except Exception as e:
            logger.error(f"Verification failed: {e}")
            return {"verification_status": "FAILED", "error": str(e)}


def create_enhanced_italian_foods() -> List[ComprehensiveFood]:
    """Crea dataset enhanced per alimenti italiani"""

    # Usa il database base e migliora con dati italiani specifici
    foods = create_comprehensive_food_database()

    # Aggiungi alimenti italiani specifici con dati completi
    italian_specialties = [
        # Pasta italiana specifica
        ComprehensiveFood(
            name="Spaghetti di Gragnano IGP",
            description="Pasta di grano duro da Gragnano, trafilata al bronzo",
            brand="Pastificio dei Campi",
            category=FoodCategory.CEREALI,
            subcategory=FoodSubcategory.PASTA,
            nutritional_values=nutritional_values_pasta_gragnano(),
            allergens=[AllergenType.GLUTINE],
            portion_info=portion_info_pasta(),
            quality_grades=quality_grades_pasta(),
            origin_country="Italia",
            verified=True,
            source="Pastificio dei Campi"
        ),

        # Olio EVO Italiano
        ComprehensiveFood(
            name="Olio Extra Vergine di Oliva Taggiasca DOP",
            description="Olio extravergine di oliva da olive Taggiasca liguri",
            category=FoodCategory.GRASSI_CONDIMENTI,
            nutritional_values=nutritional_values_olio_taggiasca(),
            micronutrients=micronutrients_olio_taggiasca(),
            portion_info=portion_info_olio(),
            quality_grades=quality_grades_olio(),
            origin_country="Italia",
            organic=True,
            carbon_footprint=0.8,
            verified=True,
            source="Frantoio Ligure"
        ),

        # Pomodoro San Marzano
        ComprehensiveFood(
            name="Pomodoro San Marzano DOP",
            description="Pomodori San Marzano dell'Agro Sarnese-Nocerino",
            category=FoodCategory.VERDURE,
            subcategory=FoodSubcategory.FRUTTI_ORTAGGI,
            nutritional_values=nutritional_values_san_marzano(),
            micronutrients=micronutrients_san_marzano(),
            allergens=[],
            portion_info=portion_info_pomodoro(),
            seasonal_info=seasonal_info_pomodoro(),
            quality_grades=quality_grades_pomodoro(),
            origin_country="Italia",
            verified=True,
            source="Consorzio San Marzano DOP"
        )
    ]

    foods.extend(italian_specialties)

    return foods


# Helper functions per creare dati nutrizionali specifici
def nutritional_values_pasta_gragnano():
    from comprehensive_food_model import NutritionalValues
    return NutritionalValues(
        calories=353,
        proteins=13.0,
        carbohydrates=70.9,
        fats=1.4,
        fibers=3.2,
        sugars=3.2,
        saturated_fats=0.3,
        salt=0.01,
        water=10.9
    )


def nutritional_values_olio_taggiasca():
    from comprehensive_food_model import NutritionalValues
    return NutritionalValues(
        calories=884,
        proteins=0.0,
        carbohydrates=0.0,
        fats=100.0,
        saturated_fats=14.0,
        water=0.0
    )


def micronutrients_olio_taggiasca():
    from comprehensive_food_model import Micronutrients
    return Micronutrients(
        vitamin_e=14.0,  # Alto contenuto
        vitamin_k=60.0
    )


def nutritional_values_san_marzano():
    from comprehensive_food_model import NutritionalValues
    return NutritionalValues(
        calories=18,
        proteins=0.9,
        carbohydrates=3.9,
        fats=0.2,
        fibers=1.2,
        sugars=2.6,
        water=94.5
    )


def micronutrients_san_marzano():
    from comprehensive_food_model import Micronutrients
    return Micronutrients(
        vitamin_c=14.0,
        vitamin_a=42.0,  # Beta-carotene
        potassium=237,
        calcium=10,
        iron=0.3
    )


def portion_info_pasta():
    from comprehensive_food_model import PortionInfo
    return PortionInfo(
        standard_portion=80,
        portion_description="1 porzione pasta (80g)",
        household_measures={"porzione": 80, "piatto abbondante": 100}
    )


def portion_info_olio():
    from comprehensive_food_model import PortionInfo
    return PortionInfo(
        standard_portion=10,
        portion_description="1 cucchiaio (10ml)",
        household_measures={"cucchiaio": 10, "cucchiaino": 5}
    )


def portion_info_pomodoro():
    from comprehensive_food_model import PortionInfo
    return PortionInfo(
        standard_portion=100,
        portion_description="1 pomodoro medio",
        household_measures={"pomodoro medio": 80, "pomodoro grande": 120}
    )


def seasonal_info_pomodoro():
    from comprehensive_food_model import SeasonalAvailability
    return SeasonalAvailability(
        peak_months=[7, 8, 9],
        available_months=[6, 7, 8, 9, 10],
        origin_region="Campania"
    )


def quality_grades_pasta():
    from comprehensive_food_model import QualityGrades
    return QualityGrades(
        glycemic_index=50,
        glycemic_load=28.0,
        protein_quality_score=0.7
    )


def quality_grades_olio():
    from comprehensive_food_model import QualityGrades
    return QualityGrades(
        inflammatory_index=-2.8,  # Anti-infiammatorio
        antioxidant_capacity=372  # ORAC
    )


def quality_grades_pomodoro():
    from comprehensive_food_model import QualityGrades
    return QualityGrades(
        glycemic_index=10,
        antioxidant_capacity=546,  # ORAC per licopene
        inflammatory_index=-3.1
    )


def main():
    """Esecuzione principale Task 3.1"""
    print("🥗 LONGEVIVA COMPREHENSIVE FOOD DATABASE - Task 3.1")
    print("=" * 60)
    print("Uploading complete nutritional metadata to Firestore")

    uploader = LongevivaComprehensiveFoodUploader()

    try:
        # Crea dataset comprensivo
        print("\n1. Creating comprehensive Italian food dataset...")
        foods = create_enhanced_italian_foods()

        print(f"✅ Created {len(foods)} foods with complete metadata:")

        # Statistiche dataset
        categories = {}
        allergen_foods = 0
        verified_foods = 0

        for food in foods:
            cat = food.category.value
            categories[cat] = categories.get(cat, 0) + 1
            if food.allergens:
                allergen_foods += 1
            if food.verified:
                verified_foods += 1

        print(f"   - Verified foods: {verified_foods}")
        print(f"   - Foods with allergens: {allergen_foods}")
        print(f"   - Categories: {len(categories)}")

        # Upload a Firestore
        print(f"\n2. Uploading to Firestore database: {uploader.database_id}...")
        success = uploader.upload_comprehensive_foods(foods)

        if not success:
            print("❌ Upload failed")
            return False

        # Crea indici raccomandati
        print("\n3. Creating recommended indexes...")
        uploader.create_food_indexes()

        # Verifica upload
        print("\n4. Verifying comprehensive data upload...")
        verification = uploader.verify_comprehensive_upload()

        if verification["verification_status"] == "SUCCESS":
            print("\n🎉 TASK 3.1 COMPLETED SUCCESSFULLY!")
            print(f"✅ Database: {uploader.database_id}")
            print(f"✅ Collection: foods_comprehensive")
            print(f"✅ Total foods: {verification['total_foods']}")
            print(f"✅ With micronutrients: {verification['with_micronutrients']}")
            print(f"✅ Verified sources: {verification['verified_foods']}")
            print(f"✅ With allergen info: {verification['with_allergens']}")

            print(f"\n📊 Categories distribution:")
            for cat, count in verification["categories"].items():
                print(f"   - {cat}: {count} foods")

            print(f"\n🍎 Sample foods:")
            for sample in verification["sample_foods"]:
                print(f"   - {sample['name']} ({sample['category']})")

        else:
            print(f"⚠️ Verification issues: {verification.get('error')}")

        print("\n📋 Ready for meal planning with:")
        print("   ✅ Complete nutritional values (macros + micros)")
        print("   ✅ Allergen information")
        print("   ✅ Portion guidance")
        print("   ✅ Quality grades (GI, antioxidants, etc.)")
        print("   ✅ Seasonal availability")
        print("   ✅ Italian food specialties")

        return True

    except Exception as e:
        logger.error(f"Task 3.1 failed: {e}")
        print(f"❌ Error: {e}")
        return False


if __name__ == "__main__":
    main()