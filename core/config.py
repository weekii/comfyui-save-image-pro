"""
配置管理模块

提供统一的配置管理、验证和预设模板功能。
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
import re


@dataclass
class ValidationResult:
    """配置验证结果"""
    valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    def add_error(self, message: str):
        """添加错误信息"""
        self.errors.append(message)
        self.valid = False
    
    def add_warning(self, message: str):
        """添加警告信息"""
        self.warnings.append(message)


@dataclass
class SaveConfig:
    """保存配置数据类"""
    filename_prefix: str = "ComfyUI"
    filename_keys: str = "sampler_name, cfg, steps, %F %H-%M-%S"
    foldername_prefix: str = ""
    foldername_keys: str = "ckpt_name"
    delimiter: str = "-"
    output_format: str = ".webp"
    quality: int = 75
    save_metadata: bool = True
    counter_digits: int = 4
    counter_position: str = "last"
    one_counter_per_folder: bool = True
    save_job_data: str = "disabled"
    job_data_per_image: bool = False
    job_custom_text: str = ""
    image_preview: bool = True
    
    def get_filename_keys_list(self) -> List[str]:
        """获取文件名键值列表"""
        return [key.strip() for key in self.filename_keys.split(',') if key.strip()]
    
    def get_foldername_keys_list(self) -> List[str]:
        """获取文件夹名键值列表"""
        return [key.strip() for key in self.foldername_keys.split(',') if key.strip()]


class ConfigManager:
    """配置管理器"""
    
    # 预设模板
    PRESETS = {
        "simple": {
            "filename_keys": "sampler_name, steps",
            "foldername_keys": "ckpt_name",
            "delimiter": "-",
            "description": "简单模式：采样器-步数"
        },
        "detailed": {
            "filename_keys": "sampler_name, cfg, steps, %Y-%m-%d_%H-%M-%S",
            "foldername_keys": "ckpt_name, ./sampler_name",
            "delimiter": "_",
            "description": "详细模式：包含时间戳和子文件夹"
        },
        "organized": {
            "filename_keys": "ckpt_name, sampler_name, cfg, steps",
            "foldername_keys": "%Y-%m-%d, ./ckpt_name",
            "delimiter": "-",
            "description": "组织模式：按日期和模型分类"
        },
        "minimal": {
            "filename_keys": "%Y%m%d_%H%M%S",
            "foldername_keys": "",
            "delimiter": "",
            "description": "最简模式：仅时间戳"
        }
    }
    
    # 支持的输出格式
    SUPPORTED_FORMATS = ['.avif', '.webp', '.png', '.jpg', '.jpeg', '.gif', '.tiff', '.bmp']
    
    # 帮助文本
    HELP_TEXT = {
        "filename_keys": """
文件名键值说明：
• sampler_name: 采样器名称 (如: euler_a)
• cfg: CFG引导强度 (如: 7.5)
• steps: 采样步数 (如: 20)
• ckpt_name: 模型名称 (如: sd_xl_base)
• seed: 随机种子
• %Y-%m-%d: 日期格式 (如: 2024-01-15)
• %H-%M-%S: 时间格式 (如: 14-30-25)
• 节点ID.参数名: 引用特定节点参数 (如: 5.seed)
        """.strip(),
        
        "foldername_keys": """
文件夹键值说明：
• ckpt_name: 模型名称
• sampler_name: 采样器名称
• ./子文件夹: 创建子文件夹
• ../上级文件夹: 创建上级文件夹
• %Y-%m-%d: 按日期分组
• 节点ID.参数名: 引用特定节点参数
        """.strip(),
        
        "delimiter": "文件名分隔符，建议使用 - 或 _ 避免特殊字符",
        "quality": "图像质量 1-100，100为无损（仅AVIF/WebP支持）",
        "counter_position": "计数器位置：last=文件名末尾，first=文件名开头"
    }
    
    @classmethod
    def get_preset(cls, preset_name: str) -> Optional[Dict[str, Any]]:
        """获取预设配置"""
        return cls.PRESETS.get(preset_name)
    
    @classmethod
    def list_presets(cls) -> Dict[str, str]:
        """列出所有预设及其描述"""
        return {name: preset["description"] for name, preset in cls.PRESETS.items()}
    
    @classmethod
    def get_help(cls, field_name: str) -> str:
        """获取字段帮助信息"""
        return cls.HELP_TEXT.get(field_name, "暂无帮助信息")
    
    def validate_config(self, config: SaveConfig) -> ValidationResult:
        """验证配置有效性"""
        result = ValidationResult(valid=True)
        
        # 验证文件名键值
        self._validate_keys(config.get_filename_keys_list(), "filename_keys", result)
        
        # 验证文件夹名键值
        self._validate_keys(config.get_foldername_keys_list(), "foldername_keys", result)
        
        # 验证输出格式
        if config.output_format not in self.SUPPORTED_FORMATS:
            result.add_error(f"不支持的输出格式: {config.output_format}")
        
        # 验证质量参数
        if not (1 <= config.quality <= 100):
            result.add_error("质量参数必须在1-100之间")
        
        # 验证计数器位数
        if not (1 <= config.counter_digits <= 8):
            result.add_error("计数器位数必须在1-8之间")
        
        # 验证计数器位置
        if config.counter_position not in ["first", "last"]:
            result.add_error("计数器位置必须是 'first' 或 'last'")
        
        # 验证分隔符
        if not config.delimiter or len(config.delimiter) > 3:
            result.add_warning("建议使用简短的分隔符 (如: -, _)")
        
        return result
    
    def _validate_keys(self, keys: List[str], field_name: str, result: ValidationResult):
        """验证键值列表"""
        for key in keys:
            if not key:
                continue
            
            # 检查节点引用格式 (如: 5.seed)
            if '.' in key and not '%' in key:
                parts = key.split('.')
                if len(parts) == 2 and parts[0].isdigit():
                    continue  # 正确的节点引用格式
                else:
                    result.add_error(f"{field_name}: 节点引用格式错误: {key} (应为: 节点ID.参数名)")
            
            # 检查时间格式
            elif '%' in key:
                try:
                    datetime.now().strftime(key)
                except ValueError:
                    result.add_error(f"{field_name}: 时间格式错误: {key}")
            
            # 检查路径格式 (文件夹专用)
            elif field_name == "foldername_keys" and key.startswith(('./', '../')):
                if not re.match(r'^\.\.?/[\w\-_]+$', key):
                    result.add_warning(f"{field_name}: 路径格式可能有问题: {key}")
    
    def preview_filename(self, config: SaveConfig, sample_data: Optional[Dict] = None) -> str:
        """预览生成的文件名"""
        if sample_data is None:
            sample_data = {
                "sampler_name": "euler_a",
                "cfg": "7.5", 
                "steps": "20",
                "ckpt_name": "sd_xl_base",
                "seed": "12345"
            }
        
        # 简化的预览逻辑
        keys = config.get_filename_keys_list()
        parts = []
        
        for key in keys:
            if key.startswith('%'):
                try:
                    parts.append(datetime.now().strftime(key))
                except:
                    parts.append(f"[时间格式错误:{key}]")
            elif key in sample_data:
                parts.append(str(sample_data[key]))
            elif '.' in key:
                parts.append(f"[节点引用:{key}]")
            else:
                parts.append(f"[未知键:{key}]")
        
        filename = config.delimiter.join(parts) if parts else config.filename_prefix
        return f"{filename}-0001{config.output_format}"
