from typing import List, Optional, Dict, Any, Union, Tuple
from PIL import Image
import uuid
import time

from app.services.model_service import model_service
from app.services.vector_service import vector_service
from app.models.object_data import ObjectData, ImageSearchResponse, ImageUploadRequest
from app.utils.image_utils import image_utils
from app.utils.logger_utils import get_logger

logger = get_logger(__name__)

class ObjectService:
    """物品识别服务 - 按细化需求实现"""
    
    def add_image(self,
                 image_source: Union[Image.Image, str],
                 object_id: str,
                 save_files: bool = True,
                 custom_data: Optional[Dict[str, Any]] = None) -> ObjectData:
        """
        添加图片入库 - 完整流程
        
        Args:
            image_source: PIL图片对象或图片URL
            object_id: 物品ID
            save_files: 是否保存文件（原图和抠图）
            custom_data: 自定义数据
            
        Returns:
            图片数据对象
        """
        try:
            # 生成image_id
            image_id = str(uuid.uuid4())
            logger.info(f"Processing image with ID: {image_id}")
            
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
            
            # 2. 保存原图（可选）
            img_url = None
            img_object_url = None
            
            if save_files:
                # 保存原图到 data/upload/object_id/image_id/
                save_original_start = time.time()
                original_path, object_path_placeholder = image_utils.save_upload_image(
                    image=image,
                    object_id=object_id,
                    image_id=image_id,
                    save_processed=True
                )
                save_original_time = time.time() - save_original_start
                logger.timing("Save original image", save_original_time)
                
                if original_path:
                    img_url = image_utils.get_image_url(original_path)
                    logger.info(f"Original image saved: {img_url}")
                
                # 3. 抠图剪裁（可选）
                if object_path_placeholder:
                    logger.info("Removing background...")
                    bg_removal_start = time.time()
                    processed_image = model_service.remove_background(image)
                    bg_removal_time = time.time() - bg_removal_start
                    logger.timing("Background removal", bg_removal_time)
                    
                    if processed_image:
                        # 保存抠图后的图片
                        save_processed_start = time.time()
                        object_path = image_utils.save_processed_image(
                            processed_image, 
                            object_path_placeholder
                        )
                        img_object_url = image_utils.get_image_url(object_path)
                        save_processed_time = time.time() - save_processed_start
                        logger.timing("Save processed image", save_processed_time)
                        logger.info(f"Processed image saved: {img_object_url}")
            
            # 4. 提取特征值
            logger.info("Extracting features...")
            feature_start = time.time()
            features = model_service.extract_features(image, normalize=True)
            if features is None:
                raise ValueError("Failed to extract features")
            feature_time = time.time() - feature_start
            logger.timing("Feature extraction", feature_time)
            
            # 5. 创建数据对象
            image_data = ObjectData(
                image_id=image_id,
                object_id=object_id,
                img_url=img_url,
                img_object_url=img_object_url,
                feature_vector=features,
                custom_data=custom_data or {}
            )
            
            # 6. 入库
            db_start = time.time()
            vector_service.add_image(image_data)
            db_time = time.time() - db_start
            logger.timing("Database insert", db_time)
            logger.info(f"Image added to database: {image_id}")
            
            # 总耗时
            total_time = time.time() - total_start
            logger.timing("TOTAL TIME", total_time)
            
            return image_data
            
        except Exception as e:
            logger.error(f"Error adding image: {e}")
            raise
    def match_image(self,
                   image_source: Union[Image.Image, str],
                   save_temp: bool = False,
                   object_ids: Optional[List[str]] = None,
                   confidence: float = 0.7,
                   top_k: int = 10) -> Dict[str, Any]:
        """
        匹配图片 - 按需求实现
        
        Args:
            image_source: PIL图片对象或URL
            save_temp: 是否保存到temp（只保存对象图）
            object_ids: 限定的object_id范围（可选）
            confidence: 置信度阈值
            top_k: 返回结果数量
            
        Returns:
            按object_id合并的匹配结果
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
            
            # 2. 抠图剪裁
            logger.info("Removing background for query image...")
            bg_removal_start = time.time()
            processed_image = model_service.remove_background(image)
            bg_removal_time = time.time() - bg_removal_start
            logger.timing("Background removal", bg_removal_time)
            
            # 3. 保存临时文件（可选）
            temp_path = None
            if save_temp and processed_image:
                save_temp_start = time.time()
                temp_path = image_utils.save_temp_image(
                    processed_image,
                    temp_id,
                    only_object=True
                )
                save_temp_time = time.time() - save_temp_start
                logger.timing("Save temp image", save_temp_time)
                logger.info(f"Temp image saved: {temp_path}")
            
            # 4. 提取特征值
            logger.info("Extracting query features...")
            feature_start = time.time()
            # 使用处理后的图片提取特征
            query_image = processed_image if processed_image else image
            features = model_service.extract_features(query_image, normalize=True)
            feature_time = time.time() - feature_start
            logger.timing("Feature extraction", feature_time)
            
            if features is None:
                raise ValueError("Failed to extract features")
            
            # 5. 搜索相似图片
            search_start = time.time()
            # 如果指定了object_ids，需要逐个搜索并合并
            all_results = []
            
            if object_ids:
                # 按指定的object_id搜索
                for obj_id in object_ids:
                    results = vector_service.search_similar(
                        feature_vector=features,
                        top_k=top_k,
                        threshold=confidence,
                        filter_object_id=obj_id
                    )
                    all_results.extend(results)
            else:
                # 搜索所有
                all_results = vector_service.search_similar(
                    feature_vector=features,
                    top_k=top_k * 2,  # 获取更多结果以便按object分组
                    threshold=confidence
                )
            search_time = time.time() - search_start
            logger.timing(f"Vector search (found {len(all_results)} results)", search_time)
            
            # 6. 按object_id合并结果
            process_start = time.time()
            grouped_results = {}
            for result in all_results:
                obj_id = result.object_id
                if obj_id not in grouped_results:
                    grouped_results[obj_id] = {
                        "object_id": obj_id,
                        "images": [],
                        "max_similarity": 0
                    }
                
                grouped_results[obj_id]["images"].append({
                    "image_id": result.image_id,
                    "similarity": round(result.similarity, 2),
                    "img_url": result.img_url,
                    "img_object_url": result.img_object_url,
                    "custom_data": result.custom_data
                })

                # 更新最大相似度
                if result.similarity > grouped_results[obj_id]["max_similarity"]:
                    grouped_results[obj_id]["max_similarity"] = round(result.similarity, 2)
            
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
            return {
                "query_id": temp_id,
                "temp_path": temp_path,
                "total_matches": len(all_results),
                "grouped_matches": sorted_groups,
                "confidence_threshold": confidence,
                "top_k": top_k,
                "processing_time": {
                    "load": round(load_time, 2),
                    "background_removal": round(bg_removal_time, 2),
                    "feature_extraction": round(feature_time, 2),
                    "vector_search": round(search_time, 2),
                    "result_processing": round(process_time, 2),
                    "total": round(total_time, 2)
                }
            }
            
        except Exception as e:
            logger.error(f"Error matching image: {e}")
            raise

# 单例实例
object_service = ObjectService()