"""MongoDB database connection and operations."""
from typing import Optional, Dict, List
from pymongo import MongoClient
from pymongo.database import Database
from pymongo.collection import Collection
from apps.config.Setting import settings
from apps.config.Tracing import get_logger

logger = get_logger(__name__)


class MongoDB:
    """MongoDB connection manager."""
    
    _client: Optional[MongoClient] = None
    _database: Optional[Database] = None
    
    @classmethod
    def connect(cls) -> None:
        """Establish MongoDB connection."""
        if cls._client is None:
            try:
                cls._client = MongoClient(settings.mongodb_url)
                cls._database = cls._client[settings.mongodb_database]
                logger.info(f"Connected to MongoDB: {settings.mongodb_database}")
            except Exception as e:
                logger.error(f"Failed to connect to MongoDB: {e}")
                raise
    
    @classmethod
    def disconnect(cls) -> None:
        """Close MongoDB connection."""
        if cls._client:
            cls._client.close()
            cls._client = None
            cls._database = None
            logger.info("Disconnected from MongoDB")
    
    @classmethod
    def get_database(cls) -> Database:
        """Get database instance."""
        if cls._database is None:
            cls.connect()
        return cls._database
    
    @classmethod
    def get_collection(cls, collection_name: str) -> Collection:
        """Get a collection from the database."""
        db = cls.get_database()
        return db[collection_name]


class ProductRepository:
    """Repository for product data."""
    
    COLLECTION_NAME = "products"
    
    @classmethod
    def get_collection(cls) -> Collection:
        """Get products collection."""
        return MongoDB.get_collection(cls.COLLECTION_NAME)
    
    @classmethod
    def get_product_by_id(cls, product_id: str) -> Optional[Dict]:
        """Get product by ID (ASIN)."""
        collection = cls.get_collection()
        return collection.find_one({"asin": product_id})
    
    @classmethod
    def get_products_by_ids(cls, product_ids: List[str]) -> List[Dict]:
        """Get multiple products by IDs."""
        collection = cls.get_collection()
        return list(collection.find({"asin": {"$in": product_ids}}))
    
    @classmethod
    def get_product_description(cls, product_id: str) -> Optional[str]:
        """Get product description for a given product ID."""
        product = cls.get_product_by_id(product_id)
        if product:
            # Use product_description field (which contains title + categories)
            # Fall back to product_title if description is not available
            description = product.get("product_description", "")
            if not description:
                description = product.get("product_title", "")
            return description.strip()
        return None
    
    @classmethod
    def bulk_insert(cls, products: List[Dict], upsert: bool = True) -> None:
        """
        Insert multiple products. Uses upsert to handle duplicates gracefully.
        
        Args:
            products: List of product dictionaries to insert
            upsert: If True, update existing products instead of skipping (default: True)
        """
        if not products:
            return
        collection = cls.get_collection()
        # Create index on asin for faster lookups and to prevent duplicates
        collection.create_index("asin", unique=True)
        
        if upsert:
            # Use bulk_write with replace_one for upsert behavior
            from pymongo import UpdateOne
            operations = []
            for product in products:
                operations.append(
                    UpdateOne(
                        {"asin": product["asin"]},
                        {"$set": product},
                        upsert=True
                    )
                )
            if operations:
                result = collection.bulk_write(operations, ordered=False)
                logger.info(f"Upserted {result.upserted_count} new products, "
                          f"updated {result.modified_count} existing products")
        else:
            # Try insert_many, skip duplicates
            try:
                collection.insert_many(products, ordered=False)
                logger.info(f"Inserted {len(products)} products")
            except Exception as e:
                # If duplicates exist, insert them one by one
                inserted = 0
                skipped = 0
                for product in products:
                    try:
                        collection.insert_one(product)
                        inserted += 1
                    except Exception:
                        skipped += 1
                logger.info(f"Inserted {inserted} products, skipped {skipped} duplicates")

