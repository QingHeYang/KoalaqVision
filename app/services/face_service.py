from typing import List, Optional, Dict, Any, Union
from PIL import Image
import uuid
import time
import cv2
import numpy as np

from app.services.pipelines.face_pipeline import face_pipeline
from app.services.vector_service import vector_service
from app.models.face_data import FaceData, FaceSearchResponse
from app.utils.image_utils import image_utils
from app.utils.logger_utils import get_logger

logger = get_logger(__name__)

class FaceService:
    """人脸识别服务"""

    def add_face(self,
                 image_source: Union[Image.Image, str],
                 person_id: str,
                 save_files: bool = True,
                 custom_data: Optional[Dict[str, Any]] = None,
                 enable_liveness: bool = False) -> FaceData:
        """
        注册人脸 - 完整流程

        Args:
            image_source: PIL图片对象或图片URL
            person_id: 人员ID
            save_files: 是否保存文件（原图和人脸图）
            custom_data: 自定义数据
            enable_liveness: 是否启用活体检测（默认False）

        Returns:
            人脸数据对象
        """
        try:
            # 生成image_id
            image_id = str(uuid.uuid4())
            logger.info(f"Processing face image with ID: {image_id}, person: {person_id}")

            # 记录总开始时间
            total_start = time.time()

            # 1. 获取图片对象
            load_start = time.time()
            if isinstance(image_source, str):
                # 从URL下载并压缩
                logger.info(f"Downloading image from URL: {image_source}")
                image = image_utils.download_and_compress(image_source)
            else:
                # 压缩传入的图片
                image = image_utils.compress_image(image_source)
            load_time = time.time() - load_start
            logger.timing("Load/compress image", load_time)

            # 2. 人脸检测和活体检测
            logger.info("Detecting face...")
            face_detect_start = time.time()
            face_data = face_pipeline.preprocess(image, enable_liveness=enable_liveness)
            face_detect_time = time.time() - face_detect_start
            logger.timing("Face detection", face_detect_time)

            if face_data is None:
                raise ValueError("No face detected in image")

            # 提取人脸信息和活体检测结果
            face = face_data.get("face") if isinstance(face_data, dict) else face_data
            liveness_result = face_data.get("liveness") if isinstance(face_data, dict) else None

            # 活体检测失败则拒绝
            if liveness_result and not liveness_result.get("passed"):
                raise ValueError(
                    f"Liveness check failed: score={liveness_result['score']:.4f}, "
                    f"label={liveness_result['details']['label_text']}"
                )

            # 记录人脸信息
            face_bbox = face.bbox.tolist() if hasattr(face, 'bbox') else None
            face_score = float(face.det_score) if hasattr(face, 'det_score') else None
            face_landmarks = face.kps.tolist() if hasattr(face, 'kps') else None

            logger.info(f"Face detected - bbox: {face_bbox}, score: {face_score:.3f}")

            # 3. 提取特征向量
            logger.info("Extracting face features...")
            feature_start = time.time()
            features = face_pipeline.extract_features(face_data)
            feature_time = time.time() - feature_start
            logger.timing("Feature extraction", feature_time)

            if features is None:
                raise ValueError("Failed to extract face features")

            # 4. 保存图片（可选）
            img_url = None
            img_face_url = None

            if save_files:
                save_start = time.time()

                # 保存原图到 data/upload/person_id/image_id/
                original_path, face_path_placeholder = image_utils.save_upload_image(
                    image=image,
                    object_id=person_id,
                    image_id=image_id,
                    save_processed=True
                )

                if original_path:
                    img_url = image_utils.get_image_url(original_path)
                    logger.info(f"Original image saved: {img_url}")

                # 保存人脸区域图片（裁剪后的人脸）
                if face_path_placeholder and face_bbox:
                    # 根据bbox裁剪人脸区域
                    img_cv2 = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
                    x1, y1, x2, y2 = [int(v) for v in face_bbox]
                    face_crop = img_cv2[y1:y2, x1:x2]

                    # 转换回PIL并保存
                    face_crop_pil = Image.fromarray(cv2.cvtColor(face_crop, cv2.COLOR_BGR2RGB))
                    face_path = image_utils.save_processed_image(
                        face_crop_pil,
                        face_path_placeholder
                    )
                    img_face_url = image_utils.get_image_url(face_path)
                    logger.info(f"Face crop saved: {img_face_url}")

                save_time = time.time() - save_start
                logger.timing("Save files", save_time)

            # 5. 创建数据对象
            face_data = FaceData(
                image_id=image_id,
                person_id=person_id,
                img_url=img_url,
                img_face_url=img_face_url,
                feature_vector=features,
                face_bbox=[round(v, 2) for v in face_bbox] if face_bbox else None,
                face_score=round(face_score, 2) if face_score is not None else None,
                face_landmarks=face_landmarks,
                custom_data=custom_data or {}
            )

            # 6. 入库
            db_start = time.time()
            vector_service.add_image(face_data)
            db_time = time.time() - db_start
            logger.timing("Database insert", db_time)
            logger.info(f"Face added to database: {image_id}")

            # 总耗时
            total_time = time.time() - total_start
            logger.timing("TOTAL TIME", total_time)

            return face_data

        except Exception as e:
            logger.error(f"Error adding face: {e}")
            raise

    def match_face(self,
                   image_source: Union[Image.Image, str],
                   save_temp: bool = False,
                   person_ids: Optional[List[str]] = None,
                   confidence: float = 0.75,
                   top_k: int = 10,
                   enable_liveness: bool = True) -> Dict[str, Any]:
        """
        人脸识别 (1:N 匹配)

        Args:
            image_source: PIL图片对象或URL
            save_temp: 是否保存到temp（保存原图+绿色人脸框）
            person_ids: 限定的person_id范围（可选）
            confidence: 置信度阈值（默认0.75，推荐0.75以上）
            top_k: 返回结果数量
            enable_liveness: 是否启用活体检测（默认True）

        Returns:
            按person_id合并的匹配结果
        """
        try:
            # 生成临时image_id
            temp_id = str(uuid.uuid4())

            # 记录总开始时间
            total_start = time.time()

            # 1. 获取图片
            load_start = time.time()
            if isinstance(image_source, str):
                logger.info(f"Downloading query image from: {image_source}")
                image = image_utils.download_and_compress(image_source)
            else:
                image = image_utils.compress_image(image_source)
            load_time = time.time() - load_start
            logger.timing("Load/compress query image", load_time)

            # 2. 人脸检测和活体检测
            logger.info("Detecting face in query image...")
            face_detect_start = time.time()
            face_data = face_pipeline.preprocess(image, enable_liveness=enable_liveness)
            face_detect_time = time.time() - face_detect_start
            logger.timing("Face detection", face_detect_time)

            if face_data is None:
                raise ValueError("No face detected in query image")

            # 提取人脸信息和活体检测结果
            face = face_data.get("face") if isinstance(face_data, dict) else face_data
            liveness_result = face_data.get("liveness") if isinstance(face_data, dict) else None

            # 活体检测失败则拒绝
            if liveness_result and not liveness_result.get("passed"):
                raise ValueError(
                    f"Liveness check failed: score={liveness_result['score']:.4f}, "
                    f"label={liveness_result['details']['label_text']}"
                )

            face_bbox = face.bbox.tolist() if hasattr(face, 'bbox') else None
            face_score = float(face.det_score) if hasattr(face, 'det_score') else None
            logger.info(f"Face detected - score: {face_score:.3f}")

            # 3. 保存临时文件（可选）- 保存原图+绿色人脸框
            temp_path = None
            if save_temp and face_bbox:
                save_temp_start = time.time()

                # 在原图上画绿色框标注人脸位置
                img_cv2 = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
                x1, y1, x2, y2 = [int(v) for v in face_bbox]

                # 画绿色矩形框 (BGR格式，绿色是 (0, 255, 0)，线宽3)
                cv2.rectangle(img_cv2, (x1, y1), (x2, y2), (0, 255, 0), 3)

                # 转回PIL格式
                img_with_bbox = Image.fromarray(cv2.cvtColor(img_cv2, cv2.COLOR_BGR2RGB))

                temp_path = image_utils.save_temp_image(
                    img_with_bbox,
                    temp_id,
                    only_object=False  # 保存完整图片（原图+框）
                )

                save_temp_time = time.time() - save_temp_start
                logger.timing("Save temp image", save_temp_time)
                logger.info(f"Temp image with face bbox saved: {temp_path}")

            # 4. 提取特征值
            logger.info("Extracting query face features...")
            feature_start = time.time()
            features = face_pipeline.extract_features(face_data)
            feature_time = time.time() - feature_start
            logger.timing("Feature extraction", feature_time)

            if features is None:
                raise ValueError("Failed to extract face features")

            # 5. 搜索相似人脸
            search_start = time.time()
            all_results = []

            if person_ids:
                # 按指定的person_id搜索
                for person_id in person_ids:
                    results = vector_service.search_similar(
                        feature_vector=features,
                        top_k=top_k,
                        threshold=confidence,
                        filter_object_id=person_id
                    )
                    all_results.extend(results)
            else:
                # 搜索所有
                all_results = vector_service.search_similar(
                    feature_vector=features,
                    top_k=top_k * 2,  # 获取更多结果以便按person分组
                    threshold=confidence
                )
            search_time = time.time() - search_start
            logger.timing(f"Vector search (found {len(all_results)} results)", search_time)

            # 6. 按person_id合并结果
            process_start = time.time()
            grouped_results = {}
            for result in all_results:
                person_id = result.object_id  # object_id 映射到 person_id
                if person_id not in grouped_results:
                    grouped_results[person_id] = {
                        "person_id": person_id,
                        "faces": [],
                        "max_similarity": 0
                    }

                grouped_results[person_id]["faces"].append({
                    "image_id": result.image_id,
                    "similarity": round(result.similarity, 2),
                    "img_url": result.img_url,
                    "img_face_url": result.img_object_url,  # object_url 映射到 face_url
                    "face_bbox": result.custom_data.get("face_bbox") if result.custom_data else None,
                    "face_score": result.custom_data.get("face_score") if result.custom_data else None,
                    "custom_data": result.custom_data
                })

                # 更新最大相似度
                if result.similarity > grouped_results[person_id]["max_similarity"]:
                    grouped_results[person_id]["max_similarity"] = round(result.similarity, 2)

            # 7. 排序并限制top_k
            sorted_groups = sorted(
                grouped_results.values(),
                key=lambda x: x["max_similarity"],
                reverse=True
            )[:top_k]

            process_time = time.time() - process_start
            logger.timing("Result processing", process_time)

            # 总耗时
            total_time = time.time() - total_start
            logger.timing("TOTAL MATCH TIME", total_time)

            # 8. 构建返回结果
            result = {
                "query_id": temp_id,
                "temp_path": temp_path,
                "query_face": {
                    "bbox": [round(v, 2) for v in face_bbox] if face_bbox else None,
                    "score": round(face_score, 2) if face_score else None
                },
                "total_matches": len(all_results),
                "grouped_matches": sorted_groups,
                "confidence_threshold": confidence,
                "top_k": top_k,
                "processing_time": {
                    "load": round(load_time, 2),
                    "face_detection": round(face_detect_time, 2),
                    "feature_extraction": round(feature_time, 2),
                    "vector_search": round(search_time, 2),
                    "result_processing": round(process_time, 2),
                    "total": round(total_time, 2)
                }
            }

            # 添加活体检测信息（如果有）
            if liveness_result:
                result["liveness"] = {
                    "passed": liveness_result["passed"],
                    "score": round(liveness_result["score"], 4),
                    "label": liveness_result["details"]["label_text"],
                    "threshold": liveness_result["details"]["threshold"]
                }

            return result

        except Exception as e:
            logger.error(f"Error matching face: {e}")
            raise

# 单例实例
face_service = FaceService()
