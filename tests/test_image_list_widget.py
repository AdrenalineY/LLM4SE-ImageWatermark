#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图片列表组件测试
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
    from PyQt5.QtWidgets import QApplication
    from PyQt5.QtCore import QTimer, Qt, QMimeData, QUrl
    from PyQt5.QtTest import QTest
    from PyQt5.QtGui import QDragEnterEvent, QDropEvent
    from photo_watermark_gui.ui.image_list_widget import ImageListWidget, ImageListItem
    PYQT_AVAILABLE = True
except ImportError:
    PYQT_AVAILABLE = False


@unittest.skipUnless(PYQT_AVAILABLE, "PyQt5 not available")
class TestImageListWidget(unittest.TestCase):
    """图片列表组件测试"""
    
    @classmethod
    def setUpClass(cls):
        """类级别设置"""
        if not QApplication.instance():
            cls.app = QApplication([])
        else:
            cls.app = QApplication.instance()
    
    def setUp(self):
        """测试前准备"""
        self.test_dir = Path(tempfile.mkdtemp())
        
        # 创建测试图片
        self.test_images = []
        for i in range(3):
            img_path = self.test_dir / f"test_{i}.jpg"
            test_img = Image.new('RGB', (100, 100), color=['red', 'green', 'blue'][i])
            test_img.save(img_path, 'JPEG')
            self.test_images.append(str(img_path))
        
        # 创建组件
        self.widget = ImageListWidget()
    
    def tearDown(self):
        """测试后清理"""
        if self.widget:
            self.widget.close()
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_widget_initialization(self):
        """测试组件初始化"""
        self.assertIsNotNone(self.widget)
        self.assertEqual(self.widget.count(), 0)
        self.assertEqual(len(self.widget.image_paths), 0)
        self.assertTrue(self.widget.acceptDrops())
    
    def test_supported_formats(self):
        """测试支持的格式检查"""
        # 支持的格式
        self.assertTrue(self.widget.is_supported_format("test.jpg"))
        self.assertTrue(self.widget.is_supported_format("test.jpeg"))
        self.assertTrue(self.widget.is_supported_format("test.png"))
        self.assertTrue(self.widget.is_supported_format("test.bmp"))
        
        # 不支持的格式
        self.assertFalse(self.widget.is_supported_format("test.txt"))
        self.assertFalse(self.widget.is_supported_format("test.pdf"))
        self.assertFalse(self.widget.is_supported_format("test.mp4"))
    
    def test_add_images(self):
        """测试添加图片"""
        # 添加图片
        self.widget.add_images(self.test_images[:2])
        
        # 检查结果
        self.assertEqual(self.widget.count(), 2)
        self.assertEqual(len(self.widget.image_paths), 2)
        
        # 检查路径
        for img_path in self.test_images[:2]:
            self.assertIn(img_path, self.widget.image_paths)
    
    def test_add_duplicate_images(self):
        """测试添加重复图片"""
        # 先添加图片
        self.widget.add_images(self.test_images[:2])
        original_count = self.widget.count()
        
        # 再次添加相同图片
        self.widget.add_images(self.test_images[:2])
        
        # 应该没有增加
        self.assertEqual(self.widget.count(), original_count)
    
    def test_get_image_info(self):
        """测试获取图片信息"""
        if self.test_images:
            info = self.widget.get_image_info(self.test_images[0])
            
            self.assertIn('size_mb', info)
            self.assertIn('dimensions', info)
            self.assertIn('date_taken', info)
            self.assertIn('format', info)
            
            # 检查尺寸信息
            self.assertEqual(info['dimensions'], (100, 100))
            self.assertGreater(info['size_mb'], 0)
    
    def test_clear_images(self):
        """测试清空图片"""
        # 先添加图片
        self.widget.add_images(self.test_images)
        self.assertGreater(self.widget.count(), 0)
        
        # 清空
        self.widget.clear_images()
        
        # 检查结果
        self.assertEqual(self.widget.count(), 0)
        self.assertEqual(len(self.widget.image_paths), 0)
    
    def test_image_selection(self):
        """测试图片选择"""
        # 添加图片
        self.widget.add_images(self.test_images[:2])
        
        # 模拟选择第一张图片
        self.widget.setCurrentRow(0)
        
        # 检查选择
        selected = self.widget.get_selected_image()
        self.assertEqual(selected, self.test_images[0])
    
    def test_remove_selected_image(self):
        """测试移除选中图片"""
        # 添加图片
        self.widget.add_images(self.test_images[:2])
        original_count = self.widget.count()
        
        # 选择第一张图片
        self.widget.setCurrentRow(0)
        first_image = self.widget.get_selected_image()
        
        # 移除选中图片
        self.widget.remove_selected_image()
        
        # 检查结果
        self.assertEqual(self.widget.count(), original_count - 1)
        self.assertNotIn(first_image, self.widget.image_paths)
    
    def test_get_all_images(self):
        """测试获取所有图片"""
        # 添加图片
        self.widget.add_images(self.test_images)
        
        # 获取所有图片
        all_images = self.widget.get_all_images()
        
        # 检查结果
        self.assertEqual(len(all_images), len(self.test_images))
        for img_path in self.test_images:
            self.assertIn(img_path, all_images)
    
    def test_add_directory(self):
        """测试添加目录"""
        # 创建子目录和更多图片
        sub_dir = self.test_dir / "subdir"
        sub_dir.mkdir()
        
        sub_img = sub_dir / "sub_test.png" 
        test_img = Image.new('RGB', (50, 50), 'yellow')
        test_img.save(sub_img, 'PNG')
        
        # 添加目录
        self.widget.add_files([str(self.test_dir)])
        
        # 应该包含目录中所有支持的图片
        self.assertGreaterEqual(self.widget.count(), 4)  # 3个原始 + 1个子目录
    
    def test_signals(self):
        """测试信号发送"""
        # 准备信号接收
        images_added_received = []
        image_selected_received = []
        
        def on_images_added(images):
            images_added_received.extend(images)
        
        def on_image_selected(image):
            image_selected_received.append(image)
        
        # 连接信号
        self.widget.images_added.connect(on_images_added)
        self.widget.image_selected.connect(on_image_selected)
        
        # 添加图片
        self.widget.add_images(self.test_images[:2])
        
        # 处理事件循环
        QTest.qWait(100)
        
        # 检查信号
        self.assertEqual(len(images_added_received), 2)
        
        # 选择图片
        self.widget.setCurrentRow(0)
        QTest.qWait(100)
        
        # 检查选择信号
        if image_selected_received:
            self.assertEqual(image_selected_received[0], self.test_images[0])


