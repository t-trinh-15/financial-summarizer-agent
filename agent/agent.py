'''Financial Summarizer Agent'''

'''
Takes a messy transaction string and returns a structured, plain-English explanation.'''

from dotenv import load_dotenv
from pydantic_ai import Agent
from pydantic_ai.models.anthropic import AnthropicModel
from agent.models import TranslatedTransaction

# Load the ANTHROPIC_API_KEY from the .env file
load_dotenv()

SYSTEM_PROMPT = """
You are a Financial Translation Agent.

Your job: take a messy or jargon-filled transaction string from a bank
statement, receipt, or invoice, and translate it into structured data plus
a plain-English explanation a non-expert can understand.

Rules:
- Extract the merchant, amount, currency, date, and transaction type when present.
- If a field is not present in the input, leave it null. Do NOT guess wildly.
- Decode common abbreviations: POS = point-of-sale, ACH = bank transfer,
  SQ * = processed via Square, AMZN = Amazon, etc.
- The plain-English explanation should be 1-2 sentences, friendly, and
  assume the reader has no banking background.
- Set confidence to 'low' if you had to guess heavily, 'high' if everything
  was clear in the input.
""".strip()

 # This is THE agent. Three things go in: which model, what output shape, what instructions.
financial_translator = Agent(
    model=AnthropicModel("claude-sonnet-4-5"),
    output_type=TranslatedTransaction,
    system_prompt=SYSTEM_PROMPT,
)


def translate(transaction_string: str) -> TranslatedTransaction:
    """Translate one transaction string into a structured plain-English result."""
    result = financial_translator.run_sync(transaction_string)
    return result.output


if __name__ == "__main__":
    test_input = "POS DEBIT 0428 SQ *COFFEE BAR $4.75"
    result = translate(test_input)
    print(result.model_dump_json(indent=2))
    





