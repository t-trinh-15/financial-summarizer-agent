import os
import mimetypes
from google.api_core.client_options import ClientOptions
from google.cloud import documentai


# ============================================================
# CONFIGURATION
# ============================================================

PROJECT_ID = os.getenv("DOCUMENT_AI_PROJECT_ID")
LOCATION = os.getenv("DOCUMENT_AI_LOCATION", "us")
PROCESSOR_ID = os.getenv("DOCUMENT_AI_PROCESSOR_ID")

if not PROJECT_ID:
    raise ValueError(
        "DOCUMENT_AI_PROJECT_ID environment variable is not set."
    )

if not PROCESSOR_ID:
    raise ValueError(
        "DOCUMENT_AI_PROCESSOR_ID environment variable is not set."
    )


# ============================================================
# PROCESS RECEIPT
# ============================================================

def process_receipt(file_path: str) -> dict:
    """
    Sends a receipt image/PDF to Google Document AI and
    returns structured receipt data.
    """

    mime_type, _ = mimetypes.guess_type(file_path)

    if mime_type is None:
        mime_type = "image/jpeg"

    opts = ClientOptions(
        api_endpoint=f"{LOCATION}-documentai.googleapis.com"
    )

    client = documentai.DocumentProcessorServiceClient(
        client_options=opts
    )

    processor_name = client.processor_path(
        PROJECT_ID,
        LOCATION,
        PROCESSOR_ID,
    )

    with open(file_path, "rb") as f:
        file_content = f.read()

    raw_document = documentai.RawDocument(
        content=file_content,
        mime_type=mime_type,
    )

    request = documentai.ProcessRequest(
        name=processor_name,
        raw_document=raw_document,
    )

    result = client.process_document(
        request=request
    )

    return extract_receipt_data(
        result.document
    )


# ============================================================
# EXTRACT STRUCTURED DATA
# ============================================================

def extract_receipt_data(document) -> dict:
    """
    Converts Document AI entities into a structured receipt JSON.
    """

    data = {
        "merchant_name": None,
        "transaction_date": None,
        "transaction_time": None,
        "currency": None,
        "subtotal": None,
        "tax": None,
        "total": None,
        "items": [],
    }

    for entity in document.entities:

        entity_type = entity.type_
        value = entity.mention_text

        normalized = (
            entity.normalized_value.text
            if entity.normalized_value
            else None
        )

        # ----------------------------------------------------
        # Top-level receipt fields
        # ----------------------------------------------------

        if entity_type == "supplier_name":
            data["merchant_name"] = (
                normalized or value
            )

        elif entity_type == "invoice_date":
            data["transaction_date"] = (
                normalized or value
            )

        elif entity_type == "invoice_time":
            data["transaction_time"] = (
                normalized or value
            )

        elif entity_type == "total_amount":
            data["total"] = (
                normalized or value
            )

        elif entity_type == "subtotal_amount":
            data["subtotal"] = (
                normalized or value
            )

        elif entity_type == "total_tax_amount":
            data["tax"] = (
                normalized or value
            )

        elif entity_type == "currency":
            data["currency"] = (
                normalized or value
            )

        # ----------------------------------------------------
        # Receipt line items
        # ----------------------------------------------------

        elif entity_type == "line_item":

            item = {
                "description": None,
                "quantity": None,
                "unit_price": None,
                "total_price": None,
            }

            for prop in entity.properties:

                if prop.type_ == "line_item/description":
                    item["description"] = (
                        prop.mention_text
                    )

                elif prop.type_ == "line_item/quantity":
                    item["quantity"] = (
                        prop.mention_text
                    )

                elif prop.type_ == "line_item/unit_price":
                    item["unit_price"] = (
                        prop.mention_text
                    )

                elif prop.type_ == "line_item/amount":
                    item["total_price"] = (
                        prop.mention_text
                    )

            data["items"].append(item)

    return data


# ============================================================
# OPTIONAL HELPER FOR CHAINLIT
# ============================================================

def receipt_to_text(receipt_data: dict) -> str:
    """
    Converts structured receipt JSON into plain text
    that can be passed to your translate() agent.
    """

    lines = []

    if receipt_data.get("merchant_name"):
        lines.append(
            f"Merchant: {receipt_data['merchant_name']}"
        )

    if receipt_data.get("transaction_date"):
        lines.append(
            f"Date: {receipt_data['transaction_date']}"
        )

    if receipt_data.get("total"):
        lines.append(
            f"Total: {receipt_data['total']}"
        )

    if receipt_data.get("currency"):
        lines.append(
            f"Currency: {receipt_data['currency']}"
        )

    for item in receipt_data.get("items", []):
        desc = item.get("description")
        amount = item.get("total_price")

        if desc:
            lines.append(
                f"Item: {desc} {amount or ''}"
            )

    return "\n".join(lines)


# ============================================================
# LOCAL TEST
# ============================================================

if __name__ == "__main__":

    TEST_FILE = "sample_receipt.jpg"

    receipt = process_receipt(TEST_FILE)

    print(receipt)

    print("\n--- OCR TEXT ---\n")

    print(
        receipt_to_text(receipt)
    )

