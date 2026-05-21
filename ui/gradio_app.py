import gradio as gr


def respond(message, history):
    return f"""
I can help with that. Let me look at this charge for you.

Analyzing your charge...

✅ Captured transaction text
✅ Prepared placeholder merchant/category analysis
✅ Ready to connect with backend agent later

Input received:
{message}

This is the Week 1 Gradio demo. Later, this interface will connect to the real backend agent and return:
merchant, amount, category, explanation, and confidence score.
"""


demo = gr.ChatInterface(
    fn=respond,
    title="Financial Transaction Assistant",
    description="Enter a transaction or receipt text and get a plain-language explanation."
)


if __name__ == "__main__":
    demo.launch()