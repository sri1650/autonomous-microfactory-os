from __future__ import annotations

from math import atan2, degrees, hypot

import cv2
import numpy as np

from .contracts import AlignmentResult


def _normalise_axis_angle(angle_deg: float) -> float:
    """Normalise an unoriented major-axis angle to [-90, 90)."""
    angle = angle_deg % 180.0
    if angle >= 90.0:
        angle -= 180.0
    return angle


def _axis_error(measured_deg: float, expected_deg: float) -> float:
    measured = _normalise_axis_angle(measured_deg)
    expected = _normalise_axis_angle(expected_deg)
    diff = abs(measured - expected)
    return min(diff, 180.0 - diff)


def estimate_alignment(
    image: np.ndarray,
    *,
    expected_center_px: tuple[float, float],
    expected_angle_deg: float,
    threshold: int = 127,
) -> AlignmentResult:
    """Estimate foreground centroid and major-axis alignment from a labelled fixture image.

    This deliberately simple baseline is designed to be explainable and
    deterministic. Learned detectors can later feed the same verification policy.
    """
    if image.ndim == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    elif image.ndim == 2:
        gray = image
    else:
        raise ValueError("image must be HxW or HxWx3")

    _, mask = cv2.threshold(gray, threshold, 255, cv2.THRESH_BINARY)
    points = cv2.findNonZero(mask)
    if points is None or len(points) < 5:
        raise ValueError("insufficient foreground pixels for alignment")

    xy = points.reshape(-1, 2).astype(np.float64)
    center = xy.mean(axis=0)
    centered = xy - center
    covariance = np.cov(centered, rowvar=False, bias=True)
    eigenvalues, eigenvectors = np.linalg.eigh(covariance)
    order = np.argsort(eigenvalues)
    major = eigenvectors[:, order[-1]]
    measured_angle = _normalise_axis_angle(degrees(atan2(float(major[1]), float(major[0]))))

    major_value = float(eigenvalues[order[-1]])
    minor_value = float(eigenvalues[order[-2]])
    anisotropy = (major_value - minor_value) / max(major_value + minor_value, 1e-12)
    confidence = max(0.0, min(1.0, anisotropy))

    dx = float(center[0] - expected_center_px[0])
    dy = float(center[1] - expected_center_px[1])
    return AlignmentResult(
        expected_center_px=expected_center_px,
        measured_center_px=(float(center[0]), float(center[1])),
        expected_angle_deg=float(expected_angle_deg),
        measured_angle_deg=float(measured_angle),
        dx_px=dx,
        dy_px=dy,
        position_error_px=hypot(dx, dy),
        angle_error_deg=_axis_error(measured_angle, expected_angle_deg),
        confidence=confidence,
        foreground_pixels=int(len(xy)),
    )
