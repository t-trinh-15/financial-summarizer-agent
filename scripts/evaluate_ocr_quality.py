# scripts/evaluate_ocr_quality.py

from ocr.quality_predictor import assess_image_quality
from pathlib import Path
import csv

IMAGE_DIR   = Path("data/sample_receipts")
OUTPUT_PATH = Path("evals/results/ocr_quality_report.csv")

def main():
    images = list(IMAGE_DIR.glob("*.jpg"))
    if not images:
        print(f"No images found in {IMAGE_DIR}")
        return

    print(f"Testing {len(images)} images...\n")

    rows = []
    for img in sorted(images):
        report = assess_image_quality(img)
        rows.append({
            "filename":         img.name,
            "blur_score":       report.blur_score,
            "contrast_score":   report.contrast_score,
            "resolution_score": report.resolution_score,
            "overall_score":    report.overall_score,
            "passed":           report.passed,
            "message":          report.message,
        })
        status = "PASS" if report.passed else "FAIL"
        print(f"  {img.name}: overall={report.overall_score}  blur={report.blur_score}  contrast={report.contrast_score}  [{status}]")

    OUTPUT_PATH.parent.mkdir(exist_ok=True)
    with open(OUTPUT_PATH, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    passed     = sum(1 for r in rows if r["passed"])
    avg_score  = round(sum(r["overall_score"] for r in rows) / len(rows), 3)
    avg_blur   = round(sum(r["blur_score"] for r in rows) / len(rows), 2)
    avg_contrast = round(sum(r["contrast_score"] for r in rows) / len(rows), 2)

    print(f"\n{'='*50}")
    print(f"  OCR QUALITY SUMMARY")
    print(f"{'='*50}")
    print(f"  Total images:   {len(rows)}")
    print(f"  Passed:         {passed}/{len(rows)} ({round(passed/len(rows)*100, 1)}%)")
    print(f"  Failed:         {len(rows)-passed}/{len(rows)}")
    print(f"  Avg score:      {avg_score}")
    print(f"  Avg blur:       {avg_blur}")
    print(f"  Avg contrast:   {avg_contrast}")
    print(f"{'='*50}")
    print(f"\n  Saved to: {OUTPUT_PATH}\n")

if __name__ == "__main__":
    main()