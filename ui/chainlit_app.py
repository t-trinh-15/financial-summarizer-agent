import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from typing import Any, Dict
from decimal import Decimal
import chainlit as cl
from agent.agent import translate

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
    "INR": "₹",   "IQD": "ع.د", "IRR": "﷼",   "ISK": "kr",  "JMD": "J$",
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
    "USD": "$",    "UYU": "$U",   "UZS": "лв",  "VES": "Bs.S","VND": "₫",
    "VUV": "Vt",   "WST": "T",    "XAF": "Fr",   "XCD": "EC$", "XOF": "Fr",
    "XPF": "Fr",   "YER": "﷼",   "ZAR": "R",    "ZMW": "ZK",  "ZWL": "$",
}

CONFIDENCE_ICONS = {
    "high":   "🟢 High",
    "medium": "🟡 Medium",
    "low":    "🔴 Low",
}

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
        "merchant":   result.merchant or "—",
        "amount":     amount_display,
        "currency":   currency,
        "date":       str(result.date) if hasattr(result, "date") and result.date else "—",
        "category":   result.transaction_type.value.capitalize() if result.transaction_type else "—",
        "explanation": result.plain_english_explanation or "—",
        "confidence": result.confidence.value if hasattr(result.confidence, "value") else str(result.confidence),
        "raw_input":  content,
    }


def format_agent_response(result: Dict[str, Any]) -> str:
    """
    Format the agent result for display in Chainlit.
    """
    input_type_label = "📝 Text" if result["input_type"] == "text_paste" else "🖼️ Image"
    confidence_label = CONFIDENCE_ICONS.get(result["confidence"].lower(), result["confidence"])

    return f"""## Transaction Analysis Result

**Input Type:** {input_type_label}
**Merchant:** {result["merchant"]}
**Amount:** {result["amount"]}
**Date:** {result["date"]}
**Transaction Type:** {result["category"]}
**Confidence:** {confidence_label}

**Explanation:**
{result["explanation"]}

> **Raw Input:** {result["raw_input"]}
"""


@cl.on_chat_start
async def start():
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

        result = await call_agent(
            input_type="image_upload",
            content="uploaded receipt image",
        )

        processing_msg.content = format_agent_response(result)
        await processing_msg.update()

    else:
        text_input = message.content.strip()

        if not text_input:
            await cl.Message(
                content="Please paste a transaction description or upload a receipt image."
            ).send()
            return

        processing_msg = cl.Message(
            content="Processing pasted transaction text..."
        )
        await processing_msg.send()

        result = await call_agent(
            input_type="text_paste",
            content=text_input,
        )

        processing_msg.content = format_agent_response(result)
        await processing_msg.update()








        