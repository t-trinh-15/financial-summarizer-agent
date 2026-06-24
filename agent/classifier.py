import joblib
from pathlib import Path
from functools import lru_cache

MODEL_PATH = Path(__file__).parent.parent / 'shared' / 'category_classifier.pkl'

@lru_cache(maxsize=1)
def _load_model():
    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"Classifier not found at {MODEL_PATH}. "
            "Run: python -m scripts.train_classifier"
        )
    return joblib.load(MODEL_PATH)

def predict_category(transaction_text: str) -> str | None:
    """
    Returns a category label only when the classifier is highly confident.
    Threshold raised to 0.92 to reduce false-positive 'purchase' overrides
    on ambiguous inputs like restaurant receipts and utility bills.
    """
    model = _load_model()
    proba = model.predict_proba([transaction_text])[0]
    if proba.max() < 0.92:
        return None
    return model.classes_[proba.argmax()]