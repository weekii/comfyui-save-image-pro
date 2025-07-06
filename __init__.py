"""
ComfyUI Save Image Pro - 专业级图像保存插件

高性能、模块化的 ComfyUI 图像保存插件，支持多种格式、
自定义命名和高级功能。采用现代化架构设计，提供卓越的
性能和可扩展性。

@author: weekii
@title: ComfyUI Save Image Pro
@nickname: Save Image Pro
@description: 专业级图像保存插件，支持多格式、自定义命名和高级功能
@version: latest
@repository: https://github.com/weekii/comfyui-save-image-pro
"""

from .save_image_advanced import NODE_CLASS_MAPPINGS as ADVANCED_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS as ADVANCED_DISPLAY_MAPPINGS
from .save_image_simple import NODE_CLASS_MAPPINGS as SIMPLE_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS as SIMPLE_DISPLAY_MAPPINGS

# 合并节点映射
NODE_CLASS_MAPPINGS = {**ADVANCED_MAPPINGS, **SIMPLE_MAPPINGS}
NODE_DISPLAY_NAME_MAPPINGS = {**ADVANCED_DISPLAY_MAPPINGS, **SIMPLE_DISPLAY_MAPPINGS}

__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS']

