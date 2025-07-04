import json
import requests
import os
import difflib

class NutritionFetcher:
    def __init__(self, local_json="nutrition/nutrition.json"):
        self.local_json = local_json
        if os.path.exists(local_json):
            with open(local_json, "r") as f:
                self.local_data = json.load(f)
        else:
            self.local_data = {}

    def get_info(self, product_name):
        name = product_name.lower()
        if name in self.local_data:
            return {**self.local_data[name], "source": "local"}

        api_data = self.fetch_from_openfoodfacts(product_name)

        if "calories" in api_data and "error" not in api_data:
            key = api_data.get("actual_product_name", product_name).lower()
            self.local_data[key] = api_data
            self.save_to_local()
        return api_data

    def fetch_from_openfoodfacts(self, query):
        try:
            url = "https://world.openfoodfacts.org/cgi/search.pl"
            params = {
                "search_terms": query,
                "search_simple": 1,
                "action": "process",
                "json": 1,
                "page_size": 5
            }

            res = requests.get(url, params=params)
            products = res.json().get("products", [])
            if not products:
                return {"error": "No products found on OpenFoodFacts."}

            # Match best product name
            product_names = [p.get("product_name", "").lower() for p in products if p.get("product_name")]
            best_match = difflib.get_close_matches(query.lower(), product_names, n=1, cutoff=0.4)

            selected = None
            if best_match:
                for p in products:
                    if p.get("product_name", "").lower() == best_match[0]:
                        selected = p
                        break
            else:
                selected = products[0]

            if not selected:
                return {"error": "No valid product found."}

            nutriments = selected.get("nutriments", {})

            return {
                "calories": nutriments.get("energy-kcal_100g", "N/A"),
                "fat": nutriments.get("fat_100g", "N/A"),
                "carbs": nutriments.get("carbohydrates_100g", "N/A"),
                "protein": nutriments.get("proteins_100g", "N/A"),
                "source": "OpenFoodFacts",
                "actual_product_name": selected.get("product_name", query)
            }

        except Exception as e:
            return {"error": f"Failed to fetch from OpenFoodFacts: {str(e)}"}

    def get_info_by_barcode(self, barcode):
        try:
            url = f"https://world.openfoodfacts.org/api/v0/product/{barcode}.json"
            res = requests.get(url)
            data = res.json()

            if data.get("status") != 1:
                return {"error": "Product not found by barcode."}

            product = data["product"]
            nutriments = product.get("nutriments", {})
            return {
                "calories": nutriments.get("energy-kcal_100g", "N/A"),
                "fat": nutriments.get("fat_100g", "N/A"),
                "carbs": nutriments.get("carbohydrates_100g", "N/A"),
                "protein": nutriments.get("proteins_100g", "N/A"),
                "source": "OpenFoodFacts",
                "actual_product_name": product.get("product_name", barcode)
            }

        except Exception as e:
            return {"error": f"Barcode lookup failed: {str(e)}"}

    def save_to_local(self):
        with open(self.local_json, "w") as f:
            json.dump(self.local_data, f, indent=2)
