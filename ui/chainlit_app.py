"""
ui/chainlit_app.py
Personal Finance Expense Summarizer — Chainlit UI
"""
import sys
import os
import re
import asyncio

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


import chainlit as cl
from shared.storage import init_db, log_interaction, log_feedback, log_followup
from agent.agent import translate
from shared.feedback import save_feedback

try:
    from ocr.document_ai import process_receipt, receipt_to_text
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False

try:
    from PIL import Image as PilImage
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


# ============================================================
# STARTUP CHECK
# ============================================================

if not os.getenv("ANTHROPIC_API_KEY"):
    raise EnvironmentError(
        "\n\n❌ ANTHROPIC_API_KEY is not set.\n"
        "Add it to your .env file and restart the app.\n"
        "Example: ANTHROPIC_API_KEY=sk-ant-your-key-here\n"
    )


# ============================================================
# CONSTANTS
# ============================================================

SUPPORTED_IMAGE_TYPES = {".jpg", ".jpeg", ".png", ".webp", ".tiff", ".bmp", ".gif"}
MAX_FILE_SIZE_MB = 10
HISTORY_COMMAND = "history"
OCR_MAX_PX = 1500  # max dimension before resizing for OCR

FINANCIAL_KEYWORDS = [
    "debit", "credit", "charge", "payment", "purchase", "withdrawal",
    "deposit", "transfer", "refund", "reimbursement", "fee", "interest",
    "pos", "ach", "atm", "wire", "zelle", "venmo", "paypal", "cashapp",
    "autopay", "direct deposit", "check", "memo", "balance",
    "total", "subtotal", "tax", "tip", "receipt", "invoice", "amount due",
    "qty", "quantity", "unit price", "order",
    # Currency symbols
    "$", "€", "£", "¥", "₹", "₩", "₺", "₴", "₽", "฿", "₫", "₱", "₦",
    "₲", "₡", "₵", "₸", "₼", "₾", "﷼", "؋", "৳", "₭", "₮", "₪",
    # Major ISO 4217 codes
    "usd", "eur", "gbp", "jpy", "cad", "aud", "sgd", "chf", "mxn", "inr",
    "cny", "krw", "brl", "hkd", "nok", "sek", "dkk", "nzd", "zar", "rub",
    "try", "pln", "thb", "idr", "myr", "php", "vnd", "egp", "aed", "sar",
    "qar", "kwd", "bhd", "omr", "jod", "ils", "czk", "huf", "ron", "bgn",
    "hrk", "isk", "cop", "ars", "clp", "pen", "uyu", "bob", "pyg", "gtq",
    "hnl", "nio", "crc", "dop", "jmd", "ttd", "bbd", "xcd", "bsd", "kyd",
    "ngn", "ghs", "kes", "tzs", "ugx", "etb", "mad", "tnd", "dzd", "lyd",
    "sdg", "xof", "xaf", "mwk", "zmw", "bwp", "szl", "lsl", "mzn", "aoa",
    "pkr", "lkr", "bdt", "npr", "mmk", "khr", "lak", "mnt", "afn", "irr",
    "iqd", "syp", "lbp", "pab", "bzd", "gyd", "srd", "fkp", "shp", "awg",
    "ang", "amd", "azn", "gel", "kzt", "kgs", "uzs", "tjs", "tmt", "mdl",
    "all", "mkd", "rsd", "bam", "uah", "byr", "byn", "lvl", "ltl", "eek",
    "amazon", "amzn", "walmart", "target", "costco", "starbucks", "sq *",
    "doordash", "uber", "lyft", "netflix", "spotify", "apple", "google",
]

AMOUNT_PATTERN = re.compile(r"\d+[\.,]\d{2}")

MONTHS_PATTERN = (
    r"JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC|"
    r"JANUARY|FEBRUARY|MARCH|APRIL|JUNE|JULY|AUGUST|"
    r"SEPTEMBER|OCTOBER|NOVEMBER|DECEMBER"
)

