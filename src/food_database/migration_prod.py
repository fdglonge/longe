#!/usr/bin/env python3
"""
Longeviva Food Database Production Migration
Migrates validated food data from development to production environment
"""

import json
import logging
from typing import Dict, List, Any, Optional
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class LongevivaDatabaseMigrator:
    """Handle migration between Firebase environments"""

    def __init__(self,
                 dev_project: str = "longeviva-web-app-dev-sviluppo",
                 prod_project: str = "longeviva-web-app-prod"):
        self.dev_project = dev_project
        self.prod_project = prod_project
        self.dev_db = None
        self.prod_db = None

    def initialize_environments(self,
                                dev_credentials: str = "dev-service-account.json",
                                prod_credentials: str = "prod-service-account.json"):
        """Initialize both development and production Firebase connections"""
        try:
            # Initialize development
            if os.path.exists(dev_credentials):
                dev_cred = credentials.Certificate(dev_credentials)
                dev_app = firebase_admin.initialize_app(dev_cred, {
                    'projectId': self.dev_project
                }, name='dev')
                self.dev_db = firestore.client(app=dev_app)
                logger.info(f"Development environment initialized: {self.dev_project}")

            # Initialize production
            if os.path.exists(prod_credentials):
                prod_cred = credentials.Certificate(prod_credentials)
                prod_app = firebase_admin.initialize_app(prod_cred, {
                    'projectId': self.prod_project
                }, name='prod')
                self.prod_db = firestore.client(app=prod_app)
                logger.info(f"Production environment initialized: {self.prod_project}")

        except Exception as e:
            logger.error(f"Environment initialization failed: {e}")
            raise

    def validate_dev_data(self, collection_name: str = "foods") -> Dict[str, Any]:
        """Validate development data before migration"""
        try:
            if not self.dev_db:
                raise Exception("Development database not initialized")

            collection_ref = self.dev_db.collection(collection_name)
            docs = collection_ref.get()

            validation_results = {
                "total_count": len(docs),
                "valid_foods": 0,
                "invalid_foods": 0,
                "validation_errors": [],
                "sample_data": []
            }

            required_fields = ["name", "calories", "weight", "proteins", "fats", "carbohydrates"]

            for doc in docs:
                data = doc.to_dict()

                # Check required fields
                missing_fields = [field for field in required_fields if field not in data]
                if missing_fields:
                    validation_results["invalid_foods"] += 1
                    validation_results["validation_errors"].append({
                        "doc_id": doc.id,
                        "error": f"Missing fields: {missing_fields}"
                    })
                    continue

                # Check data format
                if not all(isinstance(data[field], str) for field in required_fields):
                    validation_results["invalid_foods"] += 1
                    validation_results["validation_errors"].append({
                        "doc_id": doc.id,
                        "error": "Invalid field types"
                    })
                    continue

                validation_results["valid_foods"] += 1

                # Collect sample data
                if len(validation_results["sample_data"]) < 5:
                    validation_results["sample_data"].append(data)

            logger.info(f"Validation complete: {validation_results['valid_foods']} valid, "
                        f"{validation_results['invalid_foods']} invalid foods")

            return validation_results

        except Exception as e:
            logger.error(f"Validation failed: {e}")
            return {"error": str(e)}

    def export_dev_data(self, collection_name: str = "foods",
                        output_file: str = "longeviva_foods_export.json") -> bool:
        """Export development data to JSON file"""
        try:
            if not self.dev_db:
                raise Exception("Development database not initialized")

            collection_ref = self.dev_db.collection(collection_name)
            docs = collection_ref.get()

            export_data = {
                "export_timestamp": datetime.now().isoformat(),
                "source_project": self.dev_project,
                "collection": collection_name,
                "total_count": len(docs),
                "foods": []
            }

            for doc in docs:
                food_data = doc.to_dict()
                # Convert datetime objects to strings
                for key, value in food_data.items():
                    if isinstance(value, datetime):
                        food_data[key] = value.isoformat()

                export_data["foods"].append({
                    "id": doc.id,
                    "data": food_data
                })

            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)

            logger.info(f"Data exported to {output_file}: {len(docs)} foods")
            return True

        except Exception as e:
            logger.error(f"Export failed: {e}")
            return False

    def import_to_production(self,
                             collection_name: str = "foods",
                             backup_existing: bool = True,
                             dry_run: bool = True) -> bool:
        """Import validated data to production"""
        try:
            if not self.prod_db:
                raise Exception("Production database not initialized")

            if dry_run:
                logger.info("🔍 DRY RUN MODE - No actual changes will be made")

            collection_ref = self.prod_db.collection(collection_name)

            # Backup existing production data
            if backup_existing and not dry_run:
                backup_file = f"prod_backup_{collection_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                self._backup_collection(collection_ref, backup_file)

            # Get development data
            if not self.dev_db:
                raise Exception("Development database not initialized")

            dev_collection = self.dev_db.collection(collection_name)
            dev_docs = dev_collection.get()

            logger.info(f"Migrating {len(dev_docs)} foods to production...")

            if dry_run:
                logger.info(f"Would migrate {len(dev_docs)} foods to production")
                return True

            # Clear existing production data (optional)
            # self._clear_collection(collection_ref)

            # Import in batches
            batch_size = 500
            batch = self.prod_db.batch()
            batch_count = 0

            for i, doc in enumerate(dev_docs):
                data = doc.to_dict()

                # Update timestamps
                data['migrated_at'] = datetime.now()
                data['updated_at'] = datetime.now()

                # Create new document in production
                new_doc_ref = collection_ref.document()
                batch.set(new_doc_ref, data)
                batch_count += 1

                if batch_count >= batch_size:
                    batch.commit()
                    batch = self.prod_db.batch()
                    batch_count = 0
                    logger.info(f"Migrated {i + 1} foods...")

            # Commit remaining
            if batch_count > 0:
                batch.commit()

            logger.info(f"✅ Migration completed: {len(dev_docs)} foods migrated to production")
            return True

        except Exception as e:
            logger.error(f"Migration to production failed: {e}")
            return False

    def _backup_collection(self, collection_ref, backup_file: str):
        """Backup collection to JSON file"""
        docs = collection_ref.get()
        backup_data = {
            "backup_timestamp": datetime.now().isoformat(),
            "collection": collection_ref.id,
            "count": len(docs),
            "data": []
        }

        for doc in docs:
            data = doc.to_dict()
            for key, value in data.items():
                if isinstance(value, datetime):
                    data[key] = value.isoformat()
            backup_data["data"].append({"id": doc.id, "data": data})

        with open(backup_file, 'w', encoding='utf-8') as f:
            json.dump(backup_data, f, ensure_ascii=False, indent=2)

        logger.info(f"Backup saved to {backup_file}")

    def verify_migration(self, collection_name: str = "foods") -> Dict[str, Any]:
        """Verify migration success"""
        try:
            if not self.dev_db or not self.prod_db:
                raise Exception("Both databases must be initialized")

            dev_count = len(self.dev_db.collection(collection_name).get())
            prod_count = len(self.prod_db.collection(collection_name).get())

            verification = {
                "dev_count": dev_count,
                "prod_count": prod_count,
                "migration_success": dev_count == prod_count,
                "difference": prod_count - dev_count
            }

            if verification["migration_success"]:
                logger.info("✅ Migration verification successful")
            else:
                logger.warning(f"⚠️  Count mismatch: dev={dev_count}, prod={prod_count}")

            return verification

        except Exception as e:
            logger.error(f"Verification failed: {e}")
            return {"error": str(e)}


