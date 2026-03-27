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


# caching the Scryfall image fetch to avoid redundant calls
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
    
    # category totals + dropdowns ------------------------------
    st.subheader("Category Totals")

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

    # display
    all_categories = sorted(list({tag for r in results for tag in r["tags"]}))
    for cat, cards in sorted(category_map.items()):

        # header with count
        with st.expander(f"{cat} ({len(cards)})"):

            for r in cards:
                col1, col2 = st.columns([1, 3])

                with col1:
                    try:
                        # fetch card image from Scryfall
                        img = get_card_image(r["name"])
                        if img:
                            st.image(img)
                    except:
                        st.write("No image")

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