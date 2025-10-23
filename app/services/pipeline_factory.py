from app.config.settings import settings
from app.services.pipelines.base_pipeline import BasePipeline
from app.utils.logger_utils import get_logger

logger = get_logger(__name__)

def get_pipeline() -> BasePipeline:
    """Get pipeline based on app_mode and backend selection"""
    if settings.app_mode == "object":
        # Object mode: support ONNX (CPU) or PyTorch (GPU) backend
        if settings.object_backend == "pytorch":
            logger.info("🚀 Loading PyTorch backend (GPU-accelerated)")
            from app.services.pipelines.object_pipeline_pytorch import get_object_pipeline_pytorch
            return get_object_pipeline_pytorch()
        else:
            logger.info("💻 Loading ONNX backend (CPU-optimized)")
            from app.services.pipelines.object_pipeline import object_pipeline
            return object_pipeline
    elif settings.app_mode == "face":
        from app.services.pipelines.face_pipeline import face_pipeline
        return face_pipeline
    else:
        raise ValueError(f"Unknown app mode: {settings.app_mode}")
