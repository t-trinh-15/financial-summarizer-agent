import json
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agent.agent import translate
from evals.scorer import (
    field_match_score,
    schema_completeness,
    unsupported_explanation_check,
    merchant_accuracy,
    amount_accuracy,
    date_accuracy,
    category_accuracy,
    explanation_quality_score,
)

THRESHOLDS = {
    "avg_merchant_accuracy":         0.80,
    "avg_amount_accuracy":           0.90,
    "avg_date_accuracy":             0.75,
    "avg_category_accuracy":         0.80,
    "avg_field_match_score":         0.85,
    "avg_explanation_quality_score": 0.70,
}

def average(values):
    return round(sum(values) / len(values), 3) if values else 0.0

def percentile(values, pct):
    if not values:
        return 0.0
    values = sorted(values)
    index = int(round((len(values) - 1) * pct))
    return round(values[index], 4)

def agent_to_eval_format(input_text):
    import re as _re
    result = translate(input_text)

    date_str = ""
    iso_match = _re.search(r"\d{4}-(\d{2})-(\d{2})", input_text)
    short_match = _re.search(r"(\d{2}/\d{2})", input_text)
    if iso_match:
        date_str = f"{iso_match.group(1)}/{iso_match.group(2)}"
    elif short_match:
        date_str = short_match.group(1)

    amount_str = ""
    if result.amount:
        try:
            amount_str = f"{result.amount:.2f}".rstrip("0").rstrip(".")
            if "." not in amount_str:
                amount_str = amount_str
        except Exception:
            amount_str = str(result.amount)

    return {
        "merchant":                   result.merchant or "",
        "total_amount":               amount_str,
        "date":                       date_str,
        "category":                   result.transaction_type.value if result.transaction_type else "",
        "plain_language_explanation": result.plain_english_explanation or "",
        "confidence":                 result.confidence.value if hasattr(result.confidence, "value") else "",
    }

def check_thresholds(summary):
    failures = []
    for metric, threshold in THRESHOLDS.items():
        score = summary.get(metric, 0.0)
        if score < threshold:
            failures.append({"metric": metric, "score": score, "threshold": threshold})
    return failures

def main():
    data_path = Path(__file__).parent / "golden_set.json"
    if not data_path.exists():
        print(f"ERROR: golden_set.json not found at {data_path}")
        sys.exit(1)

    examples = json.loads(data_path.read_text())
    print(f"\nRunning evals on {len(examples)} examples against the real Claude agent...\n")

    results = []
    start_all = time.time()

    for i, example in enumerate(examples, 1):
        print(f"  [{i}/{len(examples)}] {example['id']} ...", end=" ", flush=True)
        start = time.time()
        try:
            prediction = agent_to_eval_format(example["input_text"])
            status = "ok"
        except Exception as e:
            print(f"ERROR: {e}")
            prediction = {}
            status = f"error: {e}"
        latency = round(time.time() - start, 4)

        result = {
            "id":                           example["id"],
            "status":                       status,
            "merchant_accuracy":            merchant_accuracy(prediction, example["expected"]),
            "amount_accuracy":              amount_accuracy(prediction, example["expected"]),
            "date_accuracy":                date_accuracy(prediction, example["expected"]),
            "category_accuracy":            category_accuracy(prediction, example["expected"]),
            "field_match_score":            field_match_score(prediction, example["expected"]),
            "schema_completeness":          schema_completeness(prediction),
            "unsupported_explanation_safe": unsupported_explanation_check(prediction),
            "explanation_quality_score":    explanation_quality_score(prediction),
            "latency_seconds":              latency,
            "prediction":                   prediction,
            "expected":                     example["expected"],
        }
        results.append(result)
        print(f"field_match={result['field_match_score']:.2f}  latency={latency}s")

    latencies = [r["latency_seconds"] for r in results]

    summary = {
        "run_timestamp":                 datetime.now().isoformat(),
        "num_examples":                  len(results),
        "avg_merchant_accuracy":         average([r["merchant_accuracy"] for r in results]),
        "avg_amount_accuracy":           average([r["amount_accuracy"] for r in results]),
        "avg_date_accuracy":             average([r["date_accuracy"] for r in results]),
        "avg_category_accuracy":         average([r["category_accuracy"] for r in results]),
        "avg_field_match_score":         average([r["field_match_score"] for r in results]),
        "avg_schema_completeness":       average([r["schema_completeness"] for r in results]),
        "avg_explanation_quality_score": average([r["explanation_quality_score"] for r in results]),
        "all_explanations_safe":         all(r["unsupported_explanation_safe"] for r in results),
        "avg_latency_seconds":           average(latencies),
        "p50_latency_seconds":           percentile(latencies, 0.50),
        "p95_latency_seconds":           percentile(latencies, 0.95),
        "total_eval_latency_seconds":    round(time.time() - start_all, 3),
    }

    failures = check_thresholds(summary)
    summary["thresholds_passed"] = len(failures) == 0
    summary["threshold_failures"] = failures

    print("\n" + "=" * 55)
    print("  EVAL SUMMARY")
    print("=" * 55)
    print(f"  Examples run:        {summary['num_examples']}")
    print(f"  Merchant accuracy:   {summary['avg_merchant_accuracy']}")
    print(f"  Amount accuracy:     {summary['avg_amount_accuracy']}")
    print(f"  Date accuracy:       {summary['avg_date_accuracy']}")
    print(f"  Category accuracy:   {summary['avg_category_accuracy']}")
    print(f"  Field match score:   {summary['avg_field_match_score']}")
    print(f"  Schema completeness: {summary['avg_schema_completeness']}")
    print(f"  Explanation quality: {summary['avg_explanation_quality_score']}")
    print(f"  All explanations safe: {summary['all_explanations_safe']}")
    print(f"  Avg latency:         {summary['avg_latency_seconds']}s")
    print(f"  P95 latency:         {summary['p95_latency_seconds']}s")
    print("=" * 55)

    if failures:
        print("\n  THRESHOLD FAILURES:")
        for f in failures:
            print(f"  x  {f['metric']}: {f['score']} < {f['threshold']}")
    else:
        print("\n  All thresholds passed.")

    results_dir = Path(__file__).parent / "results"
    results_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
    report = {"summary": summary, "results": results}

    timestamped_path = results_dir / f"eval_report_{timestamp}.json"
    timestamped_path.write_text(json.dumps(report, indent=2))

    latest_path = results_dir / "eval_report_latest.json"
    latest_path.write_text(json.dumps(report, indent=2))

    print(f"\n  Saved: {timestamped_path.name}")
    print(f"  Latest: {latest_path.name}\n")

    if failures:
        sys.exit(1)

if __name__ == "__main__":
    main()
