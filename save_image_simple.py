"""
ComfyUI Save Image Pro - 简化版节点

简化版图像保存节点，提供基础的图像保存功能。

@version: latest
@author: AudioscavengeR
"""

import os
import sys
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
import folder_paths

# 导入重构后的核心模块
from .core import (
    SaveConfig, ConfigManager, ValidationResult,
    ImageSaver, FileNameGenerator, CounterManager,
    MetadataHandler, PathManager, JobDataExporter
)

# 版本信息
VERSION = "latest"

# 设置日志
logger = logging.getLogger(__name__)

def check_optional_dependencies():
    """检查可选依赖项"""
    supported = {
        'avif': False,
        'jxl': False
    }
    
    try:
        from PIL import Image
        # 检查 AVIF 支持
        try:
            import pillow_avif
            supported['avif'] = True
        except ImportError:
            pass
        
        # 检查 JXL 支持
        try:
            import jxlpy
            supported['jxl'] = True
        except ImportError:
            pass
    except ImportError:
        pass
    
    return supported

# 检查支持的格式
SUPPORTED_FORMATS = check_optional_dependencies()


class SaveImageSimple:
    """
    ComfyUI Save Image Pro - 简化版
    
    提供基础的图像保存功能，包含最常用的参数。
    """
    
    RETURN_TYPES = ()
    FUNCTION = 'save_images'
    OUTPUT_NODE = True
    CATEGORY = 'image'
    DESCRIPTION = """
### ComfyUI Save Image Pro - 简化版

**基础功能:**
- 支持多种图像格式 (PNG, WebP, JPEG, AVIF, JXL, TIFF, GIF, BMP)
- 自定义文件名前缀
- 自定义文件夹前缀
- 质量控制
- 作业数据导出
- 图像预览

**简化设计:**
- 精简的参数设置
- 快速上手使用
- 保留核心功能
"""
    
    def __init__(self):
        self.config_manager = ConfigManager()
        self.output_dir = folder_paths.get_output_directory()
        self.image_saver = None
        self.job_exporter = None
        
        # 初始化日志
        self._setup_logging()
    
    def _setup_logging(self):
        """设置日志系统"""
        logging.basicConfig(
            level=logging.INFO,
            format='[%(name)s] %(levelname)s: %(message)s'
        )
        logger.info("ComfyUI Save Image Pro (Simple) initialized")
    
    @classmethod
    def INPUT_TYPES(cls):
        """定义输入类型 - 简化版"""
        # 获取支持的格式列表
        output_formats = ['.webp', '.png', '.jpg', '.jpeg', '.gif', '.tiff', '.bmp']
        
        if SUPPORTED_FORMATS['jxl']:
            output_formats.insert(0, '.jxl')
        if SUPPORTED_FORMATS['avif']:
            output_formats.insert(0, '.avif')
        
        return {
            "required": {
                "images": ("IMAGE", ),
                "filename_prefix": ("STRING", {"default": "ComfyUI"}),
                "foldername_prefix": ("STRING", {"default": ""}),
                "output_format": (output_formats, {"default": ".webp"}),
                "quality": ("INT", {"default": 75, "min": 1, "max": 100, "step": 1}),
                "job_data_per_image": ("BOOLEAN", {"default": False}),
                "image_preview": ("BOOLEAN", {"default": True}),
            },
            "hidden": {
                "prompt": "PROMPT",
                "extra_pnginfo": "EXTRA_PNGINFO"
            }
        }
    
    def save_images(self, images, filename_prefix="ComfyUI", foldername_prefix="",
                   output_format=".webp", quality=75, job_data_per_image=False,
                   image_preview=True, prompt=None, extra_pnginfo=None):
        """
        保存图像的主要方法 - 简化版
        """
        try:
            # 创建简化的配置对象
            config = SaveConfig(
                filename_prefix=filename_prefix,
                filename_keys="",  # 简化版不使用复杂的文件名键
                foldername_prefix=foldername_prefix,  # 使用用户输入的文件夹前缀
                foldername_keys="",  # 简化版不使用文件夹键
                delimiter="-",
                output_format=output_format,
                quality=quality,
                save_metadata=True,  # 简化版默认保存元数据
                counter_digits=4,
                counter_position="last",
                one_counter_per_folder=True,
                save_job_data="basic" if job_data_per_image else "disabled",
                job_data_per_image=job_data_per_image,
                job_custom_text="",
                image_preview=image_preview
            )
            
            # 验证配置
            validation = self.config_manager.validate_config(config)
            if not validation.valid:
                logger.error(f"Configuration validation failed: {validation.errors}")
                return {"ui": {"images": []}}
            
            # 初始化图像保存器
            if not self.image_saver:
                self.image_saver = ImageSaver(config, self.output_dir)
            else:
                self.image_saver.update_config(config)
            
            # 保存图像
            results = self.image_saver.save_images(
                images=images,
                prompt=prompt,
                extra_pnginfo=extra_pnginfo
            )
            
            # 导出作业数据（如果启用）
            if config.save_job_data != "disabled":
                if not self.job_exporter:
                    self.job_exporter = JobDataExporter(config)
                else:
                    self.job_exporter.update_config(config)
                
                self.job_exporter.export_job_data(
                    results=results,
                    prompt=prompt,
                    extra_pnginfo=extra_pnginfo
                )
            
            logger.info(f"Successfully saved {len(results)} images")
            
            # 返回结果
            if config.image_preview:
                return {"ui": {"images": results}}
            else:
                return {"ui": {"images": []}}
                
        except Exception as e:
            logger.error(f"Error occurred while saving images: {str(e)}")
            import traceback
            traceback.print_exc()
            return {"ui": {"images": []}}


# 节点类映射
NODE_CLASS_MAPPINGS = {
    "SaveImageSimple": SaveImageSimple
}

# 节点显示名称映射
NODE_DISPLAY_NAME_MAPPINGS = {
    "SaveImageSimple": "comfyui-save-image-pro (Simple)"
}
