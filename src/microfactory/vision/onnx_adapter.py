from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol, Sequence

import cv2
import numpy as np


class _InputInfo(Protocol):
    name: str


class InferenceSession(Protocol):
    def get_inputs(self) -> Sequence[_InputInfo]: ...

    def run(self, output_names: Any, input_feed: dict[str, np.ndarray]) -> list[np.ndarray]: ...


@dataclass(frozen=True, slots=True)
class OnnxInferenceResult:
    outputs: tuple[np.ndarray, ...]
    input_shape: tuple[int, ...]


class OnnxDetectorAdapter:
    """Thin injectable ONNX Runtime boundary.

    Decoding detector-specific tensors is intentionally outside this adapter so
    model semantics cannot leak into the verification policy.
    """

    def __init__(self, session: InferenceSession, *, input_size: tuple[int, int] = (224, 224)) -> None:
        inputs = list(session.get_inputs())
        if len(inputs) != 1:
            raise ValueError("baseline adapter expects exactly one model input")
        self._session = session
        self._input_name = inputs[0].name
        self._input_size = input_size

    @classmethod
    def from_path(
        cls,
        model_path: str | Path,
        *,
        input_size: tuple[int, int] = (224, 224),
        providers: list[str] | None = None,
    ) -> "OnnxDetectorAdapter":
        try:
            import onnxruntime as ort  # type: ignore[import-not-found]
        except ImportError as exc:
            raise RuntimeError("onnxruntime is required to load an ONNX model") from exc
        session = ort.InferenceSession(str(model_path), providers=providers or ["CPUExecutionProvider"])
        return cls(session, input_size=input_size)

    def infer(self, image: np.ndarray) -> OnnxInferenceResult:
        if image.ndim == 2:
            bgr = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
        elif image.ndim == 3 and image.shape[2] == 3:
            bgr = image
        else:
            raise ValueError("image must be HxW or HxWx3")
        width, height = self._input_size
        resized = cv2.resize(bgr, (width, height), interpolation=cv2.INTER_LINEAR)
        rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
        tensor = rgb.astype(np.float32) / 255.0
        tensor = np.transpose(tensor, (2, 0, 1))[None, ...]
        outputs = self._session.run(None, {self._input_name: tensor})
        return OnnxInferenceResult(tuple(np.asarray(output) for output in outputs), tuple(tensor.shape))