def main():
    """Execute migration workflow"""
    migrator = LongevivaDatabaseMigrator()

    print("🚀 Longeviva Food Database Migration")
    print("====================================")

    try:
        # Initialize environments
        migrator.initialize_environments()

        # Validate development data
        print("\n1. Validating development data...")
        validation = migrator.validate_dev_data()

        if validation.get("error"):
            print(f"❌ Validation failed: {validation['error']}")
            return

        print(f"✅ Validation complete:")
        print(f"   - Total foods: {validation['total_count']}")
        print(f"   - Valid foods: {validation['valid_foods']}")
        print(f"   - Invalid foods: {validation['invalid_foods']}")

        if validation['invalid_foods'] > 0:
            print("⚠️  Invalid foods found. Review and fix before migration.")
            for error in validation['validation_errors'][:5]:
                print(f"   - {error}")
            return

        # Export data
        print("\n2. Exporting development data...")
        export_success = migrator.export_dev_data()

        if not export_success:
            print("❌ Export failed")
            return

        print("✅ Data exported successfully")

        # Test migration (dry run)
        print("\n3. Testing migration (dry run)...")
        dry_run_success = migrator.import_to_production(dry_run=True)

        if not dry_run_success:
            print("❌ Dry run failed")
            return

        print("✅ Dry run successful")

        # Confirm actual migration
        confirm = input("\n🔥 Ready for PRODUCTION migration. Continue? (y/N): ")
        if confirm.lower() != 'y':
            print("Migration cancelled")
            return

        # Actual migration
        print("\n4. Migrating to production...")
        migration_success = migrator.import_to_production(dry_run=False)

        if not migration_success:
            print("❌ Migration failed")
            return

        # Verify migration
        print("\n5. Verifying migration...")
        verification = migrator.verify_migration()

        if verification.get("error"):
            print(f"❌ Verification error: {verification['error']}")
            return

        if verification["migration_success"]:
            print("🎉 Migration completed successfully!")
            print(f"   - Development: {verification['dev_count']} foods")
            print(f"   - Production: {verification['prod_count']} foods")
        else:
            print("⚠️  Migration verification failed")
            print(f"   - Count difference: {verification['difference']}")

    except Exception as e:
        logger.error(f"Migration workflow failed: {e}")
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()