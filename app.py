import streamlit as st
from main import tag_deck
from ml.corrections import save_correction
from ml.train_model import train_model
from collections import Counter
import io
import joblib
from pathlib import Path
import requests
import time

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_MODEL_PATH = BASE_DIR / "ml" / "ml_model.pkl"


# caching the Scryfall image fetch to avoid redundant calls
@st.cache_data
def get_card_image(name):
    try:
        res = requests.get(
            f"https://api.scryfall.com/cards/named?exact={name}"
        )
        data = res.json()

        if "object" in data and data["object"] == "error":
            print(f"ERROR for {name}: {data}")
            return None

        if "image_uris" in data:
            return data["image_uris"]["small"]
        elif "card_faces" in data:
            return data["card_faces"][0]["image_uris"]["small"]

    except Exception as e:
        return None

if "model" not in st.session_state:
    try:
        model, mlb = joblib.load(DEFAULT_MODEL_PATH)

        st.session_state.model = model
        st.session_state.mlb = mlb
        st.session_state.model_name = "ml_model.pkl (default)"

    except Exception as e:
        st.session_state.model = None
        st.session_state.mlb = None
        st.session_state.model_name = "Failed to load default model"
        st.error(f"Error loading default model: {e}")

st.title("Moxfield Deck Tagger")

# session state
if "model" not in st.session_state:
    st.session_state.model = None
    st.session_state.mlb = None
    st.session_state.model_name = "None"
if "results" not in st.session_state:
    st.session_state.results = None
if "loading" not in st.session_state:
    st.session_state.loading = False
if "rendering_complete" not in st.session_state:
    st.session_state.rendering_complete = False
# Initialize url in session state if not present
if "url" not in st.session_state:
    st.session_state.url = ""

st.subheader("Model Selection")

st.write(f"**Current model:** {st.session_state.model_name}")

uploaded_model = st.file_uploader(
    "Select a .pkl model file",
    type=["pkl"],
    key="model_uploader"
)

if uploaded_model is not None:
    try:
        model, mlb = joblib.load(uploaded_model)

        st.session_state.model = model
        st.session_state.mlb = mlb
        st.session_state.model_name = uploaded_model.name

        st.success(f"Loaded model: {uploaded_model.name}")

        st.rerun()

    except Exception as e:
        st.error(f"Failed to load model: {e}")

url = st.text_input("Enter Moxfield deck URL:", key="url")

# Fix: Check if URL has content, not just if it exists in session state
tag_clicked = st.button(
    "Tag Deck",
    disabled=(not st.session_state.get("url", "").strip()) or st.session_state.get("loading", False)
)

if tag_clicked:
    st.session_state.loading = True
    st.session_state.results = None
    st.session_state.rendering_complete = False
    st.rerun()

# Show loading spinner while results are being fetched OR rendered
if st.session_state.loading:
    with st.spinner("Loading..."):
        # Only fetch results if we don't have them yet
        if st.session_state.results is None:
            st.session_state.results = tag_deck(url)
        
        # After fetching, set rendering to complete
        if not st.session_state.rendering_complete:
            # Pre-fetch images for all cards
            if st.session_state.results:
                image_cache = {}
                for r in st.session_state.results:
                    name = r["name"]
                    if name not in image_cache:
                        image_cache[name] = get_card_image(name)
                        time.sleep(0.1)  #  delay to avoid hitting API rate limits
                st.session_state.image_cache = image_cache
            st.session_state.rendering_complete = True
    
    # Clear loading state after everything is done
    if st.session_state.rendering_complete:
        st.session_state.loading = False
        st.rerun()

results = st.session_state.results

if results and st.session_state.rendering_complete:

    # Use cached images if available
    image_cache = getattr(st.session_state, 'image_cache', {})
    
    # If image_cache is empty, rebuild it
    if not image_cache:
        for r in results:
            name = r["name"]
            if name not in image_cache:
                image_cache[name] = get_card_image(name)
        st.session_state.image_cache = image_cache

    # build category mapping: category -> cards
    category_map = {}

    for r in results:
        r["tags"] = [t for t in r["tags"] if t.lower() != "none"]
        for tag in r["tags"]:
            if tag not in category_map:
                category_map[tag] = []
            category_map[tag].append(r)

    # untagged category
    untagged_cards = [r for r in results if not r["tags"]]
    if untagged_cards:
        category_map["Untagged"] = untagged_cards

    all_categories = sorted(list({tag for r in results for tag in r["tags"]}))

    st.subheader("Category Totals")

    
    for idx, (cat, cards) in enumerate(sorted(category_map.items())):
        with st.expander(f"{cat} ({len(cards)})"):

            for r in sorted(cards, key=lambda x: x["name"]):
                col1, col2 = st.columns([1, 3])

                with col1:
                    img = image_cache.get(r["name"])
                    if img:
                        st.image(img)

                with col2:
                    st.write(f"**{r['name']}**")
                    st.write("Current:", ", ".join(r["tags"]))

                    st.markdown("**Manually Tag:**")

                    selected = st.multiselect(
                        "Select tags",
                        options=all_categories,
                        default=r["tags"],
                        key=f"tags_{r['name']}_{cat}"
                    )

                    if st.button(f"Apply to {r['name']}", key=f"btn_{r['name']}_{cat}"):
                        try:
                            save_correction(r["card"], selected)
                            st.success(f"Saved correction for {r['name']}")
                        except Exception as e:
                            st.error(f"Error: {e}")
    
    # retrain ------------------------------
    st.subheader("Retrain Model")

    if st.button("Retrain Model"):
        with st.spinner("Training..."):
            pipeline, mlb = train_model()

            # save to memory buffer
            buffer = io.BytesIO()
            joblib.dump((pipeline, mlb), buffer)
            buffer.seek(0)

        st.success("Model retrained!")

        st.download_button(
            label="Download merged model",
            data=buffer,
            file_name="merged_model.pkl",
            mime="application/octet-stream"
        )