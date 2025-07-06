"""
作业数据导出模块

负责导出作业数据到JSON文件。
"""

import json
import os
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path

from .config import SaveConfig


class JobDataExporter:
    """作业数据导出器"""
    
    def __init__(self, config: SaveConfig):
        self.config = config
    
    def should_export(self) -> bool:
        """是否应该导出作业数据"""
        return self.config.save_job_data != 'disabled'
    
    def export_job_data(self, prompt: Dict, output_path: str, filename: str,
                       positive_text: Optional[str] = None, negative_text: Optional[str] = None,
                       resolution: str = "", timestamp: Optional[datetime] = None) -> bool:
        """
        导出作业数据到JSON文件
        
        Args:
            prompt: ComfyUI提示字典
            output_path: 输出路径
            filename: 文件名（不含扩展名）
            positive_text: 正面提示文本
            negative_text: 负面提示文本
            resolution: 图像分辨率
            timestamp: 时间戳
            
        Returns:
            是否成功导出
        """
        if not self.should_export():
            return False
        
        if timestamp is None:
            timestamp = datetime.now()
        
        try:
            # 收集要保存的数据
            job_data = self._collect_job_data(
                prompt, positive_text, negative_text, resolution, timestamp
            )
            
            # 确定输出文件路径
            if self.config.job_data_per_image:
                json_filename = f"{filename}.json"
            else:
                json_filename = "jobs.json"
            
            json_path = os.path.join(output_path, json_filename)
            
            # 保存数据
            if self.config.job_data_per_image:
                self._save_single_job(json_path, job_data)
            else:
                self._append_to_jobs_file(json_path, job_data, filename)
            
            return True
        
        except Exception as e:
            print(f"作业数据导出错误: {e}")
            return False
    
    def _collect_job_data(self, prompt: Dict, positive_text: Optional[str],
                         negative_text: Optional[str], resolution: str,
                         timestamp: datetime) -> Dict[str, Any]:
        """收集作业数据"""
        job_data = {}
        
        # 基础信息
        if 'basic' in self.config.save_job_data:
            job_data.update({
                'timestamp': timestamp.isoformat(),
                'resolution': resolution,
                'filename_prefix': self.config.filename_prefix
            })
        
        # 自定义文本
        if self.config.job_custom_text:
            job_data['custom_text'] = self.config.job_custom_text
        
        # 提示文本
        if positive_text:
            job_data['positive_prompt'] = positive_text
        
        if negative_text:
            job_data['negative_prompt'] = negative_text
        
        # 模型信息
        if 'models' in self.config.save_job_data:
            models_info = self._extract_models_info(prompt)
            if models_info:
                job_data['models'] = models_info
        
        # 采样器信息
        if 'sampler' in self.config.save_job_data:
            sampler_info = self._extract_sampler_info(prompt)
            if sampler_info:
                job_data['sampler'] = sampler_info
        
        # 完整提示（如果需要）
        if 'prompt' in self.config.save_job_data:
            job_data['full_prompt'] = prompt
        
        return job_data
    
    def _extract_models_info(self, prompt: Dict) -> Dict[str, Any]:
        """提取模型信息"""
        models = {}
        
        # 递归搜索模型相关信息
        def search_models(obj, path=""):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    current_path = f"{path}.{key}" if path else key
                    
                    # 检查是否是模型相关的键
                    if any(model_key in key.lower() for model_key in 
                          ['ckpt', 'model', 'vae', 'lora', 'embedding', 'controlnet']):
                        if isinstance(value, str) and value:
                            models[current_path] = value
                    
                    # 递归搜索
                    if isinstance(value, (dict, list)):
                        search_models(value, current_path)
            
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    current_path = f"{path}[{i}]" if path else f"[{i}]"
                    search_models(item, current_path)
        
        search_models(prompt)
        return models
    
    def _extract_sampler_info(self, prompt: Dict) -> Dict[str, Any]:
        """提取采样器信息"""
        sampler_info = {}
        
        # 常见的采样器参数
        sampler_keys = [
            'sampler_name', 'scheduler', 'steps', 'cfg', 'seed',
            'denoise', 'noise_seed', 'control_after_generate'
        ]
        
        def search_sampler_params(obj, path=""):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    current_path = f"{path}.{key}" if path else key
                    
                    # 检查是否是采样器参数
                    if key.lower() in [k.lower() for k in sampler_keys]:
                        sampler_info[key] = value
                    
                    # 递归搜索
                    if isinstance(value, (dict, list)):
                        search_sampler_params(value, current_path)
            
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    current_path = f"{path}[{i}]" if path else f"[{i}]"
                    search_sampler_params(item, current_path)
        
        search_sampler_params(prompt)
        return sampler_info
    
    def _save_single_job(self, json_path: str, job_data: Dict[str, Any]):
        """保存单个作业数据"""
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(job_data, f, indent=2, ensure_ascii=False)
    
    def _append_to_jobs_file(self, json_path: str, job_data: Dict[str, Any], filename: str):
        """追加到作业文件"""
        # 读取现有数据
        jobs_data = []
        if os.path.exists(json_path):
            try:
                with open(json_path, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
                    if isinstance(existing_data, list):
                        jobs_data = existing_data
                    elif isinstance(existing_data, dict):
                        jobs_data = [existing_data]
            except (json.JSONDecodeError, IOError):
                # 如果文件损坏，从空列表开始
                jobs_data = []
        
        # 添加新的作业数据
        job_entry = {
            'filename': filename,
            **job_data
        }
        jobs_data.append(job_entry)
        
        # 保存更新后的数据
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(jobs_data, f, indent=2, ensure_ascii=False)
    
    def export_batch_summary(self, output_path: str, batch_info: Dict[str, Any]):
        """
        导出批量处理摘要
        
        Args:
            output_path: 输出路径
            batch_info: 批量信息
        """
        try:
            summary_path = os.path.join(output_path, "batch_summary.json")
            
            with open(summary_path, 'w', encoding='utf-8') as f:
                json.dump(batch_info, f, indent=2, ensure_ascii=False)
        
        except Exception as e:
            print(f"批量摘要导出错误: {e}")
    
    def cleanup_old_jobs(self, output_path: str, max_files: int = 100):
        """
        清理旧的作业文件
        
        Args:
            output_path: 输出路径
            max_files: 最大保留文件数
        """
        try:
            json_files = []
            for file in os.listdir(output_path):
                if file.endswith('.json') and file != 'jobs.json':
                    file_path = os.path.join(output_path, file)
                    stat = os.stat(file_path)
                    json_files.append((file_path, stat.st_mtime))
            
            # 按修改时间排序
            json_files.sort(key=lambda x: x[1], reverse=True)
            
            # 删除超出限制的文件
            for file_path, _ in json_files[max_files:]:
                try:
                    os.remove(file_path)
                except OSError:
                    pass
        
        except Exception as e:
            print(f"清理旧作业文件错误: {e}")
    
    def get_export_stats(self, output_path: str) -> Dict[str, Any]:
        """获取导出统计信息"""
        try:
            json_files = [f for f in os.listdir(output_path) if f.endswith('.json')]
            
            return {
                'total_job_files': len(json_files),
                'has_jobs_file': 'jobs.json' in json_files,
                'individual_files': len([f for f in json_files if f != 'jobs.json'])
            }
        
        except Exception:
            return {
                'total_job_files': 0,
                'has_jobs_file': False,
                'individual_files': 0
            }
