#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
主窗口集成测试
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
    from PyQt5.QtCore import QTimer
    from PyQt5.QtTest import QTest
    from photo_watermark_gui.ui.main_window import MainWindow
    PYQT_AVAILABLE = True
except ImportError:
    PYQT_AVAILABLE = False


@unittest.skipUnless(PYQT_AVAILABLE, "PyQt5 not available")
class TestMainWindow(unittest.TestCase):
    """主窗口集成测试"""
    
    @classmethod
    def setUpClass(cls):
        """类级别设置 - 创建QApplication"""
        if not QApplication.instance():
            cls.app = QApplication([])
        else:
            cls.app = QApplication.instance()
    
    def setUp(self):
        """测试前准备"""
        self.test_dir = Path(tempfile.mkdtemp())
        
        # 创建测试图片
        self.test_images = []
        for i in range(2):
            img_path = self.test_dir / f"test_{i}.jpg"
            test_img = Image.new('RGB', (100, 100), color=['red', 'green'][i])
            test_img.save(img_path, 'JPEG')
            self.test_images.append(str(img_path))
        
        # 创建主窗口
        self.window = MainWindow()
        
        # 使用临时配置文件路径
        self.window.config_manager.config_path = self.test_dir / "test_config.json"
        self.window.config_manager.templates_path = self.test_dir / "test_templates.json"
    
    def tearDown(self):
        """测试后清理"""
        if self.window:
            self.window.close()
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_window_initialization(self):
        """测试窗口初始化"""
        self.assertIsNotNone(self.window)
        self.assertEqual(self.window.windowTitle(), "Photo Watermark 2.0")
        self.assertGreaterEqual(self.window.width(), 1200)
        self.assertGreaterEqual(self.window.height(), 800)
    
    def test_core_components_initialization(self):
        """测试核心组件初始化"""
        self.assertIsNotNone(self.window.image_manager)
        self.assertIsNotNone(self.window.watermark_engine)
        self.assertIsNotNone(self.window.config_manager)
    
    def test_ui_components_exist(self):
        """测试UI组件存在"""
        # 检查菜单栏
        menubar = self.window.menuBar()
        self.assertIsNotNone(menubar)
        
        # 检查状态栏
        statusbar = self.window.statusBar()
        self.assertIsNotNone(statusbar)
        
        # 检查中央部件
        central_widget = self.window.centralWidget()
        self.assertIsNotNone(central_widget)
    
    def test_menu_actions_exist(self):
        """测试菜单动作存在"""
        menubar = self.window.menuBar()
        
        # 检查文件菜单
        file_menu = None
        for action in menubar.actions():
            if '文件' in action.text():
                file_menu = action.menu()
                break
        
        self.assertIsNotNone(file_menu)
        
        # 检查菜单项
        menu_texts = [action.text() for action in file_menu.actions() if not action.isSeparator()]
        self.assertIn('导入文件...', menu_texts)
        self.assertIn('导入文件夹...', menu_texts)
        self.assertIn('导出图片...', menu_texts)
    
    def test_initial_ui_state(self):
        """测试初始UI状态"""
        # 图片管理器应该为空
        self.assertTrue(self.window.image_manager.is_empty)
        
        # 导出按钮应该被禁用
        if hasattr(self.window, 'export_button'):
            self.assertFalse(self.window.export_button.isEnabled())
    
    def test_status_message(self):
        """测试状态消息显示"""
        test_message = "Test Status Message"
        
        # 发送状态消息
        self.window.status_message.emit(test_message, 1000)
        
        # 处理事件
        QTest.qWait(100)
        
        # 检查状态栏是否显示消息
        if hasattr(self.window, 'status_label'):
            self.assertEqual(self.window.status_label.text(), test_message)
    
    def test_add_images_signal_handling(self):
        """测试添加图片信号处理"""
        initial_count = self.window.image_manager.image_count
        
        # 模拟添加图片
        added_images = self.window.image_manager.add_images(self.test_images)
        
        # 检查是否正确添加
        self.assertEqual(len(added_images), 2)
        self.assertEqual(self.window.image_manager.image_count, initial_count + 2)
        
        # 检查UI状态是否更新
        if hasattr(self.window, 'export_button'):
            self.assertTrue(self.window.export_button.isEnabled())
    
    def test_clear_images_with_confirmation(self):
        """测试清空图片确认对话框"""
        # 先添加图片
        self.window.image_manager.add_images(self.test_images)
        self.assertFalse(self.window.image_manager.is_empty)
        
        # 直接调用清空方法（跳过确认对话框）
        self.window.image_manager.clear_images()
        
        # 检查是否清空
        self.assertTrue(self.window.image_manager.is_empty)
    
    def test_window_close_event(self):
        """测试窗口关闭事件"""
        # 模拟窗口关闭
        self.window.close()
        
        # 检查配置是否保存（如果配置文件存在）
        if self.window.config_manager.config_path.exists():
            # 配置应该已保存
            pass
    
    def test_config_save_on_close(self):
        """测试关闭时保存配置"""
        # 修改一些设置
        original_geometry = self.window.saveGeometry()
        
        # 调用保存配置
        self.window.save_config()
        
        # 检查配置文件是否创建
        self.assertTrue(self.window.config_manager.config_path.exists())
    
    def test_statistics_update(self):
        """测试统计信息更新"""
        # 初始统计信息
        self.window.update_statistics()
        
        # 添加图片后更新统计信息
        self.window.image_manager.add_images(self.test_images)
        self.window.update_statistics()
        
        # 检查统计信息是否更新
        if hasattr(self.window, 'stats_label'):
            stats_text = self.window.stats_label.text()
            self.assertIn('图片:', stats_text)
            self.assertIn('2 张', stats_text)
    
    def test_about_dialog(self):
        """测试关于对话框"""
        # 这个测试只检查方法是否可调用，不检查对话框显示
        try:
            # 由于QMessageBox.about会阻塞，我们只检查方法存在
            self.assertTrue(hasattr(self.window, 'show_about'))
            self.assertTrue(callable(self.window.show_about))
        except Exception as e:
            self.fail(f"show_about method failed: {e}")


