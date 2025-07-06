"""
文件名生成器模块测试
"""

import unittest
from datetime import datetime
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config import SaveConfig
from core.filename_generator import FileNameGenerator, ParameterExtractor


class TestParameterExtractor(unittest.TestCase):
    """ParameterExtractor测试类"""
    
    def setUp(self):
        """设置测试环境"""
        self.extractor = ParameterExtractor()
        self.sample_prompt = {
            "1": {
                "inputs": {
                    "sampler_name": "euler",
                    "steps": 20,
                    "cfg": 7.5
                }
            },
            "5": {
                "inputs": {
                    "seed": 12345,
                    "ckpt_name": "sd_xl_base.safetensors"
                }
            }
        }
    
    def test_find_parameter_values(self):
        """测试查找参数值"""
        keys = ["sampler_name", "steps", "cfg"]
        result = self.extractor.find_parameter_values(self.sample_prompt, keys)
        
        self.assertEqual(result["sampler_name"], "euler")
        self.assertEqual(result["steps"], "20")
        self.assertEqual(result["cfg"], "7.5")
    
    def test_extract_node_reference(self):
        """测试提取节点引用"""
        keys = ["5.seed", "5.ckpt_name"]
        result = self.extractor.find_parameter_values(self.sample_prompt, keys)
        
        self.assertEqual(result["5.seed"], "12345")
        self.assertEqual(result["5.ckpt_name"], "sd_xl_base.safetensors")
    
    def test_extract_time_format(self):
        """测试提取时间格式"""
        keys = ["%Y", "%m", "%d"]
        result = self.extractor.find_parameter_values({}, keys)
        
        now = datetime.now()
        self.assertEqual(result["%Y"], str(now.year))
        self.assertEqual(result["%m"], f"{now.month:02d}")
        self.assertEqual(result["%d"], f"{now.day:02d}")
    
    def test_cache_functionality(self):
        """测试缓存功能"""
        keys = ["sampler_name"]
        
        # 第一次调用
        result1 = self.extractor.find_parameter_values(self.sample_prompt, keys)
        
        # 第二次调用应该使用缓存
        result2 = self.extractor.find_parameter_values(self.sample_prompt, keys)
        
        self.assertEqual(result1, result2)
    
    def test_clear_cache(self):
        """测试清空缓存"""
        keys = ["sampler_name"]
        self.extractor.find_parameter_values(self.sample_prompt, keys)
        
        # 确保缓存有内容
        self.assertTrue(len(self.extractor.cache) > 0)
        
        # 清空缓存
        self.extractor.clear_cache()
        self.assertEqual(len(self.extractor.cache), 0)


class TestFileNameGenerator(unittest.TestCase):
    """FileNameGenerator测试类"""
    
    def setUp(self):
        """设置测试环境"""
        self.config = SaveConfig(
            filename_prefix="Test",
            filename_keys="sampler_name, steps",
            foldername_prefix="Folder",
            foldername_keys="ckpt_name",
            delimiter="_"
        )
        self.generator = FileNameGenerator(self.config)
        self.sample_prompt = {
            "1": {
                "inputs": {
                    "sampler_name": "euler",
                    "steps": 20
                }
            },
            "5": {
                "inputs": {
                    "ckpt_name": "sd_xl_base.safetensors"
                }
            }
        }
    
    def test_generate_filename(self):
        """测试生成文件名"""
        timestamp = datetime(2024, 1, 1, 12, 0, 0)
        filename = self.generator.generate_filename(self.sample_prompt, timestamp)
        
        self.assertIn("Test", filename)
        self.assertIn("euler", filename)
        self.assertIn("20", filename)
        self.assertIn("_", filename)  # 分隔符
    
    def test_generate_foldername(self):
        """测试生成文件夹名"""
        timestamp = datetime(2024, 1, 1, 12, 0, 0)
        foldername = self.generator.generate_foldername(self.sample_prompt, timestamp)
        
        self.assertIn("Folder", foldername)
        self.assertIn("sd_xl_base.safetensors", foldername)
    
    def test_generate_full_filename(self):
        """测试生成完整文件名"""
        timestamp = datetime(2024, 1, 1, 12, 0, 0)
        full_filename = self.generator.generate_full_filename(
            self.sample_prompt, 1, timestamp
        )
        
        self.assertTrue(full_filename.endswith(".webp"))
        self.assertIn("0001", full_filename)  # 计数器
    
    def test_clean_filename(self):
        """测试清理文件名"""
        dirty_name = "test<>:|?*file"
        clean_name = self.generator._clean_filename(dirty_name)
        
        # 应该移除或替换无效字符
        invalid_chars = '<>:|?*'
        for char in invalid_chars:
            self.assertNotIn(char, clean_name)
    
    def test_counter_position_last(self):
        """测试计数器位置在最后"""
        config = SaveConfig(counter_position="last")
        generator = FileNameGenerator(config)
        
        timestamp = datetime(2024, 1, 1, 12, 0, 0)
        filename = generator.generate_full_filename({}, 42, timestamp)
        
        self.assertTrue(filename.endswith("0042.webp"))
    
    def test_counter_position_first(self):
        """测试计数器位置在开头"""
        config = SaveConfig(counter_position="first")
        generator = FileNameGenerator(config)
        
        timestamp = datetime(2024, 1, 1, 12, 0, 0)
        filename = generator.generate_full_filename({}, 42, timestamp)
        
        self.assertTrue(filename.startswith("0042"))
    
    def test_preview_names(self):
        """测试预览名称"""
        timestamp = datetime(2024, 1, 1, 12, 0, 0)
        filename, foldername = self.generator.preview_names(
            self.sample_prompt, 1, timestamp
        )
        
        self.assertIsInstance(filename, str)
        self.assertIsInstance(foldername, str)
        self.assertTrue(len(filename) > 0)
    
    def test_cache_functionality(self):
        """测试缓存功能"""
        timestamp = datetime(2024, 1, 1, 12, 0, 0)
        
        # 第一次生成
        filename1 = self.generator.generate_filename(self.sample_prompt, timestamp)
        
        # 第二次生成应该使用缓存
        filename2 = self.generator.generate_filename(self.sample_prompt, timestamp)
        
        self.assertEqual(filename1, filename2)
    
    def test_clear_cache(self):
        """测试清空缓存"""
        timestamp = datetime(2024, 1, 1, 12, 0, 0)
        self.generator.generate_filename(self.sample_prompt, timestamp)
        
        # 清空缓存
        self.generator.clear_cache()
        
        # 缓存应该被清空
        self.assertEqual(len(self.generator.extractor.cache), 0)


if __name__ == '__main__':
    unittest.main()
