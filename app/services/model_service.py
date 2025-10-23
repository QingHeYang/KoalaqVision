# Compatibility layer - delegates to pipeline selected by factory
from app.services.pipeline_factory import get_pipeline
from PIL import Image
from typing import Optional

class ModelService:
    """Compatibility wrapper for pipeline (supports ONNX/PyTorch backends)"""

    def __init__(self):
        self._pipeline = get_pipeline()

    def __getattr__(self, name):
        """Delegate attribute access to pipeline (supports both ONNX and PyTorch)"""
        return getattr(self._pipeline, name)

    def extract_features(self, image: Image.Image, normalize: bool = True) -> Optional[list]:
        """Extract features"""
        return self._pipeline.extract_features(image, normalize)

    def remove_background(self, image: Image.Image) -> Optional[Image.Image]:
        """Remove background"""
        return self._pipeline.remove_background(image)

model_service = ModelService()
