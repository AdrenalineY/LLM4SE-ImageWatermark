#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图片预览组件
实现图片预览、缩放和水印预览功能
"""

import os
from pathlib import Path
from typing import Optional, Tuple
from PIL import Image
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QScrollArea, QFrame, QButtonGroup, QToolButton, QSlider
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QSize, QRectF
from PyQt5.QtGui import QPixmap, QPainter, QFont, QColor, QPen


class ImagePreviewThread(QThread):
    """图片预览加载线程"""
    
    image_loaded = pyqtSignal(QPixmap)  # 加载完成信号
    error_occurred = pyqtSignal(str)    # 错误信号
    
    def __init__(self, image_path: str, max_size: Tuple[int, int] = (800, 600)):
        super().__init__()
        self.image_path = image_path
        self.max_width, self.max_height = max_size
        self._stop_flag = False
    
    def stop(self):
        """停止线程"""
        self._stop_flag = True
    
    def run(self):
        """加载图片"""
        try:
            if self._stop_flag:
                return
            
            # 加载图片
            image = Image.open(self.image_path)
            
            if self._stop_flag:
                return
            
            # 获取原始尺寸
            orig_width, orig_height = image.size
            
            # 计算缩放比例（保持纵横比）
            scale_x = self.max_width / orig_width
            scale_y = self.max_height / orig_height
            scale = min(scale_x, scale_y, 1.0)  # 不放大，只缩小
            
            if scale < 1.0:
                new_width = int(orig_width * scale)
                new_height = int(orig_height * scale)
                image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            if self._stop_flag:
                return
            
            # 转换为RGB（如果是RGBA）
            if image.mode == 'RGBA':
                # 创建白色背景
                background = Image.new('RGB', image.size, (255, 255, 255))
                background.paste(image, mask=image.split()[-1])  # 使用alpha通道作为mask
                image = background
            elif image.mode != 'RGB':
                image = image.convert('RGB')
            
            # 转换为QPixmap
            from io import BytesIO
            buffer = BytesIO()
            image.save(buffer, format='PNG')
            buffer.seek(0)
            
            pixmap = QPixmap()
            pixmap.loadFromData(buffer.getvalue())
            
            if not self._stop_flag:
                self.image_loaded.emit(pixmap)
                
        except Exception as e:
            if not self._stop_flag:
                self.error_occurred.emit(str(e))


class PreviewLabel(QLabel):
    """可缩放的预览标签"""
    
    def __init__(self):
        super().__init__()
        self.setAlignment(Qt.AlignCenter)
        self.setMinimumSize(400, 300)
        self.setStyleSheet("""
            QLabel {
                border: 2px dashed #ccc;
                background-color: #fafafa;
                color: #666;
            }
        """)
        
        # 设置默认显示
        self.setText("拖拽图片到此处或从左侧列表选择图片进行预览")
        self.setWordWrap(True)
        
        self._original_pixmap = None
        self._current_scale = 1.0
    
    def set_image(self, pixmap: QPixmap):
        """设置图片"""
        self._original_pixmap = pixmap
        self._current_scale = 1.0
        self.update_display()
    
    def update_display(self):
        """更新显示"""
        if self._original_pixmap and not self._original_pixmap.isNull():
            if self._current_scale != 1.0:
                scaled_size = self._original_pixmap.size() * self._current_scale
                scaled_pixmap = self._original_pixmap.scaled(
                    scaled_size, Qt.KeepAspectRatio, Qt.SmoothTransformation
                )
                self.setPixmap(scaled_pixmap)
            else:
                self.setPixmap(self._original_pixmap)
        else:
            self.clear()
            self.setText("拖拽图片到此处或从左侧列表选择图片进行预览")
    
    def zoom_in(self):
        """放大"""
        if self._original_pixmap:
            self._current_scale = min(self._current_scale * 1.2, 5.0)
            self.update_display()
    
    def zoom_out(self):
        """缩小"""
        if self._original_pixmap:
            self._current_scale = max(self._current_scale / 1.2, 0.1)
            self.update_display()
    
    def zoom_fit(self):
        """适应窗口"""
        if self._original_pixmap:
            self._current_scale = 1.0
            self.update_display()
    
    def zoom_actual(self):
        """实际大小"""
        if self._original_pixmap:
            # 计算实际大小对应的缩放比例
            widget_size = self.size()
            pixmap_size = self._original_pixmap.size()
            
            scale_x = widget_size.width() / pixmap_size.width()
            scale_y = widget_size.height() / pixmap_size.height()
            
            # 使用原始图片的实际缩放比例（从预览加载时的缩放）
            self._current_scale = 1.0  # 这里是预览时的实际大小
            self.update_display()
    
    def get_current_scale(self) -> float:
        """获取当前缩放比例"""
        return self._current_scale


class ImagePreviewWidget(QWidget):
    """图片预览组件"""
    
    # 缩放模式
    ZOOM_FIT = "fit"
    ZOOM_ACTUAL = "actual"
    ZOOM_CUSTOM = "custom"
    
    def __init__(self):
        super().__init__()
        self.current_image_path = None
        self.preview_thread = None
        
        self.setup_ui()
        self.connect_signals()
    
    def setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # 工具栏
        toolbar_layout = QHBoxLayout()
        
        # 缩放按钮
        self.zoom_in_btn = QToolButton()
        self.zoom_in_btn.setText("🔍+")
        self.zoom_in_btn.setToolTip("放大")
        self.zoom_in_btn.setFixedSize(32, 32)
        
        self.zoom_out_btn = QToolButton()
        self.zoom_out_btn.setText("🔍-")
        self.zoom_out_btn.setToolTip("缩小")
        self.zoom_out_btn.setFixedSize(32, 32)
        
        self.zoom_fit_btn = QToolButton()
        self.zoom_fit_btn.setText("⭕")
        self.zoom_fit_btn.setToolTip("适应窗口")
        self.zoom_fit_btn.setFixedSize(32, 32)
        
        self.zoom_actual_btn = QToolButton()
        self.zoom_actual_btn.setText("📐")
        self.zoom_actual_btn.setToolTip("实际大小")
        self.zoom_actual_btn.setFixedSize(32, 32)
        
        # 缩放滑块
        self.zoom_slider = QSlider(Qt.Horizontal)
        self.zoom_slider.setRange(10, 500)  # 10% 到 500%
        self.zoom_slider.setValue(100)
        self.zoom_slider.setFixedWidth(150)
        
        # 缩放标签
        self.zoom_label = QLabel("100%")
        self.zoom_label.setFixedWidth(50)
        self.zoom_label.setAlignment(Qt.AlignCenter)
        
        toolbar_layout.addWidget(self.zoom_in_btn)
        toolbar_layout.addWidget(self.zoom_out_btn)
        toolbar_layout.addWidget(self.zoom_fit_btn)
        toolbar_layout.addWidget(self.zoom_actual_btn)
        toolbar_layout.addWidget(QLabel("|"))  # 分隔符
        toolbar_layout.addWidget(QLabel("缩放:"))
        toolbar_layout.addWidget(self.zoom_slider)
        toolbar_layout.addWidget(self.zoom_label)
        toolbar_layout.addStretch()
        
        layout.addLayout(toolbar_layout)
        
        # 预览区域（带滚动条）
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setAlignment(Qt.AlignCenter)
        
        # 预览标签
        self.preview_label = PreviewLabel()
        self.scroll_area.setWidget(self.preview_label)
        
        layout.addWidget(self.scroll_area)
        
        # 状态信息
        self.info_layout = QHBoxLayout()
        
        self.image_info_label = QLabel("未选择图片")
        self.image_info_label.setStyleSheet("color: #666; font-size: 12px;")
        
        self.info_layout.addWidget(self.image_info_label)
        self.info_layout.addStretch()
        
        layout.addLayout(self.info_layout)
    
    def connect_signals(self):
        """连接信号"""
        self.zoom_in_btn.clicked.connect(self.zoom_in)
        self.zoom_out_btn.clicked.connect(self.zoom_out)
        self.zoom_fit_btn.clicked.connect(self.zoom_fit)
        self.zoom_actual_btn.clicked.connect(self.zoom_actual)
        self.zoom_slider.valueChanged.connect(self.on_zoom_slider_changed)
    
    def load_image(self, image_path: str):
        """加载图片"""
        if not os.path.exists(image_path):
            self.show_error("文件不存在")
            return
        
        self.current_image_path = image_path
        
        # 停止之前的加载线程
        if self.preview_thread and self.preview_thread.isRunning():
            self.preview_thread.stop()
            self.preview_thread.wait()
        
        # 更新信息显示
        self.update_image_info(image_path)
        
        # 启动加载线程
        widget_size = self.scroll_area.size()
        max_size = (widget_size.width() - 50, widget_size.height() - 50)
        
        self.preview_thread = ImagePreviewThread(image_path, max_size)
        self.preview_thread.image_loaded.connect(self.on_image_loaded)
        self.preview_thread.error_occurred.connect(self.show_error)
        self.preview_thread.start()
    
    def on_image_loaded(self, pixmap: QPixmap):
        """图片加载完成"""
        self.preview_label.set_image(pixmap)
        self.zoom_fit()  # 默认适应窗口
    
    def show_error(self, error_message: str):
        """显示错误"""
        self.preview_label.clear()
        self.preview_label.setText(f"加载失败: {error_message}")
        self.image_info_label.setText("加载失败")
    
    def update_image_info(self, image_path: str):
        """更新图片信息"""
        try:
            # 获取文件信息
            file_size = os.path.getsize(image_path) / (1024 * 1024)
            filename = Path(image_path).name
            
            # 获取图片尺寸
            with Image.open(image_path) as img:
                width, height = img.size
                format_name = img.format or "Unknown"
            
            info_text = f"{filename} | {width}x{height} | {format_name} | {file_size:.1f} MB"
            self.image_info_label.setText(info_text)
            
        except Exception as e:
            self.image_info_label.setText(f"信息获取失败: {e}")
    
    def zoom_in(self):
        """放大"""
        self.preview_label.zoom_in()
        self.update_zoom_controls()
    
    def zoom_out(self):
        """缩小"""
        self.preview_label.zoom_out()
        self.update_zoom_controls()
    
    def zoom_fit(self):
        """适应窗口"""
        self.preview_label.zoom_fit()
        self.update_zoom_controls()
    
    def zoom_actual(self):
        """实际大小"""
        self.preview_label.zoom_actual()
        self.update_zoom_controls()
    
    def on_zoom_slider_changed(self, value):
        """缩放滑块变更"""
        if hasattr(self, '_updating_slider'):
            return
        
        scale = value / 100.0
        self.preview_label._current_scale = scale
        self.preview_label.update_display()
        self.update_zoom_label()
    
    def update_zoom_controls(self):
        """更新缩放控件"""
        if self.preview_label._original_pixmap:
            scale = self.preview_label.get_current_scale()
            
            # 更新滑块（避免递归调用）
            self._updating_slider = True
            self.zoom_slider.setValue(int(scale * 100))
            delattr(self, '_updating_slider')
            
            # 更新标签
            self.update_zoom_label()
    
    def update_zoom_label(self):
        """更新缩放标签"""
        scale = self.preview_label.get_current_scale()
        self.zoom_label.setText(f"{int(scale * 100)}%")
    
    def clear_preview(self):
        """清空预览"""
        if self.preview_thread and self.preview_thread.isRunning():
            self.preview_thread.stop()
            self.preview_thread.wait()
        
        self.preview_label.clear()
        self.preview_label.setText("拖拽图片到此处或从左侧列表选择图片进行预览")
        self.image_info_label.setText("未选择图片")
        self.current_image_path = None
        
        # 重置缩放控件
        self.zoom_slider.setValue(100)
        self.zoom_label.setText("100%")
    
    def get_current_image(self) -> Optional[str]:
        """获取当前预览的图片路径"""
        return self.current_image_path
    
    def resizeEvent(self, event):
        """窗口大小变更事件"""
        super().resizeEvent(event)
        
        # 如果当前是适应窗口模式，重新调整
        if (self.current_image_path and 
            self.preview_label._original_pixmap and 
            abs(self.preview_label.get_current_scale() - 1.0) < 0.01):
            
            # 延迟调整，避免在窗口调整过程中频繁更新
            from PyQt5.QtCore import QTimer
            QTimer.singleShot(100, self.zoom_fit)