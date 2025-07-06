"""
文件名生成器模块

负责根据配置和提示数据生成文件名和文件夹名。
"""

import re
import os
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from .config import SaveConfig


class ParameterExtractor:
    """参数提取器 - 从ComfyUI提示中提取参数值"""
    
    def __init__(self):
        self.cache = {}  # 简单缓存机制
    
    def find_parameter_values(self, prompt: Dict, keys: List[str]) -> Dict[str, str]:
        """从提示中查找参数值"""
        result = {}
        
        for key in keys:
            value = self._extract_single_parameter(prompt, key)
            if value is not None:
                result[key] = str(value)
        
        return result
    
    def _extract_single_parameter(self, prompt: Dict, key: str) -> Optional[str]:
        """提取单个参数值"""
        # 缓存键
        cache_key = f"{id(prompt)}_{key}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        value = None
        
        # 处理时间格式
        if key.startswith('%'):
            try:
                value = datetime.now().strftime(key)
            except ValueError:
                value = None
        
        # 处理节点引用 (如: 5.seed)
        elif '.' in key:
            parts = key.split('.')
            if len(parts) == 2 and parts[0].isdigit():
                node_id = parts[0]
                param_name = parts[1]
                value = self._find_in_node(prompt, node_id, param_name)
        
        # 处理普通键值
        else:
            value = self._find_keys_recursively(prompt, key)
        
        # 缓存结果
        self.cache[cache_key] = value
        return value
    
    def _find_in_node(self, prompt: Dict, node_id: str, param_name: str) -> Optional[str]:
        """在指定节点中查找参数"""
        try:
            if node_id in prompt:
                node_data = prompt[node_id]
                if isinstance(node_data, dict) and 'inputs' in node_data:
                    inputs = node_data['inputs']
                    if param_name in inputs:
                        return str(inputs[param_name])
        except (KeyError, TypeError):
            pass
        return None
    
    def _find_keys_recursively(self, obj: Any, key: str) -> Optional[str]:
        """递归查找键值"""
        if isinstance(obj, dict):
            # 直接匹配
            if key in obj:
                return str(obj[key])
            
            # 递归搜索
            for value in obj.values():
                result = self._find_keys_recursively(value, key)
                if result is not None:
                    return result
        
        elif isinstance(obj, list):
            for item in obj:
                result = self._find_keys_recursively(item, key)
                if result is not None:
                    return result
        
        return None
    
    def clear_cache(self):
        """清空缓存"""
        self.cache.clear()


class FileNameGenerator:
    """文件名生成器"""
    
    def __init__(self, config: SaveConfig):
        self.config = config
        self.extractor = ParameterExtractor()
        
        # 需要移除的扩展名
        self.ext_to_remove = ['.safetensors', '.ckpt', '.pt', '.bin', '.pth']
    
    def generate_filename(self, prompt: Dict, timestamp: Optional[datetime] = None) -> str:
        """生成文件名（不包含扩展名和计数器）"""
        if timestamp is None:
            timestamp = datetime.now()
        
        keys = self.config.get_filename_keys_list()
        return self._generate_custom_name(
            keys, 
            self.config.filename_prefix, 
            self.config.delimiter, 
            prompt, 
            timestamp
        )
    
    def generate_foldername(self, prompt: Dict, timestamp: Optional[datetime] = None) -> str:
        """生成文件夹名"""
        if timestamp is None:
            timestamp = datetime.now()
        
        keys = self.config.get_foldername_keys_list()
        return self._generate_custom_name(
            keys,
            self.config.foldername_prefix,
            self.config.delimiter,
            prompt,
            timestamp
        )
    
    def _generate_custom_name(self, keys: List[str], prefix: str, delimiter: str, 
                            prompt: Dict, timestamp: datetime) -> str:
        """生成自定义名称的核心逻辑"""
        custom_name = prefix
        
        # 提取所有参数值
        parameter_values = self.extractor.find_parameter_values(prompt, keys)
        
        for key in keys:
            if not key:
                continue
            
            value = None
            delim = delimiter
            
            # 处理时间格式
            if key.startswith('%'):
                try:
                    value = timestamp.strftime(key)
                except ValueError:
                    continue
            
            # 处理路径分隔符 (文件夹专用)
            elif key.startswith('./'):
                value = key[2:]  # 移除 ./
                delim = '/'
            elif key.startswith('../'):
                value = key[3:]  # 移除 ../
                delim = '/'
            
            # 使用提取的参数值
            elif key in parameter_values:
                value = parameter_values[key]
                # 清理文件名中的无效字符
                value = self._clean_filename(value)
            
            # 添加到自定义名称
            if value:
                if custom_name and not custom_name.endswith('/'):
                    custom_name += delim
                custom_name += value
        
        # 清理最终结果
        return self._clean_final_name(custom_name, delimiter)
    
    def _clean_filename(self, value: str) -> str:
        """清理文件名中的无效字符"""
        # 移除指定的扩展名
        for ext in self.ext_to_remove:
            if value.endswith(ext):
                value = value[:-len(ext)]
                break
        
        # 移除或替换无效字符
        # Windows文件名不能包含: < > : " | ? * \
        invalid_chars = r'[<>:"|?*\\]'
        value = re.sub(invalid_chars, '_', value)
        
        # 移除前后空格
        value = value.strip()
        
        return value
    
    def _clean_final_name(self, name: str, delimiter: str) -> str:
        """清理最终的名称"""
        # 移除前后的分隔符和点
        name = name.strip(delimiter).strip('.').strip('/').strip(delimiter)
        
        # 如果名称为空，使用默认前缀
        if not name:
            name = "ComfyUI"
        
        return name
    
    def generate_full_filename(self, prompt: Dict, counter: int, 
                             timestamp: Optional[datetime] = None) -> str:
        """生成完整的文件名（包含计数器和扩展名）"""
        base_filename = self.generate_filename(prompt, timestamp)
        
        # 格式化计数器
        counter_str = f"{counter:0{self.config.counter_digits}d}"
        
        # 根据计数器位置组合文件名
        if self.config.counter_position == 'first':
            filename = f"{counter_str}{self.config.delimiter}{base_filename}"
        else:  # 'last'
            filename = f"{base_filename}{self.config.delimiter}{counter_str}"
        
        # 添加扩展名
        return f"{filename}{self.config.output_format}"
    
    def preview_names(self, prompt: Dict, counter: int = 1, 
                     timestamp: Optional[datetime] = None) -> Tuple[str, str]:
        """预览生成的文件名和文件夹名"""
        if timestamp is None:
            timestamp = datetime.now()
        
        filename = self.generate_full_filename(prompt, counter, timestamp)
        foldername = self.generate_foldername(prompt, timestamp)
        
        return filename, foldername
    
    def clear_cache(self):
        """清空缓存"""
        self.extractor.clear_cache()
