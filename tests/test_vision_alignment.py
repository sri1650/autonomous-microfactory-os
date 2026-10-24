import json
from pathlib import Path

import cv2
import numpy as np
import pytest

from microfactory.vision.alignment import estimate_alignment

ROOT = Path(__file__).parents[1]


def render(case):
    height, width = case["image_size"]
    image = np.zeros((height, width), dtype=np.uint8)
    rect = (tuple(case["center"]), tuple(case["size"]), float(case["angle_deg"]))
    box = cv2.boxPoints(rect).astype(np.int32)
    cv2.fillConvexPoly(image, box, 255)
    return image


@pytest.mark.parametrize("case", json.loads((ROOT / "tests/fixtures/vision/alignment_cases.json").read_text()))
def test_alignment_matches_labelled_synthetic_fixture(case):
    result = estimate_alignment(
        render(case),
        expected_center_px=tuple(case["expected_center"]),
        expected_angle_deg=case["expected_angle_deg"],
    )
    expected_position = float(np.linalg.norm(np.array(case["center"]) - np.array(case["expected_center"])))
    assert result.position_error_px == pytest.approx(expected_position, abs=1.0)
    assert result.angle_error_deg <= 1.5
    assert result.confidence > 0.5


def test_alignment_rejects_empty_image():
    with pytest.raises(ValueError, match="insufficient foreground"):
        estimate_alignment(
            np.zeros((100, 100), dtype=np.uint8),
            expected_center_px=(50, 50),
            expected_angle_deg=0,
        )
