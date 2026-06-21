import json
import os
from datetime import datetime
from typing import Any, Optional


# ============================================================
# PATH CONFIGURATION
# ============================================================

FEEDBACK_LOG_PATH = os.path.join(
    os.path.dirname(__file__),
    "..",
    "data",
    "feedback_log.json",
)


# ============================================================
# SAVE FEEDBACK
# ============================================================

def save_feedback(
    verdict: str,
    raw_input: str,
    result: Any = None,
    error_type: Optional[str] = None,
    user_correction: Optional[str] = None,
) -> None:
    """
    Appends a structured feedback entry to feedback_log.json.

    Parameters
    ----------
    verdict         : "accepted" or "rejected"
    raw_input       : the original transaction string the user submitted
    result          : the TranslatedTransaction object returned by translate()
    error_type      : one of the 8 error codes, or None if accepted
    user_correction : free-text correction from the user, or None
    """

    log_path = os.path.abspath(FEEDBACK_LOG_PATH)

    # Load existing entries or start fresh
    if os.path.exists(log_path):
        with open(log_path, "r", encoding="utf-8") as f:
            try:
                entries = json.load(f)
            except json.JSONDecodeError:
                entries = []
    else:
        entries = []

    # Extract fields from the Pydantic AI result object
    merchant  = None
    amount    = None
    currency  = None
    category  = None
    confidence = None
    explanation = None

    if result is not None:
        try:
            merchant    = result.merchant
            amount      = str(result.amount)
            currency    = result.currency
            category    = str(result.transaction_type)
            confidence  = str(result.confidence)
            explanation = result.plain_english_explanation
        except Exception:
            pass

    entry = {
        "timestamp":       datetime.now().isoformat(timespec="seconds"),
        "verdict":         verdict,
        "error_type":      error_type,
        "user_correction": user_correction,
        "raw_input":       raw_input,
        "merchant":        merchant,
        "amount":          amount,
        "currency":        currency,
        "category":        category,
        "confidence":      confidence,
        "explanation":     explanation,
    }

    entries.append(entry)

    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(entries, f, indent=2, ensure_ascii=False)