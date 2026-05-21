test_examples = [
    "STARBUCKS STORE 1234 BOSTON MA $6.50",
    "UBER TRIP HELP.UBER.COM $18.20",
    "AMZN MKTP US $42.99"
]


def hello_agent(transaction_text):
    return {
        "input": transaction_text,
        "merchant": "demo merchant",
        "amount": "demo amount",
        "category": "demo category",
        "explanation": "This is a placeholder explanation for the transaction.",
        "confidence": 0.50
    }


def run_eval():
    print("Running hello agent evaluation...\n")

    for i, example in enumerate(test_examples, start=1):
        result = hello_agent(example)

        print(f"Example {i}")
        print("-" * 40)
        print(f"Input: {result['input']}")
        print(f"Merchant: {result['merchant']}")
        print(f"Amount: {result['amount']}")
        print(f"Category: {result['category']}")
        print(f"Explanation: {result['explanation']}")
        print(f"Confidence: {result['confidence']}")
        print()


if __name__ == "__main__":
    run_eval()