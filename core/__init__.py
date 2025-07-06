"""
Save Image Extended - 核心模块

这个包包含了重构后的核心组件，遵循SOLID原则设计。

模块结构:
- config: 配置管理
- filename_generator: 文件名生成器
- counter_manager: 计数器管理
- metadata_handler: 元数据处理
- image_saver: 图像保存协调器
- job_data_exporter: 作业数据导出
- path_manager: 路径管理
"""

from .config import SaveConfig, ConfigManager, ValidationResult
from .filename_generator import FileNameGenerator, ParameterExtractor
from .counter_manager import CounterManager
from .metadata_handler import MetadataHandler
from .image_saver import ImageSaver
from .job_data_exporter import JobDataExporter
from .path_manager import PathManager
from .error_handler import (
    ErrorHandler, ErrorContext, ValidationError,
    ImageProcessingError, FileOperationError,
    get_error_handler, setup_global_error_handler,
    log_info, log_warning, log_error, log_debug,
    handle_exception, error_context
)

__all__ = [
    'SaveConfig',
    'ConfigManager',
    'ValidationResult',
    'FileNameGenerator',
    'ParameterExtractor',
    'CounterManager',
    'MetadataHandler',
    'ImageSaver',
    'JobDataExporter',
    'PathManager',
    'ErrorHandler',
    'ErrorContext',
    'ValidationError',
    'ImageProcessingError',
    'FileOperationError',
    'get_error_handler',
    'setup_global_error_handler',
    'log_info',
    'log_warning',
    'log_error',
    'log_debug',
    'handle_exception',
    'error_context'
]
