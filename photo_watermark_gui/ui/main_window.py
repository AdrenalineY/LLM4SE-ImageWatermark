#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
主窗口模块
实现Photo Watermark 2.0的主用户界面
"""

import sys
from pathlib import Path
from typing import Optional
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QMenuBar, QStatusBar, QAction, QMessageBox, QLabel, QPushButton,
    QFrame, QSizePolicy
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QIcon, QKeySequence

# 导入核心模块
from core.image_manager import ImageManager
from core.watermark_engine import WatermarkEngine, WatermarkSettings
from core.config_manager import ConfigManager


class MainWindow(QMainWindow):
    """主窗口类"""
    
    # 信号定义
    status_message = pyqtSignal(str, int)  # 状态消息, 显示时间(ms)
    
    def __init__(self):
        super().__init__()
        
        # 核心组件
        self.image_manager = ImageManager()
        self.watermark_engine = WatermarkEngine()
        self.config_manager = ConfigManager()
        
        # UI组件（后续实现）
        self.image_list_widget = None
        self.preview_widget = None  
        self.settings_panel = None
        
        # 状态管理
        self.current_image_index = -1
        self.is_modified = False
        
        # 初始化UI
        self.setup_ui()
        self.setup_layout()
        self.setup_connections()
        self.setup_menu_bar()
        self.setup_status_bar()
        
        # 加载配置
        self.load_config()
        
        # 设置初始状态
        self.update_ui_state()
    
    def setup_ui(self):
        """设置用户界面基础属性"""
        self.setWindowTitle("Photo Watermark 2.0")
        self.setMinimumSize(900, 600)
        self.resize(1000, 700)
        
        # 设置窗口图标（如果存在）
        icon_path = Path(__file__).parent.parent / "resources" / "icon.ico"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))
        
        # 窗口居中显示
        self.center_window()
        self._is_fullscreen = False
    
    def setup_layout(self):
        """设置窗口布局"""
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建主要布局（水平分割器）
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)
        
        # 创建三栏式布局的分割器
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)
        
        # 左侧面板：图片列表
        left_panel = self.create_left_panel()
        splitter.addWidget(left_panel)
        
        # 中央面板：预览区域
        center_panel = self.create_center_panel()
        splitter.addWidget(center_panel)
        
        # 右侧面板：设置面板
        right_panel = self.create_right_panel()
        splitter.addWidget(right_panel)
        
        # 设置分割器比例 (1:2:1)
        splitter.setSizes([300, 600, 300])
        splitter.setChildrenCollapsible(False)
        
        # 保存分割器引用
        self.main_splitter = splitter
    
    def create_left_panel(self) -> QWidget:
        """创建左侧图片列表面板"""
        panel = QFrame()
        panel.setFrameStyle(QFrame.StyledPanel)
        panel.setMinimumWidth(250)
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # 标题
        title_label = QLabel("图片列表")
        title_label.setStyleSheet("font-weight: bold; font-size: 14px; padding: 5px;")
        layout.addWidget(title_label)
        
        # 图片列表区域（占位符）
        list_placeholder = QLabel("图片列表组件\n（待实现）")
        list_placeholder.setAlignment(Qt.AlignCenter)
        list_placeholder.setStyleSheet("border: 1px dashed gray; padding: 20px; color: gray;")
        list_placeholder.setMinimumHeight(300)
        layout.addWidget(list_placeholder)
        
        # 操作按钮
        btn_layout = QVBoxLayout()
        
        import_file_btn = QPushButton("导入文件")
        import_file_btn.clicked.connect(self.import_files)
        btn_layout.addWidget(import_file_btn)
        
        import_folder_btn = QPushButton("导入文件夹")
        import_folder_btn.clicked.connect(self.import_folder)
        btn_layout.addWidget(import_folder_btn)
        
        clear_btn = QPushButton("清空列表")
        clear_btn.clicked.connect(self.clear_images)
        btn_layout.addWidget(clear_btn)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        return panel
    
    def create_center_panel(self) -> QWidget:
        """创建中央预览面板"""
        panel = QFrame()
        panel.setFrameStyle(QFrame.StyledPanel)
        panel.setMinimumWidth(400)
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # 标题
        title_label = QLabel("预览区域")
        title_label.setStyleSheet("font-weight: bold; font-size: 14px; padding: 5px;")
        layout.addWidget(title_label)
        
        # 预览区域（占位符）
        preview_placeholder = QLabel("预览区域\n\n请导入图片开始使用")
        preview_placeholder.setAlignment(Qt.AlignCenter)
        preview_placeholder.setStyleSheet(
            "border: 2px dashed #ccc; "
            "background-color: #f9f9f9; "
            "padding: 40px; "
            "color: #666; "
            "font-size: 16px;"
        )
        preview_placeholder.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(preview_placeholder)
        
        # 图片信息栏
        info_label = QLabel("就绪")
        info_label.setStyleSheet("padding: 5px; background-color: #f0f0f0; border: 1px solid #ddd;")
        layout.addWidget(info_label)
        
        # 保存组件引用
        self.preview_placeholder = preview_placeholder
        self.image_info_label = info_label
        
        return panel
    
    def create_right_panel(self) -> QWidget:
        """创建右侧设置面板"""
        panel = QFrame()
        panel.setFrameStyle(QFrame.StyledPanel)
        panel.setMinimumWidth(250)
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # 标题
        title_label = QLabel("水印设置")
        title_label.setStyleSheet("font-weight: bold; font-size: 14px; padding: 5px;")
        layout.addWidget(title_label)
        
        # 设置区域（占位符）
        settings_placeholder = QLabel("水印设置面板\n（待实现）")
        settings_placeholder.setAlignment(Qt.AlignCenter)
        settings_placeholder.setStyleSheet("border: 1px dashed gray; padding: 20px; color: gray;")
        settings_placeholder.setMinimumHeight(400)
        layout.addWidget(settings_placeholder)
        
        # 导出设置
        export_layout = QVBoxLayout()
        
        export_title = QLabel("导出设置")
        export_title.setStyleSheet("font-weight: bold; padding: 5px;")
        export_layout.addWidget(export_title)
        
        export_placeholder = QLabel("导出设置组件\n（待实现）")
        export_placeholder.setAlignment(Qt.AlignCenter)
        export_placeholder.setStyleSheet("border: 1px dashed gray; padding: 10px; color: gray;")
        export_layout.addWidget(export_placeholder)
        
        # 导出按钮
        export_btn = QPushButton("开始导出")
        export_btn.clicked.connect(self.export_images)
        export_btn.setEnabled(False)  # 初始状态禁用
        export_layout.addWidget(export_btn)
        
        layout.addLayout(export_layout)
        layout.addStretch()
        
        # 保存组件引用
        self.export_button = export_btn
        
        return panel
    
    def setup_connections(self):
        """设置信号连接"""
        # 图片管理器信号
        self.image_manager.images_added.connect(self.on_images_added)
        self.image_manager.images_removed.connect(self.on_images_removed)
        self.image_manager.images_cleared.connect(self.on_images_cleared)
        
        # 水印引擎信号
        self.watermark_engine.preview_ready.connect(self.on_preview_ready)
        self.watermark_engine.progress_updated.connect(self.on_progress_updated)
        self.watermark_engine.processing_finished.connect(self.on_processing_finished)
        
        # 配置管理器信号
        self.config_manager.config_loaded.connect(self.on_config_loaded)
        self.config_manager.config_saved.connect(self.on_config_saved)
        
        # 状态消息信号
        self.status_message.connect(self.show_status_message)
    
    def setup_menu_bar(self):
        """设置菜单栏"""
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu('文件(&F)')
        
        # 导入文件
        import_files_action = QAction('导入文件...', self)
        import_files_action.setShortcut(QKeySequence.Open)
        import_files_action.triggered.connect(self.import_files)
        file_menu.addAction(import_files_action)
        
        # 导入文件夹
        import_folder_action = QAction('导入文件夹...', self)
        import_folder_action.setShortcut('Ctrl+Shift+O')
        import_folder_action.triggered.connect(self.import_folder)
        file_menu.addAction(import_folder_action)
        
        file_menu.addSeparator()
        
        # 导出
        export_action = QAction('导出图片...', self)
        export_action.setShortcut('Ctrl+E')
        export_action.triggered.connect(self.export_images)
        file_menu.addAction(export_action)
        
        file_menu.addSeparator()
        
        # 退出
        exit_action = QAction('退出', self)
        exit_action.setShortcut(QKeySequence.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 编辑菜单
        edit_menu = menubar.addMenu('编辑(&E)')
        
        # 清空列表
        clear_action = QAction('清空图片列表', self)
        clear_action.setShortcut('Ctrl+L')
        clear_action.triggered.connect(self.clear_images)
        edit_menu.addAction(clear_action)
        
        edit_menu.addSeparator()
        
        # 设置
        settings_action = QAction('设置...', self)
        settings_action.triggered.connect(self.show_settings)
        edit_menu.addAction(settings_action)
        
        # 视图菜单
        view_menu = menubar.addMenu('视图(&V)')
        
        # 窗口模式切换
        self.window_mode_action = QAction('最大化窗口', self)
        self.window_mode_action.setShortcut('F11')
        self.window_mode_action.triggered.connect(self.toggle_window_mode)
        view_menu.addAction(self.window_mode_action)
        
        # 帮助菜单
        help_menu = menubar.addMenu('帮助(&H)')
        
        # 关于
        about_action = QAction('关于...', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def setup_status_bar(self):
        """设置状态栏"""
        statusbar = self.statusBar()
        
        # 左侧状态信息
        self.status_label = QLabel("就绪")
        statusbar.addWidget(self.status_label)
        
        # 右侧统计信息
        self.stats_label = QLabel("")
        statusbar.addPermanentWidget(self.stats_label)
        
        # 更新统计信息
        self.update_statistics()
    
    def load_config(self):
        """加载配置"""
        config = self.config_manager.load_config()
        self.config_manager.load_templates()
        
        # 恢复窗口几何信息（如果存在且合理）
        geometry = self.config_manager.get_config('window', 'geometry')
        if geometry:
            try:
                geometry_bytes = bytes.fromhex(geometry)
                self.restoreGeometry(geometry_bytes)
                
                # 检查窗口是否超出屏幕，如果是则重新调整
                from PyQt5.QtWidgets import QDesktopWidget
                screen = QDesktopWidget().screenGeometry()
                if (self.width() > screen.width() * 0.9 or 
                    self.height() > screen.height() * 0.9):
                    # 重新设置为合适的大小并居中
                    self.resize(1000, 700)
                    self.center_window()
            except Exception:
                # 如果恢复失败，使用默认设置
                self.resize(1000, 700)
                self.center_window()
        
        # 恢复分割器状态
        splitter_sizes = self.config_manager.get_config('window', 'splitter_sizes')
        if splitter_sizes and hasattr(self, 'main_splitter'):
            self.main_splitter.setSizes(splitter_sizes)
    
    def save_config(self):
        """保存配置"""
        # 保存窗口状态
        self.config_manager.set_config('window', 'geometry', self.saveGeometry().data().hex())
        self.config_manager.set_config('window', 'maximized', self.isMaximized())
        
        # 保存分割器状态
        if hasattr(self, 'main_splitter'):
            sizes = [int(size) for size in self.main_splitter.sizes()]
            self.config_manager.set_config('window', 'splitter_sizes', sizes)
        
        self.config_manager.save_config()
    
    def update_ui_state(self):
        """更新UI状态"""
        has_images = not self.image_manager.is_empty
        
        # 更新导出按钮状态
        if hasattr(self, 'export_button'):
            self.export_button.setEnabled(has_images)
        
        # 更新预览区域
        if not has_images:
            if hasattr(self, 'preview_placeholder'):
                self.preview_placeholder.setText("预览区域\n\n请导入图片开始使用")
        
        # 更新统计信息
        self.update_statistics()
    
    def update_statistics(self):
        """更新统计信息"""
        stats = self.image_manager.get_statistics()
        
        if stats['count'] > 0:
            stats_text = f"图片: {stats['count']} 张 | 大小: {stats['total_size_mb']:.1f} MB"
        else:
            stats_text = ""
        
        if hasattr(self, 'stats_label'):
            self.stats_label.setText(stats_text)
    
    # 槽函数实现
    def on_images_added(self, images):
        """图片添加完成"""
        self.status_message.emit(f"成功添加 {len(images)} 张图片", 3000)
        self.update_ui_state()
    
    def on_images_removed(self, images):
        """图片移除完成"""
        self.status_message.emit(f"移除了 {len(images)} 张图片", 2000)
        self.update_ui_state()
    
    def on_images_cleared(self):
        """图片列表清空"""
        self.status_message.emit("图片列表已清空", 2000)
        self.update_ui_state()
    
    def on_preview_ready(self, preview_image):
        """预览准备完成"""
        # TODO: 在预览组件中显示图片
        pass
    
    def on_progress_updated(self, current, total):
        """进度更新"""
        progress_text = f"处理进度: {current}/{total}"
        self.status_label.setText(progress_text)
    
    def on_processing_finished(self, success, message):
        """处理完成"""
        self.status_message.emit(message, 5000)
        if success:
            QMessageBox.information(self, "导出完成", message)
        else:
            QMessageBox.warning(self, "导出失败", message)
    
    def on_config_loaded(self, config):
        """配置加载完成"""
        # 恢复窗口状态
        geometry = config.get('window', {}).get('geometry')
        if geometry:
            try:
                self.restoreGeometry(bytes.fromhex(geometry))
            except:
                pass
        
        # 恢复分割器状态
        splitter_sizes = config.get('window', {}).get('splitter_sizes')
        if splitter_sizes and hasattr(self, 'main_splitter'):
            self.main_splitter.setSizes(splitter_sizes)
    
    def on_config_saved(self):
        """配置保存完成"""
        pass
    
    def show_status_message(self, message: str, timeout: int = 5000):
        """显示状态消息"""
        self.status_label.setText(message)
        
        # 设置定时器清除消息
        if timeout > 0:
            QTimer.singleShot(timeout, lambda: self.status_label.setText("就绪"))
    
    # 菜单动作实现
    def import_files(self):
        """导入文件"""
        self.status_message.emit("导入文件功能待实现", 3000)
        # TODO: 实现文件选择对话框
    
    def import_folder(self):
        """导入文件夹"""
        self.status_message.emit("导入文件夹功能待实现", 3000)
        # TODO: 实现文件夹选择对话框
    
    def clear_images(self):
        """清空图片列表"""
        if not self.image_manager.is_empty:
            reply = QMessageBox.question(
                self, '确认清空', 
                '确定要清空所有图片吗？',
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                self.image_manager.clear_images()
    
    def export_images(self):
        """导出图片"""
        if self.image_manager.is_empty:
            QMessageBox.information(self, "提示", "请先导入图片")
            return
        
        self.status_message.emit("导出功能待实现", 3000)
        # TODO: 实现导出对话框和批量处理
    
    def show_settings(self):
        """显示设置对话框"""
        self.status_message.emit("设置对话框待实现", 3000)
        # TODO: 实现设置对话框
    
    def toggle_window_mode(self):
        """切换窗口模式（最大化/正常）"""
        if self.isMaximized():
            self.showNormal()
            self.center_window()  # 还原后居中显示
            self.window_mode_action.setText('最大化窗口')
            self.status_message.emit("已还原窗口大小", 2000)
        else:
            self.showMaximized()
            self.window_mode_action.setText('还原窗口')
            self.status_message.emit("已最大化窗口", 2000)
    
    def show_about(self):
        """显示关于对话框"""
        about_text = """
        <h3>Photo Watermark 2.0</h3>
        <p>基于EXIF拍摄时间信息为图片添加水印的桌面应用程序</p>
        <p>版本: 2.0.0</p>
        <p>开发: LLM4SE Project</p>
        <p>GitHub: <a href="https://github.com/AdrenalineY/LLM4SE-ImageWatermark">
        https://github.com/AdrenalineY/LLM4SE-ImageWatermark</a></p>
        """
        
        QMessageBox.about(self, "关于 Photo Watermark 2.0", about_text)
    
    def center_window(self):
        """将窗口居中显示在屏幕上"""
        from PyQt5.QtWidgets import QDesktopWidget
        
        # 获取屏幕几何信息
        screen = QDesktopWidget().screenGeometry()
        window = self.geometry()
        
        # 计算居中位置
        x = (screen.width() - window.width()) // 2
        y = (screen.height() - window.height()) // 2
        
        # 移动窗口到居中位置
        self.move(x, y)
    
    def keyPressEvent(self, event):
        """键盘按键事件处理"""
        if event.key() == Qt.Key_F11:
            # F11键切换窗口模式
            self.toggle_window_mode()
        else:
            super().keyPressEvent(event)
    
    def closeEvent(self, event):
        """窗口关闭事件"""
        # 保存配置
        self.save_config()
        
        # 检查是否有未保存的更改
        if self.is_modified:
            reply = QMessageBox.question(
                self, '确认退出',
                '有未保存的更改，确定要退出吗？',
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.No:
                event.ignore()
                return
        
        event.accept()