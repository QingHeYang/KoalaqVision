"""
SSL Certificate Auto-Discovery Utility

Automatically finds SSL certificate and private key files in a directory.
Supports various naming conventions used by different certificate providers.
"""

from pathlib import Path
from typing import Optional, Tuple
from app.utils.logger_utils import get_logger

logger = get_logger(__name__)


class SSLCertFinder:
    """SSL 证书自动发现工具"""

    # 证书文件可能的命名模式（优先级从高到低）
    CERT_PATTERNS = [
        "fullchain.pem",      # Let's Encrypt 标准
        "cert.pem",           # 通用命名
        "certificate.pem",    # 通用命名
        "server.crt",         # 服务器证书
        "*.crt",              # 任意 .crt 文件
        "*-cert.pem",         # 带 cert 后缀的 pem
        "*.pem",              # 任意 .pem 文件（最后尝试）
    ]

    # 私钥文件可能的命名模式（优先级从高到低）
    KEY_PATTERNS = [
        "privkey.pem",        # Let's Encrypt 标准
        "private.key",        # 通用命名
        "server.key",         # 服务器私钥
        "key.pem",            # 通用命名
        "*.key",              # 任意 .key 文件
        "*-key.pem",          # 带 key 后缀的 pem
    ]

    @staticmethod
    def find_cert_files(cert_dir: str) -> Optional[Tuple[str, str]]:
        """
        自动发现 SSL 证书和私钥文件

        Args:
            cert_dir: 证书目录路径

        Returns:
            (cert_file_path, key_file_path) 元组，如果未找到则返回 None

        Examples:
            >>> finder = SSLCertFinder()
            >>> result = finder.find_cert_files("/app/certs")
            >>> if result:
            >>>     cert_file, key_file = result
            >>>     print(f"Found: {cert_file}, {key_file}")
        """
        cert_path = Path(cert_dir)

        # 检查目录是否存在
        if not cert_path.exists():
            logger.warning(f"SSL cert directory not found: {cert_dir}")
            return None

        if not cert_path.is_dir():
            logger.warning(f"SSL cert path is not a directory: {cert_dir}")
            return None

        # 查找证书文件
        cert_file = SSLCertFinder._find_file(cert_path, SSLCertFinder.CERT_PATTERNS, "certificate")
        if not cert_file:
            logger.warning(f"No SSL certificate file found in: {cert_dir}")
            return None

        # 查找私钥文件
        key_file = SSLCertFinder._find_file(cert_path, SSLCertFinder.KEY_PATTERNS, "private key")
        if not key_file:
            logger.warning(f"No SSL private key file found in: {cert_dir}")
            return None

        logger.info(f"SSL certificate found: {cert_file}")
        logger.info(f"SSL private key found: {key_file}")

        return (str(cert_file), str(key_file))

    @staticmethod
    def _find_file(cert_path: Path, patterns: list, file_type: str) -> Optional[Path]:
        """
        根据模式列表查找文件

        Args:
            cert_path: 证书目录路径
            patterns: 文件名模式列表
            file_type: 文件类型（用于日志）

        Returns:
            文件路径或 None
        """
        for pattern in patterns:
            if "*" in pattern:
                # 通配符查找
                files = list(cert_path.glob(pattern))
                if files:
                    # 如果是 *.pem，需要排除已经匹配的证书文件
                    if pattern == "*.pem" and file_type == "private key":
                        # 过滤掉常见的证书文件名
                        cert_keywords = ["fullchain", "cert", "certificate"]
                        files = [
                            f for f in files
                            if not any(keyword in f.stem.lower() for keyword in cert_keywords)
                        ]
                    if files:
                        logger.debug(f"Found {file_type} with pattern '{pattern}': {files[0].name}")
                        return files[0]
            else:
                # 精确匹配
                file_path = cert_path / pattern
                if file_path.exists() and file_path.is_file():
                    logger.debug(f"Found {file_type} with exact name: {pattern}")
                    return file_path

        return None

    @staticmethod
    def validate_cert_files(cert_file: str, key_file: str) -> bool:
        """
        验证证书文件是否可读

        Args:
            cert_file: 证书文件路径
            key_file: 私钥文件路径

        Returns:
            是否有效
        """
        cert_path = Path(cert_file)
        key_path = Path(key_file)

        if not cert_path.exists():
            logger.error(f"SSL certificate file not found: {cert_file}")
            return False

        if not key_path.exists():
            logger.error(f"SSL private key file not found: {key_file}")
            return False

        if not cert_path.is_file():
            logger.error(f"SSL certificate path is not a file: {cert_file}")
            return False

        if not key_path.is_file():
            logger.error(f"SSL private key path is not a file: {key_file}")
            return False

        # 检查文件是否可读
        try:
            with open(cert_file, 'r') as f:
                f.read(1)
        except Exception as e:
            logger.error(f"Cannot read SSL certificate file: {e}")
            return False

        try:
            with open(key_file, 'r') as f:
                f.read(1)
        except Exception as e:
            logger.error(f"Cannot read SSL private key file: {e}")
            return False

        logger.info("SSL certificate files validated successfully")
        return True
