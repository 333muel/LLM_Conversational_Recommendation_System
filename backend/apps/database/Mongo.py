"""MongoDB database connection and operations."""
from datetime import datetime
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
    def filter_products(
        cls, 
        product_ids: List[str], 
        category: Optional[str] = None,
        max_price: Optional[float] = None,
        min_rating: Optional[float] = None,
        keywords: Optional[List[str]] = None
    ) -> List[Dict]:
        """
        Filter a list of product IDs by additional constraints using Text Index.
        """
        collection = cls.get_collection()
        
        # Ensure text index exists
        # weights priority: title > categories > description
        collection.create_index([
            ("product_title", "text"),
            ("product_categories", "text"),
            ("product_description", "text")
        ], weights={
            "product_title": 10,
            "product_categories": 5,
            "product_description": 1
        }, name="product_text_index")

        query = {"asin": {"$in": product_ids}}
        
        # Combine category and keywords for text search
        search_terms = []
        if category:
            search_terms.append(category)
        if keywords:
            search_terms.extend(keywords)
            
        if search_terms:
            query["$text"] = {"$search": " ".join(search_terms)}

        if min_rating is not None:
            query["product_avg_rating"] = {"$gte": min_rating}
            
        # If search terms exist, sort by text score and filter by threshold
        if search_terms:
            results = list(collection.find(
                query,
                {"score": {"$meta": "textScore"}}
            ).sort([("score", {"$meta": "textScore"})]))
            
            # Lower limit threshold to avoid irrelevant matches
            # A score of 1.0 is a reasonable starting point for "relevant enough"
            results = [p for p in results if p.get("score", 0) >= 1.0]
        else:
            results = list(collection.find(query))
        
        # Post-process price filtering in Python because it's a string in DB
        if max_price is not None:
            filtered_results = []
            for p in results:
                try:
                    price_str = p.get("product_price", "0").replace("$", "").strip()
                    if float(price_str) <= max_price:
                        filtered_results.append(p)
                except (ValueError, TypeError):
                    filtered_results.append(p)
            return filtered_results
            
        return results

    @classmethod
    def get_top_rated_by_category(cls, category: str, limit: int = 10) -> List[Dict]:
        """Get best rated products in a category using text index with threshold."""
        collection = cls.get_collection()
        
        # Text search with score threshold
        results = list(collection.find(
            {"$text": {"$search": category}},
            {"score": {"$meta": "textScore"}}
        ).sort([
            ("score", {"$meta": "textScore"}),
            ("product_avg_rating", -1)
        ]))
        
        # Apply threshold and limit
        relevant_results = [p for p in results if p.get("score", 0) >= 1.0]
        return relevant_results[:limit]
    
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


class ConversationRepository:
    """Repository for conversation history with volatile storage (TTL)."""
    
    COLLECTION_NAME = "conversations"
    TTL_SECONDS = 3600 * 24  # 24 hours
    
    @classmethod
    def get_collection(cls) -> Collection:
        """Get conversations collection and ensure TTL index."""
        collection = MongoDB.get_collection(cls.COLLECTION_NAME)
        # Create TTL index on 'updated_at' field
        collection.create_index("updated_at", expireAfterSeconds=cls.TTL_SECONDS)
        collection.create_index("conversation_id", unique=True)
        return collection
    
    @classmethod
    def get_history(cls, conversation_id: str) -> List[Dict]:
        """Get conversation history by ID."""
        collection = cls.get_collection()
        doc = collection.find_one({"conversation_id": conversation_id})
        return doc.get("messages", []) if doc else []
    
    @classmethod
    def save_history(cls, conversation_id: str, messages: List[Dict]) -> None:
        """Save conversation history."""
        collection = cls.get_collection()
        collection.update_one(
            {"conversation_id": conversation_id},
            {
                "$set": {
                    "messages": messages,
                    "updated_at": datetime.utcnow()
                }
            },
            upsert=True
        )

