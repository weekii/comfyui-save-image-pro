"""
图像格式保存策略基类

定义了所有图像格式保存策略的接口。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from PIL import Image


class FormatStrategy(ABC):
    """图像格式保存策略基类"""
    
    @abstractmethod
    def save_image(self, image: Image.Image, path: str, metadata: Optional[Dict[str, Any]] = None, 
                   quality: int = 75, **kwargs) -> None:
        """
        保存图像
        
        Args:
            image: PIL图像对象
            path: 保存路径
            metadata: 元数据字典
            quality: 图像质量 (1-100)
            **kwargs: 其他格式特定参数
        """
        pass
    
    @abstractmethod
    def supports_metadata(self) -> bool:
        """是否支持元数据"""
        pass
    
    @abstractmethod
    def supports_quality(self) -> bool:
        """是否支持质量设置"""
        pass
    
    @abstractmethod
    def supports_lossless(self) -> bool:
        """是否支持无损压缩"""
        pass
    
    @abstractmethod
    def get_file_extension(self) -> str:
        """获取文件扩展名"""
        pass
    
    def get_default_quality(self) -> int:
        """获取默认质量设置"""
        return 75
    
    def validate_quality(self, quality: int) -> int:
        """验证并调整质量参数"""
        if not self.supports_quality():
            return self.get_default_quality()
        
        return max(1, min(100, quality))
    
    def prepare_save_kwargs(self, metadata: Optional[Dict[str, Any]] = None, 
                          quality: int = 75, **kwargs) -> Dict[str, Any]:
        """
        准备保存参数
        
        Args:
            metadata: 元数据
            quality: 质量
            **kwargs: 其他参数
            
        Returns:
            保存参数字典
        """
        save_kwargs = {}
        
        # 处理质量参数
        if self.supports_quality():
            validated_quality = self.validate_quality(quality)
            save_kwargs['quality'] = validated_quality
            
            # 处理无损压缩
            if self.supports_lossless() and validated_quality == 100:
                save_kwargs['lossless'] = True
        
        # 处理元数据
        if self.supports_metadata() and metadata:
            metadata_kwargs = self._prepare_metadata(metadata)
            save_kwargs.update(metadata_kwargs)
        
        # 添加其他参数
        save_kwargs.update(kwargs)
        
        return save_kwargs
    
    def _prepare_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        准备元数据参数（子类可重写）
        
        Args:
            metadata: 原始元数据
            
        Returns:
            格式化的元数据参数
        """
        return {}
    
    def get_format_info(self) -> Dict[str, Any]:
        """获取格式信息"""
        return {
            'extension': self.get_file_extension(),
            'supports_metadata': self.supports_metadata(),
            'supports_quality': self.supports_quality(),
            'supports_lossless': self.supports_lossless(),
            'default_quality': self.get_default_quality()
        }
