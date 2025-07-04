import os
import shutil
import uuid
import json
import hashlib
from backend.nutrition import NutritionFetcher

def get_image_hash(image_path):
    with open(image_path, 'rb') as f:
        return hashlib.md5(f.read()).hexdigest()

def save_image_and_fetch_nutrition(image_path, label, 
                                    dest_dir="data/images", 
                                    json_path="nutrition/nutrition.json",
                                    cache_path="data/image_cache.json"):
    os.makedirs(dest_dir, exist_ok=True)
    os.makedirs(os.path.dirname(cache_path), exist_ok=True)

    # Generate hash of image
    img_hash = get_image_hash(image_path)

    # Load image-label cache
    if os.path.exists(cache_path):
        with open(cache_path, "r") as f:
            cache = json.load(f)
    else:
        cache = {}

    # Save image and label if not already cached
    if img_hash not in cache:
        unique_name = f"{label.lower().replace(' ', '_')}_{uuid.uuid4().hex[:6]}.jpg"
        dest_path = os.path.join(dest_dir, unique_name)
        shutil.copy(image_path, dest_path)
        cache[img_hash] = label.lower()

        # Update cache file
        with open(cache_path, "w") as f:
            json.dump(cache, f, indent=2)

    # Fetch and update nutrition info if not already there
    fetcher = NutritionFetcher(local_json=json_path)
    nutrition = fetcher.fetch_from_openfoodfacts(label)

    if "error" not in nutrition:
        if os.path.exists(json_path):
            with open(json_path, "r") as f:
                data = json.load(f)
        else:
            data = {}
        data[label.lower()] = nutrition
        with open(json_path, "w") as f:
            json.dump(data, f, indent=2)

    return nutrition