DATE_PATTERNS = [
    # ── ISO and numeric formats ──────────────────────────────
    # YYYY-MM-DD
    (re.compile(r"\b(\d{4}-\d{2}-\d{2})\b"), None),
    # YYYY/MM/DD
    (re.compile(r"\b(\d{4}/\d{2}/\d{2})\b"), None),
    # YYYYMMDD
    (re.compile(r"\b(20\d{2})(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])\b"), "{g1}-{g2}-{g3}"),
    # MM/DD/YYYY
    (re.compile(r"\b(\d{1,2}/\d{1,2}/\d{4})\b"), None),
    # MM/DD/YY
    (re.compile(r"\b(\d{1,2}/\d{1,2}/\d{2})\b"), None),
    # MM/DD (no year)
    (re.compile(r"\b(\d{1,2}/\d{1,2})\b"), None),
    # MM-DD-YYYY
    (re.compile(r"\b(\d{1,2}-\d{1,2}-\d{4})\b"), None),
    # MM-DD-YY
    (re.compile(r"\b(\d{1,2}-\d{1,2}-\d{2})\b"), None),
    # MM.DD.YYYY
    (re.compile(r"\b(\d{1,2}\.\d{1,2}\.\d{4})\b"), None),
    # MM.DD.YY
    (re.compile(r"\b(\d{1,2}\.\d{1,2}\.\d{2})\b"), None),

    # ── Written month formats ────────────────────────────────
    # DD-Mon-YYYY (30-Aug-2019)
    (re.compile(rf"\b(\d{{1,2}})-({MONTHS_PATTERN})-(\d{{4}})\b", re.IGNORECASE), "{g1} {g2} {g3}"),
    # DD Mon YYYY (30 Aug 2019)
    (re.compile(rf"\b(\d{{1,2}})\s({MONTHS_PATTERN})\s(\d{{4}})\b", re.IGNORECASE), "{g1} {g2} {g3}"),
    # Mon DD YYYY (Aug 30 2019)
    (re.compile(rf"\b({MONTHS_PATTERN})\s(\d{{1,2}})\s(\d{{4}})\b", re.IGNORECASE), "{g1} {g2} {g3}"),
    # Mon DD, YYYY (Aug 30, 2019)
    (re.compile(rf"\b({MONTHS_PATTERN})\s(\d{{1,2}}),\s(\d{{4}})\b", re.IGNORECASE), "{g1} {g2} {g3}"),
    # Mon-DD-YYYY (Aug-30-2019)
    (re.compile(rf"\b({MONTHS_PATTERN})-(\d{{1,2}})-(\d{{4}})\b", re.IGNORECASE), "{g1} {g2} {g3}"),
    # DDMonYYYY (30Aug2019)
    (re.compile(rf"\b(\d{{1,2}})({MONTHS_PATTERN})(\d{{4}})\b", re.IGNORECASE), "{g1} {g2} {g3}"),
    # MonYYYY (Aug2019)
    (re.compile(rf"\b({MONTHS_PATTERN})\s*(\d{{4}})\b", re.IGNORECASE), "{g1} {g2}"),
    # Mon DD YY (Aug 30 19)
    (re.compile(rf"\b({MONTHS_PATTERN})\s(\d{{1,2}})\s(\d{{2}})\b", re.IGNORECASE), "{g1} {g2} 20{g3}"),

    # ── Compact receipt formats ──────────────────────────────
    # Jun28'17 — MonDD'YY no spaces
    (re.compile(rf"\b({MONTHS_PATTERN})(\d{{1,2}})['\u2019](\d{{2}})\b", re.IGNORECASE), "{g1} {g2} 20{g3}"),
    # Jun28 — MonDD no year
    (re.compile(rf"\b({MONTHS_PATTERN})(\d{{1,2}})\b", re.IGNORECASE), "{g1} {g2}"),
    # Oct 17' — Mon DD' optional 2-digit year
    (re.compile(rf"\b({MONTHS_PATTERN})\s+(\d{{1,2}})['\u2019\s]*(\d{{2}})?\b", re.IGNORECASE), "{g1} {g2}"),
]

