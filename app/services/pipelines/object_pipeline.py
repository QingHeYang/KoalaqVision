import onnxruntime as ort
import numpy as np
from pathlib import Path
from PIL import Image
from typing import Optional, Tuple
from app.config.settings import settings
from app.services.pipelines.base_pipeline import BasePipeline
from app.database.model_change_detector import model_change_detector
from app.utils.logger_utils import get_logger

ort.set_default_logger_severity(3)
logger = get_logger(__name__)

class ObjectPipeline(BasePipeline):
    """Object recognition pipeline"""

    def __init__(self):
        self.dinov3_session: Optional[ort.InferenceSession] = None
        self.birefnet_session: Optional[ort.InferenceSession] = None
        self.u2net_session: Optional[ort.InferenceSession] = None
        self.u2netp_session: Optional[ort.InferenceSession] = None
        self.bg_removal_session: Optional[ort.InferenceSession] = None
        self.providers = settings.onnx_providers
        self.bg_model_type = settings.bg_removal_model

    def get_vector_dim(self) -> int:
        """Get vector dimension from model path"""
        model_dims = {
            "vits16": 384,
            "vitb16": 768,
            "vitl16": 1024,
            "vith16plus": 1280
        }
        model_path = settings.get_dinov3_model_path()
        for model_name, dim in model_dims.items():
            if model_name in model_path:
                return dim
        return 0

    def get_collection_name(self) -> str:
        """Get collection name"""
        return "ObjectData"

    def load_models(self):
        """Load ONNX models"""
        try:
            # 检查模型变化，必要时清空数据库
            model_change_detector.reset_collection_if_needed()

            # 1. Check and load background removal model
            bg_model = settings.bg_removal_model.lower()
            bg_path = None

            if bg_model == 'birefnet':
                bg_path = Path(settings.birefnet_model_path)
            elif bg_model == 'u2net':
                bg_path = Path(settings.u2net_model_path)
            elif bg_model == 'u2netp':
                bg_path = Path(settings.u2netp_model_path)
            else:
                error_msg = f"Unknown background removal model: {bg_model}"
                logger.error(error_msg)
                raise ValueError(error_msg)

            # Check if background removal model exists
            if not bg_path.exists():
                error_msg = (
                    f"\n{'='*70}\n"
                    f"❌ Background Removal Model Not Found\n"
                    f"{'='*70}\n"
                    f"Model: {bg_model}\n"
                    f"Path:  {bg_path}\n\n"
                    f"📥 How to fix:\n"
                    f"   1. Download models from GitHub releases or use Docker image\n"
                    f"   2. Extract to: data/models/\n"
                    f"   3. Or use Docker: docker pull 775495797/koalaqvision:latest\n\n"
                    f"💡 Quick start with Docker:\n"
                    f"   docker compose -f deploy/docker-compose.yml up -d\n"
                    f"{'='*70}\n"
                )
                logger.error(error_msg)
                raise FileNotFoundError(f"{bg_model} model not found at {bg_path}")

            # Load background removal model
            logger.info(f"Loading {bg_model.upper()} model from {bg_path}")
            if bg_model == 'birefnet':
                self.birefnet_session = ort.InferenceSession(
                    str(bg_path),
                    providers=self.providers
                )
                self.bg_removal_session = self.birefnet_session
            elif bg_model == 'u2net':
                self.u2net_session = ort.InferenceSession(
                    str(bg_path),
                    providers=self.providers
                )
                self.bg_removal_session = self.u2net_session
            elif bg_model == 'u2netp':
                self.u2netp_session = ort.InferenceSession(
                    str(bg_path),
                    providers=self.providers
                )
                self.bg_removal_session = self.u2netp_session
            logger.info(f"{bg_model.upper()} model loaded successfully")

            # 2. Check and load DINOv3 model
            dinov3_path = Path(settings.get_dinov3_model_path())

            if not dinov3_path.exists():
                error_msg = (
                    f"\n{'='*70}\n"
                    f"❌ DINOv3 Model Not Found\n"
                    f"{'='*70}\n"
                    f"Path: {dinov3_path}\n\n"
                    f"📥 How to fix:\n"
                    f"   1. Download models from GitHub releases or use Docker image\n"
                    f"   2. Extract to: data/models/\n"
                    f"   3. Or use Docker: docker pull 775495797/koalaqvision:latest\n\n"
                    f"💡 Available model presets in .env:\n"
                    f"   DINOV3_MODEL=vits16   # Fast (83MB, 384-dim)\n"
                    f"   DINOV3_MODEL=vitl16   # Recommended (185MB, 1024-dim)\n\n"
                    f"💡 Quick start with Docker:\n"
                    f"   docker compose -f deploy/docker-compose.yml up -d\n"
                    f"{'='*70}\n"
                )
                logger.error(error_msg)
                raise FileNotFoundError(f"DINOv3 model not found at {dinov3_path}")

            # Load DINOv3 model
            logger.info(f"Loading DINOv3 model from {dinov3_path}")
            sess_options = ort.SessionOptions()

            # Configure threading based on mode
            thread_mode = settings.onnx_thread_mode.lower()

            if thread_mode == "auto":
                # Balanced mode: Auto threads + Sequential execution
                # Best for most scenarios - automatic optimization with CPU affinity
                sess_options.intra_op_num_threads = 0  # Auto = physical cores
                sess_options.inter_op_num_threads = 0
                sess_options.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL
                logger.info("🔧 ONNX threading: AUTO mode (balanced, intra=0, inter=0, SEQUENTIAL)")

            elif thread_mode == "performance":
                # Low latency mode: Auto threads + Parallel execution
                # For single requests or low concurrency scenarios
                sess_options.intra_op_num_threads = 0
                sess_options.inter_op_num_threads = 0
                sess_options.execution_mode = ort.ExecutionMode.ORT_PARALLEL
                logger.info("🚀 ONNX threading: PERFORMANCE mode (low latency, intra=0, inter=0, PARALLEL)")

            elif thread_mode == "single":
                # High concurrency mode: Single thread per session
                # Best for web servers - improves total throughput by ~50%
                sess_options.intra_op_num_threads = 1
                sess_options.inter_op_num_threads = 1
                sess_options.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL
                logger.info("⚡ ONNX threading: SINGLE mode (high concurrency, intra=1, inter=1, SEQUENTIAL)")

            else:
                # Fallback to auto mode if invalid option
                logger.warning(f"⚠️  Invalid ONNX_THREAD_MODE '{thread_mode}', falling back to 'auto'")
                sess_options.intra_op_num_threads = 0
                sess_options.inter_op_num_threads = 0
                sess_options.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL

            sess_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL

            self.dinov3_session = ort.InferenceSession(
                str(dinov3_path),
                sess_options=sess_options,
                providers=self.providers
            )
            logger.info("DINOv3 model loaded successfully with optimization")

        except Exception as e:
            logger.error(f"Error loading models: {e}")
            raise

    def _preprocess_u2net(self, image: Image.Image, size: Tuple[int, int] = (320, 320)) -> np.ndarray:
        """Preprocess for U2Net"""
        image = image.resize(size, Image.BILINEAR)
        if image.mode != 'RGB':
            image = image.convert('RGB')
        img_array = np.array(image).astype(np.float32) / 255.0
        mean = np.array([0.485, 0.456, 0.406])
        std = np.array([0.229, 0.224, 0.225])
        img_array = (img_array - mean) / std
        img_array = img_array.transpose(2, 0, 1).astype(np.float32)
        img_array = np.expand_dims(img_array, axis=0)
        return img_array

    def _preprocess_birefnet(self, image: Image.Image, size: Tuple[int, int] = (1024, 1024)) -> np.ndarray:
        """Preprocess for BiRefNet"""
        image = image.resize(size, Image.BILINEAR)
        if image.mode != 'RGB':
            image = image.convert('RGB')
        img_array = np.array(image).astype(np.float32) / 255.0
        img_array = img_array.transpose(2, 0, 1)
        img_array = np.expand_dims(img_array, axis=0)
        return img_array

    def _preprocess_dinov3(self, image: Image.Image, size: int = 518) -> np.ndarray:
        """Preprocess for DINOv3"""
        image = image.resize((size, size), Image.BILINEAR)
        if image.mode != 'RGB':
            image = image.convert('RGB')
        img_array = np.array(image).astype(np.float32) / 255.0
        mean = np.array([0.485, 0.456, 0.406])
        std = np.array([0.229, 0.224, 0.225])
        img_array = (img_array - mean) / std
        img_array = img_array.transpose(2, 0, 1).astype(np.float32)
        img_array = np.expand_dims(img_array, axis=0)
        return img_array

    def preprocess(self, image: Image.Image) -> Optional[Image.Image]:
        """Remove background"""
        if not self.bg_removal_session:
            logger.error("Background removal model not loaded")
            return None

        try:
            original_size = image.size

            if image.mode != 'RGB':
                if image.mode == 'RGBA':
                    background = Image.new('RGB', image.size, (255, 255, 255))
                    background.paste(image, mask=image.split()[3])
                    image = background
                else:
                    image = image.convert('RGB')

            if self.bg_model_type == 'birefnet':
                input_tensor = self._preprocess_birefnet(image)
            else:
                input_tensor = self._preprocess_u2net(image)

            input_name = self.bg_removal_session.get_inputs()[0].name
            outputs = self.bg_removal_session.run(None, {input_name: input_tensor})

            if self.bg_model_type in ['u2net', 'u2netp']:
                mask = outputs[0]
                mask = mask.squeeze()

                mask_min = mask.min()
                mask_max = mask.max()
                if mask_max - mask_min > 0:
                    mask_prob = (mask - mask_min) / (mask_max - mask_min)
                else:
                    mask_prob = mask
            else:
                mask_logits = outputs[0]

                def sigmoid(x):
                    return 1 / (1 + np.exp(-x))

                mask_prob = sigmoid(mask_logits)

            mask_prob = mask_prob.squeeze()
            if len(mask_prob.shape) == 3:
                mask_prob = mask_prob[0]

            mask_uint8 = (mask_prob * 255).clip(0, 255).astype(np.uint8)

            mask_pil = Image.fromarray(mask_uint8, mode='L')
            mask_resized = mask_pil.resize(original_size, Image.LANCZOS)

            image_rgba = image.convert("RGBA")
            image_rgba.putalpha(mask_resized)

            bbox = image_rgba.getbbox()
            if bbox:
                image_rgba = image_rgba.crop(bbox)
                logger.debug(f"Cropped to content: {bbox}")

            logger.info(f"Background removed using {self.bg_model_type}")
            return image_rgba

        except Exception as e:
            logger.error(f"Error removing background: {e}")
            return None

    def extract_features(self, image: Image.Image, normalize: bool = True) -> Optional[list]:
        """Extract feature vector using DINOv3"""
        if not self.dinov3_session:
            logger.error("DINOv3 model not loaded")
            return None

        try:
            if image.mode != 'RGB':
                image = image.convert('RGB')

            input_tensor = self._preprocess_dinov3(image)

            input_name = self.dinov3_session.get_inputs()[0].name
            outputs = self.dinov3_session.run(None, {input_name: input_tensor})

            features = None

            if len(outputs) > 1 and outputs[1] is not None:
                features = outputs[1]
                logger.debug(f"Using pooler_output, shape: {features.shape}")
            elif len(outputs) > 0 and outputs[0] is not None:
                last_hidden = outputs[0]
                if len(last_hidden.shape) == 3:
                    features = last_hidden[:, 0, :]
                    logger.debug(f"Using CLS token from last_hidden_state, shape: {features.shape}")
                else:
                    features = last_hidden

            if features is None:
                logger.error("No valid features extracted from model")
                return None

            feature_vector = features.squeeze()

            if normalize:
                norm = np.linalg.norm(feature_vector)
                if norm > 1e-8:
                    feature_vector = feature_vector / norm

            feature_list = feature_vector.tolist()

            logger.info(f"Feature vector dimensions: {len(feature_list)}")
            logger.debug(f"Extracted features: dimension={len(feature_list)}, normalized={normalize}")

            return feature_list

        except Exception as e:
            logger.error(f"Error extracting features: {e}")
            return None

    def remove_background(self, image: Image.Image) -> Optional[Image.Image]:
        """Alias for preprocess"""
        return self.preprocess(image)

object_pipeline = ObjectPipeline()
