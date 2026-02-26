"""API controller for product endpoints."""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from collections import defaultdict
from apps.database.Mongo import ProductRepository
from apps.config.Tracing import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/products", tags=["products"], redirect_slashes=False)


def count_non_empty_fields(product: dict) -> int:
    """Count number of non-empty fields in a product."""
    count = 0
    for key, value in product.items():
        if key == "_id":
            continue
        if value is not None and value != "":
            if isinstance(value, (list, dict)):
                if len(value) > 0:
                    count += 1
            else:
                count += 1
    return count


def select_best_product(products: list) -> dict:
    """
    Select the best product from a list of products with the same parent_asin.
    Prefers products with more complete data, images, and ratings.
    """
    if len(products) == 1:
        return products[0]
    
    def score_product(product: dict) -> tuple:
        """Calculate a score for product quality (higher is better)."""
        field_count = count_non_empty_fields(product)
        has_image = 1 if product.get("product_image_url") else 0
        has_rating = 1 if product.get("product_avg_rating") else 0
        rating_value = product.get("product_avg_rating", 0) or 0
        return (field_count, has_image, has_rating, rating_value)
    
    # Sort by score (descending) and return the best one
    products.sort(key=score_product, reverse=True)
    return products[0]


def has_required_fields(product: dict) -> bool:
    """
    Check if product has all required fields for display.
    Required fields: asin, product_title, product_price
    """
    asin = (product.get("asin") or "").strip()
    title = (product.get("product_title") or "").strip()
    price = (product.get("product_price") or "").strip()
    
    return bool(asin and title and price)


def filter_valid_products(products: list) -> list:
    """
    Filter out products missing required fields.
    """
    return [p for p in products if has_required_fields(p)]


def deduplicate_by_parent_asin(products: list) -> list:
    """
    Deduplicate products by parent_asin.
    Products with the same parent_asin are considered variants of the same product.
    """
    # Group by parent_asin (use asin if parent_asin is empty/null)
    groups = defaultdict(list)
    
    for product in products:
        parent_asin = (product.get("parent_asin") or "").strip()
        if not parent_asin:
            # If no parent_asin, use asin as the grouping key
            parent_asin = (product.get("asin") or "").strip()
        
        if parent_asin:
            groups[parent_asin].append(product)
    
    # Select best product from each group
    deduplicated = []
    for parent_asin, group_products in groups.items():
        best_product = select_best_product(group_products)
        deduplicated.append(best_product)
    
    return deduplicated


@router.get("")
@router.get("/")
def get_products(
    limit: int = Query(20, ge=1, le=100, description="Number of products to return"),
    skip: int = Query(0, ge=0, description="Number of products to skip"),
    category: Optional[str] = Query(None, description="Filter by main category")
) -> dict:
    """
    Get a list of products with pagination.
    Products are deduplicated by parent_asin (only one product per parent_asin group is returned).
    
    Args:
        limit: Maximum number of products to return (default: 20, max: 100)
        skip: Number of products to skip for pagination (default: 0)
        category: Optional category filter
    
    Returns:
        Dictionary with products list and metadata
    """
    try:
        collection = ProductRepository.get_collection()
        
        # Build query
        query = {}
        if category:
            query["product_main_category"] = category
        
        # Fetch more products than needed to account for deduplication
        # We'll fetch up to 2x the limit to ensure we have enough after deduplication
        fetch_limit = max(limit * 2, 100)
        
        # Get products sorted by rating (descending)
        cursor = collection.find(query).sort("product_avg_rating", -1).limit(fetch_limit)
        all_products = list(cursor)
        
        # Remove MongoDB _id field
        for product in all_products:
            product.pop("_id", None)
        
        # Filter out products missing required fields (price, title, etc.)
        valid_products = filter_valid_products(all_products)
        
        # Deduplicate by parent_asin
        deduplicated_products = deduplicate_by_parent_asin(valid_products)
        
        # Apply pagination after deduplication
        total_unique = len(deduplicated_products)
        paginated_products = deduplicated_products[skip:skip + limit]
        
        logger.info(
            f"Retrieved {len(paginated_products)} unique products "
            f"(after deduplication: {len(all_products)} -> {total_unique}, skip={skip}, limit={limit})"
        )
        
        return {
            "products": paginated_products,
            "total": total_unique,
            "skip": skip,
            "limit": limit,
            "has_more": (skip + limit) < total_unique
        }
        
    except Exception as e:
        logger.error(f"Error fetching products: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{asin}")
def get_product(asin: str) -> dict:
    """
    Get a single product by ASIN.
    
    Args:
        asin: Product ASIN identifier
    
    Returns:
        Product dictionary
    """
    try:
        product = ProductRepository.get_product_by_id(asin)
        
        if not product:
            raise HTTPException(status_code=404, detail=f"Product with ASIN {asin} not found")
        
        # Remove MongoDB _id field
        product.pop("_id", None)
        
        logger.info(f"Retrieved product: {asin}")
        return product
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching product {asin}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/categories/list")
def get_categories() -> dict:
    """
    Get list of available product categories.
    
    Returns:
        Dictionary with list of unique categories
    """
    try:
        collection = ProductRepository.get_collection()
        
        # Get distinct categories
        categories = collection.distinct("product_main_category")
        categories = [cat for cat in categories if cat]  # Filter out None/empty
        
        logger.info(f"Retrieved {len(categories)} categories")
        
        return {
            "categories": sorted(categories),
            "count": len(categories)
        }
        
    except Exception as e:
        logger.error(f"Error fetching categories: {e}")
        raise HTTPException(status_code=500, detail=str(e))
