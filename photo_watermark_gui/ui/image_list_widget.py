#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图片列表组件
实现拖拽导入和图片列表显示功能
"""

import os
from pathlib import Path
from typing import List, Optional
from PIL import Image
from PyQt5.QtWidgets import (
    QListWidget, QListWidgetItem, QWidget, QVBoxLayout, 
    QHBoxLayout, QLabel, QPushButton, QAbstractItemView,
    QFileDialog, QMessageBox, QProgressDialog
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QSize, QMimeData
from PyQt5.QtGui import QPixmap, QIcon, QDragEnterEvent, QDropEvent


class ThumbnailThread(QThread):
    """缩略图生成线程"""
    
    thumbnail_ready = pyqtSignal(str, QPixmap)  # 文件路径, 缩略图
    progress_updated = pyqtSignal(int)  # 进度
    
    def __init__(self, image_paths: List[str], thumbnail_size: int = 64):
        super().__init__()
        self.image_paths = image_paths
        self.thumbnail_size = thumbnail_size
        self._stop_flag = False
    
    def stop(self):
        """停止线程"""
        self._stop_flag = True
    
    def run(self):
        """生成缩略图"""
        total = len(self.image_paths)
        
        for i, image_path in enumerate(self.image_paths):
            if self._stop_flag:
                break
                
            try:
                # 生成缩略图
                image = Image.open(image_path)
                
                # 保持纵横比缩放
                image.thumbnail((self.thumbnail_size, self.thumbnail_size), Image.Resampling.LANCZOS)
                
                # 转换为QPixmap
                if image.mode == 'RGBA':
                    # 处理透明度
                    image = image.convert('RGB')
                
                # 保存为临时字节数据
                from io import BytesIO
                buffer = BytesIO()
                image.save(buffer, format='PNG')
                buffer.seek(0)
                
                # 创建QPixmap
                pixmap = QPixmap()
                pixmap.loadFromData(buffer.getvalue())
                
                self.thumbnail_ready.emit(image_path, pixmap)
                
            except Exception as e:
                print(f"生成缩略图失败 {image_path}: {e}")
                # 发送默认图标
                self.thumbnail_ready.emit(image_path, QPixmap())
            
            self.progress_updated.emit(i + 1)


class ImageListItem(QWidget):
    """图片列表项"""
    
    def __init__(self, image_path: str, image_info: dict):
        super().__init__()
        self.image_path = image_path
        self.image_info = image_info
        self.thumbnail = None
        
        self.setup_ui()
    
    def setup_ui(self):
        """设置UI"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(10)
        
        # 缩略图
        self.thumbnail_label = QLabel()
        self.thumbnail_label.setFixedSize(64, 64)
        self.thumbnail_label.setAlignment(Qt.AlignCenter)
        self.thumbnail_label.setStyleSheet("""
            border: 1px solid #ccc;
            background-color: #f8f8f8;
        """)
        layout.addWidget(self.thumbnail_label)
        
        # 文件信息
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)
        
        # 文件名
        filename = Path(self.image_path).name
        self.filename_label = QLabel(filename)
        self.filename_label.setStyleSheet("font-weight: bold;")
        info_layout.addWidget(self.filename_label)
        
        # 文件大小和尺寸
        size_text = f"{self.image_info.get('size_mb', 0):.1f} MB"
        if 'dimensions' in self.image_info:
            w, h = self.image_info['dimensions']
            size_text += f" | {w}x{h}"
        
        self.size_label = QLabel(size_text)
        self.size_label.setStyleSheet("color: #666; font-size: 12px;")
        info_layout.addWidget(self.size_label)
        
        # 拍摄时间（如果有）
        if self.image_info.get('date_taken'):
            date_label = QLabel(f"拍摄时间: {self.image_info['date_taken']}")
            date_label.setStyleSheet("color: #888; font-size: 11px;")
            info_layout.addWidget(date_label)
        
        layout.addLayout(info_layout)
        layout.addStretch()
    
    def set_thumbnail(self, pixmap: QPixmap):
        """设置缩略图"""
        if not pixmap.isNull():
            scaled_pixmap = pixmap.scaled(60, 60, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.thumbnail_label.setPixmap(scaled_pixmap)
        else:
            # 设置默认图标
            self.thumbnail_label.setText("📷")
            self.thumbnail_label.setStyleSheet("""
                border: 1px solid #ccc;
                background-color: #f0f0f0;
                font-size: 24px;
            """)


class ImageListWidget(QListWidget):
    """图片列表组件"""
    
    # 信号定义
    images_added = pyqtSignal(list)  # 添加图片信号
    image_selected = pyqtSignal(str)  # 选择图片信号
    
    # 支持的图片格式
    SUPPORTED_FORMATS = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.webp'}
    
    def __init__(self):
        super().__init__()
        self.image_paths = []
        self.thumbnail_thread = None
        
        self.setup_ui()
        self.setup_drag_drop()
        self.connect_signals()
    
    def setup_ui(self):
        """设置UI"""
        self.setMinimumWidth(280)
        self.setSpacing(2)
        self.setAlternatingRowColors(True)
        
        # 设置选择模式
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        
        # 样式
        self.setStyleSheet("""
            QListWidget {
                border: 1px solid #ddd;
                background-color: white;
            }
            QListWidget::item {
                border-bottom: 1px solid #eee;
                padding: 2px;
            }
            QListWidget::item:selected {
                background-color: #e3f2fd;
                border: 2px solid #2196f3;
            }
        """)
    
    def setup_drag_drop(self):
        """设置拖拽功能"""
        self.setAcceptDrops(True)
        self.setDragDropMode(QAbstractItemView.DropOnly)
    
    def connect_signals(self):
        """连接信号"""
        self.itemSelectionChanged.connect(self.on_selection_changed)
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        """拖拽进入事件"""
        if event.mimeData().hasUrls():
            # 检查是否包含图片文件
            urls = event.mimeData().urls()
            has_images = False
            
            for url in urls:
                file_path = url.toLocalFile()
                if os.path.isfile(file_path):
                    ext = Path(file_path).suffix.lower()
                    if ext in self.SUPPORTED_FORMATS:
                        has_images = True
                        break
                elif os.path.isdir(file_path):
                    has_images = True  # 目录可能包含图片
                    break
            
            if has_images:
                event.acceptProposedAction()
            else:
                event.ignore()
        else:
            event.ignore()
    
    def dragMoveEvent(self, event):
        """拖拽移动事件"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()
    
    def dropEvent(self, event: QDropEvent):
        """拖拽放下事件"""
        if event.mimeData().hasUrls():
            file_paths = []
            
            for url in event.mimeData().urls():
                file_path = url.toLocalFile()
                if os.path.exists(file_path):
                    file_paths.append(file_path)
            
            if file_paths:
                self.add_files(file_paths)
            
            event.acceptProposedAction()
        else:
            event.ignore()
    
    def is_supported_format(self, file_path: str) -> bool:
        """检查是否为支持的图片格式"""
        ext = Path(file_path).suffix.lower()
        return ext in self.SUPPORTED_FORMATS
    
    def get_image_info(self, image_path: str) -> dict:
        """获取图片信息"""
        try:
            # 文件大小
            file_size = os.path.getsize(image_path)
            size_mb = file_size / (1024 * 1024)
            
            # 图片尺寸
            with Image.open(image_path) as img:
                dimensions = img.size
                
                # EXIF信息
                exif_info = {}
                if hasattr(img, '_getexif') and img._getexif():
                    exif_info = img._getexif() or {}
                
                # 提取拍摄时间
                date_taken = None
                if exif_info:
                    # 尝试获取拍摄时间
                    from PIL.ExifTags import TAGS
                    for tag_id, value in exif_info.items():
                        tag = TAGS.get(tag_id, tag_id)
                        if tag in ['DateTime', 'DateTimeOriginal', 'DateTimeDigitized']:
                            date_taken = str(value)
                            break
                
                return {
                    'size_mb': size_mb,
                    'dimensions': dimensions,
                    'date_taken': date_taken,
                    'format': img.format
                }
                
        except Exception as e:
            print(f"获取图片信息失败 {image_path}: {e}")
            return {
                'size_mb': os.path.getsize(image_path) / (1024 * 1024),
                'dimensions': None,
                'date_taken': None,
                'format': None
            }
    
    def add_files(self, file_paths: List[str]):
        """添加文件"""
        image_files = []
        
        for file_path in file_paths:
            if os.path.isfile(file_path):
                if self.is_supported_format(file_path):
                    if file_path not in self.image_paths:
                        image_files.append(file_path)
            elif os.path.isdir(file_path):
                # 扫描目录中的图片
                for root, _, files in os.walk(file_path):
                    for file in files:
                        full_path = os.path.join(root, file)
                        if self.is_supported_format(full_path):
                            if full_path not in self.image_paths:
                                image_files.append(full_path)
        
        if image_files:
            self.add_images(image_files)
    
    def add_images(self, image_paths: List[str]):
        """添加图片到列表"""
        if not image_paths:
            return
        
        # 过滤重复图片
        filtered_paths = []
        for path in image_paths:
            if path not in self.image_paths:
                filtered_paths.append(path)
        
        if not filtered_paths:
            return
        
        # 显示进度对话框
        progress_dialog = QProgressDialog("正在加载图片...", "取消", 0, len(filtered_paths), self)
        progress_dialog.setModal(True)
        progress_dialog.show()
        
        new_images = []
        
        try:
            for i, image_path in enumerate(filtered_paths):
                if progress_dialog.wasCanceled():
                    break
                
                # 获取图片信息
                image_info = self.get_image_info(image_path)
                
                # 创建列表项
                item = QListWidgetItem()
                item.setData(Qt.UserRole, image_path)
                item.setSizeHint(QSize(260, 80))
                
                # 创建自定义组件
                item_widget = ImageListItem(image_path, image_info)
                
                # 添加到列表
                self.addItem(item)
                self.setItemWidget(item, item_widget)
                
                # 记录路径
                self.image_paths.append(image_path)
                new_images.append(image_path)
                
                progress_dialog.setValue(i + 1)
        
        finally:
            progress_dialog.close()
        
        if new_images:
            # 启动缩略图生成线程
            self.generate_thumbnails(new_images)
            
            # 发送信号
            self.images_added.emit(new_images)
            
            # 选择第一张图片
            if self.count() == len(new_images):
                self.setCurrentRow(0)
    
    def generate_thumbnails(self, image_paths: List[str]):
        """生成缩略图"""
        if self.thumbnail_thread and self.thumbnail_thread.isRunning():
            self.thumbnail_thread.stop()
            self.thumbnail_thread.wait()
        
        self.thumbnail_thread = ThumbnailThread(image_paths)
        self.thumbnail_thread.thumbnail_ready.connect(self.on_thumbnail_ready)
        self.thumbnail_thread.start()
    
    def on_thumbnail_ready(self, image_path: str, pixmap: QPixmap):
        """缩略图生成完成"""
        # 找到对应的列表项
        for i in range(self.count()):
            item = self.item(i)
            if item.data(Qt.UserRole) == image_path:
                widget = self.itemWidget(item)
                if isinstance(widget, ImageListItem):
                    widget.set_thumbnail(pixmap)
                break
    
    def on_selection_changed(self):
        """选择变更"""
        current_item = self.currentItem()
        if current_item:
            image_path = current_item.data(Qt.UserRole)
            self.image_selected.emit(image_path)
    
    def clear_images(self):
        """清空图片列表"""
        if self.thumbnail_thread and self.thumbnail_thread.isRunning():
            self.thumbnail_thread.stop()
            self.thumbnail_thread.wait()
        
        self.clear()
        self.image_paths.clear()
    
    def get_selected_image(self) -> Optional[str]:
        """获取当前选中的图片"""
        current_item = self.currentItem()
        if current_item:
            return current_item.data(Qt.UserRole)
        return None
    
    def get_all_images(self) -> List[str]:
        """获取所有图片路径"""
        return self.image_paths.copy()
    
    def remove_selected_image(self):
        """移除选中的图片"""
        current_row = self.currentRow()
        if current_row >= 0:
            item = self.takeItem(current_row)
            if item:
                image_path = item.data(Qt.UserRole)
                if image_path in self.image_paths:
                    self.image_paths.remove(image_path)