@unittest.skipUnless(PYQT_AVAILABLE, "PyQt5 not available")
class TestImageListItem(unittest.TestCase):
    """图片列表项测试"""
    
    @classmethod
    def setUpClass(cls):
        """类级别设置"""
        if not QApplication.instance():
            cls.app = QApplication([])
        else:
            cls.app = QApplication.instance()
    
    def setUp(self):
        """测试前准备"""
        self.test_dir = Path(tempfile.mkdtemp())
        
        # 创建测试图片
        self.test_image = self.test_dir / "test.jpg"
        img = Image.new('RGB', (200, 150), 'blue')
        img.save(self.test_image, 'JPEG')
        
        # 创建图片信息
        self.image_info = {
            'size_mb': 0.1,
            'dimensions': (200, 150),
            'date_taken': '2023:01:01 12:00:00',
            'format': 'JPEG'
        }
    
    def tearDown(self):
        """测试后清理"""
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_item_creation(self):
        """测试列表项创建"""
        item = ImageListItem(str(self.test_image), self.image_info)
        
        self.assertIsNotNone(item)
        self.assertEqual(item.image_path, str(self.test_image))
        self.assertEqual(item.image_info, self.image_info)
    
    def test_item_display(self):
        """测试列表项显示"""
        item = ImageListItem(str(self.test_image), self.image_info)
        
        # 检查文件名标签
        self.assertIsNotNone(item.filename_label)
        self.assertEqual(item.filename_label.text(), "test.jpg")
        
        # 检查大小标签
        self.assertIsNotNone(item.size_label)
        size_text = item.size_label.text()
        self.assertIn("0.1 MB", size_text)
        self.assertIn("200x150", size_text)
    
    def test_thumbnail_setting(self):
        """测试缩略图设置"""
        item = ImageListItem(str(self.test_image), self.image_info)
        
        # 创建测试缩略图
        from PyQt5.QtGui import QPixmap
        pixmap = QPixmap(64, 64)
        pixmap.fill(Qt.blue)
        
        # 设置缩略图
        item.set_thumbnail(pixmap)
        
        # 检查是否设置成功
        label_pixmap = item.thumbnail_label.pixmap()
        self.assertIsNotNone(label_pixmap)


if __name__ == '__main__':
    unittest.main()