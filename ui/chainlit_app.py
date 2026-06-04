# ============================================================
# 1. Imports and project path setup
# ============================================================
# This section imports required libraries and makes sure Python can find
# project-level modules such as agent.agent when running this file from /ui.

import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional

import chainlit as cl

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from agent.agent import translate


# ============================================================
# 2. Display constants
# ============================================================
# These dictionaries control how currencies and confidence levels are displayed
# in the Chainlit UI.

CURRENCY_SYMBOLS = {
    "AED": "د.إ",  "AFN": "؋",   "ALL": "L",    "AMD": "֏",   "ANG": "ƒ",
    "AOA": "Kz",   "ARS": "$",    "AUD": "A$",   "AWG": "ƒ",   "AZN": "₼",
    "BAM": "KM",   "BBD": "Bds$", "BDT": "৳",   "BGN": "лв",  "BHD": "BD",
    "BIF": "Fr",   "BMD": "$",    "BND": "B$",   "BOB": "Bs.", "BRL": "R$",
    "BSD": "$",    "BTN": "Nu",   "BWP": "P",    "BYN": "Br",  "BZD": "BZ$",
    "CAD": "CA$",  "CDF": "Fr",   "CHF": "Fr",   "CLP": "$",   "CNY": "¥",
    "COP": "$",    "CRC": "₡",   "CUP": "$",    "CVE": "$",   "CZK": "Kč",
    "DJF": "Fr",   "DKK": "kr",   "DOP": "RD$",  "DZD": "دج", "EGP": "£",
    "ERN": "Nfk",  "ETB": "Br",   "EUR": "€",    "FJD": "FJ$", "FKP": "£",
    "GBP": "£",    "GEL": "₾",   "GHS": "₵",   "GIP": "£",   "GMD": "D",
    "GNF": "Fr",   "GTQ": "Q",    "GYD": "G$",   "HKD": "HK$", "HNL": "L",
    "HRK": "kn",   "HTG": "G",    "HUF": "Ft",   "IDR": "Rp",  "ILS": "₪",
    "INR": "₹",    "IQD": "ع.د", "IRR": "﷼",   "ISK": "kr",  "JMD": "J$",
    "JOD": "JD",   "JPY": "¥",    "KES": "KSh",  "KGS": "с",  "KHR": "៛",
    "KMF": "Fr",   "KPW": "₩",   "KRW": "₩",   "KWD": "KD",  "KYD": "CI$",
    "KZT": "₸",   "LAK": "₭",   "LBP": "£",    "LKR": "₨",  "LRD": "L$",
    "LSL": "L",    "LYD": "LD",   "MAD": "MAD",  "MDL": "L",   "MGA": "Ar",
    "MKD": "ден", "MMK": "K",    "MNT": "₮",   "MOP": "P",   "MRU": "UM",
    "MUR": "₨",   "MVR": "Rf",   "MWK": "MK",   "MXN": "$",   "MYR": "RM",
    "MZN": "MT",   "NAD": "N$",   "NGN": "₦",   "NIO": "C$",  "NOK": "kr",
    "NPR": "₨",   "NZD": "NZ$",  "OMR": "﷼",   "PAB": "B/.", "PEN": "S/.",
    "PGK": "K",    "PHP": "₱",   "PKR": "₨",   "PLN": "zł",  "PYG": "₲",
    "QAR": "﷼",   "RON": "lei",  "RSD": "din",  "RUB": "₽",  "RWF": "Fr",
    "SAR": "﷼",   "SBD": "SI$",  "SCR": "₨",   "SDG": "£",   "SEK": "kr",
    "SGD": "S$",   "SHP": "£",    "SLL": "Le",   "SOS": "Sh",  "SRD": "$",
    "STN": "Db",   "SVC": "₡",   "SYP": "£",    "SZL": "L",   "THB": "฿",
    "TJS": "SM",   "TMT": "T",    "TND": "DT",   "TOP": "T$",  "TRY": "₺",
    "TTD": "TT$",  "TWD": "NT$",  "TZS": "Sh",   "UAH": "₴",  "UGX": "Sh",
    "USD": "$",    "UYU": "$U",   "UZS": "лв",   "VES": "Bs.S", "VND": "₫",
    "VUV": "Vt",   "WST": "T",    "XAF": "Fr",   "XCD": "EC$", "XOF": "Fr",
    "XPF": "Fr",   "YER": "﷼",   "ZAR": "R",    "ZMW": "ZK",  "ZWL": "$",
}

CONFIDENCE_ICONS = {
    "high": "🟢 High",
    "medium": "🟡 Medium",
    "low": "🔴 Low",
}


# ============================================================
# 3. Input validation and user-friendly error messages
# ============================================================
# These helper functions prevent obviously unrelated inputs from being sent to
# the agent and show friendly messages instead of technical errors.

