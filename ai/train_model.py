import pandas as pd
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import MultiLabelBinarizer
from sklearn.linear_model import LogisticRegression
from sklearn.multiclass import OneVsRestClassifier
from sklearn.pipeline import Pipeline
from pathlib import Path
from corrections import load_corrections

def train_model(csv_path=None):
    base_dir = Path(__file__).parent
    if csv_path is None:
        csv_path = base_dir / "training_data.csv"

    df = pd.read_csv(csv_path)

    corrections_df = load_corrections()
    if corrections_df is not None:
        df = pd.concat([df, corrections_df], ignore_index=True)

    df["combined"] = df["oracle_text"] + " " + df["type_line"]
    df["tags"] = df["tags"].apply(lambda x: x.split(","))

    df = df[df["tags"].notna()]  # remove NaN rows

    df["tags"] = df["tags"].apply(
        lambda x: [t.strip() for t in str(x).split(",") if t.strip()]
    )

    df = df[df["tags"].map(len) > 0]  # remove empty tag rows

    mlb = MultiLabelBinarizer()
    y = mlb.fit_transform(df["tags"])

    pipeline = Pipeline([
        ("tfidf", TfidfVectorizer(stop_words="english", ngram_range=(1, 2))),
        ("clf", OneVsRestClassifier(LogisticRegression(max_iter=1000, class_weight="balanced")))
    ])

    pipeline.fit(df["combined"], y)

    out_path = base_dir / "ml_model.pkl"
    joblib.dump((pipeline, mlb), out_path)
    print(f"Trained model and wrote {out_path}")

if __name__ == "__main__":
    print("Starting training...")
    try:
        train_model()
    except FileNotFoundError as e:
        print(f"Error: {e}")