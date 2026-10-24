from dataclasses import dataclass

import numpy as np
import pytest

from microfactory.vision.onnx_adapter import OnnxDetectorAdapter


@dataclass
class FakeInput:
    name: str = "images"


class FakeSession:
    def __init__(self):
        self.last_feed = None

    def get_inputs(self):
        return [FakeInput()]

    def run(self, output_names, input_feed):
        self.last_feed = input_feed
        batch = input_feed["images"]
        return [np.array([[float(batch.mean()), float(batch.max())]], dtype=np.float32)]


def test_adapter_preprocesses_to_nchw_float_and_returns_outputs():
    session = FakeSession()
    adapter = OnnxDetectorAdapter(session, input_size=(64, 32))
    image = np.full((10, 20, 3), 255, dtype=np.uint8)
    result = adapter.infer(image)
    assert result.input_shape == (1, 3, 32, 64)
    assert session.last_feed["images"].dtype == np.float32
    assert result.outputs[0].shape == (1, 2)


def test_from_path_fails_cleanly_without_runtime():
    try:
        import onnxruntime  # noqa: F401
    except ImportError:
        with pytest.raises(RuntimeError, match="onnxruntime"):
            OnnxDetectorAdapter.from_path("missing.onnx")