CONFIDENCE_ICONS = {
    "high":   "🟢",
    "medium": "🟡",
    "low":    "🔴",
}

CATEGORY_ICONS = {
    "purchase":   "🛍️",
    "transfer":   "🔄",
    "fee":        "💸",
    "refund":     "↩️",
    "deposit":    "📥",
    "withdrawal": "🏧",
    "payment":    "💳",
    "other":      "📄",
}

ERROR_TYPES = [
    ("wrong_merchant",    "Wrong merchant name"),
    ("wrong_amount",      "Wrong amount"),
    ("wrong_currency",    "Wrong currency"),
    ("wrong_date",        "Wrong date / timestamp"),
    ("wrong_category",    "Wrong transaction type / category"),
    ("wrong_explanation", "Incorrect explanation"),
    ("everything_wrong",  "Everything wrong"),
    ("other",             "Other feedback"),
]

FOLLOWUP_KEYWORDS = [
    "category", "what is", "explain", "why", "how", "what does",
    "what type", "tell me more", "what kind", "what was", "what does that mean",
    "more detail", "clarify", "elaborate",
]


# ============================================================
# HELPERS
# ============================================================

def looks_like_financial_input(text: str) -> bool:
    lowered = text.lower()
    if AMOUNT_PATTERN.search(text):
        return True
    return any(kw in lowered for kw in FINANCIAL_KEYWORDS)


def looks_like_receipt_text(text: str) -> bool:
    """
    More permissive check specifically for OCR-extracted receipt text.
    Receipts often have numbers, merchant names, and amounts without
    standard financial keywords.
    """
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    has_multiple_lines = len(lines) >= 3
    has_numbers = bool(re.search(r"\d+", text))
    has_amount = bool(AMOUNT_PATTERN.search(text))
    return (has_multiple_lines and has_numbers) or has_amount


def format_amount(amount) -> str:
    """Always show exactly two decimal places for financial amounts."""
    try:
        return f"{float(amount):.2f}"
    except Exception:
        return str(amount)


def clean_enum(value) -> str:
    """
    Strip enum class prefix from string representation.
    e.g. 'Transaction.Purchase' -> 'Purchase'
         'Confidence.High'      -> 'High'
    """
    return str(value).split(".")[-1].title()


def get_confidence_icon(confidence) -> str:
    key = str(confidence).split(".")[-1].lower()
    return CONFIDENCE_ICONS.get(key, "⚪")


def get_category_icon(category) -> str:
    key = str(category).split(".")[-1].lower()
    return CATEGORY_ICONS.get(key, "📄")


def resize_for_ocr(file_path: str, max_px: int = OCR_MAX_PX) -> str:
    """
    Resizes an image to max_px on its longest dimension before sending
    to Document AI. Reduces upload size and OCR processing time.
    Returns the original path if PIL is unavailable or resizing is not needed.
    """
    if not PIL_AVAILABLE:
        return file_path
    try:
        img = PilImage.open(file_path)
        if max(img.size) > max_px:
            img.thumbnail((max_px, max_px), PilImage.LANCZOS)
            resized_path = file_path + "_resized.jpg"
            img.save(resized_path, "JPEG", quality=85)
            return resized_path
    except Exception:
        pass
    return file_path


def extract_date_from_raw(raw_input: str, explanation: str) -> str:
    for text in [raw_input, explanation]:
        for pattern, fmt in DATE_PATTERNS:
            match = pattern.search(text)
            if match:
                if fmt is None:
                    return match.group(1).title() if not match.group(1)[0].isdigit() else match.group(1)
                result = fmt
                for i, g in enumerate(match.groups(), 1):
                    if g is not None:
                        result = result.replace(
                            f"{{g{i}}}",
                            str(g).title() if g and not g[0].isdigit() else str(g)
                        )
                return result
    return "—"


