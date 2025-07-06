"""
错误处理和日志模块

提供统一的错误处理、日志记录和异常管理功能。
"""

import logging
import traceback
import os
from datetime import datetime
from typing import Optional, Dict, Any
from pathlib import Path


class ErrorHandler:
    """错误处理器"""
    
    def __init__(self, log_level: int = logging.INFO, log_file: Optional[str] = None):
        self.logger = self._setup_logger(log_level, log_file)
        self.error_count = 0
        self.warning_count = 0
    
    def _setup_logger(self, log_level: int, log_file: Optional[str]) -> logging.Logger:
        """设置日志记录器"""
        logger = logging.getLogger('save_image_extended')
        logger.setLevel(log_level)
        
        # 避免重复添加处理器
        if logger.handlers:
            return logger
        
        # 创建格式化器
        formatter = logging.Formatter(
            '[%(asctime)s] [%(name)s] %(levelname)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # 文件处理器（如果指定了日志文件）
        if log_file:
            try:
                # 确保日志目录存在
                log_path = Path(log_file)
                log_path.parent.mkdir(parents=True, exist_ok=True)
                
                file_handler = logging.FileHandler(log_file, encoding='utf-8')
                file_handler.setLevel(log_level)
                file_handler.setFormatter(formatter)
                logger.addHandler(file_handler)
            except Exception as e:
                logger.warning(f"无法创建日志文件 {log_file}: {e}")
        
        return logger
    
    def log_info(self, message: str, **kwargs):
        """记录信息日志"""
        self.logger.info(message, **kwargs)
    
    def log_warning(self, message: str, **kwargs):
        """记录警告日志"""
        self.warning_count += 1
        self.logger.warning(message, **kwargs)
    
    def log_error(self, message: str, exception: Optional[Exception] = None, **kwargs):
        """记录错误日志"""
        self.error_count += 1
        
        if exception:
            self.logger.error(f"{message}: {str(exception)}", **kwargs)
            self.logger.debug(traceback.format_exc())
        else:
            self.logger.error(message, **kwargs)
    
    def log_debug(self, message: str, **kwargs):
        """记录调试日志"""
        self.logger.debug(message, **kwargs)
    
    def handle_exception(self, exception: Exception, context: str = "", 
                        reraise: bool = False) -> bool:
        """
        处理异常
        
        Args:
            exception: 异常对象
            context: 异常上下文描述
            reraise: 是否重新抛出异常
            
        Returns:
            是否成功处理异常
        """
        try:
            error_msg = f"异常发生在 {context}: {str(exception)}" if context else str(exception)
            self.log_error(error_msg, exception)
            
            if reraise:
                raise exception
            
            return True
        
        except Exception as e:
            # 处理异常时发生的异常
            print(f"错误处理器异常: {e}")
            return False
    
    def create_error_context(self, operation: str, **kwargs) -> 'ErrorContext':
        """创建错误上下文管理器"""
        return ErrorContext(self, operation, **kwargs)
    
    def get_stats(self) -> Dict[str, int]:
        """获取错误统计"""
        return {
            'error_count': self.error_count,
            'warning_count': self.warning_count
        }
    
    def reset_stats(self):
        """重置统计计数"""
        self.error_count = 0
        self.warning_count = 0


class ErrorContext:
    """错误上下文管理器"""
    
    def __init__(self, error_handler: ErrorHandler, operation: str, **kwargs):
        self.error_handler = error_handler
        self.operation = operation
        self.context_data = kwargs
        self.start_time = None
    
    def __enter__(self):
        self.start_time = datetime.now()
        self.error_handler.log_debug(f"开始操作: {self.operation}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = datetime.now() - self.start_time
        
        if exc_type is None:
            self.error_handler.log_debug(
                f"操作完成: {self.operation} (耗时: {duration.total_seconds():.3f}s)"
            )
        else:
            self.error_handler.handle_exception(
                exc_val, 
                f"{self.operation} (耗时: {duration.total_seconds():.3f}s)",
                reraise=False
            )
        
        return True  # 抑制异常传播


class ValidationError(Exception):
    """配置验证错误"""
    pass


class ImageProcessingError(Exception):
    """图像处理错误"""
    pass


class FileOperationError(Exception):
    """文件操作错误"""
    pass


# 全局错误处理器实例
_global_error_handler = None


def get_error_handler() -> ErrorHandler:
    """获取全局错误处理器"""
    global _global_error_handler
    if _global_error_handler is None:
        _global_error_handler = ErrorHandler()
    return _global_error_handler


def setup_global_error_handler(log_level: int = logging.INFO, 
                              log_file: Optional[str] = None) -> ErrorHandler:
    """设置全局错误处理器"""
    global _global_error_handler
    _global_error_handler = ErrorHandler(log_level, log_file)
    return _global_error_handler


# 便捷函数
def log_info(message: str, **kwargs):
    """记录信息日志"""
    get_error_handler().log_info(message, **kwargs)


def log_warning(message: str, **kwargs):
    """记录警告日志"""
    get_error_handler().log_warning(message, **kwargs)


def log_error(message: str, exception: Optional[Exception] = None, **kwargs):
    """记录错误日志"""
    get_error_handler().log_error(message, exception, **kwargs)


def log_debug(message: str, **kwargs):
    """记录调试日志"""
    get_error_handler().log_debug(message, **kwargs)


def handle_exception(exception: Exception, context: str = "", reraise: bool = False) -> bool:
    """处理异常"""
    return get_error_handler().handle_exception(exception, context, reraise)


def error_context(operation: str, **kwargs) -> ErrorContext:
    """创建错误上下文管理器"""
    return get_error_handler().create_error_context(operation, **kwargs)
