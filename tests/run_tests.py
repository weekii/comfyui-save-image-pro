"""
测试运行器

运行所有单元测试并生成报告。
"""

import unittest
import sys
import os
from io import StringIO

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def run_all_tests():
    """运行所有测试"""
    # 发现并加载所有测试
    loader = unittest.TestLoader()
    start_dir = os.path.dirname(os.path.abspath(__file__))
    suite = loader.discover(start_dir, pattern='test_*.py')
    
    # 创建测试运行器
    stream = StringIO()
    runner = unittest.TextTestRunner(
        stream=stream,
        verbosity=2,
        descriptions=True,
        failfast=False
    )
    
    # 运行测试
    print("=" * 70)
    print("Save Image Extended - 单元测试")
    print("=" * 70)
    
    result = runner.run(suite)
    
    # 输出结果
    output = stream.getvalue()
    print(output)
    
    # 生成摘要
    print("\n" + "=" * 70)
    print("测试摘要")
    print("=" * 70)
    print(f"运行测试数: {result.testsRun}")
    print(f"失败数: {len(result.failures)}")
    print(f"错误数: {len(result.errors)}")
    print(f"跳过数: {len(result.skipped)}")
    
    if result.failures:
        print(f"\n失败的测试:")
        for test, traceback in result.failures:
            print(f"  - {test}")
    
    if result.errors:
        print(f"\n错误的测试:")
        for test, traceback in result.errors:
            print(f"  - {test}")
    
    # 计算成功率
    if result.testsRun > 0:
        success_rate = ((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun) * 100
        print(f"\n成功率: {success_rate:.1f}%")
    
    print("=" * 70)
    
    return result.wasSuccessful()


def run_specific_test(test_module):
    """运行特定测试模块"""
    try:
        # 导入测试模块
        module = __import__(f'test_{test_module}', fromlist=[''])
        
        # 创建测试套件
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromModule(module)
        
        # 运行测试
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        
        return result.wasSuccessful()
    
    except ImportError as e:
        print(f"无法导入测试模块 'test_{test_module}': {e}")
        return False


if __name__ == '__main__':
    if len(sys.argv) > 1:
        # 运行特定测试
        test_name = sys.argv[1]
        success = run_specific_test(test_name)
    else:
        # 运行所有测试
        success = run_all_tests()
    
    # 设置退出代码
    sys.exit(0 if success else 1)