def looks_like_financial_input(text: str) -> bool:
    """
    Basic UI-side validation for pasted transaction text.

    This is intentionally simple. The backend agent will still make the final
    interpretation, but the UI can reject obviously unrelated or empty inputs.
    """
    if not text or not text.strip():
        return False

    lowered = text.lower()

    financial_keywords = [
        "$", "usd", "debit", "credit", "pos", "ach", "withdrawal",
        "deposit", "payment", "fee", "refund", "autopay", "card",
        "visa", "mastercard", "amex", "bank", "transaction",
        "receipt", "total", "subtotal", "tax", "merchant"
    ]

    has_keyword = any(keyword in lowered for keyword in financial_keywords)
    has_digit = any(char.isdigit() for char in text)

    return has_keyword or has_digit


def friendly_error_message(error_type: str = "general") -> str:
    """
    Return user-friendly error messages instead of exposing technical errors.
    """
    if error_type == "invalid_input":
        return """
I’m designed to analyze receipts and financial transactions.

Please paste a transaction description, bank statement line, or upload a receipt image.
"""

    if error_type == "image_not_ready":
        return """
I received your uploaded file, but the OCR image-processing service is not connected yet.

Please try pasting the receipt text directly for now, or try again once OCR integration is available.
"""

    if error_type == "agent_failure":
        return """
Sorry, I could not process this transaction right now.

Please try again with a clearer transaction description, or try again later.
"""

    return """
Sorry, something went wrong while processing your request.

Please try again.
"""


# ============================================================
# 4. OCR upload preparation
# ============================================================
# These functions prepare the image upload flow for future OCR integration.
# Aayush can later connect the real OCR endpoint inside call_ocr_service().

def validate_uploaded_file(file_path: Optional[str]) -> Optional[str]:
    """
    Basic UI-side validation for uploaded receipt files.

    Returns an error message if the file is not suitable for OCR.
    Returns None if the file passes the basic validation.
    """
    if not file_path:
        return "I could not read the uploaded file. Please try uploading the receipt again."

    path = Path(file_path)

    allowed_extensions = {".png", ".jpg", ".jpeg", ".webp", ".pdf"}
    if path.suffix.lower() not in allowed_extensions:
        return (
            "This file type is not supported for receipt OCR. "
            "Please upload a receipt image such as PNG, JPG, JPEG, WEBP, or PDF."
        )

    max_size_mb = 10
    if path.exists():
        size_mb = path.stat().st_size / (1024 * 1024)
        if size_mb > max_size_mb:
            return (
                f"This file is too large ({size_mb:.1f} MB). "
                f"Please upload a file under {max_size_mb} MB."
            )

    return None


async def call_ocr_service(file_path: str) -> str:
    """
    Placeholder wrapper for the OCR endpoint.

    This function is intentionally prepared for future OCR integration.
    Once the OCR endpoint is ready, replace this placeholder with an HTTP call
    to the OCR service and return the extracted receipt text.
    """
    ocr_endpoint_url = os.getenv("OCR_ENDPOINT_URL")

    if not ocr_endpoint_url:
        raise RuntimeError("OCR endpoint is not configured.")

    # TODO:
    # Replace this placeholder with the real OCR HTTP request once the endpoint,
    # request format, and response schema are confirmed.
    #
    # Expected future flow:
    # 1. Send uploaded file to OCR endpoint
    # 2. Receive extracted text
    # 3. Return extracted text to Chainlit
    #
    # Example future return:
    # return extracted_text

    raise NotImplementedError("OCR endpoint integration is not implemented yet.")


# ============================================================
# 5. Conversation memory helpers
# ============================================================
# This section stores analyzed transactions in the Chainlit user session.
# It prepares the app for future memory-based questions such as:
# "How much did I spend on coffee this week?"

def save_transaction_to_session(result: Dict[str, Any]) -> None:
    """
    Store analyzed transactions in Chainlit session memory.
    """
    transactions = cl.user_session.get("transactions", [])
    transactions.append(result)
    cl.user_session.set("transactions", transactions)


# ============================================================
# 6. Agent call wrapper
# ============================================================
# This function calls the backend financial translator agent and converts
# the agent output into a dictionary that the UI can display.

async def call_agent(input_type: str, content: str) -> Dict[str, Any]:
    """
    Calls the real financial translator agent.
    """
    result = translate(content)

    currency = (result.currency or "USD").upper()
    symbol = CURRENCY_SYMBOLS.get(currency, currency + " ")
    amount_display = f"{symbol}{result.amount}" if result.amount else "—"

    return {
        "input_type": input_type,
        "merchant": result.merchant or "—",
        "amount": amount_display,
        "currency": currency,
        "date": str(result.date) if hasattr(result, "date") and result.date else "—",
        "category": result.transaction_type.value.capitalize() if result.transaction_type else "—",
        "explanation": result.plain_english_explanation or "—",
        "confidence": result.confidence.value if hasattr(result.confidence, "value") else str(result.confidence),
        "raw_input": content,
    }


