import json
import sys
import time
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app import extract_fields_from_text
from scorer import field_match_score, schema_completeness, unsupported_explanation_check

def main():
    data_path = Path(__file__).parent / "golden_set.json"
    examples = json.loads(data_path.read_text())
    results = []
    start_all = time.time()

    for example in examples:
        start = time.time()
        prediction = extract_fields_from_text(example["input_text"])
        latency = time.time() - start
        results.append({
            "id": example["id"],
            "field_match_score": field_match_score(prediction, example["expected"]),
            "schema_completeness": schema_completeness(prediction),
            "unsupported_explanation_safe": unsupported_explanation_check(prediction),
            "latency_seconds": round(latency, 4),
            "prediction": prediction
        })

    report = {
        "summary": {
            "num_examples": len(results),
            "avg_field_match_score": round(sum(r["field_match_score"] for r in results) / len(results), 3),
            "avg_schema_completeness": round(sum(r["schema_completeness"] for r in results) / len(results), 3),
            "all_explanations_safe": all(r["unsupported_explanation_safe"] for r in results),
            "total_eval_latency_seconds": round(time.time() - start_all, 3)
        },
        "results": results
    }

    output_path = Path(__file__).parent / "eval_report.json"
    output_path.write_text(json.dumps(report, indent=2))
    print(json.dumps(report["summary"], indent=2))
    print(f"Saved detailed report to {output_path}")

if __name__ == "__main__":
    main()
