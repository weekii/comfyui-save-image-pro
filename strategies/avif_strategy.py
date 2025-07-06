"""
AVIF格式保存策略
"""

from typing import Dict, Any, Optional
from PIL import Image
from .format_strategy import FormatStrategy
import json


class AVIFStrategy(FormatStrategy):
    """AVIF格式保存策略"""
    
    def save_image(self, image: Image.Image, path: str, metadata: Optional[Dict[str, Any]] = None, 
                   quality: int = 60, **kwargs) -> None:
        """保存AVIF格式图像"""
        save_kwargs = self.prepare_save_kwargs(metadata, quality, **kwargs)
        image.save(path, format='AVIF', **save_kwargs)
    
    def supports_metadata(self) -> bool:
        """AVIF支持EXIF元数据"""
        return True
    
    def supports_quality(self) -> bool:
        """AVIF支持质量设置"""
        return True
    
    def supports_lossless(self) -> bool:
        """AVIF支持无损压缩"""
        return True
    
    def get_file_extension(self) -> str:
        """获取文件扩展名"""
        return '.avif'
    
    def get_default_quality(self) -> int:
        """AVIF默认质量"""
        return 60
    
    def _prepare_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """准备AVIF的EXIF元数据"""
        if not metadata:
            return {}
        
        # AVIF使用EXIF格式存储元数据
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
            print(f"AVIF元数据处理错误: {e}")
            return None
