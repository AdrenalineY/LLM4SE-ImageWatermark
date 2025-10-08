#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
水印引擎模块
继承命令行版本的水印处理功能，适配GUI版本需求
"""

import sys
import os
from pathlib import Path
from typing import Optional, Dict, Any, Tuple, Callable
from PIL import Image, ImageDraw, ImageFont
from PIL.ExifTags import TAGS
import exifread
from PyQt5.QtCore import QObject, pyqtSignal, QThread

# 导入现有的命令行版本水印功能
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from image_watermark import ImageWatermarker
except ImportError:
    # 如果无法导入，则定义一个简化版本
    class ImageWatermarker:
        def __init__(self):
            self.supported_formats = {'.jpg', '.jpeg', '.png', '.tiff', '.bmp'}
            self.position_map = {
                'top-left': 'top_left',
                'top-center': 'top_center', 
                'top-right': 'top_right',
                'center-left': 'center_left',
                'center': 'center',
                'center-right': 'center_right',
                'bottom-left': 'bottom_left',
                'bottom-center': 'bottom_center',
                'bottom-right': 'bottom_right'
            }


class WatermarkSettings:
    """水印设置类"""
    
    def __init__(self):
        # 文本水印设置
        self.text = ""
        self.font_size = 36
        self.font_family = "Arial"
        self.font_bold = False
        self.font_italic = False
        self.color = "white"
        self.opacity = 100  # 0-100
        self.position = "bottom-right"
        
        # 文本效果
        self.shadow_enabled = False
        self.shadow_offset = (2, 2)
        self.shadow_color = "black"
        self.shadow_opacity = 50
        
        self.stroke_enabled = False
        self.stroke_width = 1
        self.stroke_color = "black"
        
        # 图片水印设置（高级功能）
        self.image_watermark_path = ""
        self.image_scale = 1.0
        self.image_opacity = 100
        
        # 位置调整
        self.custom_position = None  # (x, y) 自定义位置
        self.rotation = 0  # 旋转角度
        
        # 输出设置
        self.output_format = "JPEG"
        self.jpeg_quality = 95
        self.preserve_exif = True
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'text': self.text,
            'font_size': self.font_size,
            'font_family': self.font_family,
            'font_bold': self.font_bold,
            'font_italic': self.font_italic,
            'color': self.color,
            'opacity': self.opacity,
            'position': self.position,
            'shadow_enabled': self.shadow_enabled,
            'shadow_offset': self.shadow_offset,
            'shadow_color': self.shadow_color,
            'shadow_opacity': self.shadow_opacity,
            'stroke_enabled': self.stroke_enabled,
            'stroke_width': self.stroke_width,
            'stroke_color': self.stroke_color,
            'image_watermark_path': self.image_watermark_path,
            'image_scale': self.image_scale,
            'image_opacity': self.image_opacity,
            'custom_position': self.custom_position,
            'rotation': self.rotation,
            'output_format': self.output_format,
            'jpeg_quality': self.jpeg_quality,
            'preserve_exif': self.preserve_exif
        }
    
    def from_dict(self, data: Dict[str, Any]):
        """从字典加载"""
        for key, value in data.items():
            if hasattr(self, key):
                setattr(self, key, value)


class WatermarkEngine(QObject):
    """水印处理引擎"""
    
    # 信号定义
    preview_ready = pyqtSignal(object)  # 预览准备完成
    progress_updated = pyqtSignal(int, int)  # 进度更新 (current, total)
    processing_finished = pyqtSignal(bool, str)  # 处理完成 (success, message)
    
    def __init__(self):
        super().__init__()
        self.base_watermarker = ImageWatermarker()
        self.current_settings = WatermarkSettings()
        
    def apply_preview_watermark(self, image_path: str, settings: WatermarkSettings) -> Optional[Image.Image]:
        """应用水印用于预览（不保存文件）"""
        try:
            with Image.open(image_path) as img:
                # 复制图片以避免修改原图
                preview_img = img.copy()
                
                # 如果没有文本，直接返回原图
                if not settings.text.strip():
                    return preview_img
                
                # 应用水印
                watermarked_img = self._apply_text_watermark(preview_img, settings)
                return watermarked_img
                
        except Exception as e:
            print(f"预览水印应用失败: {e}")
            return None
    
    def _apply_text_watermark(self, img: Image.Image, settings: WatermarkSettings) -> Image.Image:
        """应用文本水印"""
        # 转换为RGBA模式以支持透明度
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
        
        # 创建绘图对象
        draw = ImageDraw.Draw(img)
        
        # 加载字体
        font = self._load_font(settings.font_family, settings.font_size, 
                              settings.font_bold, settings.font_italic)
        
        # 获取文本尺寸
        bbox = draw.textbbox((0, 0), settings.text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        # 计算位置
        if settings.custom_position:
            x, y = settings.custom_position
        else:
            x, y = self._calculate_text_position(
                img.size, (text_width, text_height), settings.position
            )
        
        # 解析颜色和透明度
        text_color = self._parse_color(settings.color, settings.opacity)
        
        # 应用阴影效果
        if settings.shadow_enabled:
            shadow_color = self._parse_color(settings.shadow_color, settings.shadow_opacity)
            shadow_x = x + settings.shadow_offset[0]
            shadow_y = y + settings.shadow_offset[1]
            draw.text((shadow_x, shadow_y), settings.text, font=font, fill=shadow_color)
        
        # 应用描边效果
        if settings.stroke_enabled:
            stroke_color = self._parse_color(settings.stroke_color, 100)
            # 简单的描边实现
            for adj_x in range(-settings.stroke_width, settings.stroke_width + 1):
                for adj_y in range(-settings.stroke_width, settings.stroke_width + 1):
                    if adj_x != 0 or adj_y != 0:
                        draw.text((x + adj_x, y + adj_y), settings.text, 
                                font=font, fill=stroke_color)
        
        # 绘制主文本
        draw.text((x, y), settings.text, font=font, fill=text_color)
        
        return img
    
    def _load_font(self, family: str, size: int, bold: bool = False, italic: bool = False) -> ImageFont.ImageFont:
        """加载字体"""
        try:
            # Windows系统常用字体路径
            font_paths = [
                f'C:/Windows/Fonts/{family.lower()}.ttf',
                'C:/Windows/Fonts/simhei.ttf',  # 黑体
                'C:/Windows/Fonts/msyh.ttc',    # 微软雅黑
                'C:/Windows/Fonts/arial.ttf',   # Arial
            ]
            
            font = None
            for font_path in font_paths:
                if os.path.exists(font_path):
                    font = ImageFont.truetype(font_path, size)
                    break
            
            if font is None:
                font = ImageFont.load_default()
            
            return font
            
        except Exception:
            return ImageFont.load_default()
    
    def _calculate_text_position(self, img_size: Tuple[int, int], text_size: Tuple[int, int], 
                                position: str, margin: int = 20) -> Tuple[int, int]:
        """计算文本位置"""
        img_width, img_height = img_size
        text_width, text_height = text_size
        
        # 使用现有的位置映射
        position_key = self.base_watermarker.position_map.get(position, 'bottom_right')
        
        positions = {
            'top_left': (margin, margin),
            'top_center': ((img_width - text_width) // 2, margin),
            'top_right': (img_width - text_width - margin, margin),
            'center_left': (margin, (img_height - text_height) // 2),
            'center': ((img_width - text_width) // 2, (img_height - text_height) // 2),
            'center_right': (img_width - text_width - margin, (img_height - text_height) // 2),
            'bottom_left': (margin, img_height - text_height - margin),
            'bottom_center': ((img_width - text_width) // 2, img_height - text_height - margin),
            'bottom_right': (img_width - text_width - margin, img_height - text_height - margin)
        }
        
        return positions.get(position_key, positions['bottom_right'])
    
    def _parse_color(self, color: str, opacity: int) -> Tuple[int, int, int, int]:
        """解析颜色和透明度"""
        if color.startswith('#'):
            # 十六进制颜色
            color = color.lstrip('#')
            rgb = tuple(int(color[i:i+2], 16) for i in (0, 2, 4))
        else:
            # 预定义颜色
            color_map = {
                'white': (255, 255, 255),
                'black': (0, 0, 0),
                'red': (255, 0, 0),
                'blue': (0, 0, 255),
                'green': (0, 255, 0),
                'yellow': (255, 255, 0)
            }
            rgb = color_map.get(color.lower(), (255, 255, 255))
        
        # 添加透明度
        alpha = int(255 * opacity / 100)
        return rgb + (alpha,)
    
    def extract_exif_date(self, image_path: str) -> Optional[str]:
        """提取EXIF日期信息"""
        # 使用现有的日期提取逻辑
        return self.base_watermarker.extract_date_from_exif(image_path)
    
    def update_settings(self, settings: WatermarkSettings):
        """更新水印设置"""
        self.current_settings = settings


class BatchProcessingThread(QThread):
    """批量处理线程"""
    
    progress_updated = pyqtSignal(int, int)  # current, total
    item_processed = pyqtSignal(str, bool, str)  # filename, success, message
    finished_processing = pyqtSignal(bool, str)  # overall success, message
    
    def __init__(self, image_paths: list, settings: WatermarkSettings, 
                 output_dir: str, naming_rule: str):
        super().__init__()
        self.image_paths = image_paths
        self.settings = settings
        self.output_dir = output_dir
        self.naming_rule = naming_rule
        self.engine = WatermarkEngine()
        self._stop_requested = False
    
    def run(self):
        """执行批量处理"""
        total = len(self.image_paths)
        success_count = 0
        
        for i, image_path in enumerate(self.image_paths):
            if self._stop_requested:
                break
                
            try:
                # 处理单张图片
                success = self._process_single_image(image_path)
                if success:
                    success_count += 1
                    
                self.item_processed.emit(
                    Path(image_path).name, success, 
                    "成功" if success else "失败"
                )
                
            except Exception as e:
                self.item_processed.emit(
                    Path(image_path).name, False, str(e)
                )
            
            self.progress_updated.emit(i + 1, total)
        
        # 发出完成信号
        if not self._stop_requested:
            message = f"处理完成: {success_count}/{total} 张图片成功"
            self.finished_processing.emit(success_count > 0, message)
    
    def _process_single_image(self, image_path: str) -> bool:
        """处理单张图片"""
        try:
            # 应用水印
            watermarked_img = self.engine.apply_preview_watermark(image_path, self.settings)
            if watermarked_img is None:
                return False
            
            # 生成输出文件名
            output_path = self._generate_output_path(image_path)
            
            # 保存文件
            if self.settings.output_format.upper() == 'JPEG':
                if watermarked_img.mode == 'RGBA':
                    # JPEG不支持透明度，转换为RGB
                    rgb_img = Image.new('RGB', watermarked_img.size, (255, 255, 255))
                    rgb_img.paste(watermarked_img, mask=watermarked_img.split()[-1])
                    rgb_img.save(output_path, 'JPEG', quality=self.settings.jpeg_quality)
                else:
                    watermarked_img.save(output_path, 'JPEG', quality=self.settings.jpeg_quality)
            else:
                watermarked_img.save(output_path, self.settings.output_format)
            
            return True
            
        except Exception:
            return False
    
    def _generate_output_path(self, image_path: str) -> str:
        """生成输出文件路径"""
        input_path = Path(image_path)
        
        if self.naming_rule == 'prefix':
            filename = f"wm_{input_path.stem}"
        elif self.naming_rule == 'suffix':
            filename = f"{input_path.stem}_watermarked"
        else:  # original
            filename = input_path.stem
        
        # 根据输出格式确定扩展名
        if self.settings.output_format.upper() == 'JPEG':
            ext = '.jpg'
        else:
            ext = f'.{self.settings.output_format.lower()}'
        
        return str(Path(self.output_dir) / f"{filename}{ext}")
    
    def stop(self):
        """停止处理"""
        self._stop_requested = True