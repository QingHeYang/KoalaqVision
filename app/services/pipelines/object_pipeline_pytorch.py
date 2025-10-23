"""
PyTorch-based Object Recognition Pipeline
使用 PyTorch + Transformers 实现的对象识别管道，支持 GPU 加速
"""
import numpy as np
import torch
from PIL import Image
from typing import Optional, List
from transformers import AutoModelForImageSegmentation, AutoModel, AutoImageProcessor
from torchvision import transforms
from app.config.settings import settings
from app.services.pipelines.base_pipeline import BasePipeline
from app.database.model_change_detector import model_change_detector
from app.utils.logger_utils import get_logger

logger = get_logger(__name__)


class ObjectPipelinePyTorch(BasePipeline):
    """PyTorch Object Pipeline - GPU Accelerated"""

    def __init__(self):
        """Initialize PyTorch pipeline"""
        self.device = None
        self.birefnet = None
        self.birefnet_transform = None
        self.dino_model = None
        self.dino_processor = None
        self.vector_dim = 1280  # DINOv3-ViTH16Plus dimension

        # Feature extraction optimization parameters (from settings)
        self.temperature = settings.dinov3_temperature
        self.use_multi_scale = settings.dinov3_use_multi_scale
        self.cls_weight = settings.dinov3_cls_weight
        self.patch_weight = settings.dinov3_patch_weight
        self.feature_enhancement = settings.dinov3_feature_enhancement

        logger.info("🚀 Initializing PyTorch Object Pipeline...")
        logger.info(f"   📊 Feature optimization: temperature={self.temperature}, multi_scale={self.use_multi_scale}")
        if self.use_multi_scale:
            logger.info(f"   🔍 Multi-scale weights: CLS={self.cls_weight}, Patches={self.patch_weight}")
        self._detect_device()
        self.load_models()

    def _detect_device(self):
        """Detect available device (CUDA/CPU)"""
        if settings.use_gpu and torch.cuda.is_available():
            self.device = 'cuda'
            logger.success(f"✅ GPU detected: {torch.cuda.get_device_name(0)}")
            logger.info(f"   CUDA version: {torch.version.cuda}")
            logger.info(f"   GPU memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")
        else:
            self.device = 'cpu'
            if settings.use_gpu:
                logger.warning("⚠️  USE_GPU=true but CUDA not available, falling back to CPU")
            else:
                logger.info("💻 Using CPU mode")

    def load_models(self):
        """Load BiRefNet and DINOv3 models"""
        logger.info("📦 Loading PyTorch models...")

        # 检查模型变化，必要时清空数据库
        model_change_detector.reset_collection_if_needed()

        # Load BiRefNet for background removal
        self._load_birefnet()

        # Load DINOv3 for feature extraction
        self._load_dinov3()

        logger.success("✅ PyTorch models loaded successfully")

    def _load_birefnet(self):
        """Load BiRefNet background removal model"""
        try:
            from pathlib import Path

            birefnet_path = settings.pytorch_birefnet_path

            # Check if model directory exists
            if not Path(birefnet_path).exists():
                error_msg = (
                    f"\n{'='*70}\n"
                    f"❌ BiRefNet (PyTorch) Model Not Found\n"
                    f"{'='*70}\n"
                    f"Path: {birefnet_path}\n\n"
                    f"📥 How to fix:\n"
                    f"   1. Download BiRefNet PyTorch model from HuggingFace\n"
                    f"   2. Extract to: {birefnet_path}\n"
                    f"   3. Or switch to ONNX backend: OBJECT_BACKEND=onnx\n\n"
                    f"💡 Quick start with ONNX:\n"
                    f"   Change .env: OBJECT_BACKEND=onnx\n"
                    f"{'='*70}\n"
                )
                logger.error(error_msg)
                raise FileNotFoundError(f"BiRefNet model not found at {birefnet_path}")

            logger.info(f"   Loading BiRefNet from: {birefnet_path}")

            self.birefnet = AutoModelForImageSegmentation.from_pretrained(
                birefnet_path,
                trust_remote_code=True,
                local_files_only=True
            )
            self.birefnet.to(self.device)
            self.birefnet.eval()

            # Use half precision for GPU
            if self.device == 'cuda':
                self.birefnet.half()
                logger.info("   ⚡ BiRefNet using FP16 precision")

            # BiRefNet preprocessing transform
            self.birefnet_transform = transforms.Compose([
                transforms.Resize((1024, 1024)),
                transforms.ToTensor(),
                transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
            ])

            logger.success("   ✅ BiRefNet loaded")

        except Exception as e:
            logger.error(f"❌ Failed to load BiRefNet: {e}")
            raise

    def _load_dinov3(self):
        """Load DINOv3 feature extraction model"""
        try:
            from pathlib import Path

            dino_path = settings.pytorch_dinov3_path

            # Check if model directory exists
            if not Path(dino_path).exists():
                error_msg = (
                    f"\n{'='*70}\n"
                    f"❌ DINOv3 (PyTorch) Model Not Found\n"
                    f"{'='*70}\n"
                    f"Path: {dino_path}\n\n"
                    f"📥 How to fix:\n"
                    f"   1. Download DINOv3 PyTorch model from HuggingFace\n"
                    f"   2. Extract to: {dino_path}\n"
                    f"   3. Or switch to ONNX backend: OBJECT_BACKEND=onnx\n\n"
                    f"💡 Quick start with ONNX:\n"
                    f"   Change .env: OBJECT_BACKEND=onnx\n"
                    f"   Then download ONNX models or use Docker\n"
                    f"{'='*70}\n"
                )
                logger.error(error_msg)
                raise FileNotFoundError(f"DINOv3 model not found at {dino_path}")

            logger.info(f"   Loading DINOv3 from: {dino_path}")

            # Load processor
            self.dino_processor = AutoImageProcessor.from_pretrained(
                dino_path,
                local_files_only=True
            )

            # Load model
            self.dino_model = AutoModel.from_pretrained(
                dino_path,
                output_attentions=True,
                output_hidden_states=True,
                return_dict=True,
                local_files_only=True
            )
            self.dino_model.to(self.device)
            self.dino_model.eval()

            # Note: DINOv3 uses FP32 for numerical stability (FP16 causes NaN)
            logger.success(f"   ✅ DINOv3 loaded (output dim: {self.vector_dim})")

        except Exception as e:
            logger.error(f"❌ Failed to load DINOv3: {e}")
            raise

    def preprocess(self, image: Image.Image) -> Optional[Image.Image]:
        """
        Remove background from image using BiRefNet

        Args:
            image: Input PIL Image (RGB)

        Returns:
            PIL Image (RGBA) with transparent background, cropped to content
        """
        return self.remove_background(image)

    def remove_background(self, image: Image.Image) -> Optional[Image.Image]:
        """
        Remove background from image using BiRefNet

        Args:
            image: Input PIL Image (RGB)

        Returns:
            PIL Image (RGBA) with transparent background, cropped to content
        """
        try:
            # Convert to RGB if needed
            if image.mode != 'RGB':
                image = image.convert('RGB')

            original_size = image.size

            # Preprocess
            input_tensor = self.birefnet_transform(image).unsqueeze(0)
            input_tensor = input_tensor.to(self.device)

            if self.device == 'cuda':
                input_tensor = input_tensor.half()

            # Inference
            with torch.no_grad():
                outputs = self.birefnet(input_tensor)
                preds = outputs[0].squeeze()

            # Post-process mask
            pred_mask = torch.sigmoid(preds).cpu().numpy()
            pred_mask = (pred_mask * 255).astype(np.uint8)

            # Resize mask to original size
            mask_image = Image.fromarray(pred_mask).resize(original_size, Image.LANCZOS)

            # Create RGBA image
            result = image.copy()
            result.putalpha(mask_image)

            # Crop to content bbox
            bbox = result.getbbox()
            if bbox:
                result = result.crop(bbox)

            return result

        except Exception as e:
            logger.error(f"❌ Background removal failed: {e}")
            return None

    def extract_features(self, image: Image.Image, normalize: bool = True) -> Optional[List[float]]:
        """
        Extract feature vector from image using DINOv3 with optimization

        Args:
            image: Input PIL Image (RGB or RGBA)
            normalize: Whether to L2-normalize the feature vector

        Returns:
            Feature vector (1280-dimensional) as list of floats
        """
        try:
            # Convert to RGB if needed
            if image.mode != 'RGB':
                image = image.convert('RGB')

            # Preprocess
            inputs = self.dino_processor(images=image, return_tensors="pt")
            inputs = {k: v.to(self.device) if isinstance(v, torch.Tensor) else v
                      for k, v in inputs.items()}

            # Note: Keep FP32 for DINOv3 to avoid NaN issues
            # Inference
            with torch.no_grad():
                outputs = self.dino_model(**inputs)

            # Multi-scale feature extraction
            if self.use_multi_scale and hasattr(outputs, 'last_hidden_state'):
                # Extract CLS token (global features)
                cls_features = outputs.last_hidden_state[:, 0, :]  # [batch, dim]

                # Extract patch tokens (local features)
                patch_features = outputs.last_hidden_state[:, 1:, :]  # [batch, num_patches, dim]

                # Aggregate patch features (mean pooling or max pooling)
                patch_aggregated = patch_features.mean(dim=1)  # [batch, dim]

                # Weighted fusion of global and local features
                features = (self.cls_weight * cls_features +
                           self.patch_weight * patch_aggregated)

                features = features.squeeze()
                logger.debug(f"   🔍 Multi-scale fusion: CLS({self.cls_weight}) + Patches({self.patch_weight})")
            else:
                # Fallback to standard extraction
                if hasattr(outputs, 'pooler_output') and outputs.pooler_output is not None:
                    features = outputs.pooler_output.squeeze()
                else:
                    features = outputs.last_hidden_state[:, 0, :].squeeze()

            # Move to CPU for processing
            features = features.cpu()

            # Feature enhancement techniques
            if self.feature_enhancement:
                features = self._enhance_features(features)
                # Already normalized in _enhance_features, skip normalization below
                normalize = False

            # Convert to numpy
            features = features.numpy() if isinstance(features, torch.Tensor) else features

            # Apply L2 normalization (only if not already done in enhancement)
            if normalize:
                norm = np.linalg.norm(features)
                if norm > 1e-8:  # Avoid division by zero
                    features = features / norm
                    logger.debug(f"   📏 L2 normalized (norm={norm:.4f})")

            return features.tolist()

        except Exception as e:
            logger.error(f"❌ Feature extraction failed: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None

    def _enhance_features(self, features: torch.Tensor) -> torch.Tensor:
        """
        Apply feature enhancement techniques

        Args:
            features: Input feature tensor

        Returns:
            Enhanced feature tensor
        """
        # Only apply L2 normalization here, not standardization
        # Standardization makes all vectors have similar norms (~sqrt(dim))
        # which reduces discriminative power

        if len(features.shape) == 1:
            features = features.unsqueeze(0)

        # Log original norm before normalization
        original_norm = torch.norm(features, p=2, dim=-1).item()

        # Apply L2 normalization directly on torch tensor
        features = torch.nn.functional.normalize(features, p=2, dim=-1)
        logger.debug(f"   📏 L2 normalized (original norm={original_norm:.4f})")

        return features.squeeze()

    def compute_similarity(self, feat1: np.ndarray, feat2: np.ndarray,
                          use_temperature: bool = True) -> float:
        """
        Compute temperature-scaled cosine similarity between features

        Args:
            feat1: First feature vector
            feat2: Second feature vector
            use_temperature: Whether to apply temperature scaling

        Returns:
            Similarity score (0-1 range after sigmoid)
        """
        # Ensure numpy arrays
        if isinstance(feat1, list):
            feat1 = np.array(feat1)
        if isinstance(feat2, list):
            feat2 = np.array(feat2)

        # L2 normalize
        feat1_norm = feat1 / (np.linalg.norm(feat1) + 1e-8)
        feat2_norm = feat2 / (np.linalg.norm(feat2) + 1e-8)

        # Compute cosine similarity
        similarity = np.dot(feat1_norm, feat2_norm)

        # Apply temperature scaling
        if use_temperature:
            similarity = similarity / self.temperature
            # Apply sigmoid to map to 0-1 range
            similarity = 1 / (1 + np.exp(-similarity))
            logger.debug(f"   🌡️ Temperature-scaled similarity: {similarity:.4f} (τ={self.temperature})")
        else:
            # Map from [-1, 1] to [0, 1]
            similarity = (similarity + 1) / 2

        return float(similarity)

    def get_vector_dim(self) -> int:
        """Get feature vector dimension"""
        return self.vector_dim

    def get_collection_name(self) -> str:
        """Get collection name for vector database"""
        return "ObjectData"


# Global singleton instance
object_pipeline_pytorch = None

def get_object_pipeline_pytorch():
    """Get or create PyTorch object pipeline singleton"""
    global object_pipeline_pytorch
    if object_pipeline_pytorch is None:
        object_pipeline_pytorch = ObjectPipelinePyTorch()
    return object_pipeline_pytorch
