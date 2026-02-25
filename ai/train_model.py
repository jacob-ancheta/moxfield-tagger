import pandas as pd
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import MultiLabelBinarizer
from sklearn.linear_model import LogisticRegression
from sklearn.multiclass import OneVsRestClassifier
from sklearn.pipeline import Pipeline
from pathlib import Path

def train_model(csv_path=None):
    base_dir = Path(__file__).parent
    if csv_path is None:
        csv_path = base_dir / "training_data.csv"

    df = pd.read_csv(csv_path)

    df["combined"] = df["oracle_text"] + " " + df["type_line"]
    df["tags"] = df["tags"].apply(lambda x: x.split(","))

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