"""
Save Image Extended - ComfyUI插件 (重构版本)

使用模块化架构重构的图像保存插件，支持多种格式和自定义配置。

@version: 3.0
@author: AudioscavengeR (重构版本)
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
VERSION = "3.0"

# 设置日志
logger = logging.getLogger(__name__)

# 检查可选依赖
def check_optional_dependencies():
    """检查可选依赖的可用性"""
    dependencies = {
        'avif': False,
        'jxl': False
    }
    
    try:
        import pillow_avif
        dependencies['avif'] = True
        logger.info("AVIF支持已启用")
    except ImportError:
        logger.info("AVIF不可用，如需支持请安装: pip install pillow-avif-plugin")
    
    try:
        from jxlpy import JXLImagePlugin
        dependencies['jxl'] = True
        logger.info("JXL支持已启用")
    except ImportError:
        logger.info("JXL不可用，如需支持请安装: pip install jxlpy")
    
    return dependencies

# 检查依赖
SUPPORTED_FORMATS = check_optional_dependencies()


class SaveImageExtended:
    """
    Save Image Extended - 重构版本
    
    使用模块化架构的图像保存节点，支持多种格式和自定义配置。
    """
    
    RETURN_TYPES = ()
    FUNCTION = 'save_images'
    OUTPUT_NODE = True
    CATEGORY = 'image'
    DESCRIPTION = """
### Save Image Extended v3.0 (重构版本)

**功能特性:**
- 支持多种图像格式 (PNG, WebP, JPEG, AVIF, JXL, TIFF, GIF, BMP)
- 自定义文件名和文件夹结构
- 元数据保存和作业数据导出
- 高性能缓存和批量处理
- 完善的错误处理和日志

**文件夹和文件名:**
- 使用 / 或 ./ 或 ../ 创建子文件夹
- 支持日期时间格式: %F (%Y-%m-%d), %H-%M-%S 等
- 引用节点参数: 节点ID.参数名 (如: 5.seed)

**配置预设:**
- 基础配置: 简单的文件名和格式设置
- 高级配置: 完整的自定义选项
- 专业配置: 包含元数据和作业数据导出
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
        logger.info(f"Save Image Extended v{VERSION} 已初始化")
    
    @classmethod
    def INPUT_TYPES(cls):
        """定义输入类型"""
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
                "filename_keys": ("STRING", {"default": "sampler_name, cfg, steps, %F %H-%M-%S"}),
                "foldername_prefix": ("STRING", {"default": ""}),
                "foldername_keys": ("STRING", {"default": "ckpt_name"}),
                "delimiter": ("STRING", {"default": "-"}),
                "output_format": (output_formats, {"default": ".webp"}),
                "quality": ("INT", {"default": 75, "min": 1, "max": 100, "step": 1}),
                "save_metadata": ("BOOLEAN", {"default": True}),
                "counter_digits": ("INT", {"default": 4, "min": 1, "max": 10, "step": 1}),
                "counter_position": (["last", "first"], {"default": "last"}),
                "one_counter_per_folder": ("BOOLEAN", {"default": True}),
                "save_job_data": (["disabled", "basic", "models", "sampler", "prompt"], {"default": "disabled"}),
                "job_data_per_image": ("BOOLEAN", {"default": False}),
                "job_custom_text": ("STRING", {"default": ""}),
                "image_preview": ("BOOLEAN", {"default": True}),
            },
            "optional": {
                "positive_text": ("STRING", {"forceInput": True}),
                "negative_text": ("STRING", {"forceInput": True}),
            },
            "hidden": {
                "prompt": "PROMPT",
                "extra_pnginfo": "EXTRA_PNGINFO"
            }
        }
    
    def save_images(self, images, filename_prefix="ComfyUI", filename_keys="sampler_name, cfg, steps, %F %H-%M-%S",
                   foldername_prefix="", foldername_keys="ckpt_name", delimiter="-", output_format=".webp",
                   quality=75, save_metadata=True, counter_digits=4, counter_position="last",
                   one_counter_per_folder=True, save_job_data="disabled", job_data_per_image=False,
                   job_custom_text="", image_preview=True, positive_text=None, negative_text=None,
                   prompt=None, extra_pnginfo=None):
        """
        保存图像的主要方法
        """
        try:
            # 创建配置对象
            config = SaveConfig(
                filename_prefix=filename_prefix,
                filename_keys=filename_keys,
                foldername_prefix=foldername_prefix,
                foldername_keys=foldername_keys,
                delimiter=delimiter,
                output_format=output_format,
                quality=quality,
                save_metadata=save_metadata,
                counter_digits=counter_digits,
                counter_position=counter_position,
                one_counter_per_folder=one_counter_per_folder,
                save_job_data=save_job_data,
                job_data_per_image=job_data_per_image,
                job_custom_text=job_custom_text,
                image_preview=image_preview
            )
            
            # 验证配置
            validation = self.config_manager.validate_config(config)
            if not validation.valid:
                logger.error(f"配置验证失败: {validation.errors}")
                raise ValueError(f"配置错误: {'; '.join(validation.errors)}")
            
            # 创建图像保存器
            self.image_saver = ImageSaver(config, self.output_dir)
            
            # 保存图像
            results = self.image_saver.save_images(
                images, prompt or {}, extra_pnginfo, positive_text, negative_text
            )
            
            logger.info(f"成功保存 {len(results)} 张图像")
            
            return {"ui": {"images": results}}
        
        except Exception as e:
            logger.error(f"保存图像时发生错误: {e}")
            # 返回空结果而不是抛出异常，避免中断ComfyUI工作流
            return {"ui": {"images": []}}


# ComfyUI节点映射
NODE_CLASS_MAPPINGS = {
    "SaveImageExtended": SaveImageExtended,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "SaveImageExtended": "Save Image Extended (v3.0)",
}
