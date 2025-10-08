#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图片管理器模块
负责图片文件的加载、验证、缩略图生成等功能
"""

import os
from pathlib import Path
from typing import List, Optional, Dict, Any
from PIL import Image, ImageQt
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import QObject, pyqtSignal


class ImageInfo:
    """图片信息类"""
    
    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        self.name = self.file_path.name
        self.size = self.file_path.stat().st_size if self.file_path.exists() else 0
        self.dimensions = None  # (width, height)
        self.thumbnail = None   # QPixmap缩略图
        self._loaded = False
        
    def load_info(self) -> bool:
        """加载图片信息"""
        try:
            with Image.open(self.file_path) as img:
                self.dimensions = img.size
                self._loaded = True
                return True
        except Exception:
            return False
    
    def generate_thumbnail(self, size: tuple = (64, 64)) -> Optional[QPixmap]:
        """生成缩略图"""
        try:
            with Image.open(self.file_path) as img:
                # 保持宽高比的缩略图
                img.thumbnail(size, Image.Resampling.LANCZOS)
                
                # 转换为Qt格式
                if img.mode == 'RGBA':
                    qt_image = ImageQt.ImageQt(img)
                else:
                    # 确保是RGB模式
                    img = img.convert('RGB')
                    qt_image = ImageQt.ImageQt(img)
                
                self.thumbnail = QPixmap.fromImage(qt_image)
                return self.thumbnail
        except Exception:
            return None
    
    @property
    def is_loaded(self) -> bool:
        return self._loaded
    
    @property
    def size_mb(self) -> float:
        """文件大小（MB）"""
        return self.size / (1024 * 1024)


class ImageManager(QObject):
    """图片管理器"""
    
    # 信号定义
    images_added = pyqtSignal(list)  # 添加图片时发出信号
    images_removed = pyqtSignal(list)  # 移除图片时发出信号
    images_cleared = pyqtSignal()  # 清空图片时发出信号
    
    def __init__(self):
        super().__init__()
        self.supported_formats = {'.jpg', '.jpeg', '.png', '.tiff', '.tif', '.bmp'}
        self.images: List[ImageInfo] = []
        self.current_index = -1
    
    def add_images(self, file_paths: List[str]) -> List[ImageInfo]:
        """添加图片文件"""
        added_images = []
        
        for file_path in file_paths:
            if self.is_supported_format(file_path) and not self.is_already_added(file_path):
                image_info = ImageInfo(file_path)
                if image_info.load_info():
                    self.images.append(image_info)
                    added_images.append(image_info)
        
        if added_images:
            self.images_added.emit(added_images)
        
        return added_images
    
    def add_directory(self, directory: str, recursive: bool = False) -> List[ImageInfo]:
        """添加目录中的所有图片"""
        dir_path = Path(directory)
        if not dir_path.exists() or not dir_path.is_dir():
            return []
        
        file_paths = []
        if recursive:
            for ext in self.supported_formats:
                file_paths.extend(dir_path.rglob(f'*{ext}'))
                file_paths.extend(dir_path.rglob(f'*{ext.upper()}'))
        else:
            for ext in self.supported_formats:
                file_paths.extend(dir_path.glob(f'*{ext}'))
                file_paths.extend(dir_path.glob(f'*{ext.upper()}'))
        
        return self.add_images([str(fp) for fp in file_paths])
    
    def remove_image(self, index: int) -> bool:
        """移除指定索引的图片"""
        if 0 <= index < len(self.images):
            removed_image = self.images.pop(index)
            self.images_removed.emit([removed_image])
            
            # 调整当前索引
            if self.current_index >= index:
                self.current_index = max(-1, self.current_index - 1)
            
            return True
        return False
    
    def remove_images(self, indices: List[int]) -> bool:
        """移除多个图片"""
        if not indices:
            return False
        
        # 按降序排序，从后往前删除
        indices.sort(reverse=True)
        removed_images = []
        
        for index in indices:
            if 0 <= index < len(self.images):
                removed_images.append(self.images.pop(index))
        
        if removed_images:
            self.images_removed.emit(removed_images)
            
            # 重置当前索引
            if self.current_index in indices or self.current_index >= len(self.images):
                self.current_index = min(self.current_index, len(self.images) - 1)
            
            return True
        return False
    
    def clear_images(self):
        """清空所有图片"""
        self.images.clear()
        self.current_index = -1
        self.images_cleared.emit()
    
    def get_image_info(self, index: int) -> Optional[ImageInfo]:
        """获取指定索引的图片信息"""
        if 0 <= index < len(self.images):
            return self.images[index]
        return None
    
    def get_current_image(self) -> Optional[ImageInfo]:
        """获取当前选中的图片"""
        return self.get_image_info(self.current_index)
    
    def set_current_index(self, index: int) -> bool:
        """设置当前选中的图片索引"""
        if 0 <= index < len(self.images):
            self.current_index = index
            return True
        return False
    
    def is_supported_format(self, file_path: str) -> bool:
        """检查文件格式是否支持"""
        return Path(file_path).suffix.lower() in self.supported_formats
    
    def is_already_added(self, file_path: str) -> bool:
        """检查图片是否已经添加"""
        file_path = Path(file_path)
        return any(img.file_path == file_path for img in self.images)
    
    @property
    def image_count(self) -> int:
        """图片数量"""
        return len(self.images)
    
    @property
    def is_empty(self) -> bool:
        """是否为空"""
        return len(self.images) == 0
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        if not self.images:
            return {'count': 0, 'total_size_mb': 0, 'formats': {}}
        
        total_size = sum(img.size for img in self.images)
        formats = {}
        
        for img in self.images:
            ext = img.file_path.suffix.lower()
            formats[ext] = formats.get(ext, 0) + 1
        
        return {
            'count': len(self.images),
            'total_size_mb': total_size / (1024 * 1024),
            'formats': formats
        }
    
    def set_current_index_by_path(self, file_path: str):
        """通过文件路径设置当前索引"""
        for i, img in enumerate(self.images):
            if str(img.file_path) == file_path:
                self.current_index = i
                return True
        return False