"""
美化的日志工具
支持两种样式切换：
1. BLOCK - 块状风格（默认）
2. TREE - 层级树状风格
"""

import logging
import sys
import time
from datetime import datetime
from typing import Optional, Any
from enum import Enum
from pathlib import Path
import os

# 尝试从 .env 文件读取配置
def load_env_file():
    """加载 .env 文件中的配置"""
    env_file = Path('.env')
    if env_file.exists():
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    # 只设置 LOG_STYLE，避免覆盖其他环境变量
                    if key == 'LOG_STYLE' and key not in os.environ:
                        os.environ[key] = value

# 在模块加载时立即读取 .env 文件
load_env_file()

# ANSI颜色代码
class Colors:
    # 前景色
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'

    # 亮色版本
    BRIGHT_BLACK = '\033[90m'
    BRIGHT_RED = '\033[91m'
    BRIGHT_GREEN = '\033[92m'
    BRIGHT_YELLOW = '\033[93m'
    BRIGHT_BLUE = '\033[94m'
    BRIGHT_MAGENTA = '\033[95m'
    BRIGHT_CYAN = '\033[96m'
    BRIGHT_WHITE = '\033[97m'

    # 背景色
    BG_RED = '\033[41m'
    BG_GREEN = '\033[42m'
    BG_YELLOW = '\033[43m'
    BG_BLUE = '\033[44m'
    BG_MAGENTA = '\033[45m'
    BG_CYAN = '\033[46m'

    # 样式
    BOLD = '\033[1m'
    DIM = '\033[2m'
    UNDERLINE = '\033[4m'

    # 重置
    RESET = '\033[0m'


class LogStyle(Enum):
    """日志样式枚举"""
    BLOCK = "block"  # 块状风格
    TREE = "tree"    # 树状风格


class LogLevel(Enum):
    """日志级别"""
    DEBUG = ("DEBUG", Colors.BRIGHT_BLUE, "🔍")
    INFO = ("INFO ", Colors.GREEN, "✓")
    WARNING = ("WARN ", Colors.YELLOW, "⚠")
    ERROR = ("ERROR", Colors.RED, "✗")
    SUCCESS = ("SUCCESS", Colors.BRIGHT_GREEN, "✅")
    TIMING = ("TIME ", Colors.CYAN, "⏱")


