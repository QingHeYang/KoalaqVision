import os
import uuid
import requests
from PIL import Image
from io import BytesIO
from pathlib import Path
from typing import Optional, Tuple
from app.config.settings import settings
from app.utils.logger_utils import get_logger

logger = get_logger(__name__)

class ImageUtils:
    """图片工具类 - 按需求细化"""
    
    def __init__(self):
        """初始化图片工具"""
        # 使用配置中的路径
        self.upload_path = Path(settings.upload_path)
        self.temp_path = Path(settings.temp_path)
        
        # 创建目录
        self.upload_path.mkdir(parents=True, exist_ok=True)
        self.temp_path.mkdir(parents=True, exist_ok=True)
    
    def save_upload_image(self, 
                         image: Image.Image, 
                         object_id: str,
                         image_id: str,
                         save_processed: bool = True) -> Tuple[Optional[str], Optional[str]]:
        """
        按需求保存上传图片
        
        Args:
            image: 原始PIL图片对象
            object_id: 物品ID
            image_id: 图片ID
            save_processed: 是否保存处理后的图片
            
        Returns:
            (原图路径, 抠图后路径) - 如果不保存则为None
        """
        try:
            # 创建object_id文件夹
            object_dir = self.upload_path / object_id
            object_dir.mkdir(exist_ok=True)
            
            # 创建图片同名子文件夹
            image_dir = object_dir / image_id
            image_dir.mkdir(exist_ok=True)
            
            # 1. 压缩并保存原图
            compressed = self.compress_image(image)

            # 处理RGBA图片（如PNG）
            if compressed.mode == 'RGBA':
                # 创建白色背景
                background = Image.new('RGB', compressed.size, (255, 255, 255))
                background.paste(compressed, mask=compressed.split()[3])  # 使用alpha通道作为mask
                compressed = background

            original_filename = f"{image_id}.jpg"
            original_path = image_dir / original_filename
            compressed.save(original_path, 'JPEG', quality=90)
            logger.info(f"Saved original image: {original_path}")
            
            # 2. 保存抠图后的图片（如果需要）
            object_path = None
            if save_processed:
                # 这里先返回路径占位，实际抠图由model_service处理
                object_filename = f"{image_id}_object.png"
                object_path = image_dir / object_filename
            
            return str(original_path), str(object_path) if object_path else None
            
        except Exception as e:
            logger.error(f"Error saving upload image: {e}")
            raise
    
    def save_processed_image(self, 
                            image: Image.Image,
                            filepath: str) -> str:
        """
        保存处理后的图片（抠图后）
        
        Args:
            image: 处理后的图片（RGBA）
            filepath: 保存路径
            
        Returns:
            保存的文件路径
        """
        try:
            save_path = Path(filepath)
            save_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 保存为PNG保留透明通道
            image.save(save_path, 'PNG')
            logger.info(f"Saved processed image: {save_path}")
            
            return str(save_path)
            
        except Exception as e:
            logger.error(f"Error saving processed image: {e}")
            raise
    
    def save_temp_image(self,
                       image: Image.Image,
                       image_id: str,
                       only_object: bool = True,
                       is_match: bool = True) -> Optional[str]:
        """
        保存临时图片（用于match）

        Args:
            image: 图片对象
            image_id: 图片ID
            only_object: 是否只保存对象图（抠图后）
            is_match: 是否是match功能的临时图片

        Returns:
            保存的文件路径
        """
        try:
            if only_object:
                # 只保存对象图
                filename = f"{image_id}_object.png"
            else:
                filename = f"{image_id}.jpg"

            # match功能的图片保存到temp/match目录
            if is_match:
                match_path = self.temp_path / "match"
                match_path.mkdir(parents=True, exist_ok=True)
                save_path = match_path / filename
            else:
                save_path = self.temp_path / filename
            
            if image.mode == 'RGBA':
                image.save(save_path, 'PNG')
            else:
                # 压缩
                compressed = self.compress_image(image)
                compressed.save(save_path, 'JPEG', quality=90)
            
            logger.info(f"Saved temp image: {save_path}")
            return str(save_path)
            
        except Exception as e:
            logger.error(f"Error saving temp image: {e}")
            return None
    
    def compress_image(self, 
                      image: Image.Image, 
                      max_size: int = 1024) -> Image.Image:
        """
        压缩图片到指定分辨率内（保持宽高比）
        
        Args:
            image: PIL图片对象
            max_size: 最大边长（默认1024，即1k分辨率）
            
        Returns:
            压缩后的图片
        """
        try:
            # 计算缩放比例
            width, height = image.size
            if width > max_size or height > max_size:
                if width > height:
                    new_width = max_size
                    new_height = int(height * (max_size / width))
                else:
                    new_height = max_size
                    new_width = int(width * (max_size / height))
                
                # 使用高质量缩放
                image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
                logger.debug(f"Resized image from {width}x{height} to {new_width}x{new_height}")
            
            # 如果是RGBA，保持原样（用于抠图后的图片）
            # 如果是RGB，可以进一步优化
            if image.mode not in ['RGBA', 'RGB']:
                image = image.convert('RGB')
            
            return image
            
        except Exception as e:
            logger.error(f"Error compressing image: {e}")
            raise
    
    def validate_image(self, image: Image.Image) -> bool:
        """
        验证图片有效性

        Args:
            image: PIL图片对象

        Returns:
            图片是否有效
        """
        try:
            # 检查图片是否为None
            if image is None:
                logger.error("Image is None")
                return False

            # 检查图片尺寸
            if image.size[0] == 0 or image.size[1] == 0:
                logger.error("Image has zero dimension")
                return False

            # 验证图片完整性
            image.verify()
            logger.debug(f"Image validated: {image.size}, mode={image.mode}")
            return True

        except Exception as e:
            logger.error(f"Image validation failed: {e}")
            return False

    def download_and_compress(self, url: str, timeout: int = 30) -> Image.Image:
        """
        下载并压缩图片

        Args:
            url: 图片URL
            timeout: 超时时间（秒）

        Returns:
            压缩后的PIL图片对象
        """
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }

            response = requests.get(url, headers=headers, timeout=timeout)
            response.raise_for_status()

            # 从内容创建图片
            image = Image.open(BytesIO(response.content))

            # 验证图片完整性
            if not self.validate_image(image):
                raise ValueError("Downloaded image is invalid or corrupted")

            # verify() 后需要重新打开
            image = Image.open(BytesIO(response.content))

            # 压缩
            compressed = self.compress_image(image)

            logger.info(f"Downloaded and compressed image from: {url}")
            return compressed

        except requests.exceptions.RequestException as e:
            logger.error(f"Error downloading image from {url}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error processing downloaded image: {e}")
            raise
    
    def get_image_url(self, filepath: str) -> str:
        """
        生成图片访问URL (相对路径)

        Args:
            filepath: 本地文件路径

        Returns:
            可访问的图片URL (相对路径，浏览器自动使用当前host)
        """
        # 从data开始的相对路径
        try:
            path = Path(filepath)
            if path.is_relative_to(self.upload_path):
                rel_path = path.relative_to(self.upload_path.parent)
            elif path.is_relative_to(self.temp_path):
                rel_path = path.relative_to(self.temp_path.parent)
            else:
                rel_path = path

            # 返回相对路径 /images/...
            return f"/images/{rel_path}"
        except:
            return f"/images/{filepath}"
    
    def clean_temp_files(self, hours: int = 24):
        """
        清理临时文件

        Args:
            hours: 保留最近N小时的文件
        """
        import time
        current_time = time.time()

        for file_path in self.temp_path.iterdir():
            if file_path.is_file():
                file_age = current_time - file_path.stat().st_mtime
                if file_age > hours * 3600:  # 转换为秒
                    file_path.unlink()
                    logger.debug(f"Deleted temp file: {file_path}")

    def delete_image_files(self, img_url: Optional[str], img_face_url: Optional[str]) -> int:
        """
        删除图片物理文件

        Args:
            img_url: 原图URL
            img_face_url: 人脸图URL

        Returns:
            删除的文件数量
        """
        deleted_count = 0

        # 删除原图
        if img_url:
            try:
                # 从 URL 转换为文件路径
                # img_url 格式: /images/data/upload/person_id/image_id/image_id.jpg
                file_path = img_url.replace('/images/', '')
                full_path = Path(file_path)

                if full_path.exists():
                    full_path.unlink()
                    logger.debug(f"Deleted: {full_path}")
                    deleted_count += 1
            except Exception as e:
                logger.warning(f"Failed to delete {img_url}: {e}")

        # 删除人脸图
        if img_face_url:
            try:
                file_path = img_face_url.replace('/images/', '')
                full_path = Path(file_path)

                if full_path.exists():
                    full_path.unlink()
                    logger.debug(f"Deleted: {full_path}")
                    deleted_count += 1
            except Exception as e:
                logger.warning(f"Failed to delete {img_face_url}: {e}")

        return deleted_count

# 单例实例
image_utils = ImageUtils()