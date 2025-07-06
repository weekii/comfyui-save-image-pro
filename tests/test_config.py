"""
配置管理模块测试
"""

import unittest
from datetime import datetime
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config import SaveConfig, ConfigManager, ValidationResult


class TestSaveConfig(unittest.TestCase):
    """SaveConfig测试类"""
    
    def test_default_config(self):
        """测试默认配置"""
        config = SaveConfig()
        
        self.assertEqual(config.filename_prefix, "ComfyUI")
        self.assertEqual(config.output_format, ".webp")
        self.assertEqual(config.quality, 75)
        self.assertTrue(config.save_metadata)
        self.assertEqual(config.counter_digits, 4)
    
    def test_filename_keys_list(self):
        """测试文件名键值列表解析"""
        config = SaveConfig(filename_keys="sampler_name, cfg, steps")
        keys = config.get_filename_keys_list()
        
        self.assertEqual(keys, ["sampler_name", "cfg", "steps"])
    
    def test_foldername_keys_list(self):
        """测试文件夹名键值列表解析"""
        config = SaveConfig(foldername_keys="ckpt_name, model")
        keys = config.get_foldername_keys_list()
        
        self.assertEqual(keys, ["ckpt_name", "model"])


class TestConfigManager(unittest.TestCase):
    """ConfigManager测试类"""
    
    def setUp(self):
        """设置测试环境"""
        self.manager = ConfigManager()
    
    def test_get_preset_names(self):
        """测试获取预设名称"""
        presets = self.manager.get_preset_names()
        
        self.assertIn("基础配置", presets)
        self.assertIn("高级配置", presets)
        self.assertIn("专业配置", presets)
    
    def test_get_preset_config(self):
        """测试获取预设配置"""
        config = self.manager.get_preset_config("基础配置")
        
        self.assertIsInstance(config, SaveConfig)
        self.assertEqual(config.filename_prefix, "ComfyUI")
        self.assertEqual(config.output_format, ".webp")
    
    def test_validate_valid_config(self):
        """测试验证有效配置"""
        config = SaveConfig()
        result = self.manager.validate_config(config)
        
        self.assertTrue(result.valid)
        self.assertEqual(len(result.errors), 0)
    
    def test_validate_invalid_quality(self):
        """测试验证无效质量值"""
        config = SaveConfig(quality=150)  # 超出范围
        result = self.manager.validate_config(config)
        
        self.assertFalse(result.valid)
        self.assertTrue(any("质量" in error for error in result.errors))
    
    def test_validate_invalid_counter_digits(self):
        """测试验证无效计数器位数"""
        config = SaveConfig(counter_digits=0)  # 无效值
        result = self.manager.validate_config(config)
        
        self.assertFalse(result.valid)
        self.assertTrue(any("计数器位数" in error for error in result.errors))
    
    def test_validate_invalid_format(self):
        """测试验证无效格式"""
        config = SaveConfig(output_format=".invalid")
        result = self.manager.validate_config(config)
        
        self.assertFalse(result.valid)
        self.assertTrue(any("格式" in error for error in result.errors))
    
    def test_get_help_text(self):
        """测试获取帮助文本"""
        help_text = self.manager.get_help_text("filename_keys")
        
        self.assertIsInstance(help_text, str)
        self.assertTrue(len(help_text) > 0)
    
    def test_preview_filename(self):
        """测试预览文件名"""
        config = SaveConfig(
            filename_prefix="Test",
            filename_keys="sampler_name, steps",
            delimiter="_"
        )
        
        preview = self.manager.preview_filename(config)
        
        self.assertIsInstance(preview, str)
        self.assertTrue(preview.endswith(".webp"))


class TestValidationResult(unittest.TestCase):
    """ValidationResult测试类"""
    
    def test_initial_state(self):
        """测试初始状态"""
        result = ValidationResult(valid=True)
        
        self.assertTrue(result.valid)
        self.assertEqual(len(result.errors), 0)
        self.assertEqual(len(result.warnings), 0)
    
    def test_add_error(self):
        """测试添加错误"""
        result = ValidationResult(valid=True)
        result.add_error("测试错误")
        
        self.assertFalse(result.valid)
        self.assertEqual(len(result.errors), 1)
        self.assertEqual(result.errors[0], "测试错误")
    
    def test_add_warning(self):
        """测试添加警告"""
        result = ValidationResult(valid=True)
        result.add_warning("测试警告")
        
        self.assertTrue(result.valid)  # 警告不影响有效性
        self.assertEqual(len(result.warnings), 1)
        self.assertEqual(result.warnings[0], "测试警告")


if __name__ == '__main__':
    unittest.main()
