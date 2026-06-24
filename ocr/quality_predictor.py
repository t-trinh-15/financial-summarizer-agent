# ocr/quality_predictor.py

from PIL import Image
import numpy as np
from scipy.ndimage import laplace
from dataclasses import dataclass
from pathlib import Path

@dataclass
class QualityReport:
    blur_score: float
    contrast_score: float
    resolution_score: float
    overall_score: float
    passed: bool
    message: str

MIN_BLUR       = 100.0
MIN_CONTRAST   = 40.0
MIN_WIDTH      = 600
MIN_HEIGHT     = 400
PASS_THRESHOLD = 0.55

def _compute_blur_score(gray: np.ndarray) -> float:
    lap = laplace(gray.astype(float))
    return float(np.var(lap))

def _compute_contrast_score(gray: np.ndarray) -> float:
    return float(np.std(gray))

def _compute_resolution_score(width: int, height: int) -> float:
    w_ratio = min(width / MIN_WIDTH, 1.0)
    h_ratio = min(height / MIN_HEIGHT, 1.0)
    return (w_ratio + h_ratio) / 2.0

def assess_image_quality(image_path: str | Path) -> QualityReport:
    img = Image.open(image_path).convert('L')
    gray = np.array(img)
    width, height = img.size

    blur       = _compute_blur_score(gray)
    contrast   = _compute_contrast_score(gray)
    resolution = _compute_resolution_score(width, height)

    blur_norm     = min(blur / 500.0, 1.0)
    contrast_norm = min(contrast / 80.0, 1.0)

    overall = (0.5 * blur_norm) + (0.3 * contrast_norm) + (0.2 * resolution)
    passed  = overall >= PASS_THRESHOLD

    issues = []
    if blur_norm < 0.4:
        issues.append("image appears blurry")
    if contrast_norm < 0.4:
        issues.append("low contrast (try better lighting)")
    if resolution < 1.0:
        issues.append(f"low resolution ({width}x{height}px, minimum {MIN_WIDTH}x{MIN_HEIGHT}px)")

    message = "Image quality is acceptable." if passed else \
              "Image quality may affect accuracy: " + ", ".join(issues) + "."

    return QualityReport(
        blur_score=round(blur, 2),
        contrast_score=round(contrast, 2),
        resolution_score=round(resolution, 2),
        overall_score=round(overall, 3),
        passed=passed,
        message=message
    )