"""
图像保存协调器

协调各个组件完成图像保存任务。
"""

import os
from typing import Dict, List, Any, Optional, Tuple
from PIL import Image
from datetime import datetime

from .config import SaveConfig
from .filename_generator import FileNameGenerator
from .counter_manager import CounterManager
from .metadata_handler import MetadataHandler
from .path_manager import PathManager
from ..strategies import (
    FormatStrategy, PNGStrategy, WebPStrategy, AVIFStrategy, 
    JPEGStrategy, JXLStrategy, TIFFStrategy, GIFStrategy, BMPStrategy
)


class ImageSaver:
    """图像保存协调器"""
    
    def __init__(self, config: SaveConfig, output_dir: str):
        self.config = config
        self.output_dir = output_dir
        
        # 初始化组件
        self.filename_generator = FileNameGenerator(config)
        self.counter_manager = CounterManager()
        self.metadata_handler = MetadataHandler()
        self.path_manager = PathManager(output_dir)
        
        # 初始化格式策略
        self.format_strategies = self._init_format_strategies()
    
    def _init_format_strategies(self) -> Dict[str, FormatStrategy]:
        """初始化格式策略"""
        strategies = {
            '.png': PNGStrategy(),
            '.webp': WebPStrategy(),
            '.jpg': JPEGStrategy(),
            '.jpeg': JPEGStrategy(),
            '.gif': GIFStrategy(),
            '.tiff': TIFFStrategy(),
            '.bmp': BMPStrategy()
        }
        
        # 条件性添加AVIF和JXL支持
        try:
            import pillow_avif
            strategies['.avif'] = AVIFStrategy()
        except ImportError:
            pass
        
        try:
            from jxlpy import JXLImagePlugin
            strategies['.jxl'] = JXLStrategy()
        except ImportError:
            pass
        
        return strategies
    
    def save_images(self, images: List[Any], prompt: Dict, extra_pnginfo: Optional[Dict] = None,
                   positive_text: Optional[str] = None, negative_text: Optional[str] = None) -> List[Dict]:
        """
        保存图像列表
        
        Args:
            images: 图像张量列表
            prompt: ComfyUI提示字典
            extra_pnginfo: 额外的PNG信息
            positive_text: 正面提示文本
            negative_text: 负面提示文本
            
        Returns:
            保存结果列表
        """
        if not images:
            return []
        
        timestamp = datetime.now()
        results = []
        
        try:
            # 生成文件名和文件夹名
            base_filename = self.filename_generator.generate_filename(prompt, timestamp)
            foldername = self.filename_generator.generate_foldername(prompt, timestamp)
            
            # 创建输出路径
            output_path = self.path_manager.create_output_path(foldername)
            
            # 获取起始计数器
            counter = self.counter_manager.get_next_counter(
                output_path, base_filename,
                self.config.counter_digits, self.config.counter_position,
                self.config.output_format, self.config.one_counter_per_folder
            )
            
            # 准备元数据
            metadata = None
            if self.config.save_metadata:
                metadata = self.metadata_handler.prepare_metadata(
                    prompt, extra_pnginfo, positive_text, negative_text
                )
            
            # 保存每张图像
            for i, image_tensor in enumerate(images):
                # 转换为PIL图像
                pil_image = self._tensor_to_pil(image_tensor)
                
                # 生成完整文件名
                full_filename = self.filename_generator.generate_full_filename(
                    prompt, counter + i, timestamp
                )
                
                # 完整文件路径
                file_path = os.path.join(output_path, full_filename)
                
                # 保存图像
                self._save_single_image(pil_image, file_path, metadata)
                
                # 记录结果
                if self.config.image_preview:
                    subfolder = self.path_manager.get_subfolder_path(file_path)
                    results.append({
                        'filename': full_filename,
                        'subfolder': subfolder,
                        'type': 'output'
                    })
        
        except Exception as e:
            print(f"图像保存错误: {e}")
            raise
        
        return results
    
    def _save_single_image(self, image: Image.Image, file_path: str, 
                          metadata: Optional[Dict] = None):
        """保存单张图像"""
        # 获取格式策略
        file_ext = os.path.splitext(file_path)[1].lower()
        strategy = self.format_strategies.get(file_ext)
        
        if not strategy:
            raise ValueError(f"不支持的图像格式: {file_ext}")
        
        # 使用策略保存图像
        strategy.save_image(
            image, file_path, metadata, self.config.quality
        )
    
    def _tensor_to_pil(self, tensor) -> Image.Image:
        """将张量转换为PIL图像"""
        import numpy as np
        
        # 转换为numpy数组
        i = 255. * tensor.cpu().numpy()
        array = np.clip(i, 0, 255).astype(np.uint8)
        
        # 创建PIL图像
        return Image.fromarray(array)
    
    def get_supported_formats(self) -> List[str]:
        """获取支持的格式列表"""
        return list(self.format_strategies.keys())
    
    def get_format_info(self, format_ext: str) -> Optional[Dict]:
        """获取格式信息"""
        strategy = self.format_strategies.get(format_ext.lower())
        return strategy.get_format_info() if strategy else None
    
    def preview_save_path(self, prompt: Dict, counter: int = 1) -> Tuple[str, str]:
        """
        预览保存路径
        
        Returns:
            (完整文件路径, 文件夹路径)
        """
        timestamp = datetime.now()
        
        # 生成文件名和文件夹名
        filename, foldername = self.filename_generator.preview_names(prompt, counter, timestamp)
        
        # 生成完整路径
        folder_path = self.path_manager.get_full_output_path(foldername)
        file_path = os.path.join(folder_path, filename)
        
        return file_path, folder_path
    
    def clear_caches(self):
        """清空所有缓存"""
        self.filename_generator.clear_cache()
        self.counter_manager.invalidate_cache()
        self.metadata_handler.clear_cache()
    
    def update_config(self, new_config: SaveConfig):
        """更新配置"""
        self.config = new_config
        self.filename_generator = FileNameGenerator(new_config)
        # 清空缓存以确保使用新配置
        self.clear_caches()
