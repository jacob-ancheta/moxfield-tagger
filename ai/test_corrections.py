from pathlib import Path
import pandas as pd
import joblib

BASE_DIR = Path(__file__).parent
MODEL_PATH = BASE_DIR / "ml_model.pkl"
CORRECTIONS_PATH = BASE_DIR / "corrections.csv"


def predict_with_ml(card_text, pipeline, mlb, threshold=0.5):
    probs = pipeline.predict_proba([card_text])[0]

    tags = []
    for tag, prob in zip(mlb.classes_, probs):
        if prob >= threshold:
            tags.append(tag)

    return tags


def main():
    if not MODEL_PATH.exists():
        print("No trained model found.")
        return

    if not CORRECTIONS_PATH.exists():
        print("No corrections.csv found.")
        return

    print("Loading model...")
    pipeline, mlb = joblib.load(MODEL_PATH)

    print("Loading corrections...")
    df = pd.read_csv(CORRECTIONS_PATH)

    # Clean + split tags
    df["tags"] = df["tags"].apply(
        lambda x: [t.strip() for t in str(x).split(",") if t.strip().lower() != "na"]
    )

    df = df[df["tags"].map(len) > 0]

    print("\nTesting corrected cards:\n")

    correct_count = 0
    total = len(df)

    for _, row in df.iterrows():
        combined = str(row["oracle_text"]) + " " + str(row["type_line"])
        expected = sorted(row["tags"])
        predicted = sorted(predict_with_ml(combined, pipeline, mlb))

        match = expected == predicted

        print("======================================")
        print("Expected :", expected)
        print("Predicted:", predicted)
        print("Match    :", match)

        if match:
            correct_count += 1

    if total > 0:
        print("\n======================================")
        print(f"Accuracy on corrections: {correct_count}/{total} "
              f"({round(correct_count/total*100, 2)}%)")
    else:
        print("No valid corrected rows to test.")


if __name__ == "__main__":
    main()