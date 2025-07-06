"""
TIFF格式保存策略
"""

from typing import Dict, Any, Optional
from PIL import Image
from .format_strategy import FormatStrategy


class TIFFStrategy(FormatStrategy):
    """TIFF格式保存策略"""
    
    def __init__(self, optimize: bool = True):
        self.optimize = optimize
    
    def save_image(self, image: Image.Image, path: str, metadata: Optional[Dict[str, Any]] = None, 
                   quality: int = 91, **kwargs) -> None:
        """保存TIFF格式图像"""
        save_kwargs = self.prepare_save_kwargs(metadata, quality, **kwargs)
        
        # TIFF特有参数
        save_kwargs['optimize'] = self.optimize
        
        image.save(path, format='TIFF', **save_kwargs)
    
    def supports_metadata(self) -> bool:
        """TIFF不支持我们使用的元数据格式"""
        return False
    
    def supports_quality(self) -> bool:
        """TIFF支持质量设置（但效果有限）"""
        return True
    
    def supports_lossless(self) -> bool:
        """TIFF本身是无损格式"""
        return True
    
    def get_file_extension(self) -> str:
        """获取文件扩展名"""
        return '.tiff'
    
    def get_default_quality(self) -> int:
        """TIFF默认质量"""
        return 91
    
    def set_optimize(self, optimize: bool):
        """设置是否优化"""
        self.optimize = optimize
