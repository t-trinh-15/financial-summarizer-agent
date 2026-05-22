from typing import Dict, Any

REQUIRED_FIELDS = ["merchant", "total_amount", "date", "category"]

def field_match_score(predicted: Dict[str, Any], expected: Dict[str, Any]) -> float:
    matches = 0
    for field in REQUIRED_FIELDS:
        if str(predicted.get(field, "")).strip().lower() == str(expected.get(field, "")).strip().lower():
            matches += 1
    return matches / len(REQUIRED_FIELDS)

def schema_completeness(predicted: Dict[str, Any]) -> float:
    return sum(1 for field in REQUIRED_FIELDS if predicted.get(field)) / len(REQUIRED_FIELDS)

def unsupported_explanation_check(predicted: Dict[str, Any]) -> bool:
    explanation = str(predicted.get("plain_language_explanation", "")).lower()
    has_unknown = any(str(predicted.get(field, "")).lower().startswith("unknown") for field in ["merchant", "total_amount", "date"])
    overconfident_terms = ["definitely", "guaranteed", "certainly", "no risk"]
    return not (has_unknown and any(term in explanation for term in overconfident_terms))
