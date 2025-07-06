"""
BMP格式保存策略
"""

from typing import Dict, Any, Optional
from PIL import Image
from .format_strategy import FormatStrategy


class BMPStrategy(FormatStrategy):
    """BMP格式保存策略"""
    
    def save_image(self, image: Image.Image, path: str, metadata: Optional[Dict[str, Any]] = None, 
                   quality: int = 100, **kwargs) -> None:
        """保存BMP格式图像"""
        save_kwargs = self.prepare_save_kwargs(metadata, quality, **kwargs)
        
        # BMP不支持透明度，需要转换
        if image.mode in ('RGBA', 'LA'):
            # 创建白色背景
            background = Image.new('RGB', image.size, (255, 255, 255))
            background.paste(image, mask=image.split()[-1])
            image = background
        
        image.save(path, format='BMP', **save_kwargs)
    
    def supports_metadata(self) -> bool:
        """BMP不支持我们使用的元数据格式"""
        return False
    
    def supports_quality(self) -> bool:
        """BMP不支持质量设置"""
        return False
    
    def supports_lossless(self) -> bool:
        """BMP是无损格式"""
        return True
    
    def get_file_extension(self) -> str:
        """获取文件扩展名"""
        return '.bmp'
    
    def get_default_quality(self) -> int:
        """BMP不使用质量参数"""
        return 100
