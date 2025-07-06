"""
JPEG格式保存策略
"""

from typing import Dict, Any, Optional
from PIL import Image
from .format_strategy import FormatStrategy
import json


class JPEGStrategy(FormatStrategy):
    """JPEG格式保存策略"""
    
    def __init__(self, optimize: bool = True):
        self.optimize = optimize
    
    def save_image(self, image: Image.Image, path: str, metadata: Optional[Dict[str, Any]] = None, 
                   quality: int = 91, **kwargs) -> None:
        """保存JPEG格式图像"""
        save_kwargs = self.prepare_save_kwargs(metadata, quality, **kwargs)
        
        # JPEG特有参数
        save_kwargs['optimize'] = self.optimize
        
        # JPEG不支持透明度，需要转换
        if image.mode in ('RGBA', 'LA', 'P'):
            # 创建白色背景
            background = Image.new('RGB', image.size, (255, 255, 255))
            if image.mode == 'P':
                image = image.convert('RGBA')
            background.paste(image, mask=image.split()[-1] if image.mode in ('RGBA', 'LA') else None)
            image = background
        
        image.save(path, format='JPEG', **save_kwargs)
    
    def supports_metadata(self) -> bool:
        """JPEG支持EXIF元数据"""
        return True
    
    def supports_quality(self) -> bool:
        """JPEG支持质量设置"""
        return True
    
    def supports_lossless(self) -> bool:
        """JPEG不支持无损压缩"""
        return False
    
    def get_file_extension(self) -> str:
        """获取文件扩展名"""
        return '.jpg'
    
    def get_default_quality(self) -> int:
        """JPEG默认质量"""
        return 91
    
    def _prepare_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """准备JPEG的EXIF元数据"""
        if not metadata:
            return {}
        
        # JPEG使用EXIF格式存储元数据
        exif_data = self._create_exif_data(metadata)
        return {'exif': exif_data} if exif_data else {}
    
    def _create_exif_data(self, metadata: Dict[str, Any]) -> Optional[bytes]:
        """创建EXIF数据"""
        try:
            # 创建一个临时图像来生成EXIF数据
            temp_img = Image.new('RGB', (1, 1))
            exif = temp_img.getexif()
            
            # 将元数据编码到EXIF中
            if 'prompt' in metadata:
                # 0x010f: Make字段存储prompt
                exif[0x010f] = "Prompt: " + json.dumps(metadata['prompt'])
            
            if 'workflow' in metadata:
                # 0x010e: ImageDescription字段存储workflow
                exif[0x010e] = "Workflow: " + json.dumps(metadata['workflow'])
            
            return exif.tobytes()
        
        except Exception as e:
            print(f"JPEG元数据处理错误: {e}")
            return None
    
    def set_optimize(self, optimize: bool):
        """设置是否优化"""
        self.optimize = optimize
