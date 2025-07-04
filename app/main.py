import sys
import os
import json
import pandas as pd
import streamlit as st
from difflib import get_close_matches

# ✅ Set project root path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

# ✅ Imports
from backend.detector import ProductDetector
from backend.nutrition import NutritionFetcher
from backend.updator import save_image_and_fetch_nutrition, get_image_hash
from utils.barcode_reader import read_barcode

# ✅ UI Title
st.markdown("<h1 style='text-align: center;'>📦 Indian Packaged Food Detector</h1>", unsafe_allow_html=True)
st.divider()

use_barcode = st.checkbox("🔳 Automatically scan barcode from uploaded image", value=True)

# ✅ Upload or Camera
uploaded = st.file_uploader("📁 Upload a packaged food image", type=["jpg", "jpeg", "png", "webp"])
image_source = None

if "open_camera" not in st.session_state:
    st.session_state.open_camera = False

st.markdown("<p style='text-align: center; margin-top: 10px;'>📤 <b>OR</b></p>", unsafe_allow_html=True)

if st.button("📸 Take Photo Using Camera"):
    st.session_state.open_camera = True

if st.session_state.open_camera:
    st.info("👉 Use your device camera to capture the product image.")
    camera_image = st.camera_input("📷 Capture here")
    if camera_image:
        image_source = camera_image

if uploaded:
    image_source = uploaded

# ✅ Process image
if image_source:
    with open("temp.jpg", "wb") as f:
        f.write(image_source.getbuffer())

    img_hash = get_image_hash("temp.jpg")

    try:
        with open("data/image_cache.json") as f:
            cache = json.load(f)
    except FileNotFoundError:
        cache = {}

    fetcher = NutritionFetcher()
    nutrition = None

    # ✅ Barcode Detection
    if use_barcode:
        st.markdown("### 🔍 Step 1: Barcode Detection")
        st.caption("Scanning for barcode in image...")
        barcode = read_barcode("temp.jpg")

        if barcode:
            st.success(f"✅ Barcode detected: `{barcode}`")
            nutrition = fetcher.get_info_by_barcode(barcode)

            if "error" not in nutrition:
                label = nutrition.get("actual_product_name", barcode).lower()
                cache[img_hash] = label
                with open("data/image_cache.json", "w") as f:
                    json.dump(cache, f, indent=2)

                with st.expander("📊 View Nutrition Info", expanded=True):
                    display_data = nutrition.get("nutrients", nutrition)
                    df = pd.DataFrame(display_data.items(), columns=["Nutrient", "Value"])
                    st.table(df)
                st.stop()
            else:
                st.warning("⚠️ Product not found using barcode. Proceeding to image detection...")
        else:
            st.warning("❌ No barcode detected.")

        manual_barcode = st.text_input("🔢 Enter barcode manually (optional):")
        if manual_barcode:
            nutrition = fetcher.get_info_by_barcode(manual_barcode)
            if "error" not in nutrition:
                st.success(f"✅ Fetched using barcode: `{manual_barcode}`")
                label = nutrition.get("actual_product_name", manual_barcode).lower()
                cache[img_hash] = label
                with open("data/image_cache.json", "w") as f:
                    json.dump(cache, f, indent=2)

                with st.expander("📊 View Nutrition Info", expanded=True):
                    display_data = nutrition.get("nutrients", nutrition)
                    df = pd.DataFrame(display_data.items(), columns=["Nutrient", "Value"])
                    st.table(df)
                st.stop()
            else:
                st.warning("⚠️ No nutrition info found for entered barcode.")

    # ✅ Cached Match
    if img_hash in cache:
        label = cache[img_hash]
        st.success(f"📌 Found in cache: **{label}**")
        nutrition = fetcher.get_info(label)

        if "error" not in nutrition:
            with st.expander("📊 View Nutrition Info", expanded=True):
                display_data = nutrition.get("nutrients", nutrition)
                df = pd.DataFrame(display_data.items(), columns=["Nutrient", "Value"])
                st.table(df)
        else:
            st.warning(nutrition["error"])

    else:
        # ✅ Model Detection
        st.markdown("### 🧠 Step 2: Image-Based Product Detection")
        detector = ProductDetector()
        label, conf = detector.detect("temp.jpg")

        if label:
            st.success(f"✅ Detected: **{label}** ({conf*100:.1f}%)")
            nutrition = fetcher.get_info(label)

            if "error" not in nutrition:
                cache[img_hash] = nutrition.get("actual_product_name", label).lower()
                with open("data/image_cache.json", "w") as f:
                    json.dump(cache, f, indent=2)

                with st.expander("📊 View Nutrition Info", expanded=True):
                    display_data = nutrition.get("nutrients", nutrition)
                    df = pd.DataFrame(display_data.items(), columns=["Nutrient", "Value"])
                    st.table(df)
            else:
                st.warning("⚠️ Nutrition info not found.")
                user_label = st.text_input("✏️ Enter correct product name:")
                if st.button("📥 Submit"):
                    nutrition = save_image_and_fetch_nutrition("temp.jpg", user_label)
                    cache[img_hash] = nutrition.get("actual_product_name", user_label).lower()
                    with open("data/image_cache.json", "w") as f:
                        json.dump(cache, f, indent=2)

                    st.success("💾 Stored and fetched from OpenFoodFacts ✅")
                    with st.expander("📊 View Nutrition Info", expanded=True):
                        display_data = nutrition.get("nutrients", nutrition)
                        df = pd.DataFrame(display_data.items(), columns=["Nutrient", "Value"])
                        st.table(df)
        else:
            # ✅ Manual Fallback
            st.error("🚫 No product detected from image.")
            user_label = st.text_input("✏️ What do you think the product is (e.g., 'sting')?")

            if user_label:
                close_matches = get_close_matches(user_label.lower(), list(cache.values()), n=1, cutoff=0.6)
                if close_matches:
                    suggested_label = close_matches[0]
                    st.info(f"💡 Did you mean: **{suggested_label}**?")
                    if st.button(f"✅ Use **{suggested_label}**"):
                        nutrition = save_image_and_fetch_nutrition("temp.jpg", suggested_label)
                        cache[img_hash] = suggested_label.lower()
                        with open("data/image_cache.json", "w") as f:
                            json.dump(cache, f, indent=2)
                        st.success("💾 Saved and fetched from OpenFoodFacts ✅")
                        with st.expander("📊 View Nutrition Info", expanded=True):
                            display_data = nutrition.get("nutrients", nutrition)
                            df = pd.DataFrame(display_data.items(), columns=["Nutrient", "Value"])
                            st.table(df)
                elif st.button("📥 Submit"):
                    nutrition = save_image_and_fetch_nutrition("temp.jpg", user_label)
                    cache[img_hash] = nutrition.get("actual_product_name", user_label).lower()
                    with open("data/image_cache.json", "w") as f:
                        json.dump(cache, f, indent=2)
                    st.success("💾 Saved and fetched from OpenFoodFacts ✅")
                    with st.expander("📊 View Nutrition Info", expanded=True):
                        display_data = nutrition.get("nutrients", nutrition)
                        df = pd.DataFrame(display_data.items(), columns=["Nutrient", "Value"])
                        st.table(df)
