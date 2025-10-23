"""
MiniFASNet Liveness Detection using ONNX

Based on Silent-Face-Anti-Spoofing by Minivision
https://github.com/minivision-ai/Silent-Face-Anti-Spoofing
"""

import cv2
import numpy as np
import onnxruntime as ort
from typing import Tuple, Optional
from pathlib import Path
from app.utils.logger_utils import get_logger

logger = get_logger(__name__)


class MiniFASNetLiveness:
    """
    MiniFASNet 活体检测（ONNX 版本）

    特点：
    - 轻量级模型（~1.7MB）
    - CPU 友好（20-40ms）
    - 多尺度融合检测
    - 3分类输出：真人、纸质照片、电子屏幕

    性能指标（根据官方数据）：
    - FPR: 1e-5
    - TPR: 97.8%
    - 速度: 20ms (移动端)
    """

    def __init__(self, model_dir: str = "data/models/minifasnet"):
        """
        初始化活体检测器

        Args:
            model_dir: ONNX 模型目录
        """
        self.model_dir = Path(model_dir)
        self.sessions = {}
        self.input_size = (80, 80)

        # 加载所有可用模型
        self._load_models()

    def _load_models(self):
        """加载所有 ONNX 模型"""
        if not self.model_dir.exists():
            raise FileNotFoundError(f"Model directory not found: {self.model_dir}")

        onnx_files = list(self.model_dir.glob("*.onnx"))

        if not onnx_files:
            raise FileNotFoundError(f"No ONNX models found in {self.model_dir}")

        logger.info(f"Loading MiniFASNet models from: {self.model_dir}")

        for onnx_file in onnx_files:
            try:
                session = ort.InferenceSession(
                    str(onnx_file),
                    providers=['CPUExecutionProvider']
                )
                self.sessions[onnx_file.name] = session
                logger.info(f"  ✅ Loaded: {onnx_file.name}")
            except Exception as e:
                logger.error(f"  ❌ Failed to load {onnx_file.name}: {e}")

        if not self.sessions:
            raise RuntimeError("No models loaded successfully")

        logger.info(f"MiniFASNet initialized with {len(self.sessions)} model(s)")

    def _get_new_box(self, src_w: int, src_h: int, bbox: list, scale: float):
        """
        计算扩边后的裁剪框（完全复制原始项目逻辑）

        Args:
            src_w: 图像宽度
            src_h: 图像高度
            bbox: 人脸框 [x, y, w, h]
            scale: 扩边比例

        Returns:
            (left_top_x, left_top_y, right_bottom_x, right_bottom_y)
        """
        x = bbox[0]
        y = bbox[1]
        box_w = bbox[2]
        box_h = bbox[3]

        # 限制scale不超过图像边界
        scale = min((src_h-1)/box_h, min((src_w-1)/box_w, scale))

        new_width = box_w * scale
        new_height = box_h * scale
        center_x, center_y = box_w/2+x, box_h/2+y

        left_top_x = center_x - new_width/2
        left_top_y = center_y - new_height/2
        right_bottom_x = center_x + new_width/2
        right_bottom_y = center_y + new_height/2

        # 边界处理：调整另一边来保持尺寸
        if left_top_x < 0:
            right_bottom_x -= left_top_x
            left_top_x = 0

        if left_top_y < 0:
            right_bottom_y -= left_top_y
            left_top_y = 0

        if right_bottom_x > src_w-1:
            left_top_x -= right_bottom_x-src_w+1
            right_bottom_x = src_w-1

        if right_bottom_y > src_h-1:
            left_top_y -= right_bottom_y-src_h+1
            right_bottom_y = src_h-1

        return int(left_top_x), int(left_top_y), int(right_bottom_x), int(right_bottom_y)

    def _preprocess_face(self, img_bgr: np.ndarray, bbox: list, scale: float) -> np.ndarray:
        """
        预处理人脸图像（完全复制原始项目逻辑）

        Args:
            img_bgr: BGR 格式图像
            bbox: 人脸框 [x, y, w, h]
            scale: 扩边比例 (2.7 或 4.0)

        Returns:
            预处理后的图像 (80x80x3, CHW, float32, [0,255])
        """
        src_h, src_w = img_bgr.shape[:2]

        # 使用原始项目的裁剪逻辑
        left_top_x, left_top_y, right_bottom_x, right_bottom_y = self._get_new_box(
            src_w, src_h, bbox, scale
        )

        # 裁剪（注意：包含右下边界 +1）
        face_crop = img_bgr[left_top_y:right_bottom_y+1, left_top_x:right_bottom_x+1]

        # Resize 到模型输入尺寸
        face_resized = cv2.resize(face_crop, self.input_size)

        # 重要：保持 BGR 格式（不转换为 RGB）
        # 原始模型使用 cv2.imread 的 BGR 输入训练
        face_float = face_resized.astype(np.float32)  # [0, 255] 范围

        # 转换为 CHW 格式
        face_chw = np.transpose(face_float, (2, 0, 1))

        # 添加 batch 维度
        face_batch = np.expand_dims(face_chw, axis=0)

        return face_batch

    def _parse_model_name(self, model_name: str) -> Tuple[float, str]:
        """
        解析模型名称获取 scale 参数

        Examples:
            "2.7_80x80_MiniFASNetV2.onnx" -> (2.7, "MiniFASNetV2")
            "4_0_0_80x80_MiniFASNetV1SE.onnx" -> (4.0, "MiniFASNetV1SE")

        Returns:
            (scale, model_type)
        """
        parts = model_name.split('_')

        # 解析 scale
        if parts[0] == '4':
            scale = 4.0
        else:
            scale = float(parts[0])

        # 解析 model type
        model_type = parts[-1].replace('.onnx', '')

        return scale, model_type

    def predict(self, img_bgr: np.ndarray, bbox: list) -> Tuple[bool, float, dict]:
        """
        活体检测预测

        Args:
            img_bgr: BGR 格式图像
            bbox: 人脸框 [x, y, w, h]

        Returns:
            (is_real, score, details)
            - is_real: 是否为真人
            - score: 真人分数 [0,1]
            - details: 详细信息
                - real_score: 真人分数
                - paper_score: 纸质照片分数
                - screen_score: 电子屏幕分数
                - label: 标签 (0=fake, 1=real, 2=fake)
        """
        if not self.sessions:
            raise RuntimeError("No models loaded")

        # 累积多个模型的预测
        predictions = np.zeros((1, 3))  # [batch, classes]

        for model_name, session in self.sessions.items():
            # 解析模型参数
            scale, model_type = self._parse_model_name(model_name)

            # 预处理
            input_data = self._preprocess_face(img_bgr, bbox, scale)

            # 推理
            input_name = session.get_inputs()[0].name
            output_name = session.get_outputs()[0].name

            output = session.run([output_name], {input_name: input_data})[0]

            # Softmax
            exp_output = np.exp(output - np.max(output, axis=1, keepdims=True))
            softmax_output = exp_output / np.sum(exp_output, axis=1, keepdims=True)

            predictions += softmax_output

        # 平均多个模型的结果
        predictions = predictions / len(self.sessions)

        # 获取标签和分数
        label = np.argmax(predictions[0])
        scores = predictions[0]

        # 类别：0=fake, 1=real, 2=fake
        # 真人分数 = real / (real + fake)
        real_score = float(scores[1])
        fake_score = float(scores[0] + scores[2])

        # 归一化真人分数
        total = real_score + fake_score
        if total > 0:
            real_score_normalized = real_score / total
        else:
            real_score_normalized = 0.5

        # 判断是否为真人（标签1为真人）
        is_real = (label == 1)

        # 详细信息
        details = {
            "real_score": float(scores[1]),
            "paper_score": float(scores[0]),
            "screen_score": float(scores[2]),
            "label": int(label),
            "label_text": ["纸质照片", "真人", "电子屏幕"][int(label)],
            "num_models": len(self.sessions)
        }

        logger.debug(f"Liveness prediction: label={label}, real_score={real_score_normalized:.4f}, details={details}")

        return is_real, real_score_normalized, details

    def predict_with_threshold(self, img_bgr: np.ndarray, bbox: list,
                               threshold: float = 0.6,
                               paper_reject_threshold: float = 0.3,
                               screen_reject_threshold: float = 0.3) -> Tuple[bool, float, dict]:
        """
        使用阈值的活体检测（增强版）

        Args:
            img_bgr: BGR 格式图像
            bbox: 人脸框 [x, y, w, h]
            threshold: 真人阈值 [0,1]，默认 0.6
            paper_reject_threshold: 纸质照片分数拒绝阈值，默认 0.3
            screen_reject_threshold: 电子屏幕分数拒绝阈值，默认 0.3

        Returns:
            (is_real, score, details)
        """
        is_real_label, score, details = self.predict(img_bgr, bbox)

        # 获取原始分数
        real_score = details["real_score"]
        paper_score = details["paper_score"]
        screen_score = details["screen_score"]

        # 严格检测规则：
        # 1. 真人分数 > threshold (0.6)
        # 2. 纸质照片分数 < paper_reject_threshold (0.3)
        # 3. 电子屏幕分数 < screen_reject_threshold (0.3)
        is_real = (
            real_score > threshold and  # 真人分数足够高
            paper_score < paper_reject_threshold and  # 纸质照片分数不能太高
            screen_score < screen_reject_threshold  # 电子屏幕分数不能太高
        )

        # 记录拒绝原因
        reject_reason = None
        if not is_real:
            if real_score <= threshold:
                reject_reason = f"真人分数过低: {real_score:.4f} <= {threshold}"
            elif paper_score >= paper_reject_threshold:
                reject_reason = f"纸质照片分数过高: {paper_score:.4f} >= {paper_reject_threshold}"
            elif screen_score >= screen_reject_threshold:
                reject_reason = f"电子屏幕分数过高: {screen_score:.4f} >= {screen_reject_threshold}"

        details["threshold"] = threshold
        details["paper_reject_threshold"] = paper_reject_threshold
        details["screen_reject_threshold"] = screen_reject_threshold
        details["passed"] = is_real
        details["reject_reason"] = reject_reason

        return is_real, score, details


# 单例实例（可选）
_minifasnet_liveness = None

def get_liveness_detector() -> MiniFASNetLiveness:
    """获取活体检测器单例"""
    global _minifasnet_liveness
    if _minifasnet_liveness is None:
        _minifasnet_liveness = MiniFASNetLiveness()
    return _minifasnet_liveness