def format_agent_response(result, raw_input: str) -> str:
    confidence_icon = get_confidence_icon(result.confidence)
    category_icon   = get_category_icon(result.transaction_type)
    date_str        = extract_date_from_raw(raw_input, result.plain_english_explanation)
    amount_str      = format_amount(result.amount)
    category_str    = clean_enum(result.transaction_type)
    confidence_str  = clean_enum(result.confidence)

    return (
        f"### {category_icon} Transaction Summary\n\n"
        f"| Field | Value |\n"
        f"|---|---|\n"
        f"| **Merchant** | {result.merchant} |\n"
        f"| **Amount** | {result.currency} {amount_str} |\n"
        f"| **Date** | {date_str} |\n"
        f"| **Category** | {category_str} |\n"
        f"| **Confidence** | {confidence_icon} {confidence_str} |\n\n"
        f"**Plain-English Explanation:**\n\n{result.plain_english_explanation}"
    )


def save_transaction_to_session(result, raw_input: str):
    history = cl.user_session.get("transaction_history", [])
    history.append({
        "raw_input":   raw_input[:120],
        "merchant":    result.merchant,
        "amount":      format_amount(result.amount),
        "currency":    result.currency,
        "category":    clean_enum(result.transaction_type),
        "confidence":  clean_enum(result.confidence),
        "explanation": result.plain_english_explanation,
    })
    cl.user_session.set("transaction_history", history)


def format_history() -> str:
    history = cl.user_session.get("transaction_history", [])
    if not history:
        return "No transactions yet this session."
    lines = ["### 📋 Session History\n"]
    for i, t in enumerate(history, 1):
        lines.append(
            f"**{i}.** {t['merchant']} · {t['currency']} {t['amount']} "
            f"· {t['category']} · {t['confidence']}\n"
            f"> _{t['raw_input']}_\n"
        )
    return "\n".join(lines)


async def call_ocr_service(file_path: str) -> str:
    """
    Runs Document AI OCR in a thread so it does not block the async
    event loop. Resizes the image first to reduce upload and processing time.
    """
    if not OCR_AVAILABLE:
        raise RuntimeError("OCR module not available. Check ocr/document_ai.py.")
    ocr_path = resize_for_ocr(file_path)
    receipt_data = await asyncio.to_thread(process_receipt, ocr_path)
    return receipt_to_text(receipt_data)


# ============================================================
# LIFECYCLE
# ============================================================

@cl.on_chat_start
async def on_chat_start():
    init_db()

    cl.user_session.set("transaction_history", [])
    cl.user_session.set("pending_feedback", None)
    cl.user_session.set("last_result", None)
    cl.user_session.set("interaction_id", None)

    await cl.Message(
        content="# 💰 Personal Finance Expense Summarizer Assistant",
    ).send()

    logo_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "public", "logo_light.png")
    )
    if os.path.exists(logo_path):
        await cl.Message(
            content="",
            elements=[
                cl.Image(path=logo_path, name="logo", display="inline", size="small")
            ],
        ).send()

    await cl.Message(
        content=(
            "⚠️ **Privacy & Confidentiality Notice**\n\n"
            "This tool is for **personal and educational use only** and is not a substitute "
            "for professional financial or legal advice.\n\n"
            "- **Do not** enter full account numbers, passwords, PINs, SSNs, or full card numbers\n"
            "- Transactions are processed **in-session only** and are not stored on any server\n"
            "- Results may not be 100% accurate — always verify with your financial institution\n\n"
            "_By continuing, you acknowledge this notice._"
        ),
        author="System",
    ).send()

    ocr_status = (
        "- 🖼️ **Upload a receipt image** and I will extract the details for you"
        if OCR_AVAILABLE else
        "- 🖼️ **Image upload** is unavailable — paste transaction text directly for now"
    )

    await cl.Message(
        content=f"""Welcome! I help you make sense of your bank statements, receipts, and transactions — instantly.

Here is what I can do:
- 📝 **Paste a transaction** from your bank statement and I will translate it into plain English
{ocr_status}
- 💱 **Recognize currencies** from around the world and display the correct symbol
- 📊 **Categorize your spending** — purchases, transfers, fees, refunds, and more
- 🎯 **Rate my confidence** so you always know how certain I am

**To get started, paste a transaction below or upload a receipt image.**

Type `history` at any time to see your transactions from this session.

Example transactions you can try:
> `POS DEBIT 0428 SQ *COFFEE BAR $4.75`
> `ACH WITHDRAWAL CHASE CREDIT CRD AUTOPAY 05/15 -$1,247.83`
> `AMZN MKTP US*1A2B3C 04/22 $34.99`
""",
    ).send()


