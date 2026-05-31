import chainlit as cl


@cl.on_message
async def main(message: cl.Message):
    user_text = message.content

    response = f"""
I can help with that. Let me look at this charge for you.

Analyzing your charge...

✅ Captured transaction text
✅ Prepared placeholder merchant/category analysis
✅ Ready to connect with backend agent later

Input received:
{user_text}

This is the Week 1 Chainlit demo. Later, this interface will connect to the real backend agent and return:
- merchant
- amount
- category
- explanation
- confidence score
"""

    await cl.Message(content=response).send()