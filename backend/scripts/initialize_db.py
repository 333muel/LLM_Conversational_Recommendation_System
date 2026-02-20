import json
import sys
import os
from pathlib import Path
from typing import Dict, List, Set, Optional

# Add parent directory to path to allow imports from apps
script_dir = Path(__file__).parent
project_root = script_dir.parent
sys.path.insert(0, str(project_root))

from apps.database.Mongo import ProductRepository, MongoDB
from apps.config.Tracing import get_logger
from apps.config.Setting import settings

logger = get_logger(__name__)

def get_image_url(images: list) -> Optional[str]:
    """Extract the best available image URL from images array."""
    if not images:
        return None
    
    # Try to get MAIN variant first
    main_image = next((img for img in images if img.get("variant") == "MAIN"), None)
    if main_image:
        url = main_image.get("large") or main_image.get("hi_res") or main_image.get("thumb")
        if url: return url
    
    # Fallback to first image
    first_image = images[0]
    return first_image.get("large") or first_image.get("hi_res") or first_image.get("thumb")

def initialize_db(
    inter_path: str,
    item_path: str,
    meta_path: str,
    batch_size: int = 1000
):
    """
    Consolidated script to initialize MongoDB with optimized product data.
    Only includes products present in the training interactions.
    Now independent of cleaned_basic.csv to save space.
    """
    logger.info("Starting consolidated database initialization (Metadata only mode)...")

    # 1. Identify active ASINs and their Parent ASINs from RecBole files
    active_asins: Set[str] = set()
    asin_to_parent: Dict[str, str] = {}

    logger.info(f"Reading active items from {inter_path}...")
    with open(inter_path, 'r', encoding='utf-8') as f:
        # Skip header line
        next(f)
        for line in f:
            parts = line.split('\t')
            if len(parts) > 1:
                active_asins.add(parts[1])

    logger.info(f"Mapping ASINs to Parent ASINs from {item_path}...")
    with open(item_path, 'r', encoding='utf-8') as f:
        next(f)
        for line in f:
            parts = line.split('\t')
            if len(parts) >= 2:
                asin = parts[0].strip()
                parent = parts[1].strip()
                if asin in active_asins:
                    asin_to_parent[asin] = parent

    logger.info(f"Found {len(active_asins)} active ASINs in interactions.")

    # 2. Index metadata from JSONL by parent_asin
    active_parents = set(asin_to_parent.values())
    meta_index: Dict[str, dict] = {}

    logger.info(f"Indexing metadata from {meta_path}...")
    with open(meta_path, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                data = json.loads(line)
                p_asin = data.get("parent_asin")
                if p_asin in active_parents:
                    meta_index[p_asin] = data
            except:
                continue
    logger.info(f"Indexed metadata for {len(meta_index)} parent ASINs.")

    # 3. Merge and Prepare for Insertion
    logger.info("Merging data and preparing for database insertion...")
    db_products = []
    
    for asin in active_asins:
        parent = asin_to_parent.get(asin)
        meta = meta_index.get(parent, {}) if parent else {}

        # Extract Title
        title = meta.get("title") or "Untitled Product"
        
        # Extract Categories
        categories = meta.get("categories") or []
        main_category = meta.get("main_category")

        # Extract Images
        images = meta.get("images", [])
        image_url = get_image_url(images)

        # Build final object
        product = {
            "asin": asin,
            "parent_asin": parent,
            "product_title": title,
            "product_description": f"{title}. Categories: {', '.join(categories) if isinstance(categories, list) else categories}",
            "product_avg_rating": meta.get("average_rating"),
            "product_review_count": meta.get("rating_number") or 0,
            "product_price": str(meta.get("price")) if meta.get("price") else None,
            "product_store": meta.get("store"),
            "product_main_category": main_category,
            "product_image_url": image_url,
            "product_images": images,
            "features": meta.get("features", []),
            "details": meta.get("details", {})
        }
        
        db_products.append(product)

    # 4. Insert into MongoDB
    if not db_products:
        logger.error("No products found to insert!")
        return

    logger.info(f"Inserting {len(db_products)} products into MongoDB ({settings.mongodb_database})...")
    
    try:
        MongoDB.connect()
        collection = ProductRepository.get_collection()
        collection.drop()
        logger.info("Dropped existing collection to recreate from scratch.")
        
        # Batch insert
        for i in range(0, len(db_products), batch_size):
            batch = db_products[i:i+batch_size]
            ProductRepository.bulk_insert(batch, upsert=True)
            if (i // batch_size) % 5 == 0:
                print(f"Inserted {i + len(batch)}/{len(db_products)} products...")
        
        logger.info("Database initialization completed successfully!")
        print(f"Done! {len(db_products)} products inserted into {settings.mongodb_database}.products")

    except Exception as e:
        logger.error(f"Error during database insertion: {e}")
    finally:
        MongoDB.disconnect()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Consolidated DB Initialization (Metadata Only)")
    parser.add_argument("--inter-path", default="/data/amazon_sentiment_200k/amazon_sentiment_200k.inter")
    parser.add_argument("--item-path", default="/data/amazon_sentiment_200k/amazon_sentiment_200k.item")
    parser.add_argument("--meta-path", default="/data/meta_Beauty_and_Personal_Care.jsonl")
    
    args = parser.parse_args()
    
    # Resolve paths (check absolute first, then relative to script for local testing)
    inter_path = Path(args.inter_path)
    if not inter_path.exists(): inter_path = script_dir / "../" / args.inter_path
    
    item_path = Path(args.item_path)
    if not item_path.exists(): item_path = script_dir / "../" / args.item_path
    
    meta_path = Path(args.meta_path)
    if not meta_path.exists(): meta_path = script_dir / "../" / args.meta_path

    # Validate files
    for p in [inter_path, item_path, meta_path]:
        if not p.exists():
            print(f"Error: File not found: {p}")
            print(f"Ensure you have downloaded the data folder and it contains all required files.")
            sys.exit(1)

    initialize_db(str(inter_path), str(item_path), str(meta_path))
