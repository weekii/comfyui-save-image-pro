"""
PNG格式保存策略
"""

from typing import Dict, Any, Optional
from PIL import Image
from PIL.PngImagePlugin import PngInfo
from .format_strategy import FormatStrategy
import json


class PNGStrategy(FormatStrategy):
    """PNG格式保存策略"""
    
    def __init__(self, compress_level: int = 9, optimize: bool = True):
        self.compress_level = compress_level
        self.optimize = optimize
    
    def save_image(self, image: Image.Image, path: str, metadata: Optional[Dict[str, Any]] = None, 
                   quality: int = 75, **kwargs) -> None:
        """保存PNG格式图像"""
        save_kwargs = self.prepare_save_kwargs(metadata, quality, **kwargs)
        
        # PNG特有参数
        save_kwargs['compress_level'] = self.compress_level
        save_kwargs['optimize'] = self.optimize
        
        image.save(path, format='PNG', **save_kwargs)
    
    def supports_metadata(self) -> bool:
        """PNG支持PngInfo元数据"""
        return True
    
    def supports_quality(self) -> bool:
        """PNG不支持质量设置（无损格式）"""
        return False
    
    def supports_lossless(self) -> bool:
        """PNG本身就是无损格式"""
        return True
    
    def get_file_extension(self) -> str:
        """获取文件扩展名"""
        return '.png'
    
    def get_default_quality(self) -> int:
        """PNG不使用质量参数"""
        return 100
    
    def _prepare_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """准备PNG的PngInfo元数据"""
        if not metadata:
            return {}
        
        pnginfo = PngInfo()
        
        # 添加prompt信息
        if 'prompt' in metadata:
            pnginfo.add_text('prompt', json.dumps(metadata['prompt']))
        
        # 添加workflow信息
        if 'workflow' in metadata:
            pnginfo.add_text('workflow', json.dumps(metadata['workflow']))
        
        # 添加其他额外信息
        for key, value in metadata.items():
            if key not in ['prompt', 'workflow']:
                try:
                    pnginfo.add_text(key, json.dumps(value))
                except (TypeError, ValueError):
                    # 如果无法序列化，转换为字符串
                    pnginfo.add_text(key, str(value))
        
        return {'pnginfo': pnginfo}
    
    def set_compress_level(self, level: int):
        """设置压缩级别 (0-9)"""
        self.compress_level = max(0, min(9, level))
    
    def set_optimize(self, optimize: bool):
        """设置是否优化"""
        self.optimize = optimize
