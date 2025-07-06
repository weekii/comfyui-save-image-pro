"""
路径管理模块

负责处理文件路径的创建、验证和管理。
"""

import os
from pathlib import Path
from typing import Optional


class PathManager:
    """路径管理器"""
    
    def __init__(self, base_output_dir: str):
        self.base_output_dir = Path(base_output_dir).resolve()
        self.ensure_base_dir_exists()
    
    def ensure_base_dir_exists(self):
        """确保基础输出目录存在"""
        try:
            self.base_output_dir.mkdir(parents=True, exist_ok=True)
        except (OSError, PermissionError) as e:
            print(f"路径管理器错误: 无法创建基础目录 {self.base_output_dir}: {e}")
    
    def create_output_path(self, subfolder: str = "") -> str:
        """
        创建输出路径
        
        Args:
            subfolder: 子文件夹名称
            
        Returns:
            完整的输出路径
        """
        if not subfolder:
            output_path = self.base_output_dir
        else:
            # 清理子文件夹名称
            clean_subfolder = self._clean_path_component(subfolder)
            output_path = self.base_output_dir / clean_subfolder
        
        # 创建目录
        try:
            output_path.mkdir(parents=True, exist_ok=True)
        except (OSError, PermissionError) as e:
            print(f"路径管理器错误: 无法创建目录 {output_path}: {e}")
            # 回退到基础目录
            output_path = self.base_output_dir
        
        return str(output_path)
    
    def get_full_output_path(self, subfolder: str = "") -> str:
        """
        获取完整输出路径（不创建目录）
        
        Args:
            subfolder: 子文件夹名称
            
        Returns:
            完整的输出路径
        """
        if not subfolder:
            return str(self.base_output_dir)
        
        clean_subfolder = self._clean_path_component(subfolder)
        return str(self.base_output_dir / clean_subfolder)
    
    def get_subfolder_path(self, full_path: str) -> str:
        """
        获取相对于基础目录的子文件夹路径
        
        Args:
            full_path: 完整文件路径
            
        Returns:
            相对路径
        """
        try:
            full_path_obj = Path(full_path).resolve()
            relative_path = full_path_obj.relative_to(self.base_output_dir)
            return str(relative_path.parent) if relative_path.parent != Path('.') else ""
        except ValueError:
            # 如果路径不在基础目录下，返回空字符串
            return ""
    
    def _clean_path_component(self, component: str) -> str:
        """
        清理路径组件，移除无效字符
        
        Args:
            component: 原始路径组件
            
        Returns:
            清理后的路径组件
        """
        if not component:
            return ""
        
        # 处理相对路径标记
        parts = []
        for part in component.split('/'):
            if not part or part == '.':
                continue
            elif part == '..':
                # 允许上级目录，但要小心处理
                parts.append(part)
            else:
                # 清理文件名中的无效字符
                clean_part = self._clean_filename(part)
                if clean_part:
                    parts.append(clean_part)
        
        return '/'.join(parts)
    
    def _clean_filename(self, filename: str) -> str:
        """
        清理文件名中的无效字符
        
        Args:
            filename: 原始文件名
            
        Returns:
            清理后的文件名
        """
        import re
        
        # Windows文件名不能包含的字符: < > : " | ? * \
        invalid_chars = r'[<>:"|?*\\]'
        
        # 替换无效字符为下划线
        clean_name = re.sub(invalid_chars, '_', filename)
        
        # 移除前后空格和点
        clean_name = clean_name.strip(' .')
        
        # 确保不是保留名称（Windows）
        reserved_names = [
            'CON', 'PRN', 'AUX', 'NUL',
            'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
            'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
        ]
        
        if clean_name.upper() in reserved_names:
            clean_name = f"_{clean_name}"
        
        # 限制长度（Windows路径限制）
        if len(clean_name) > 200:
            clean_name = clean_name[:200]
        
        return clean_name
    
    def validate_path(self, path: str) -> bool:
        """
        验证路径是否有效
        
        Args:
            path: 要验证的路径
            
        Returns:
            是否有效
        """
        try:
            path_obj = Path(path)
            
            # 检查是否是绝对路径且在允许的范围内
            if path_obj.is_absolute():
                # 确保路径在基础目录下或其子目录中
                try:
                    path_obj.relative_to(self.base_output_dir)
                    return True
                except ValueError:
                    return False
            else:
                # 相对路径，检查是否包含危险的路径遍历
                normalized = os.path.normpath(path)
                return not normalized.startswith('..')
        
        except (OSError, ValueError):
            return False
    
    def get_available_space(self) -> Optional[int]:
        """
        获取可用磁盘空间（字节）
        
        Returns:
            可用空间字节数，如果无法获取则返回None
        """
        try:
            import shutil
            return shutil.disk_usage(self.base_output_dir).free
        except (OSError, AttributeError):
            return None
    
    def cleanup_empty_dirs(self, max_depth: int = 3):
        """
        清理空目录
        
        Args:
            max_depth: 最大清理深度
        """
        def _remove_empty_dirs(path: Path, current_depth: int = 0):
            if current_depth >= max_depth:
                return
            
            try:
                for item in path.iterdir():
                    if item.is_dir():
                        _remove_empty_dirs(item, current_depth + 1)
                        
                        # 尝试删除空目录
                        try:
                            if not any(item.iterdir()):
                                item.rmdir()
                        except OSError:
                            pass  # 目录不为空或无权限
            except (OSError, PermissionError):
                pass
        
        _remove_empty_dirs(self.base_output_dir)
    
    def get_path_info(self) -> dict:
        """获取路径信息"""
        return {
            'base_output_dir': str(self.base_output_dir),
            'exists': self.base_output_dir.exists(),
            'is_writable': os.access(self.base_output_dir, os.W_OK),
            'available_space': self.get_available_space()
        }
