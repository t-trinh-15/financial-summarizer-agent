from typing import Dict, Any

REQUIRED_FIELDS = ["merchant", "total_amount", "date", "category"]


def normalize(value: Any) -> str:
    return str(value or "").strip().lower()


def exact_match(predicted: Dict[str, Any], expected: Dict[str, Any], field: str) -> float:
    return 1.0 if normalize(predicted.get(field)) == normalize(expected.get(field)) else 0.0


def merchant_accuracy(predicted: Dict[str, Any], expected: Dict[str, Any]) -> float:
    return exact_match(predicted, expected, "merchant")


def amount_accuracy(predicted: Dict[str, Any], expected: Dict[str, Any]) -> float:
    return exact_match(predicted, expected, "total_amount")


def date_accuracy(predicted: Dict[str, Any], expected: Dict[str, Any]) -> float:
    return exact_match(predicted, expected, "date")


def category_accuracy(predicted: Dict[str, Any], expected: Dict[str, Any]) -> float:
    return exact_match(predicted, expected, "category")


def field_match_score(predicted: Dict[str, Any], expected: Dict[str, Any]) -> float:
    scores = [exact_match(predicted, expected, field) for field in REQUIRED_FIELDS]
    return sum(scores) / len(scores)


def schema_completeness(predicted: Dict[str, Any]) -> float:
    completed = sum(1 for field in REQUIRED_FIELDS if predicted.get(field))
    return completed / len(REQUIRED_FIELDS)


def unsupported_explanation_check(predicted: Dict[str, Any]) -> bool:
    explanation = normalize(predicted.get("plain_language_explanation"))
    has_unknown = any(
        normalize(predicted.get(field)).startswith("unknown")
        for field in ["merchant", "total_amount", "date"]
    )
    overconfident_terms = ["definitely", "guaranteed", "certainly", "no risk"]
    return not (has_unknown and any(term in explanation for term in overconfident_terms))


def explanation_quality_score(predicted: Dict[str, Any]) -> float:
    explanation = str(predicted.get("plain_language_explanation", "")).strip()
    if len(explanation) < 30:
        return 0.0
    score = 0.0
    if len(explanation) >= 30:
        score += 0.4
    if any(word in explanation.lower() for word in ["appears", "charge", "transaction", "subscription", "receipt", "bill"]):
        score += 0.3
    if not any(word in explanation.lower() for word in ["definitely", "guaranteed", "certainly"]):
        score += 0.3
    return round(min(score, 1.0), 3)

def score_classifier_accuracy(predicted_category: str, expected_category: str) -> float:
    """Exact match between classifier prediction and golden set label."""
    return 1.0 if predicted_category == expected_category else 0.0