#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置管理器单元测试
"""

import unittest
import tempfile
import shutil
import json
from pathlib import Path
import sys

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 尝试导入PyQt5，如果失败则跳过相关测试
try:
    from PyQt5.QtCore import QCoreApplication
    from photo_watermark_gui.core.config_manager import ConfigManager
    PYQT_AVAILABLE = True
except ImportError:
    PYQT_AVAILABLE = False


@unittest.skipUnless(PYQT_AVAILABLE, "PyQt5 not available")
class TestConfigManager(unittest.TestCase):
    """配置管理器测试"""
    
    @classmethod
    def setUpClass(cls):
        """类级别设置 - 创建QApplication"""
        if not QCoreApplication.instance():
            cls.app = QCoreApplication([])
        else:
            cls.app = QCoreApplication.instance()
    
    def setUp(self):
        """测试前准备"""
        self.test_dir = Path(tempfile.mkdtemp())
        self.manager = ConfigManager()
        
        # 使用临时文件路径
        self.manager.config_path = self.test_dir / "test_config.json"
        self.manager.templates_path = self.test_dir / "test_templates.json"
    
    def tearDown(self):
        """测试后清理"""
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_manager_initialization(self):
        """测试管理器初始化"""
        self.assertIsNotNone(self.manager.default_config)
        self.assertIn('watermark', self.manager.default_config)
        self.assertIn('export', self.manager.default_config)
        self.assertIn('ui', self.manager.default_config)
    
    def test_load_config_no_file(self):
        """测试加载不存在的配置文件"""
        config = self.manager.load_config()  
        
        # 应该返回默认配置
        self.assertEqual(config, self.manager.default_config)
    
    def test_save_and_load_config(self):
        """测试保存和加载配置"""
        # 修改配置
        self.manager.set_config('watermark', 'text', 'Test Text')
        self.manager.set_config('export', 'output_format', 'PNG')
        
        # 保存配置
        success = self.manager.save_config()
        self.assertTrue(success)
        self.assertTrue(self.manager.config_path.exists())
        
        # 创建新的管理器并加载配置
        new_manager = ConfigManager()
        new_manager.config_path = self.manager.config_path
        new_manager.templates_path = self.manager.templates_path
        
        loaded_config = new_manager.load_config()
        
        self.assertEqual(loaded_config['watermark']['text'], 'Test Text')
        self.assertEqual(loaded_config['export']['output_format'], 'PNG')
    
    def test_get_config(self):
        """测试获取配置"""
        # 获取整个section
        watermark_config = self.manager.get_config('watermark')
        self.assertIsInstance(watermark_config, dict)
        
        # 获取特定key
        font_size = self.manager.get_config('watermark', 'font_size')
        self.assertEqual(font_size, 36)
        
        # 获取不存在的key，使用默认值
        nonexistent = self.manager.get_config('watermark', 'nonexistent', 'default')
        self.assertEqual(nonexistent, 'default')
    
    def test_set_config(self):
        """测试设置配置"""
        # 设置特定key
        self.manager.set_config('watermark', 'text', 'New Text')
        self.assertEqual(self.manager.current_config['watermark']['text'], 'New Text')
        
        # 设置整个section
        new_section = {'key1': 'value1', 'key2': 'value2'}
        self.manager.set_config('new_section', value=new_section)
        self.assertEqual(self.manager.current_config['new_section'], new_section)
    
    def test_template_operations(self):
        """测试模板操作"""
        template_data = {
            'text': 'Template Text',
            'font_size': 48,
            'color': 'blue'
        }
        
        # 添加模板
        success = self.manager.add_template('test_template', template_data)
        self.assertTrue(success)
        
        # 获取模板
        retrieved = self.manager.get_template('test_template')
        self.assertEqual(retrieved['text'], 'Template Text')
        
        # 获取模板列表
        template_list = self.manager.get_template_list()
        self.assertEqual(len(template_list), 1)
        self.assertEqual(template_list[0]['name'], 'test_template')
        
        # 删除模板
        success = self.manager.remove_template('test_template')
        self.assertTrue(success)
        
        # 确认模板已删除
        retrieved = self.manager.get_template('test_template')
        self.assertIsNone(retrieved)
    
    def test_recent_directories(self):
        """测试最近使用目录"""
        # 添加最近目录
        self.manager.add_recent_directory('/path/to/dir1')
        self.manager.add_recent_directory('/path/to/dir2')
        
        recent = self.manager.get_recent_directories()
        self.assertEqual(len(recent), 2)
        self.assertEqual(recent[0], '/path/to/dir2')  # 最新的在前面
        
        # 添加重复目录
        self.manager.add_recent_directory('/path/to/dir1')
        recent = self.manager.get_recent_directories()
        self.assertEqual(len(recent), 2)
        self.assertEqual(recent[0], '/path/to/dir1')  # 重复的移到前面
    
    def test_reset_to_defaults(self):
        """测试重置为默认配置"""
        # 修改配置
        self.manager.set_config('watermark', 'text', 'Modified')
        self.assertEqual(self.manager.get_config('watermark', 'text'), 'Modified')
        
        # 重置特定section
        success = self.manager.reset_to_defaults('watermark')
        self.assertTrue(success)
        
        # 检查是否重置到默认值
        text = self.manager.get_config('watermark', 'text')
        self.assertEqual(text, '')  # 默认值应该是空字符串
    
    def test_export_import_config(self):
        """测试导出导入配置"""
        export_path = self.test_dir / "exported_config.json"
        
        # 修改配置
        self.manager.set_config('watermark', 'text', 'Export Test')
        
        # 添加模板
        template_data = {'text': 'Template'}
        self.manager.add_template('export_template', template_data)
        
        # 导出配置
        success = self.manager.export_config(str(export_path))
        self.assertTrue(success)
        self.assertTrue(export_path.exists())
        
        # 重置配置
        self.manager.reset_to_defaults()
        
        # 导入配置
        success = self.manager.import_config(str(export_path))
        self.assertTrue(success)
        
        # 检查是否正确导入
        text = self.manager.get_config('watermark', 'text')
        self.assertEqual(text, 'Export Test')
        
        template = self.manager.get_template('export_template')
        self.assertIsNotNone(template)
    
    def test_merge_configs(self):
        """测试配置合并"""
        default = {
            'section1': {'key1': 'default1', 'key2': 'default2'},
            'section2': {'key3': 'default3'}
        }
        
        loaded = {
            'section1': {'key1': 'loaded1'},  # 覆盖key1
            'section3': {'key4': 'loaded4'}   # 新增section3
        }
        
        result = self.manager._merge_configs(default, loaded)
        
        # 检查合并结果
        self.assertEqual(result['section1']['key1'], 'loaded1')  # 被覆盖
        self.assertEqual(result['section1']['key2'], 'default2')  # 保留默认
        self.assertEqual(result['section2']['key3'], 'default3')  # 保留默认
        self.assertEqual(result['section3']['key4'], 'loaded4')   # 新增
    
    def test_file_existence_properties(self):
        """测试文件存在性属性"""
        # 初始状态：文件不存在
        self.assertFalse(self.manager.config_file_exists)
        self.assertFalse(self.manager.templates_file_exists)
        
        # 保存后：文件存在
        self.manager.save_config()
        self.manager.save_templates()
        
        self.assertTrue(self.manager.config_file_exists)
        self.assertTrue(self.manager.templates_file_exists)


if __name__ == '__main__':
    unittest.main()