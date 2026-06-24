'''Financial Summarizer Agent'''

'''
Takes a messy transaction string and returns a structured, plain-English explanation.'''

from agent.classifier import predict_category
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
  SQ * = processed via Square, AMZN = Amazon, UBER* = Uber, etc.
- The plain-English explanation should be 1-2 sentences, friendly, and
  assume the reader has no banking background.
- Set confidence to 'low' if you had to guess heavily, 'high' if everything
  was clear in the input.

Date extraction rules (pay close attention):
- Dates are often written as MM/DD — for example 05/01 means May 1st.
- Dates may also appear as MM-DD, Month DD, or YYYY-MM-DD.
- ALWAYS extract the date into the date field when it appears anywhere in
  the input string, even if it is embedded mid-string.
- Return the date in MM/DD format. For example: 05/01, 04/17, 12/25.
- Do NOT leave the date null if a date pattern like 05/01 or 04/17 exists
  in the input.
- Dates may appear as DD-Mon-YYYY (30-Aug-2019), Mon DD YYYY (Aug 30 2019), Mon DD, YYYY (Aug 30, 2019), MM.DD.YYYY, MM-DD-YYYY, or compact receipt formats like Jun28'17.
- Always convert to MM/DD format in the output regardless of the input format.

Amount rules:
- Always return amount as a positive number for purchases and fees.
- For refunds, return as negative.
- Strip currency symbols before returning the number.

Transaction type rules (follow these exactly):
- Utility bills, phone bills, and subscription charges are always transaction_type=purchase.
- ACH transfers, wire transfers, and account-to-account movements are always transaction_type=transfer.
- Refunds, returns, and reversals are always transaction_type=refund, never deposit.
- Bank fees, late fees, and service charges are always transaction_type=fee.
- ATM withdrawals and cash withdrawals are always transaction_type=withdrawal.
- Payroll, direct deposits, and incoming payments are always transaction_type=deposit.
- IMPORTANT: Never classify a bill payment or vendor charge as transfer. Transfer is only for account-to-account movements with no merchant involved.

Examples:
Input: "EVRS*EVERSOURCE 800-592-2000"
Output: merchant=Eversource Energy, transaction_type=purchase,
explanation="Monthly electricity bill from Eversource, your utility provider."

Input: "SQ *BLUE BOTTLE COFFEE"
Output: merchant=Blue Bottle Coffee, transaction_type=purchase,
explanation="Coffee purchase at Blue Bottle Coffee, paid via Square terminal."

Input: "REFUND Amazon order #9876 $34.99"
Output: merchant=Amazon, transaction_type=refund,
explanation="A refund was credited back to your account for an Amazon order."

Input: "ACH TRANSFER SENT $500.00 TO SAVINGS ACCOUNT"
Output: merchant=Savings Account, transaction_type=transfer,
explanation="You transferred $500 from your account to your savings account."

Input: "LATE PAYMENT FEE $35.00 CREDIT CARD"
Output: merchant=Credit Card Account, transaction_type=fee,
explanation="A late payment fee was charged to your credit card account."

Input: "ATM WITHDRAWAL CHASE BANK $200.00"
Output: merchant=Chase Bank, transaction_type=withdrawal,
explanation="You withdrew $200 in cash from a Chase Bank ATM."

Input: "DIRECT DEPOSIT PAYROLL $2450.00 EMPLOYER: ACME CORP"
Output: merchant=Acme Corp, transaction_type=deposit,
explanation="Your payroll deposit of $2,450 from Acme Corp was received."

""".strip()

# Categories where the classifier is reliable enough to override Claude.
# Refund, deposit, transfer, and withdrawal are excluded — Claude handles
# these better than the classifier due to training data imbalance.
CLASSIFIER_TRUSTED_CATEGORIES = {"purchase", "fee"}

# This is THE agent. Three things go in: which model, what output shape, what instructions.
financial_translator = Agent(
    model=AnthropicModel("claude-sonnet-4-5"),
    output_type=TranslatedTransaction,
    system_prompt=SYSTEM_PROMPT,
)


def translate(transaction_string: str) -> TranslatedTransaction:
    """
    Translate one transaction string into a structured plain-English result.

    Classifier override rules:
    - Only overrides Claude when Claude is NOT high confidence.
    - Only overrides for 'purchase' and 'fee' — categories the classifier
      is reliably strong on.
    - For refund, deposit, transfer, withdrawal — always trusts Claude.
    - Classifier must exceed 0.92 probability to trigger (set in classifier.py).
    """
    result = financial_translator.run_sync(transaction_string)
    output = result.output
    try:
        classifier_label = predict_category(transaction_string)
        claude_confidence = str(output.confidence).split(".")[-1].lower()
        if (
            classifier_label is not None
            and classifier_label in CLASSIFIER_TRUSTED_CATEGORIES
            and claude_confidence != "high"
        ):
            output = output.model_copy(update={'transaction_type': classifier_label})
    except Exception as e:
        print(f'Classifier skipped: {e}')
    return output


if __name__ == "__main__":
    test_input = "POS DEBIT 0428 SQ *COFFEE BAR $4.75"
    result = translate(test_input)
    print(result.model_dump_json(indent=2))