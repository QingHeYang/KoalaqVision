from pydantic_settings import BaseSettings
from pydantic import Field
from pathlib import Path
from typing import Optional

class Settings(BaseSettings):
    """应用配置"""

    # 应用模式
    app_mode: str = Field(default="object", env="APP_MODE", description="object or face")

    # API配置
    app_name: str = "KoalaqVision"
    app_version: str = "0.1.0"
    api_port: int = Field(default=10770, env="API_PORT")
    api_host: str = Field(default="0.0.0.0", env="API_HOST")
    
    # 模型路径配置
    birefnet_model_path: str = Field(
        default="data/models/BiRefNet-ONNX/onnx/model.onnx",
        env="BIREFNET_MODEL_PATH",
        description="BiRefNet抠图模型路径"
    )

    dinov3_model_path: str = Field(
        default="",
        env="DINOV3_MODEL_PATH",
        description="DINOv3特征提取模型路径（自定义路径，优先级高于DINOV3_MODEL快捷选项）"
    )

    u2net_model_path: str = Field(
        default="data/models/U2Net/u2net.onnx",
        env="U2NET_MODEL_PATH",
        description="U2Net抠图模型路径"
    )

    u2netp_model_path: str = Field(
        default="data/models/U2Net/u2netp.onnx",
        env="U2NETP_MODEL_PATH",
        description="U2Net-P轻量抠图模型路径"
    )
    
    # 模型配置
    use_gpu: bool = Field(default=False, env="USE_GPU")

    # ONNX Runtime threading optimization
    onnx_thread_mode: str = Field(
        default="auto",
        env="ONNX_THREAD_MODE",
        description="ONNX threading mode: auto (balanced) / performance (low latency) / single (high concurrency)"
    )

    # DINOv3 模型选择（简单模式）
    dinov3_model: str = Field(
        default="",
        env="DINOV3_MODEL",
        description="DINOv3 model preset: vits16 / vitl16 (leave empty to use DINOV3_MODEL_PATH)"
    )

    # 背景去除模型选择
    bg_removal_model: str = Field(
        default="u2netp",
        env="BG_REMOVAL_MODEL",
        description="背景去除模型: birefnet / u2net / u2netp"
    )

    # Object mode backend selection
    object_backend: str = Field(
        default="onnx",
        env="OBJECT_BACKEND",
        description="Object recognition backend: onnx (CPU optimized) / pytorch (GPU accelerated)"
    )

    # PyTorch backend model paths
    pytorch_birefnet_path: str = Field(
        default="data/models/BiRefNet",
        env="PYTORCH_BIREFNET_PATH",
        description="PyTorch BiRefNet model directory"
    )
    pytorch_dinov3_path: str = Field(
        default="data/models/dinov3-vith16plus-pretrain-lvd1689m",
        env="PYTORCH_DINOV3_PATH",
        description="PyTorch DINOv3 model directory"
    )

    # DINOv3 feature extraction optimization
    dinov3_temperature: float = Field(
        default=0.3,
        env="DINOV3_TEMPERATURE",
        description="Temperature for similarity score scaling (lower=more discriminative, 0.1-1.0)"
    )
    dinov3_use_multi_scale: bool = Field(
        default=True,
        env="DINOV3_USE_MULTI_SCALE",
        description="Use multi-scale features (CLS + patch tokens)"
    )
    dinov3_cls_weight: float = Field(
        default=0.7,
        env="DINOV3_CLS_WEIGHT",
        description="Weight for CLS token in multi-scale fusion (0-1)"
    )
    dinov3_patch_weight: float = Field(
        default=0.3,
        env="DINOV3_PATCH_WEIGHT",
        description="Weight for patch tokens in multi-scale fusion (0-1)"
    )
    dinov3_feature_enhancement: bool = Field(
        default=True,
        env="DINOV3_FEATURE_ENHANCEMENT",
        description="Apply feature enhancement (standardization)"
    )

    # Weaviate配置
    weaviate_url: str = Field(default="http://localhost:8080", env="WEAVIATE_URL")
    weaviate_api_key: Optional[str] = Field(default=None, env="WEAVIATE_API_KEY")
    
    # 文件存储路径
    upload_path: str = Field(default="data/upload", env="UPLOAD_PATH", description="上传文件保存路径")
    temp_path: str = Field(default="data/temp", env="TEMP_PATH", description="临时文件保存路径")
    
    # 调试配置
    debug: bool = Field(default=False, env="DEBUG")
    reload: bool = Field(default=False, env="RELOAD")
    log_style: str = Field(default="block", env="LOG_STYLE", description="Logger style: block or tree")

    # SSL/HTTPS 配置
    enable_ssl: bool = Field(default=False, env="ENABLE_SSL", description="Enable HTTPS")
    ssl_cert_dir: str = Field(
        default="certs",
        env="SSL_CERT_DIR",
        description="SSL certificate directory (auto-discover cert and key files)"
    )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
    
    def get_model_paths(self) -> dict:
        """获取模型路径字典"""
        return {
            "birefnet": Path(self.birefnet_model_path),
            "dinov3": Path(self.dinov3_model_path)
        }
    
    def validate_paths(self) -> bool:
        """验证模型路径是否存在"""
        paths = self.get_model_paths()
        for name, path in paths.items():
            if not path.exists():
                print(f"Warning: Model file not found: {name} at {path}")
                return False
        return True
    
    @property
    def onnx_providers(self) -> list:
        """获取ONNX推理引擎列表"""
        if self.use_gpu:
            return ['CUDAExecutionProvider', 'CPUExecutionProvider']
        return ['CPUExecutionProvider']

    def get_dinov3_model_path(self) -> str:
        """获取 DINOv3 模型实际路径

        优先级：
        1. DINOV3_MODEL_PATH（自定义路径） - 如果设置则优先使用
        2. DINOV3_MODEL（快捷选项映射） - 如果PATH未设置则使用映射表
        3. 默认值
        """
        # 优先级1：如果设置了自定义路径（非空），直接使用
        if self.dinov3_model_path:
            return self.dinov3_model_path

        # 优先级2：使用快捷选项映射表
        if self.dinov3_model:
            DINOV3_MODEL_MAPPING = {
                "vits16": "data/models/dinov3-vits16/model.onnx",        # 83MB, 384-dim
                "vitl16": "data/models/dinov3-vitl16/model_q4.onnx",     # 185MB, 1024-dim
            }
            if self.dinov3_model in DINOV3_MODEL_MAPPING:
                return DINOV3_MODEL_MAPPING[self.dinov3_model]

        # 优先级3：都没设置，返回默认值
        return "data/models/dinov3-vitl16/model_q4.onnx"

    # Face mode config
    face_model_name: str = Field(
        default="buffalo_l",
        env="FACE_MODEL_NAME",
        description="Face model name (buffalo_l)"
    )
    face_model_root: str = Field(
        default="data/models",
        env="FACE_MODEL_ROOT",
        description="Face model root directory"
    )
    face_det_thresh: float = Field(
        default=0.3,
        env="FACE_DET_THRESH",
        description="Face detection confidence threshold [0,1], lower=more faces detected, recommended 0.3-0.5"
    )
    face_det_size: tuple = Field(
        default=(640, 640),
        description="Face detection input size (width, height) - hardcoded, not configurable via env"
    )
    face_enable_multi_scale: bool = Field(
        default=True,
        env="FACE_ENABLE_MULTI_SCALE",
        description="Enable multi-scale detection for large/close-up faces"
    )
    face_det_size_fallback: tuple = Field(
        default=(256, 256),
        description="Fallback detection size for large faces - hardcoded, not configurable via env"
    )

    # Liveness detection config
    enable_liveness: bool = Field(
        default=False,
        env="ENABLE_LIVENESS",
        description="Enable liveness detection (anti-spoofing)"
    )
    liveness_threshold: float = Field(
        default=0.6,
        env="LIVENESS_THRESHOLD",
        description="Liveness detection threshold [0,1] - real score must be > threshold"
    )
    liveness_paper_reject_threshold: float = Field(
        default=0.3,
        env="LIVENESS_PAPER_REJECT_THRESHOLD",
        description="Paper photo rejection threshold [0,1] - reject if paper score > threshold"
    )
    liveness_screen_reject_threshold: float = Field(
        default=0.3,
        env="LIVENESS_SCREEN_REJECT_THRESHOLD",
        description="Electronic screen rejection threshold [0,1] - reject if screen score > threshold"
    )
    minifasnet_model_dir: str = Field(
        default="data/models/minifasnet",
        env="MINIFASNET_MODEL_DIR",
        description="MiniFASNet ONNX models directory"
    )

# 单例配置实例
settings = Settings()