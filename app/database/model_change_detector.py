"""
统一的模型变化检测器
用于检测模型配置变化并在必要时清空对应的向量数据库集合
"""

import json
from pathlib import Path
from typing import Optional, Tuple

from app.config.settings import settings
from app.database.weaviate_client import weaviate_client
from app.utils.logger_utils import get_logger

logger = get_logger(__name__)


class ModelChangeDetector:
    """模型变化检测器 - 统一管理Object和Face模式的模型变化检测"""

    def __init__(self):
        self.config_file = Path("data/temp/config/model_config.json")
        self.app_mode = settings.app_mode
        self._cached_config = None  # 缓存配置避免重复读取

    def get_expected_vector_dim(self) -> int:
        """根据当前模式获取期望的向量维度"""
        if self.app_mode == "object":
            # Object模式 - 根据后端和模型路径判断维度
            model_dims = {
                "vits16": 384,
                "vitb16": 768,
                "vitl16": 1024,
                "vith16plus": 1280
            }

            # 根据后端选择模型路径
            if settings.object_backend == "pytorch":
                model_path = settings.pytorch_dinov3_path
            else:
                model_path = settings.get_dinov3_model_path()

            for model_name, dim in model_dims.items():
                if model_name in model_path:
                    return dim
            return 0
        elif self.app_mode == "face":
            # Face模式 - InsightFace固定512维
            return 512
        else:
            logger.warning(f"Unknown app_mode: {self.app_mode}")
            return 0

    def get_collection_name(self) -> str:
        """根据当前模式获取集合名称"""
        if self.app_mode == "object":
            return "ObjectData"
        elif self.app_mode == "face":
            return "FaceData"
        else:
            return "UnknownData"

    def _load_saved_config(self) -> dict:
        """加载已保存的配置文件（带缓存）"""
        if self._cached_config is not None:
            return self._cached_config

        config = {}
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Failed to read config file: {e}")

        self._cached_config = config
        return config

    def get_current_model_config(self) -> dict:
        """获取当前模式的模型配置"""
        if self.app_mode == "object":
            # Object模式 - 返回后端类型和模型路径
            if settings.object_backend == "pytorch":
                return {
                    "backend": "pytorch",
                    "dinov3_path": settings.pytorch_dinov3_path,
                    "birefnet_path": settings.pytorch_birefnet_path
                }
            else:
                return {
                    "backend": "onnx",
                    "dinov3_path": settings.get_dinov3_model_path(),
                    "bg_removal_model": settings.bg_removal_model
                }
        elif self.app_mode == "face":
            return {
                "backend": "insightface",
                "model_name": settings.face_model_name
            }
        else:
            return {}

    def check_model_change(self) -> Tuple[bool, str]:
        """
        检查模型配置是否变化

        逻辑：对比 .env 和 temp/config 中的模型配置，不一样就清空

        Returns:
            (need_reset, reason): 是否需要重置，原因说明
        """
        current_config = self.get_current_model_config()

        # 确保配置目录存在
        self.config_file.parent.mkdir(parents=True, exist_ok=True)

        # 读取已保存的配置
        old_config = {}
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    old_config = json.load(f)
            except:
                pass

        # 获取旧配置中的模式配置
        old_mode_config = old_config.get(self.app_mode, {})

        # 对比配置
        if old_mode_config and old_mode_config != current_config:
            return True, f"Model config changed: {old_mode_config} -> {current_config}"

        return False, ""

    def reset_collection_if_needed(self) -> bool:
        """
        如果需要，清空并重建集合

        Returns:
            是否执行了重置
        """
        need_reset, reason = self.check_model_change()
        collection_name = self.get_collection_name()

        if need_reset:
            logger.warning(f"{collection_name} reset needed: {reason}")
            try:
                # 确保数据库连接
                if not weaviate_client.client:
                    weaviate_client.connect()

                # 删除集合
                if weaviate_client.delete_collection():
                    logger.success(f"{collection_name} cleared successfully")
                    # 重建集合（根据客户端类型选择API）
                    if hasattr(weaviate_client.client, 'collections'):
                        weaviate_client.setup_collection()
                    else:
                        weaviate_client.setup_collection_legacy()
                    logger.success(f"{collection_name} collection recreated")

                # 更新配置文件
                self.save_current_config()
                return True

            except Exception as e:
                logger.error(f"Failed to clear {collection_name}: {e}")
                raise
        else:
            current_config = self.get_current_model_config()
            expected_dim = self.get_expected_vector_dim()

            # 构造友好的日志信息
            if self.app_mode == "object":
                backend = current_config.get("backend", "unknown")
                logger.info(f"Object model config OK: backend={backend}, vector_dim={expected_dim}D")
            elif self.app_mode == "face":
                model_name = current_config.get("model_name", "unknown")
                logger.info(f"Face model config OK: model={model_name}, vector_dim={expected_dim}D")

            # 保存当前配置（即使没有变化，也要确保配置文件是最新的）
            self.save_current_config()
            return False

    def save_current_config(self):
        """保存当前模型配置"""
        # 读取现有配置
        old_config = {}
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    old_config = json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Failed to read existing config: {e}")

        # 只保留有效的 app_mode 配置（object 和 face）
        # 过滤掉旧格式的顶层字段
        valid_modes = {"object", "face"}
        new_config = {k: v for k, v in old_config.items() if k in valid_modes}

        # 更新当前模式的配置
        current_mode_config = self.get_current_model_config()
        new_config[self.app_mode] = current_mode_config

        # 保存配置
        try:
            with open(self.config_file, 'w') as f:
                json.dump(new_config, f, indent=2)
            logger.debug(f"Model config saved: {new_config}")
        except (IOError, TypeError) as e:
            logger.warning(f"Failed to save model config: {e}")


# 单例实例
model_change_detector = ModelChangeDetector()