class BeautifulLogger:
    """美化的日志记录器"""

    def __init__(self, name: str, style: Optional[LogStyle] = None):
        self.name = name
        self.indent_level = 0
        self.start_times = {}

        # 优先使用传入的样式，如果没有则从环境变量读取
        if style is not None:
            self.style = style
        else:
            # 从环境变量读取样式配置
            env_style = os.getenv("LOG_STYLE", "block").lower()
            if env_style == "tree":
                self.style = LogStyle.TREE
            else:
                self.style = LogStyle.BLOCK

        # 是否启用颜色（检测是否在终端中）
        self.use_color = sys.stdout.isatty()

        # 获取模块简称
        self.module_name = self._get_short_module_name(name)

    def _get_short_module_name(self, full_name: str) -> str:
        """获取简短的模块名"""
        parts = full_name.split('.')
        if len(parts) > 2:
            # app.services.xxx -> services.xxx
            return '.'.join(parts[-2:])
        return full_name

    def _colorize(self, text: str, color: str) -> str:
        """添加颜色"""
        if self.use_color:
            return f"{color}{text}{Colors.RESET}"
        return text

    def _format_block_style(self, level: LogLevel, message: str, duration: Optional[float] = None) -> str:
        """块状风格格式化"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        level_text = f"[{level.value[0]}]"

        # 颜色处理
        if self.use_color:
            level_text = self._colorize(level_text, level.value[1])
            module_text = self._colorize(f"{self.module_name:18}", Colors.BRIGHT_BLACK)
        else:
            module_text = f"{self.module_name:18}"

        # 添加时间信息
        if duration is not None:
            message = f"{message} ({duration:.2f}s)"

        return f"{timestamp} {level_text} ▸ {module_text} : {message}"

    def _format_tree_style(self, level: LogLevel, message: str, duration: Optional[float] = None) -> str:
        """树状风格格式化"""
        timestamp = datetime.now().strftime("%H:%M:%S")

        # 缩进符号
        if self.indent_level == 0:
            prefix = "→"
        elif self.indent_level == 1:
            prefix = "├─"
        elif self.indent_level == 2:
            prefix = "│  ├─"
        else:
            prefix = "│  " * (self.indent_level - 1) + "└─"

        # 等级标签
        level_tag = level.value[0].strip()

        # 颜色处理
        if self.use_color:
            timestamp = self._colorize(f"[{timestamp}]", Colors.BRIGHT_BLACK)
            level_tag = self._colorize(level_tag.ljust(7), level.value[1])
            prefix = self._colorize(prefix, Colors.DIM)
        else:
            timestamp = f"[{timestamp}]"
            level_tag = level_tag.ljust(7)

        # 添加时间信息
        if duration is not None:
            message = f"{message} ({duration:.2f}s)"

        # 特殊处理SUCCESS级别，添加符号
        if level == LogLevel.SUCCESS:
            message = f"{message} ✓"

        return f"{timestamp} {level_tag} {prefix} {message}"

    def _log(self, level: LogLevel, message: str, duration: Optional[float] = None):
        """内部日志方法"""
        if self.style == LogStyle.BLOCK:
            output = self._format_block_style(level, message, duration)
        else:
            output = self._format_tree_style(level, message, duration)

        # 输出到标准输出或标准错误
        if level in [LogLevel.ERROR, LogLevel.WARNING]:
            print(output, file=sys.stderr)
        else:
            print(output)

    def debug(self, message: str):
        """调试日志"""
        self._log(LogLevel.DEBUG, message)

    def info(self, message: str):
        """信息日志"""
        self._log(LogLevel.INFO, message)

    def warning(self, message: str):
        """警告日志"""
        self._log(LogLevel.WARNING, message)

    def error(self, message: str, exc_info: bool = False):
        """错误日志"""
        self._log(LogLevel.ERROR, message)
        if exc_info:
            import traceback
            tb = traceback.format_exc()
            for line in tb.split('\n'):
                if line.strip():
                    print(self._colorize(f"    {line}", Colors.DIM), file=sys.stderr)

    def success(self, message: str):
        """成功日志"""
        self._log(LogLevel.SUCCESS, message)

    def timing(self, message: str, duration: float):
        """计时日志"""
        self._log(LogLevel.TIMING, message, duration)

    def start_timer(self, key: str):
        """开始计时"""
        self.start_times[key] = time.time()

    def end_timer(self, key: str, message: str):
        """结束计时并输出"""
        if key in self.start_times:
            duration = time.time() - self.start_times[key]
            self.timing(message, duration)
            del self.start_times[key]

    def indent(self):
        """增加缩进级别（用于树状风格）"""
        self.indent_level += 1
        return self

    def dedent(self):
        """减少缩进级别（用于树状风格）"""
        if self.indent_level > 0:
            self.indent_level -= 1
        return self

    def set_style(self, style: LogStyle):
        """动态切换样式"""
        self.style = style

    def section(self, title: str):
        """输出分节标题（用于重要流程）"""
        if self.style == LogStyle.TREE:
            # 树状风格的分节
            separator = "═" * 60
            if self.use_color:
                print(self._colorize(separator, Colors.BRIGHT_BLACK))
                print(self._colorize(f"▶ {title}", Colors.BOLD + Colors.BRIGHT_WHITE))
            else:
                print(separator)
                print(f"▶ {title}")
        else:
            # 块状风格的分节
            if self.use_color:
                print(self._colorize(f"\n{'─' * 60}", Colors.DIM))
                print(self._colorize(f"■ {title}", Colors.BOLD))
                print(self._colorize(f"{'─' * 60}", Colors.DIM))
            else:
                print(f"\n{'─' * 60}")
                print(f"■ {title}")
                print(f"{'─' * 60}")


# 全局日志工厂
class LoggerFactory:
    """日志工厂，用于创建和管理logger实例"""

    _loggers = {}
    _default_style = LogStyle.BLOCK

    @classmethod
    def get_logger(cls, name: str) -> BeautifulLogger:
        """获取logger实例（单例）"""
        if name not in cls._loggers:
            # 总是让 logger 自己从环境变量读取样式
            cls._loggers[name] = BeautifulLogger(name, None)
        return cls._loggers[name]

    @classmethod
    def set_global_style(cls, style: LogStyle):
        """设置全局默认样式"""
        cls._default_style = style
        # 更新所有现有logger的样式
        for logger in cls._loggers.values():
            logger.set_style(style)

    @classmethod
    def set_style_from_env(cls):
        """从环境变量设置样式"""
        style = os.getenv("LOG_STYLE", "block").lower()
        if style == "tree":
            cls.set_global_style(LogStyle.TREE)
        else:
            cls.set_global_style(LogStyle.BLOCK)


# 便捷函数
def get_logger(name: str) -> BeautifulLogger:
    """获取logger实例"""
    return LoggerFactory.get_logger(name)


# 初始化：从环境变量读取配置
LoggerFactory.set_style_from_env()


# 兼容原有logging模块的适配器
class LoggingAdapter(logging.LoggerAdapter):
    """适配器，将标准logging调用转换为美化输出"""

    def __init__(self, name: str):
        self.beautiful_logger = get_logger(name)
        super().__init__(logging.getLogger(name), {})

    def debug(self, msg, *args, **kwargs):
        self.beautiful_logger.debug(str(msg))

    def info(self, msg, *args, **kwargs):
        self.beautiful_logger.info(str(msg))

    def warning(self, msg, *args, **kwargs):
        self.beautiful_logger.warning(str(msg))

    def error(self, msg, *args, **kwargs):
        exc_info = kwargs.get('exc_info', False)
        self.beautiful_logger.error(str(msg), exc_info=exc_info)


# 为了兼容性，提供getLogger函数
def getLogger(name: str) -> LoggingAdapter:
    """兼容标准logging.getLogger"""
    return LoggingAdapter(name)


# 使用示例
if __name__ == "__main__":
    # 测试块状风格
    print("\n=== BLOCK STYLE ===")
    LoggerFactory.set_global_style(LogStyle.BLOCK)
    logger = get_logger("app.main")

    logger.info("Starting KoalaqVision API...")
    logger.debug("Debug mode enabled")
    logger.warning("GPU not available, using CPU")
    logger.success("Server started successfully")
    logger.error("Failed to connect to database")

    logger.start_timer("startup")
    time.sleep(0.5)
    logger.end_timer("startup", "Total startup time")

    # 测试树状风格
    print("\n=== TREE STYLE ===")
    LoggerFactory.set_global_style(LogStyle.TREE)

    logger.section("Application Startup")
    logger.info("Starting KoalaqVision API...")
    logger.indent()
    logger.info("App Mode: object")
    logger.info("Loading models...")
    logger.indent()
    logger.info("DINOv3 model: vits16 (384D)")
    logger.info("Background removal: u2netp")
    logger.dedent()
    logger.success("Models loaded successfully")
    logger.dedent()
    logger.timing("Total startup time", 3.45)