"""
计数器管理模块

负责管理文件计数器，支持缓存和高效查找。
"""

import os
import re
from typing import Dict, Optional
from pathlib import Path


class CounterManager:
    """计数器管理器"""
    
    def __init__(self):
        self.counter_cache: Dict[str, int] = {}
        self.cache_enabled = True
    
    def get_next_counter(self, folder_path: str, filename_prefix: str, 
                        counter_digits: int = 4, counter_position: str = 'last',
                        output_ext: str = '.webp', one_counter_per_folder: bool = True) -> int:
        """
        获取下一个可用的计数器值
        
        Args:
            folder_path: 文件夹路径
            filename_prefix: 文件名前缀
            counter_digits: 计数器位数
            counter_position: 计数器位置 ('first' 或 'last')
            output_ext: 输出扩展名
            one_counter_per_folder: 是否每个文件夹使用独立计数器
            
        Returns:
            下一个可用的计数器值
        """
        # 生成缓存键
        cache_key = self._generate_cache_key(
            folder_path, filename_prefix, counter_position, 
            output_ext, one_counter_per_folder
        )
        
        # 检查缓存
        if self.cache_enabled and cache_key in self.counter_cache:
            counter = self.counter_cache[cache_key]
            self.counter_cache[cache_key] = counter + 1
            return counter
        
        # 计算当前最大计数器值
        current_max = self._find_max_counter(
            folder_path, filename_prefix, counter_digits,
            counter_position, output_ext, one_counter_per_folder
        )
        
        next_counter = current_max + 1
        
        # 更新缓存
        if self.cache_enabled:
            self.counter_cache[cache_key] = next_counter + 1
        
        return next_counter
    
    def _find_max_counter(self, folder_path: str, filename_prefix: str,
                         counter_digits: int, counter_position: str,
                         output_ext: str, one_counter_per_folder: bool) -> int:
        """查找当前最大的计数器值"""
        if not os.path.exists(folder_path):
            return 0
        
        max_counter = 0
        
        try:
            # 构建正则表达式模式
            if one_counter_per_folder:
                # 匹配所有文件，不限制前缀
                if counter_position == 'last':
                    pattern = rf'.*-(\d{{{counter_digits}}}){re.escape(output_ext)}$'
                else:  # 'first'
                    pattern = rf'(\d{{{counter_digits}}})-.*{re.escape(output_ext)}$'
            else:
                # 只匹配特定前缀的文件
                escaped_prefix = re.escape(filename_prefix)
                if counter_position == 'last':
                    pattern = rf'{escaped_prefix}.*-(\d{{{counter_digits}}}){re.escape(output_ext)}$'
                else:  # 'first'
                    pattern = rf'(\d{{{counter_digits}}})-{escaped_prefix}.*{re.escape(output_ext)}$'
            
            compiled_pattern = re.compile(pattern)
            
            # 扫描文件夹
            for filename in os.listdir(folder_path):
                match = compiled_pattern.match(filename)
                if match:
                    try:
                        counter = int(match.group(1))
                        max_counter = max(max_counter, counter)
                    except (ValueError, IndexError):
                        continue
        
        except (OSError, PermissionError) as e:
            print(f"计数器管理器错误: 无法访问文件夹 {folder_path}: {e}")
        
        return max_counter
    
    def _generate_cache_key(self, folder_path: str, filename_prefix: str,
                           counter_position: str, output_ext: str,
                           one_counter_per_folder: bool) -> str:
        """生成缓存键"""
        # 标准化路径
        normalized_path = str(Path(folder_path).resolve())
        
        # 如果是每个文件夹一个计数器，忽略前缀
        if one_counter_per_folder:
            return f"{normalized_path}|{counter_position}|{output_ext}|global"
        else:
            return f"{normalized_path}|{filename_prefix}|{counter_position}|{output_ext}|prefix"
    
    def invalidate_cache(self, folder_path: Optional[str] = None):
        """
        使缓存失效
        
        Args:
            folder_path: 特定文件夹路径，如果为None则清空所有缓存
        """
        if folder_path is None:
            self.counter_cache.clear()
        else:
            normalized_path = str(Path(folder_path).resolve())
            keys_to_remove = [
                key for key in self.counter_cache.keys()
                if key.startswith(normalized_path)
            ]
            for key in keys_to_remove:
                del self.counter_cache[key]
    
    def set_cache_enabled(self, enabled: bool):
        """启用或禁用缓存"""
        self.cache_enabled = enabled
        if not enabled:
            self.counter_cache.clear()
    
    def get_cache_stats(self) -> Dict[str, int]:
        """获取缓存统计信息"""
        return {
            'cache_size': len(self.counter_cache),
            'cache_enabled': self.cache_enabled
        }
    
    def preload_counters(self, folder_paths: list, filename_prefix: str = "",
                        counter_digits: int = 4, counter_position: str = 'last',
                        output_ext: str = '.webp', one_counter_per_folder: bool = True):
        """
        预加载多个文件夹的计数器
        
        Args:
            folder_paths: 文件夹路径列表
            其他参数同 get_next_counter
        """
        for folder_path in folder_paths:
            if os.path.exists(folder_path):
                self.get_next_counter(
                    folder_path, filename_prefix, counter_digits,
                    counter_position, output_ext, one_counter_per_folder
                )
