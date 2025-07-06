"""
性能优化模块

提供批量处理、缓存管理和性能监控功能。
"""

import time
import threading
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
import psutil
import gc


class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self):
        self.metrics = {}
        self.start_times = {}
        self.lock = threading.Lock()
    
    def start_timer(self, operation: str):
        """开始计时"""
        with self.lock:
            self.start_times[operation] = time.time()
    
    def end_timer(self, operation: str) -> float:
        """结束计时并返回耗时"""
        with self.lock:
            if operation in self.start_times:
                duration = time.time() - self.start_times[operation]
                
                if operation not in self.metrics:
                    self.metrics[operation] = {
                        'count': 0,
                        'total_time': 0,
                        'min_time': float('inf'),
                        'max_time': 0,
                        'avg_time': 0
                    }
                
                metrics = self.metrics[operation]
                metrics['count'] += 1
                metrics['total_time'] += duration
                metrics['min_time'] = min(metrics['min_time'], duration)
                metrics['max_time'] = max(metrics['max_time'], duration)
                metrics['avg_time'] = metrics['total_time'] / metrics['count']
                
                del self.start_times[operation]
                return duration
            
            return 0.0
    
    def get_metrics(self) -> Dict[str, Any]:
        """获取性能指标"""
        with self.lock:
            return self.metrics.copy()
    
    def reset_metrics(self):
        """重置性能指标"""
        with self.lock:
            self.metrics.clear()
            self.start_times.clear()


class CacheManager:
    """缓存管理器"""
    
    def __init__(self, max_size: int = 1000, ttl_seconds: int = 3600):
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.cache = {}
        self.access_times = {}
        self.lock = threading.Lock()
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        with self.lock:
            if key in self.cache:
                # 检查是否过期
                if self._is_expired(key):
                    self._remove(key)
                    return None
                
                # 更新访问时间
                self.access_times[key] = datetime.now()
                return self.cache[key]
            
            return None
    
    def set(self, key: str, value: Any):
        """设置缓存值"""
        with self.lock:
            # 如果缓存已满，移除最旧的项
            if len(self.cache) >= self.max_size and key not in self.cache:
                self._evict_oldest()
            
            self.cache[key] = value
            self.access_times[key] = datetime.now()
    
    def remove(self, key: str):
        """移除缓存项"""
        with self.lock:
            self._remove(key)
    
    def clear(self):
        """清空缓存"""
        with self.lock:
            self.cache.clear()
            self.access_times.clear()
    
    def _is_expired(self, key: str) -> bool:
        """检查缓存项是否过期"""
        if key not in self.access_times:
            return True
        
        age = datetime.now() - self.access_times[key]
        return age.total_seconds() > self.ttl_seconds
    
    def _remove(self, key: str):
        """移除缓存项（内部方法）"""
        if key in self.cache:
            del self.cache[key]
        if key in self.access_times:
            del self.access_times[key]
    
    def _evict_oldest(self):
        """移除最旧的缓存项"""
        if not self.access_times:
            return
        
        oldest_key = min(self.access_times.keys(), 
                        key=lambda k: self.access_times[k])
        self._remove(oldest_key)
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        with self.lock:
            return {
                'size': len(self.cache),
                'max_size': self.max_size,
                'ttl_seconds': self.ttl_seconds,
                'usage_ratio': len(self.cache) / self.max_size if self.max_size > 0 else 0
            }


class BatchProcessor:
    """批量处理器"""
    
    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self.monitor = PerformanceMonitor()
    
    def process_batch(self, items: List[Any], processor_func: Callable, 
                     **kwargs) -> List[Any]:
        """
        批量处理项目
        
        Args:
            items: 要处理的项目列表
            processor_func: 处理函数
            **kwargs: 传递给处理函数的额外参数
            
        Returns:
            处理结果列表
        """
        if not items:
            return []
        
        self.monitor.start_timer('batch_processing')
        
        try:
            # 单线程处理小批量
            if len(items) <= 2:
                results = []
                for item in items:
                    result = processor_func(item, **kwargs)
                    results.append(result)
                return results
            
            # 多线程处理大批量
            results = [None] * len(items)
            
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # 提交任务
                future_to_index = {}
                for i, item in enumerate(items):
                    future = executor.submit(processor_func, item, **kwargs)
                    future_to_index[future] = i
                
                # 收集结果
                for future in as_completed(future_to_index):
                    index = future_to_index[future]
                    try:
                        results[index] = future.result()
                    except Exception as e:
                        print(f"批量处理项目 {index} 时发生错误: {e}")
                        results[index] = None
            
            return results
        
        finally:
            self.monitor.end_timer('batch_processing')
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """获取性能指标"""
        return self.monitor.get_metrics()