@unittest.skipUnless(PYQT_AVAILABLE, "PyQt5 not available") 
class TestMainWindowIntegration(unittest.TestCase):
    """主窗口集成功能测试"""
    
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
        self.window = MainWindow()
        
        # 使用临时配置
        self.window.config_manager.config_path = self.test_dir / "test_config.json"
        self.window.config_manager.templates_path = self.test_dir / "test_templates.json"
    
    def tearDown(self):
        """测试后清理"""
        if self.window:
            self.window.close()
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_component_communication(self):
        """测试组件间通信"""
        # 创建测试图片
        test_image = self.test_dir / "test.jpg"
        img = Image.new('RGB', (100, 100), color='blue')
        img.save(test_image, 'JPEG')
        
        # 添加图片到管理器
        added = self.window.image_manager.add_images([str(test_image)])
        
        # 检查添加是否成功
        self.assertEqual(len(added), 1)
        
        # 检查水印引擎是否可以处理该图片
        from photo_watermark_gui.core.watermark_engine import WatermarkSettings
        settings = WatermarkSettings()
        settings.text = "Test"
        
        result = self.window.watermark_engine.apply_preview_watermark(
            str(test_image), settings
        )
        
        self.assertIsNotNone(result)
    
    def test_config_persistence(self):
        """测试配置持久化"""
        # 修改配置
        self.window.config_manager.set_config('watermark', 'text', 'Persistent Test')
        
        # 保存配置
        self.window.save_config()
        
        # 创建新窗口并加载配置
        new_window = MainWindow()
        new_window.config_manager.config_path = self.window.config_manager.config_path
        new_window.config_manager.templates_path = self.window.config_manager.templates_path
        
        config = new_window.config_manager.load_config()
        
        # 检查配置是否正确加载
        self.assertEqual(config['watermark']['text'], 'Persistent Test')
        
        new_window.close()


if __name__ == '__main__':
    unittest.main()