import pandas as pd
from datasets import load_dataset
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import cross_val_score
import joblib, os
from sklearn.metrics import classification_report

# ── Label remapping ──────────────────────────────────────────────
# Maps Hugging Face dataset categories to your six enum values.
LABEL_MAP = {
    "Food & Dining":              "purchase",
    "Shopping & Retail":          "purchase",
    "Entertainment & Recreation": "purchase",
    "Healthcare & Medical":       "purchase",
    "Transportation":             "purchase",
    "Charity & Donations":        "purchase",
    "Utilities & Services":       "fee",
    "Financial Services":         "fee",
    "Income":                     "deposit",
    "Government & Legal":         "transfer",
}

# ── Synthetic data ───────────────────────────────────────────────
# Covers refund and withdrawal which are absent from the HF dataset.
# Subscriptions map to purchase and are already covered above.
SYNTHETIC_DATA = [
    # refund
    {"text": "REFUND Amazon order #1234",                "label": "refund"},
    {"text": "Refund from Uber trip",                    "label": "refund"},
    {"text": "Return credit Gap stores",                 "label": "refund"},
    {"text": "Refund processed Target",                  "label": "refund"},
    {"text": "Credit adjustment refund Apple Store",     "label": "refund"},
    {"text": "Partial refund Airbnb booking",            "label": "refund"},
    {"text": "Refund from cancelled order",              "label": "refund"},
    {"text": "Reversal of charge PayPal",                "label": "refund"},
    {"text": "Merchandise return Best Buy",              "label": "refund"},
    {"text": "Refund Zara online purchase",              "label": "refund"},
    {"text": "Credit back for overcharge",               "label": "refund"},
    {"text": "Refund hotel cancellation Booking.com",    "label": "refund"},
    {"text": "Return refund H&M",                        "label": "refund"},
    {"text": "Refund Delta Airlines ticket",             "label": "refund"},
    {"text": "Chargeback credit card dispute",           "label": "refund"},
    {"text": "Refund Etsy order",                        "label": "refund"},
    {"text": "Reversed transaction Venmo",               "label": "refund"},
    {"text": "Refund subscription cancelled",            "label": "refund"},
    {"text": "Credit adjustment bank error",             "label": "refund"},
    {"text": "Refund ASOS returned item",                "label": "refund"},
    # withdrawal
    {"text": "ATM withdrawal Chase Bank",                "label": "withdrawal"},
    {"text": "Cash withdrawal $200",                     "label": "withdrawal"},
    {"text": "ATM cash withdrawal fee",                  "label": "withdrawal"},
    {"text": "Withdrawal from savings account",          "label": "withdrawal"},
    {"text": "ATM withdrawal Bank of America",           "label": "withdrawal"},
    {"text": "Cash out Wells Fargo ATM",                 "label": "withdrawal"},
    {"text": "ATM withdrawal foreign currency",          "label": "withdrawal"},
    {"text": "Cash advance credit card",                 "label": "withdrawal"},
    {"text": "ATM withdrawal $100 Citibank",             "label": "withdrawal"},
    {"text": "Withdrawal money market account",          "label": "withdrawal"},
    {"text": "ATM cash disbursement",                    "label": "withdrawal"},
    {"text": "Cash withdrawal convenience fee",          "label": "withdrawal"},
    {"text": "ATM withdrawal US Bank",                   "label": "withdrawal"},
    {"text": "Teller cash withdrawal branch",            "label": "withdrawal"},
    {"text": "ATM withdrawal TD Bank",                   "label": "withdrawal"},
    {"text": "Cash withdrawal retirement account",       "label": "withdrawal"},
    {"text": "ATM withdrawal Regions Bank",              "label": "withdrawal"},
    {"text": "Cash withdrawal PNC Bank",                 "label": "withdrawal"},
    {"text": "ATM withdrawal international fee",         "label": "withdrawal"},
    {"text": "Cash withdrawal overdraft",                "label": "withdrawal"},
]


def load_training_data():
    print("Loading dataset from Hugging Face...")
    dataset = load_dataset("mitulshah/transaction-categorization", split="train")
    df = dataset.to_pandas()

    # Remap labels and drop unmapped rows
    df["label"] = df["category"].map(LABEL_MAP)
    df = df.dropna(subset=["label"])
    df = df[["transaction_description", "label"]].rename(
        columns={"transaction_description": "text"}
    )

    # Append synthetic examples for missing classes
    df_synthetic = pd.DataFrame(SYNTHETIC_DATA)
    # Oversample synthetic data so it has enough weight against 4.5M rows
    df_synthetic = pd.concat([df_synthetic] * 500, ignore_index=True)
    df = pd.concat([df, df_synthetic], ignore_index=True).sample(
        frac=1, random_state=42
    )

    print(f"Loaded {len(df):,} examples across {df['label'].nunique()} classes")
    print(df["label"].value_counts())
    return df


def build_pipeline():
    return Pipeline([
        ("tfidf", TfidfVectorizer(
            analyzer="char_wb",
            ngram_range=(2, 4),
            max_features=50_000,
            sublinear_tf=True
        )),
        ("clf", LogisticRegression(
            C=5.0,
            max_iter=1000,
            class_weight="balanced"
        ))
    ])


def evaluate_pipeline(pipeline, X, y):
    print("Running 5-fold cross-validation...")
    scores = cross_val_score(pipeline, X, y, cv=5, scoring="accuracy")
    print(f"CV accuracy: {scores.mean():.3f} ± {scores.std():.3f}")
    return scores.mean()


def report_metrics(pipeline, X, y):
    y_pred = pipeline.predict(X)
    print("\nClassification Report:")
    print(classification_report(y, y_pred))


def export_metrics_csv(pipeline, X, y):
    y_pred = pipeline.predict(X)
    report = classification_report(y, y_pred, output_dict=True)
    df_report = pd.DataFrame(report).transpose()
    os.makedirs("evals/results", exist_ok=True)
    path = "evals/results/category_classifier_metrics.csv"
    df_report.to_csv(path)
    print(f"Classifier metrics saved to {path}")


def save_model(pipeline, X, y):
    pipeline.fit(X, y)
    os.makedirs("shared", exist_ok=True)
    joblib.dump(pipeline, "shared/category_classifier.pkl")
    print("Model saved to shared/category_classifier.pkl")


def main():
    df = load_training_data()
    X, y = df["text"], df["label"]
    pipeline = build_pipeline()
    cv_score = evaluate_pipeline(pipeline, X, y)
    if cv_score < 0.70:
        print("WARNING: CV accuracy below 0.70 — review label remapping")
    save_model(pipeline, X, y)
    report_metrics(pipeline, X, y)
    export_metrics_csv(pipeline, X, y)


if __name__ == "__main__":
    main()