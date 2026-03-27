import pandas as pd
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import MultiLabelBinarizer
from sklearn.linear_model import LogisticRegression
from sklearn.multiclass import OneVsRestClassifier
from sklearn.pipeline import Pipeline
from pathlib import Path
from ai.corrections import load_corrections
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

def train_model(csv_path=None, save_path=None):
    base_dir = Path(__file__).parent

    if csv_path is None:
        csv_path = base_dir / "training_data.csv"

    df = pd.read_csv(csv_path)

    corrections_df = load_corrections()

    if corrections_df is not None and not corrections_df.empty:
        corrections_df["combined"] = corrections_df["text"]
        corrections_df["tags"] = corrections_df["tags"]

        # weight corrections higher
        corrections_df = pd.concat([corrections_df] * 3, ignore_index=True)

        df["combined"] = df["oracle_text"] + " " + df["type_line"]

        df = pd.concat([
            df[["combined", "tags"]],
            corrections_df[["combined", "tags"]]
        ], ignore_index=True)
    else:
        df["combined"] = df["oracle_text"] + " " + df["type_line"]

    def clean_tags(x):
        if isinstance(x, list):
            return x
        if isinstance(x, str):
            return [t.strip() for t in x.split(",") if t.strip()]
        return []

    df["tags"] = df["tags"].apply(clean_tags)
    df = df[df["tags"].map(len) > 0]

    mlb = MultiLabelBinarizer()
    y = mlb.fit_transform(df["tags"])

    pipeline = Pipeline([
        ("tfidf", TfidfVectorizer(stop_words="english", ngram_range=(1, 2))),
        ("clf", OneVsRestClassifier(
            LogisticRegression(max_iter=1000, class_weight="balanced")
        ))
    ])

    pipeline.fit(df["combined"], y)

    # ✅ optional save to disk
    if save_path:
        joblib.dump((pipeline, mlb), save_path)

    return pipeline, mlb

if __name__ == "__main__":
    print("Starting training...")
    try:
        train_model()
    except FileNotFoundError as e:
        print(f"Error: {e}")