# ============================================================
# MESSAGE HANDLER
# ============================================================

@cl.on_message
async def main(message: cl.Message):

    # ── Handle pending free-text feedback ──
    pending = cl.user_session.get("pending_feedback")
    if pending:
        correction = message.content.strip()
        if correction.lower() == "skip":
            save_feedback(
                verdict="rejected",
                error_type=pending.get("error_type"),
                user_correction=None,
                raw_input=pending.get("raw_input", ""),
                result=pending.get("result"),
            )
            cl.user_session.set("pending_feedback", None)
            await cl.Message(
                content="✅ Error type logged. No correction recorded.",
                author="System",
            ).send()
            return

        word_count = len(correction.split())
        if word_count > 100:
            await cl.Message(
                content="✏️ Please keep your correction under 100 words.",
                author="System",
            ).send()
            return

        save_feedback(
            verdict="rejected",
            error_type=pending.get("error_type"),
            user_correction=correction,
            raw_input=pending.get("raw_input", ""),
            result=pending.get("result"),
        )
        cl.user_session.set("pending_feedback", None)
        await cl.Message(
            content="✅ Feedback saved. Thank you for helping us improve!",
            author="System",
        ).send()
        return

    # ── History command ──
    if message.content.strip().lower() == HISTORY_COMMAND:
        await cl.Message(content=format_history()).send()
        return

    # ── Image upload ──
    if message.elements:
        for element in message.elements:
            if not hasattr(element, "path") or not element.path:
                continue
            ext = os.path.splitext(element.name or "")[1].lower()
            if ext not in SUPPORTED_IMAGE_TYPES:
                await cl.Message(
                    content=f"❌ Unsupported file type `{ext}`. Please upload a JPG, PNG, WEBP, or TIFF.",
                ).send()
                return
            size_mb = os.path.getsize(element.path) / (1024 * 1024)
            if size_mb > MAX_FILE_SIZE_MB:
                await cl.Message(
                    content=f"❌ File too large ({size_mb:.1f} MB). Please upload under {MAX_FILE_SIZE_MB} MB.",
                ).send()
                return

            # ── OCR quality gate ──
            try:
                from ocr.quality_predictor import assess_image_quality
                quality_report = assess_image_quality(element.path)
                if not quality_report.passed:
                    await cl.Message(
                        content=(
                            f"⚠️ {quality_report.message}\n\n"
                            "You can still proceed, but results may be less accurate."
                        ),
                    ).send()
            except Exception:
                pass

            async with cl.Step(name="Reading receipt with OCR..."):
                try:
                    extracted_text = await call_ocr_service(element.path)
                    print(f"DEBUG OCR output: {repr(extracted_text)}")
                except Exception as e:
                    await cl.Message(
                        content=f"❌ OCR failed: {str(e)}\n\nPlease paste the transaction text manually.",
                    ).send()
                    return

            if not extracted_text or not extracted_text.strip():
                await cl.Message(
                    content=(
                        "🤔 I couldn't read any text from that image.\n\n"
                        "Make sure the image is clear and well-lit, or paste the transaction text directly."
                    ),
                ).send()
                return

            if not looks_like_financial_input(extracted_text) and not looks_like_receipt_text(extracted_text):
                await cl.Message(
                    content=(
                        "🤔 That image doesn't appear to contain financial information.\n\n"
                        "Please upload a receipt, invoice, or bank statement screenshot."
                    ),
                ).send()
                return

            await _process_transaction(extracted_text, source="📷 image upload")
        return

    # ── Text input ──
    user_text = message.content.strip()
    if not user_text:
        return

    last_result = cl.user_session.get("last_result")
    is_followup = (
        last_result is not None
        and any(kw in user_text.lower() for kw in FOLLOWUP_KEYWORDS)
    )

    if is_followup:
        log_followup(cl.context.session.id, user_text)
        stored_result = last_result["result"]
        await cl.Message(
            content=(
                f"Here's what I found for that transaction:\n\n"
                f"**Category:** {clean_enum(stored_result.transaction_type)}\n"
                f"**Confidence:** {get_confidence_icon(stored_result.confidence)} "
                f"{clean_enum(stored_result.confidence)}\n\n"
                f"{stored_result.plain_english_explanation}"
            )
        ).send()
        return

    if not looks_like_financial_input(user_text):
        await cl.Message(
            content=(
                "🤔 That doesn't look like a financial transaction.\n\n"
                "Try pasting a bank statement line or uploading a receipt image.\n\n"
                "**Examples:**\n"
                "> `POS DEBIT 0428 SQ *COFFEE BAR $4.75`\n"
                "> `ACH WITHDRAWAL CHASE CREDIT CRD AUTOPAY 05/15 -$1,247.83`"
            ),
        ).send()
        return

    await _process_transaction(user_text, source="📝 text")


