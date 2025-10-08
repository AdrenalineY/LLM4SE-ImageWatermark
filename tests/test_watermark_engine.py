#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
水印引擎单元测试
"""

import unittest
import tempfile
import shutil
from pathlib import Path
from PIL import Image
import sys

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 尝试导入PyQt5，如果失败则跳过相关测试
try:
    from PyQt5.QtCore import QCoreApplication
    from photo_watermark_gui.core.watermark_engine import WatermarkEngine, WatermarkSettings
    PYQT_AVAILABLE = True
except ImportError:
    PYQT_AVAILABLE = False


class TestWatermarkSettings(unittest.TestCase):
    """水印设置类测试"""
    
    def test_settings_initialization(self):
        """测试设置初始化"""
        settings = WatermarkSettings()
        
        self.assertEqual(settings.text, "")
        self.assertEqual(settings.font_size, 36)
        self.assertEqual(settings.color, "white")
        self.assertEqual(settings.opacity, 100)
        self.assertEqual(settings.position, "bottom-right")
    
    def test_to_dict(self):
        """测试转换为字典"""
        settings = WatermarkSettings()
        settings.text = "Test Text"
        settings.font_size = 48
        
        data = settings.to_dict()
        
        self.assertIsInstance(data, dict)
        self.assertEqual(data['text'], "Test Text")
        self.assertEqual(data['font_size'], 48)
    
    def test_from_dict(self):
        """测试从字典加载"""
        settings = WatermarkSettings()
        data = {
            'text': 'New Text',
            'font_size': 24,
            'color': 'red',
            'opacity': 80
        }
        
        settings.from_dict(data)
        
        self.assertEqual(settings.text, 'New Text')
        self.assertEqual(settings.font_size, 24)
        self.assertEqual(settings.color, 'red')
        self.assertEqual(settings.opacity, 80)


@unittest.skipUnless(PYQT_AVAILABLE, "PyQt5 not available")
class TestWatermarkEngine(unittest.TestCase):
    """水印引擎测试"""
    
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
        self.engine = WatermarkEngine()
        
        # 创建测试图片
        self.test_image_path = self.test_dir / "test_image.jpg"
        test_img = Image.new('RGB', (200, 150), color='white')
        test_img.save(self.test_image_path, 'JPEG')
        
        # 创建测试设置
        self.test_settings = WatermarkSettings()
        self.test_settings.text = "Test Watermark"
        self.test_settings.font_size = 24
        self.test_settings.color = "black"
        self.test_settings.opacity = 100
        self.test_settings.position = "center"
    
    def tearDown(self):
        """测试后清理"""
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_engine_initialization(self):
        """测试引擎初始化"""
        self.assertIsNotNone(self.engine.base_watermarker)
        self.assertIsNotNone(self.engine.current_settings)
    
    def test_apply_preview_watermark(self):
        """测试应用预览水印"""
        result = self.engine.apply_preview_watermark(
            str(self.test_image_path), 
            self.test_settings
        )
        
        self.assertIsNotNone(result)
        self.assertIsInstance(result, Image.Image)
        self.assertEqual(result.size, (200, 150))
    
    def test_apply_preview_watermark_empty_text(self):
        """测试空文本水印"""
        empty_settings = WatermarkSettings()
        empty_settings.text = ""
        
        result = self.engine.apply_preview_watermark(
            str(self.test_image_path), 
            empty_settings
        )
        
        self.assertIsNotNone(result)
        # 空文本应该返回原图
    
    def test_apply_preview_watermark_invalid_file(self):
        """测试无效文件"""
        result = self.engine.apply_preview_watermark(
            str(self.test_dir / "nonexistent.jpg"), 
            self.test_settings
        )
        
        self.assertIsNone(result)
    
    def test_parse_color_hex(self):
        """测试十六进制颜色解析"""
        color = self.engine._parse_color("#FF0000", 100)
        
        self.assertEqual(color, (255, 0, 0, 255))
    
    def test_parse_color_named(self):
        """测试命名颜色解析"""
        color = self.engine._parse_color("red", 50)
        
        self.assertEqual(color, (255, 0, 0, 127))  # 50% opacity
    
    def test_calculate_text_position_center(self):
        """测试文本位置计算 - 居中"""
        position = self.engine._calculate_text_position(
            (200, 150), (50, 20), "center"
        )
        
        # 居中位置应该是 ((200-50)/2, (150-20)/2) = (75, 65)
        self.assertEqual(position, (75, 65))
    
    def test_calculate_text_position_top_left(self):
        """测试文本位置计算 - 左上角"""
        position = self.engine._calculate_text_position(
            (200, 150), (50, 20), "top-left", margin=10
        )
        
        self.assertEqual(position, (10, 10))
    
    def test_update_settings(self):
        """测试更新设置"""
        new_settings = WatermarkSettings()
        new_settings.text = "Updated Text"
        
        self.engine.update_settings(new_settings)
        
        self.assertEqual(self.engine.current_settings.text, "Updated Text")


if __name__ == '__main__':
    unittest.main()