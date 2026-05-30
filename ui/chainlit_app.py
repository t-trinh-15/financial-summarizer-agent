import chainlit as cl
from typing import Dict, Any


async def call_agent_placeholder(input_type: str, content: str) -> Dict[str, Any]:
    """
    Placeholder function for Week 2 UI flow.

    Helen/backend team can later replace this function with the real backend
    agent call once the input/output schema is confirmed.
    """

    return {
        "input_type": input_type,
        "merchant": "demo merchant",
        "amount": "demo amount",
        "category": "demo category",
        "explanation": (
            "This is a placeholder response from the UI layer. "
            "The real backend agent will replace this function later."
        ),
        "confidence": 0.50,
        "raw_input": content,
    }


def format_agent_response(result: Dict[str, Any]) -> str:
    """
    Format the placeholder agent result for display in Chainlit.
    """

    return f"""
## Transaction Analysis Result

**Input Type:** {result["input_type"]}

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

The real backend agent connection will be added once the backend input/output format is confirmed.
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
        uploaded_files = []

        for element in message.elements:
            file_name = getattr(element, "name", "uploaded_file")
            uploaded_files.append(file_name)

        file_summary = ", ".join(uploaded_files)

        await cl.Message(
            content=f"""
Processing uploaded file...

Received file(s): {file_summary}

OCR/backend image processing is not connected yet.  
For now, this confirms that the Chainlit UI can detect uploaded receipt images.
"""
        ).send()

        result = await call_agent_placeholder(
            input_type="image_upload",
            content=file_summary,
        )

        await cl.Message(content=format_agent_response(result)).send()

    else:
        text_input = message.content.strip()

        if not text_input:
            await cl.Message(
                content="Please paste a transaction description or upload a receipt image."
            ).send()
            return

        await cl.Message(
            content="""
Processing pasted transaction text...

Text input received. Sending it to the placeholder agent function.
"""
        ).send()

        result = await call_agent_placeholder(
            input_type="text_paste",
            content=text_input,
        )

        await cl.Message(content=format_agent_response(result)).send()