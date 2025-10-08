#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图片管理器单元测试
"""

import unittest
import tempfile
import shutil
from pathlib import Path
from PIL import Image
import sys
import os

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 尝试导入PyQt5，如果失败则跳过相关测试
try:
    from PyQt5.QtCore import QCoreApplication
    from photo_watermark_gui.core.image_manager import ImageManager, ImageInfo
    PYQT_AVAILABLE = True
except ImportError:
    PYQT_AVAILABLE = False


@unittest.skipUnless(PYQT_AVAILABLE, "PyQt5 not available")
class TestImageInfo(unittest.TestCase):
    """图片信息类测试"""
    
    def setUp(self):
        """测试前准备"""
        self.test_dir = Path(tempfile.mkdtemp())
        self.test_image_path = self.test_dir / "test_image.jpg"
        
        # 创建测试图片
        test_img = Image.new('RGB', (100, 100), color='red')
        test_img.save(self.test_image_path, 'JPEG')
    
    def tearDown(self):
        """测试后清理"""
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_image_info_creation(self):
        """测试图片信息对象创建"""
        img_info = ImageInfo(str(self.test_image_path))
        
        self.assertEqual(img_info.name, "test_image.jpg")
        self.assertGreater(img_info.size, 0)
        self.assertFalse(img_info.is_loaded)
        self.assertIsNone(img_info.dimensions)
    
    def test_load_info(self):
        """测试加载图片信息"""
        img_info = ImageInfo(str(self.test_image_path))
        
        success = img_info.load_info()
        
        self.assertTrue(success)
        self.assertTrue(img_info.is_loaded)
        self.assertEqual(img_info.dimensions, (100, 100))
    
    def test_load_info_invalid_file(self):
        """测试加载无效文件"""
        img_info = ImageInfo(str(self.test_dir / "nonexistent.jpg"))
        
        success = img_info.load_info()
        
        self.assertFalse(success)
        self.assertFalse(img_info.is_loaded)
    
    def test_size_mb(self):
        """测试文件大小计算"""
        img_info = ImageInfo(str(self.test_image_path))
        
        size_mb = img_info.size_mb
        
        self.assertGreater(size_mb, 0)
        self.assertLess(size_mb, 1)  # 测试图片应该小于1MB


@unittest.skipUnless(PYQT_AVAILABLE, "PyQt5 not available")
class TestImageManager(unittest.TestCase):
    """图片管理器测试"""
    
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
        self.manager = ImageManager()
        
        # 创建测试图片
        self.test_images = []
        for i in range(3):
            img_path = self.test_dir / f"test_{i}.jpg"
            test_img = Image.new('RGB', (100, 100), color=['red', 'green', 'blue'][i])
            test_img.save(img_path, 'JPEG')
            self.test_images.append(str(img_path))
        
        # 创建不支持的文件
        unsupported_path = self.test_dir / "test.txt"
        unsupported_path.write_text("not an image")
        self.unsupported_file = str(unsupported_path)
    
    def tearDown(self):
        """测试后清理"""
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_manager_initialization(self):
        """测试管理器初始化"""
        self.assertEqual(self.manager.image_count, 0)
        self.assertTrue(self.manager.is_empty)
        self.assertEqual(self.manager.current_index, -1)
    
    def test_add_images(self):
        """测试添加图片"""
        added = self.manager.add_images(self.test_images)
        
        self.assertEqual(len(added), 3)
        self.assertEqual(self.manager.image_count, 3)
        self.assertFalse(self.manager.is_empty)
    
    def test_add_duplicate_images(self):
        """测试添加重复图片"""
        self.manager.add_images([self.test_images[0]])
        added = self.manager.add_images([self.test_images[0]])  # 重复添加
        
        self.assertEqual(len(added), 0)
        self.assertEqual(self.manager.image_count, 1)
    
    def test_add_unsupported_file(self):
        """测试添加不支持的文件"""
        added = self.manager.add_images([self.unsupported_file])
        
        self.assertEqual(len(added), 0)
        self.assertEqual(self.manager.image_count, 0)
    
    def test_is_supported_format(self):
        """测试格式支持检查"""
        self.assertTrue(self.manager.is_supported_format("test.jpg"))
        self.assertTrue(self.manager.is_supported_format("test.PNG"))
        self.assertFalse(self.manager.is_supported_format("test.txt"))
        self.assertFalse(self.manager.is_supported_format("test.gif"))
    
    def test_remove_image(self):
        """测试移除图片"""
        self.manager.add_images(self.test_images)
        
        success = self.manager.remove_image(1)
        
        self.assertTrue(success)
        self.assertEqual(self.manager.image_count, 2)
    
    def test_remove_invalid_index(self):
        """测试移除无效索引"""
        self.manager.add_images(self.test_images)
        
        success = self.manager.remove_image(10)
        
        self.assertFalse(success)
        self.assertEqual(self.manager.image_count, 3)
    
    def test_clear_images(self):
        """测试清空图片"""
        self.manager.add_images(self.test_images)
        
        self.manager.clear_images()
        
        self.assertEqual(self.manager.image_count, 0)
        self.assertTrue(self.manager.is_empty)
        self.assertEqual(self.manager.current_index, -1)
    
    def test_set_current_index(self):
        """测试设置当前索引"""
        self.manager.add_images(self.test_images)
        
        success = self.manager.set_current_index(1)
        
        self.assertTrue(success)
        self.assertEqual(self.manager.current_index, 1)
    
    def test_get_current_image(self):
        """测试获取当前图片"""
        self.manager.add_images(self.test_images)
        self.manager.set_current_index(0)
        
        current = self.manager.get_current_image()
        
        self.assertIsNotNone(current)
        self.assertEqual(current.name, "test_0.jpg")
    
    def test_get_statistics(self):
        """测试获取统计信息"""
        stats = self.manager.get_statistics()
        self.assertEqual(stats['count'], 0)
        
        self.manager.add_images(self.test_images)
        stats = self.manager.get_statistics()
        
        self.assertEqual(stats['count'], 3)
        self.assertGreater(stats['total_size_mb'], 0)
        self.assertIn('.jpg', stats['formats'])
    
    def test_add_directory(self):
        """测试添加目录"""
        added = self.manager.add_directory(str(self.test_dir))
        
        self.assertEqual(len(added), 3)
        self.assertEqual(self.manager.image_count, 3)


if __name__ == '__main__':
    unittest.main()