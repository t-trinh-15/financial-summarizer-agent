from typing import Any, Dict

import chainlit as cl


async def call_agent_placeholder(input_type: str, content: str) -> Dict[str, Any]:
    """
    Placeholder function for Week 2 UI flow.

    This function can later be replaced with the real backend agent call
    once the input/output schema is confirmed.
    """

    return {
        "input_type": input_type,
        "merchant": "demo merchant",
        "amount": "demo amount",
        "category": "demo category",
        "explanation": (
            "This is a placeholder response from the UI layer. "
            "The real backend agent call can replace this function later."
        ),
        "confidence": 0.50,
        "raw_input": content,
    }


def format_agent_response(result: Dict[str, Any]) -> str:
    """
    Format the placeholder agent result for display in Chainlit.
    """

    if result["input_type"] == "image_upload":
        input_status = (
            "A receipt image was uploaded and detected by the Chainlit UI. "
            "OCR/backend image processing is not connected yet."
        )
    else:
        input_status = "Pasted transaction text was received by the Chainlit UI."

    return f"""
## Transaction Analysis Result

**Input Type:** {result["input_type"]}

**Input Status:**  
{input_status}

**Merchant:** {result["merchant"]}  
**Amount:** {result["amount"]}  
**Category:** {result["category"]}  
**Confidence:** {result["confidence"]}

**Explanation:**  
{result["explanation"]}

---

**Raw Input:**  
{result["raw_input"]}
"""


@cl.on_chat_start
async def start():
    await cl.Message(
        content="""
# Financial Tracking Summarizer Agent

Welcome! You can paste a transaction description or upload a receipt image.

This Week 2 UI prototype supports:
- Pasted transaction text
- Receipt image upload detection
- Placeholder agent response
- Structured response display

The backend agent connection will be added once the input/output format is confirmed.
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

        result = await call_agent_placeholder(
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

        result = await call_agent_placeholder(
            input_type="text_paste",
            content=text_input,
        )

        processing_msg.content = format_agent_response(result)
        await processing_msg.update()








        