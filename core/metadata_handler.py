"""
元数据处理模块

负责处理图像元数据的生成、格式化和缓存。
"""

import json
from typing import Dict, Any, Optional
from datetime import datetime


class MetadataHandler:
    """元数据处理器"""
    
    def __init__(self):
        self.cache = {}
        self.cache_enabled = True
    
    def prepare_metadata(self, prompt: Dict, extra_pnginfo: Optional[Dict] = None,
                        positive_text: Optional[str] = None, 
                        negative_text: Optional[str] = None) -> Dict[str, Any]:
        """
        准备元数据
        
        Args:
            prompt: ComfyUI提示字典
            extra_pnginfo: 额外的PNG信息
            positive_text: 正面提示文本
            negative_text: 负面提示文本
            
        Returns:
            格式化的元数据字典
        """
        # 生成缓存键
        cache_key = self._generate_cache_key(prompt, extra_pnginfo, positive_text, negative_text)
        
        # 检查缓存
        if self.cache_enabled and cache_key in self.cache:
            return self.cache[cache_key]
        
        metadata = {}
        
        # 添加基本提示信息
        if prompt:
            metadata['prompt'] = prompt
        
        # 添加额外信息
        if extra_pnginfo:
            metadata.update(extra_pnginfo)
        
        # 添加文本提示（如果提供）
        if positive_text:
            metadata['positive_prompt'] = positive_text
        
        if negative_text:
            metadata['negative_prompt'] = negative_text
        
        # 添加生成时间戳
        metadata['generated_at'] = datetime.now().isoformat()
        
        # 添加插件信息
        metadata['generator'] = {
            'name': 'Save Image Extended',
            'version': '3.0'
        }
        
        # 缓存结果
        if self.cache_enabled:
            self.cache[cache_key] = metadata
        
        return metadata
    
    def _generate_cache_key(self, prompt: Dict, extra_pnginfo: Optional[Dict],
                           positive_text: Optional[str], negative_text: Optional[str]) -> str:
        """生成缓存键"""
        # 使用JSON序列化生成稳定的键
        key_data = {
            'prompt_id': id(prompt),
            'extra_id': id(extra_pnginfo) if extra_pnginfo else None,
            'positive': positive_text,
            'negative': negative_text
        }
        return json.dumps(key_data, sort_keys=True)
    
    def format_for_png(self, metadata: Dict[str, Any]) -> Dict[str, str]:
        """
        格式化为PNG元数据格式
        
        Args:
            metadata: 原始元数据
            
        Returns:
            PNG格式的元数据字典
        """
        png_metadata = {}
        
        for key, value in metadata.items():
            try:
                if isinstance(value, (dict, list)):
                    png_metadata[key] = json.dumps(value, ensure_ascii=False)
                else:
                    png_metadata[key] = str(value)
            except (TypeError, ValueError):
                png_metadata[key] = str(value)
        
        return png_metadata
    
    def format_for_exif(self, metadata: Dict[str, Any]) -> bytes:
        """
        格式化为EXIF元数据格式
        
        Args:
            metadata: 原始元数据
            
        Returns:
            EXIF字节数据
        """
        try:
            from PIL import Image
            
            # 创建临时图像来生成EXIF
            temp_img = Image.new('RGB', (1, 1))
            exif = temp_img.getexif()
            
            # 将关键信息编码到EXIF字段
            if 'prompt' in metadata:
                # 0x010f: Make字段存储prompt
                exif[0x010f] = "Prompt: " + json.dumps(metadata['prompt'], ensure_ascii=False)
            
            if 'workflow' in metadata:
                # 0x010e: ImageDescription字段存储workflow
                exif[0x010e] = "Workflow: " + json.dumps(metadata['workflow'], ensure_ascii=False)
            
            # 添加生成器信息
            if 'generator' in metadata:
                # 0x0131: Software字段
                generator = metadata['generator']
                exif[0x0131] = f"{generator.get('name', 'Unknown')} v{generator.get('version', '1.0')}"
            
            return exif.tobytes()
        
        except Exception as e:
            print(f"EXIF元数据生成错误: {e}")
            return b''
    
    def extract_parameters(self, metadata: Dict[str, Any]) -> Dict[str, str]:
        """
        从元数据中提取关键参数
        
        Args:
            metadata: 元数据字典
            
        Returns:
            参数字典
        """
        parameters = {}
        
        if 'prompt' in metadata:
            prompt = metadata['prompt']
            
            # 递归提取常用参数
            extracted = self._extract_common_parameters(prompt)
            parameters.update(extracted)
        
        # 添加文本提示
        if 'positive_prompt' in metadata:
            parameters['positive_prompt'] = metadata['positive_prompt']
        
        if 'negative_prompt' in metadata:
            parameters['negative_prompt'] = metadata['negative_prompt']
        
        return parameters
    
    def _extract_common_parameters(self, obj: Any, prefix: str = "") -> Dict[str, str]:
        """递归提取常用参数"""
        parameters = {}
        
        # 常用参数名列表
        common_params = [
            'sampler_name', 'scheduler', 'steps', 'cfg', 'seed',
            'width', 'height', 'denoise', 'model', 'ckpt_name',
            'vae_name', 'clip_skip', 'lora_name'
        ]
        
        if isinstance(obj, dict):
            for key, value in obj.items():
                current_key = f"{prefix}.{key}" if prefix else key
                
                # 检查是否是常用参数
                if key.lower() in [p.lower() for p in common_params]:
                    parameters[key] = str(value)
                
                # 递归搜索
                if isinstance(value, (dict, list)):
                    nested = self._extract_common_parameters(value, current_key)
                    parameters.update(nested)
        
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                current_key = f"{prefix}[{i}]" if prefix else f"[{i}]"
                nested = self._extract_common_parameters(item, current_key)
                parameters.update(nested)
        
        return parameters
    
    def clear_cache(self):
        """清空缓存"""
        self.cache.clear()
    
    def set_cache_enabled(self, enabled: bool):
        """启用或禁用缓存"""
        self.cache_enabled = enabled
        if not enabled:
            self.cache.clear()
    
    def get_cache_stats(self) -> Dict[str, int]:
        """获取缓存统计"""
        return {
            'cache_size': len(self.cache),
            'cache_enabled': self.cache_enabled
        }
