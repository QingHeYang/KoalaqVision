import cv2
import numpy as np
from PIL import Image
from typing import Optional, Dict, Any
from pathlib import Path
from insightface.app import FaceAnalysis
from app.config.settings import settings
from app.services.pipelines.base_pipeline import BasePipeline
from app.database.model_change_detector import model_change_detector
from app.utils.logger_utils import get_logger

logger = get_logger(__name__)

class FacePipeline(BasePipeline):
    """Face recognition pipeline using InsightFace"""

    def __init__(self):
        self.app: Optional[FaceAnalysis] = None  # Primary detector (640x640)
        self.app_fallback: Optional[FaceAnalysis] = None  # Fallback detector (256x256)
        self.model_name = settings.face_model_name
        self.det_size = settings.face_det_size
        self.det_thresh = settings.face_det_thresh
        self.enable_multi_scale = settings.face_enable_multi_scale
        self.det_size_fallback = settings.face_det_size_fallback
        self.liveness_detector = None
        self.ctx_id = None  # Store ctx_id

    def load_models(self):
        """Load InsightFace models and optional liveness detector"""
        try:
            # 检查模型变化，必要时清空数据库
            model_change_detector.reset_collection_if_needed()

            # InsightFace expects: root/models/name/
            # We have: data/models/buffalo_l/
            # So set root="data", InsightFace will find data/models/buffalo_l/

            # Check if actual model files exist
            model_path = Path("data/models") / self.model_name
            if not model_path.exists():
                error_msg = (
                    f"\n{'='*70}\n"
                    f"❌ InsightFace Model Not Found\n"
                    f"{'='*70}\n"
                    f"Model: {self.model_name}\n"
                    f"Path:  {model_path}\n\n"
                    f"📥 How to fix:\n"
                    f"   1. Download InsightFace models from GitHub releases\n"
                    f"   2. Extract to: data/models/{self.model_name}/\n"
                    f"   3. Or use Docker: docker pull 775495797/koalaqvision:latest\n\n"
                    f"💡 Available models in .env:\n"
                    f"   FACE_MODEL_NAME=antelopev2  # Recommended (326MB)\n"
                    f"   FACE_MODEL_NAME=buffalo_l   # Alternative (326MB)\n"
                    f"   FACE_MODEL_NAME=buffalo_s   # Lightweight (159MB)\n\n"
                    f"💡 Quick start with Docker:\n"
                    f"   docker compose -f deploy/docker-compose.yml up -d\n"
                    f"{'='*70}\n"
                )
                logger.error(error_msg)
                raise FileNotFoundError(f"{self.model_name} model not found at {model_path}")

            # Face pipeline uses CPU mode only
            self.ctx_id = -1
            logger.info("💻 Face pipeline using CPU")

            # Load primary detector (640x640)
            logger.info(f"Loading InsightFace primary detector: {self.model_name} @ {self.det_size}")
            self.app = FaceAnalysis(
                name=self.model_name,
                root="data"
            )
            self.app.prepare(ctx_id=self.ctx_id, det_size=self.det_size, det_thresh=self.det_thresh)
            logger.success(f"✅ Primary detector loaded (det_size={self.det_size}, det_thresh={self.det_thresh})")

            # Load fallback detector if multi-scale enabled and sizes are different
            if self.enable_multi_scale and self.det_size != self.det_size_fallback:
                logger.info(f"🔄 Multi-scale detection ENABLED")
                logger.info(f"   Primary size: {self.det_size} (normal scenes)")
                logger.info(f"   Fallback size: {self.det_size_fallback} (large faces/close-ups)")
                logger.info(f"Loading InsightFace fallback detector: {self.model_name} @ {self.det_size_fallback}")
                self.app_fallback = FaceAnalysis(
                    name=self.model_name,
                    root="data"
                )
                self.app_fallback.prepare(ctx_id=self.ctx_id, det_size=self.det_size_fallback, det_thresh=self.det_thresh)
                logger.success(f"✅ Fallback detector loaded (det_size={self.det_size_fallback})")
            else:
                logger.info(f"Multi-scale detection DISABLED (enable_multi_scale={self.enable_multi_scale})")

            # Load liveness detector if enabled
            if settings.enable_liveness:
                from app.services.minifasnet_liveness import MiniFASNetLiveness
                logger.info("Loading MiniFASNet liveness detector...")
                self.liveness_detector = MiniFASNetLiveness(model_dir=settings.minifasnet_model_dir)
                logger.info(f"Liveness detector loaded (threshold={settings.liveness_threshold})")

        except Exception as e:
            logger.error(f"Failed to load models: {e}")
            raise

    def preprocess(self, image: Image.Image, enable_liveness: Optional[bool] = None) -> Optional[Dict[str, Any]]:
        """
        Detect face and optionally perform liveness detection

        Pipeline:
        1. Face detection (with multi-scale retry if enabled)
        2. Liveness detection (if enabled)
        3. Return face data with liveness info

        Args:
            image: PIL Image
            enable_liveness: 是否启用活体检测（None=使用settings配置, True/False=强制启用/禁用）

        Returns:
            Dict with:
            - face: Face object from InsightFace
            - liveness: Dict with liveness results (if enabled)
                - is_real: bool
                - score: float [0,1]
                - passed: bool (score >= threshold)
                - details: dict with full liveness info
        """
        if not self.app:
            logger.error("InsightFace model not loaded")
            return None

        try:
            # Validate image
            if image is None:
                logger.error("Input image is None")
                return None

            # Convert PIL to OpenCV format (BGR)
            img_array = np.array(image)

            # Check if image array is empty
            if img_array.size == 0:
                logger.error("Image array is empty after conversion from PIL")
                return None

            img_cv2 = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
            logger.info(f"🔍 Starting face detection (image size: {img_cv2.shape[1]}x{img_cv2.shape[0]})")

            # Try detection with primary detector (640x640)
            logger.info(f"   Step 1/2: Trying primary detector @ {self.det_size}...")
            faces = self.app.get(img_cv2)
            used_size = self.det_size

            if len(faces) > 0:
                logger.success(f"   ✅ Primary detector succeeded: found {len(faces)} face(s)")
            else:
                logger.warning(f"   ❌ Primary detector failed: no faces detected")

            # Multi-scale retry: if no faces detected and fallback detector available
            if len(faces) == 0 and self.app_fallback is not None:
                logger.warning(f"   Step 2/2: Retrying with fallback detector @ {self.det_size_fallback}...")

                # Try with fallback detector (256x256)
                faces = self.app_fallback.get(img_cv2)
                used_size = self.det_size_fallback

                if len(faces) > 0:
                    logger.success(f"   ✅ Fallback detector succeeded: found {len(faces)} face(s)")
                else:
                    logger.error(f"   ❌ Fallback detector failed: no faces detected")

            if len(faces) == 0:
                tried_sizes = [self.det_size]
                if self.app_fallback is not None:
                    tried_sizes.append(self.det_size_fallback)
                logger.error(f"❌ Face detection FAILED (tried sizes: {', '.join(str(s) for s in tried_sizes)})")
                return None

            # Use first face
            face = faces[0]
            logger.success(f"✅ Face detected at {used_size} (score={face.det_score:.3f}, bbox={face.bbox.tolist()})")

            # Prepare result
            result = {
                "face": face,
                "liveness": None
            }

            # 决定是否执行活体检测
            # 优先级：enable_liveness参数 > settings配置
            should_do_liveness = enable_liveness if enable_liveness is not None else settings.enable_liveness

            # Perform liveness detection if enabled
            if should_do_liveness and settings.enable_liveness and self.liveness_detector:
                # Convert bbox format [x1, y1, x2, y2] -> [x, y, w, h]
                x1, y1, x2, y2 = face.bbox.tolist()
                bbox = [int(x1), int(y1), int(x2 - x1), int(y2 - y1)]

                # Run liveness detection
                is_real, score, details = self.liveness_detector.predict_with_threshold(
                    img_cv2, bbox,
                    threshold=settings.liveness_threshold,
                    paper_reject_threshold=settings.liveness_paper_reject_threshold,
                    screen_reject_threshold=settings.liveness_screen_reject_threshold
                )

                result["liveness"] = {
                    "is_real": is_real,
                    "score": score,
                    "passed": details["passed"],
                    "details": details
                }

                logger.info(f"Liveness: {'✅ REAL' if is_real else '❌ FAKE'} (score={score:.4f}, label={details['label_text']})")

            return result

        except Exception as e:
            logger.error(f"Error in face preprocessing: {e}")
            return None

    def extract_features(self, face_data, normalize: bool = True) -> Optional[list]:
        """
        Extract 512D feature vector from face data

        Args:
            face_data: Dict from preprocess() or Face object (for backward compatibility)
            normalize: Not used (InsightFace already normalizes)

        Returns:
            512D feature vector (list)
        """
        try:
            if face_data is None:
                logger.error("Face data is None")
                return None

            # Handle both dict (new format) and Face object (old format)
            if isinstance(face_data, dict):
                face = face_data.get("face")
            else:
                face = face_data

            if face is None:
                logger.error("Face object is None")
                return None

            # face.normed_embedding is already L2-normalized by InsightFace
            feature_vector = face.normed_embedding.tolist()

            logger.info(f"Feature vector extracted: {len(feature_vector)}D")
            return feature_vector

        except Exception as e:
            logger.error(f"Error extracting features: {e}")
            return None

    def get_vector_dim(self) -> int:
        """Return vector dimension"""
        return 512

    def get_collection_name(self) -> str:
        """Return Weaviate collection name"""
        return "FaceData"


# Singleton instance
face_pipeline = FacePipeline()
