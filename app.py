import streamlit as st
from main import tag_deck
from ai.corrections import save_correction
from ai.train_model import train_model
from collections import Counter
import io
import joblib
from pathlib import Path
import requests

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_MODEL_PATH = BASE_DIR / "ai" / "ml_model.pkl"

@st.cache_data
def get_card_image(name):
    try:
        res = requests.get(
            f"https://api.scryfall.com/cards/named?exact={name}"
        )
        data = res.json()

        if "image_uris" in data:
            return data["image_uris"]["small"]
        elif "card_faces" in data:
            return data["card_faces"][0]["image_uris"]["small"]
    except:
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

    except Exception as e:
        st.error(f"Failed to load model: {e}")

url = st.text_input("Enter Moxfield deck URL:")

if url and st.button("Tag Deck"):
    st.session_state.results = tag_deck(url)

results = st.session_state.results

if results:
    # -----------------
    # Category totals + dropdowns
    # -----------------
    st.subheader("Category Totals")

    # Build mapping: category -> cards
    category_map = {}

    for r in results:
        for tag in r["tags"]:
            if tag not in category_map:
                category_map[tag] = []
            category_map[tag].append(r)

    # Display
    for cat, cards in sorted(category_map.items()):

        # Header with count
        with st.expander(f"{cat} ({len(cards)})"):

            for r in cards:
                col1, col2 = st.columns([1, 3])

                with col1:
                    try:
                        # Fetch card image from Scryfall
                        img = get_card_image(r["name"])
                        if img:
                            st.image(img)

                        if "image_uris" in data:
                            st.image(data["image_uris"]["small"])
                        elif "card_faces" in data:
                            st.image(data["card_faces"][0]["image_uris"]["small"])
                    except:
                        st.write("No image")

                with col2:
                    st.write(f"**{r['name']}**")
                    st.write(", ".join(r["tags"]))

    # -----------------
    # Manual corrections
    # -----------------
    st.subheader("Manual Corrections")

    cards_no_manual = [r for r in results if r["source"] != "manual"]
    card_names = [r["name"] for r in cards_no_manual]

    selected_cards = st.multiselect(
        "Select cards to correct",
        card_names
    )

    for sel_name in selected_cards:
        st.text_input(
            f"Tags for {sel_name}",
            key=f"input_{sel_name}"
        )

    if selected_cards and st.button("Save All Corrections"):
        saved = 0

        for sel_name in selected_cards:
            tags_str = st.session_state.get(f"input_{sel_name}", "")
            correct_tags = [t.strip() for t in tags_str.split(",") if t.strip()]

            if correct_tags:
                card_obj = next(r["card"] for r in cards_no_manual if r["name"] == sel_name)
                save_correction(card_obj, correct_tags)
                saved += 1

        st.success(f"Saved {saved} corrections")

    # -----------------
    # Retrain
    # -----------------
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