class MemoryManager:
    """内存管理器"""
    
    def __init__(self, memory_threshold: float = 0.8):
        self.memory_threshold = memory_threshold
    
    def check_memory_usage(self) -> Dict[str, Any]:
        """检查内存使用情况"""
        memory = psutil.virtual_memory()
        
        return {
            'total': memory.total,
            'available': memory.available,
            'used': memory.used,
            'percentage': memory.percent,
            'threshold_exceeded': memory.percent / 100 > self.memory_threshold
        }
    
    def cleanup_if_needed(self) -> bool:
        """如果需要则清理内存"""
        memory_info = self.check_memory_usage()
        
        if memory_info['threshold_exceeded']:
            # 强制垃圾回收
            gc.collect()
            return True
        
        return False
    
    def get_process_memory(self) -> Dict[str, Any]:
        """获取当前进程内存信息"""
        process = psutil.Process()
        memory_info = process.memory_info()
        
        return {
            'rss': memory_info.rss,  # 物理内存
            'vms': memory_info.vms,  # 虚拟内存
            'percent': process.memory_percent()
        }


class PerformanceOptimizer:
    """性能优化器主类"""
    
    def __init__(self, cache_size: int = 1000, max_workers: int = 4):
        self.cache_manager = CacheManager(max_size=cache_size)
        self.batch_processor = BatchProcessor(max_workers=max_workers)
        self.memory_manager = MemoryManager()
        self.monitor = PerformanceMonitor()
    
    def optimize_operation(self, operation_name: str, operation_func: Callable, 
                          *args, use_cache: bool = True, cache_key: Optional[str] = None,
                          **kwargs) -> Any:
        """
        优化操作执行
        
        Args:
            operation_name: 操作名称
            operation_func: 操作函数
            use_cache: 是否使用缓存
            cache_key: 缓存键（如果不提供则自动生成）
            *args, **kwargs: 传递给操作函数的参数
            
        Returns:
            操作结果
        """
        self.monitor.start_timer(operation_name)
        
        try:
            # 尝试从缓存获取结果
            if use_cache:
                if cache_key is None:
                    cache_key = f"{operation_name}_{hash(str(args) + str(kwargs))}"
                
                cached_result = self.cache_manager.get(cache_key)
                if cached_result is not None:
                    return cached_result
            
            # 检查内存使用情况
            self.memory_manager.cleanup_if_needed()
            
            # 执行操作
            result = operation_func(*args, **kwargs)
            
            # 缓存结果
            if use_cache and result is not None:
                self.cache_manager.set(cache_key, result)
            
            return result
        
        finally:
            self.monitor.end_timer(operation_name)
    
    def get_performance_report(self) -> Dict[str, Any]:
        """获取性能报告"""
        return {
            'cache_stats': self.cache_manager.get_stats(),
            'batch_metrics': self.batch_processor.get_performance_metrics(),
            'memory_info': self.memory_manager.check_memory_usage(),
            'process_memory': self.memory_manager.get_process_memory(),
            'operation_metrics': self.monitor.get_metrics()
        }
    
    def clear_all_caches(self):
        """清空所有缓存"""
        self.cache_manager.clear()
        self.monitor.reset_metrics()
    
    def set_cache_size(self, size: int):
        """设置缓存大小"""
        self.cache_manager.max_size = size
    
    def set_max_workers(self, workers: int):
        """设置最大工作线程数"""
        self.batch_processor.max_workers = workers
