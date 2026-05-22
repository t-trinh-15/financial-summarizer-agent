"""
Five hand-typed test transactions covering common formats.
Run with: python -m agent.test_strings
"""

from agent.agent import translate

TEST_STRINGS = [
    "POS DEBIT 0428 SQ *COFFEE BAR $4.75",
    "ACH WITHDRAWAL CHASE CREDIT CRD AUTOPAY 05/15 -$1,247.83",
    "AMZN MKTP US*1A2B3C 04/22 $34.99",
    "ATM FEE 04/30 $3.50",
    "DIRECT DEPOSIT PAYROLL ACME CORP 05/15 +$2,341.07",
]


if __name__ == "__main__":
    for i, s in enumerate(TEST_STRINGS, 1):
        print(f"\n--- Test {i} ---")
        print(f"Input:  {s}")
        result = translate(s)
        print(f"Output: {result.plain_english_explanation}")
        print(f"        merchant={result.merchant}, amount={result.amount}, type={result.transaction_type.value}")