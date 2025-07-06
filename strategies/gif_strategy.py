"""
GIF格式保存策略
"""

from typing import Dict, Any, Optional
from PIL import Image
from .format_strategy import FormatStrategy


class GIFStrategy(FormatStrategy):
    """GIF格式保存策略"""
    
    def __init__(self, optimize: bool = True):
        self.optimize = optimize
    
    def save_image(self, image: Image.Image, path: str, metadata: Optional[Dict[str, Any]] = None, 
                   quality: int = 75, **kwargs) -> None:
        """保存GIF格式图像"""
        save_kwargs = self.prepare_save_kwargs(metadata, quality, **kwargs)
        
        # GIF特有参数
        save_kwargs['optimize'] = self.optimize
        
        # GIF只支持256色，需要转换
        if image.mode not in ('P', 'L'):
            # 转换为调色板模式
            image = image.convert('P', palette=Image.ADAPTIVE)
        
        image.save(path, format='GIF', **save_kwargs)
    
    def supports_metadata(self) -> bool:
        """GIF不支持我们使用的元数据格式"""
        return False
    
    def supports_quality(self) -> bool:
        """GIF不支持质量设置"""
        return False
    
    def supports_lossless(self) -> bool:
        """GIF是无损格式（但有颜色限制）"""
        return True
    
    def get_file_extension(self) -> str:
        """获取文件扩展名"""
        return '.gif'
    
    def get_default_quality(self) -> int:
        """GIF不使用质量参数"""
        return 100
    
    def set_optimize(self, optimize: bool):
        """设置是否优化"""
        self.optimize = optimize