# ============================================================
# CORE PROCESSING
# ============================================================

async def _process_transaction(raw_input: str, source: str):
    async with cl.Step(name=f"Analyzing transaction ({source})..."):
        try:
            result = await asyncio.to_thread(translate, raw_input)
        except Exception as e:
            await cl.Message(
                content=f"❌ Agent error: {str(e)}\n\nPlease try again or rephrase your input.",
            ).send()
            return

    save_transaction_to_session(result, raw_input)

    session_id = cl.context.session.id
    interaction_id = log_interaction(session_id, raw_input, result)
    cl.user_session.set("interaction_id", interaction_id)
    cl.user_session.set("last_result", {"result": result, "raw_input": raw_input})

    response_text = format_agent_response(result, raw_input)

    actions = [
        cl.Action(name="accept", label="✅ Accept", value="accept", payload={"value": "accept"}),
        cl.Action(name="reject", label="❌ Reject", value="reject", payload={"value": "reject"}),
    ]

    await cl.Message(content=response_text, actions=actions).send()


# ============================================================
# FEEDBACK CALLBACKS
# ============================================================

@cl.action_callback("accept")
async def on_accept(action: cl.Action):
    stored = cl.user_session.get("last_result", {})

    interaction_id = cl.user_session.get("interaction_id")
    if interaction_id:
        log_feedback(cl.context.session.id, interaction_id, accepted=True)

    save_feedback(
        verdict="accepted",
        error_type=None,
        user_correction=None,
        raw_input=stored.get("raw_input", ""),
        result=stored.get("result"),
    )
    await cl.Message(
        content="✅ Got it! Glad the summary looked right. Feedback saved.",
        author="System",
    ).send()


@cl.action_callback("reject")
async def on_reject(action: cl.Action):
    interaction_id = cl.user_session.get("interaction_id")
    if interaction_id:
        log_feedback(cl.context.session.id, interaction_id, accepted=False)

    error_buttons = [
        cl.Action(
            name=f"error_{code}",
            label=label,
            value=code,
            payload={"value": code},
        )
        for code, label in ERROR_TYPES
    ]
    await cl.Message(
        content="❌ What was wrong with the response?",
        actions=error_buttons,
        author="System",
    ).send()


# Dynamically register one callback per error type
for _code, _label in ERROR_TYPES:
    def _make_callback(error_code):
        @cl.action_callback(f"error_{error_code}")
        async def _error_callback(action: cl.Action):
            stored = cl.user_session.get("last_result", {})
            cl.user_session.set("pending_feedback", {
                "error_type": error_code,
                "raw_input":  stored.get("raw_input", ""),
                "result":     stored.get("result"),
            })
            await cl.Message(
                content=(
                    f"📝 You selected: **{action.label}**\n\n"
                    "Please type the correct value below (max 100 words) and hit Enter.\n"
                    "Type `skip` to skip the correction and just log the error type."
                ),
                author="System",
            ).send()
    _make_callback(_code)