# ============================================================
# 7. Response formatting / translation card
# ============================================================
# This section formats the agent result into a readable transaction card
# shown in the Chainlit chat.

def format_agent_response(result: Dict[str, Any]) -> str:
    """
    Format the agent result as a polished translation card for Chainlit.
    """
    input_type_label = "📝 Text" if result["input_type"] == "text_paste" else "🖼️ Image"
    confidence_value = str(result.get("confidence", "")).lower()
    confidence_label = CONFIDENCE_ICONS.get(confidence_value, result.get("confidence", "—"))

    return f"""
## Transaction Translation Card

| Field | Result |
|---|---|
| **Input Type** | {input_type_label} |
| **Merchant** | {result.get("merchant", "—")} |
| **Amount** | {result.get("amount", "—")} |
| **Date** | {result.get("date", "—")} |
| **Transaction Type** | {result.get("category", "—")} |
| **Confidence** | {confidence_label} |

### Plain-English Explanation
{result.get("explanation", "—")}

---

### Raw Input
`{result.get("raw_input", "—")}`
"""


# ============================================================
# 8. Chainlit welcome message
# ============================================================
# This message is shown when the user first opens the Chainlit app.

@cl.on_chat_start
async def start():
    cl.user_session.set("transactions", [])

    await cl.Message(
        content="""
# 💰 Personal Finance Expense Tracker Assistant

Welcome! I help you make sense of your bank statements, receipts, and transactions — instantly.

Here is what I can do:
- 📝 **Paste a transaction** from your bank statement and I will translate it into plain English
- 🖼️ **Upload a receipt image** and I will extract the details for you
- 💱 **Recognize currencies** from around the world and display the correct symbol
- 📊 **Categorize your spending** — purchases, transfers, fees, refunds, and more
- 🎯 **Rate my confidence** so you always know how certain I am

**To get started, paste a transaction below or upload a receipt image.**

Example transactions you can try:
> `POS DEBIT 0428 SQ *COFFEE BAR $4.75`
> `ACH WITHDRAWAL CHASE CREDIT CRD AUTOPAY 05/15 -$1,247.83`
> `AMZN MKTP US*1A2B3C 04/22 $34.99`
"""
    ).send()


# ============================================================
# 9. Main Chainlit message flow
# ============================================================
# This is the main UI controller:
# - If the user uploads a file, use the image/OCR flow.
# - If the user pastes text, validate it and send it to the agent.
# - If anything fails, show a friendly error message.

@cl.on_message
async def main(message: cl.Message):
    """
    Main Chainlit message handler.

    If the user uploads a file, the app uses the image upload flow.
    Otherwise, it treats the message as pasted transaction text.
    """

    if message.elements:
        processing_msg = cl.Message(
            content="Processing uploaded receipt image..."
        )
        await processing_msg.send()

        try:
            uploaded_file = message.elements[0]
            file_path = getattr(uploaded_file, "path", None)

            validation_error = validate_uploaded_file(file_path)
            if validation_error:
                processing_msg.content = validation_error
                await processing_msg.update()
                return

            # OCR integration placeholder:
            # Once the OCR endpoint is ready, this function should return extracted text.
            extracted_text = await call_ocr_service(file_path)

            result = await call_agent(
                input_type="image_upload",
                content=extracted_text,
            )

            save_transaction_to_session(result)

            processing_msg.content = format_agent_response(result)
            await processing_msg.update()

        except NotImplementedError:
            processing_msg.content = friendly_error_message("image_not_ready")
            await processing_msg.update()

        except RuntimeError:
            processing_msg.content = friendly_error_message("image_not_ready")
            await processing_msg.update()

        except Exception:
            processing_msg.content = friendly_error_message("agent_failure")
            await processing_msg.update()

    else:
        text_input = message.content.strip()

        if not text_input:
            await cl.Message(
                content=friendly_error_message("invalid_input")
            ).send()
            return

        if not looks_like_financial_input(text_input):
            await cl.Message(
                content=friendly_error_message("invalid_input")
            ).send()
            return

        processing_msg = cl.Message(
            content="Processing pasted transaction text..."
        )
        await processing_msg.send()

        try:
            result = await call_agent(
                input_type="text_paste",
                content=text_input,
            )

            save_transaction_to_session(result)

            processing_msg.content = format_agent_response(result)
            await processing_msg.update()

        except Exception:
            processing_msg.content = friendly_error_message("agent_failure")
            await processing_msg.update()









            