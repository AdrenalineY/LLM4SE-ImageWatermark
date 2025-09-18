#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图片水印工具
基于EXIF拍摄时间信息为图片添加水印
"""

import os
import sys
import argparse
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from datetime import datetime

# 导入图像处理相关库
try:
    from PIL import Image, ImageDraw, ImageFont
    from PIL.ExifTags import TAGS
    import exifread
except ImportError as e:
    print(f"缺少必需的库: {e}")
    print("请运行: pip install Pillow exifread")
    sys.exit(1)


class ImageWatermarker:
    """图片水印处理类"""
    
    def __init__(self):
        # 支持的图片格式
        self.supported_formats = {'.jpg', '.jpeg', '.png', '.tiff', '.bmp'}
        # 位置映射
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
    
    def extract_date_from_exif(self, image_path: str) -> Optional[str]:
        """从EXIF信息中提取拍摄日期"""
        try:
            # 尝试使用PIL读取EXIF
            with Image.open(image_path) as img:
                exif_data = img._getexif()
                if exif_data:
                    for tag_id, value in exif_data.items():
                        tag = TAGS.get(tag_id, tag_id)
                        if tag in ['DateTime', 'DateTimeOriginal', 'DateTimeDigitized']:
                            if value:
                                # 解析日期格式: "YYYY:MM:DD HH:MM:SS"
                                date_str = str(value).split()[0]  # 只取日期部分
                                date_parts = date_str.split(':')
                                if len(date_parts) == 3:
                                    return f"{date_parts[0]}-{date_parts[1]}-{date_parts[2]}"
        except Exception as e:
            print(f"    PIL读取EXIF出错: {e}")
        
        # 如果PIL失败，尝试使用exifread
        try:
            with open(image_path, 'rb') as f:
                tags = exifread.process_file(f)
                for tag_key in ['EXIF DateTimeOriginal', 'EXIF DateTime', 'Image DateTime']:
                    if tag_key in tags:
                        date_str = str(tags[tag_key]).split()[0]
                        date_parts = date_str.split(':')
                        if len(date_parts) == 3:
                            return f"{date_parts[0]}-{date_parts[1]}-{date_parts[2]}"
        except Exception as e:
            print(f"    ExifRead读取EXIF出错: {e}")
        
        # 作为最后手段，使用文件的修改时间
        try:
            from datetime import datetime
            stat = os.path.stat(image_path)
            file_time = datetime.fromtimestamp(stat.st_mtime)
            return file_time.strftime("%Y-%m-%d")
        except Exception as e:
            print(f"    读取文件时间出错: {e}")
        
        return None
    
    def calculate_text_position(self, img_size: Tuple[int, int], text_size: Tuple[int, int], 
                               position: str, margin: int = 20) -> Tuple[int, int]:
        """计算文本在图片上的位置坐标"""
        img_width, img_height = img_size
        text_width, text_height = text_size
        
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
        
        return positions.get(position, positions['bottom_right'])
    
    def hex_to_rgb(self, hex_color: str) -> Tuple[int, int, int]:
        """将十六进制颜色转换为RGB"""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    def add_watermark(self, image_path: str, watermark_text: str, font_size: int, 
                     color: str, position: str, output_path: str) -> bool:
        """为图片添加水印"""
        try:
            # 打开图片
            with Image.open(image_path) as img:
                # 转换为RGBA模式以支持透明度
                if img.mode != 'RGBA':
                    img = img.convert('RGBA')
                
                # 创建绘图对象
                draw = ImageDraw.Draw(img)
                
                # 尝试加载字体
                try:
                    # Windows系统常用字体路径
                    font_paths = [
                        'C:/Windows/Fonts/simhei.ttf',  # 黑体
                        'C:/Windows/Fonts/msyh.ttc',    # 微软雅黑
                        'C:/Windows/Fonts/arial.ttf',   # Arial
                    ]
                    font = None
                    for font_path in font_paths:
                        if os.path.exists(font_path):
                            font = ImageFont.truetype(font_path, font_size)
                            break
                    
                    if font is None:
                        font = ImageFont.load_default()
                except Exception:
                    font = ImageFont.load_default()
                
                # 获取文本尺寸
                bbox = draw.textbbox((0, 0), watermark_text, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
                
                # 计算文本位置
                position_key = self.position_map.get(position, 'bottom_right')
                x, y = self.calculate_text_position(
                    img.size, (text_width, text_height), position_key
                )
                
                # 解析颜色
                if color.startswith('#'):
                    text_color = self.hex_to_rgb(color) + (255,)  # 添加alpha通道
                else:
                    # 预定义颜色
                    color_map = {
                        'white': (255, 255, 255, 255),
                        'black': (0, 0, 0, 255),
                        'red': (255, 0, 0, 255),
                        'blue': (0, 0, 255, 255),
                        'green': (0, 255, 0, 255),
                        'yellow': (255, 255, 0, 255)
                    }
                    text_color = color_map.get(color.lower(), (255, 255, 255, 255))
                
                # 添加阴影效果（可选）
                shadow_offset = max(1, font_size // 20)
                draw.text((x + shadow_offset, y + shadow_offset), watermark_text, 
                         font=font, fill=(0, 0, 0, 128))  # 半透明黑色阴影
                
                # 绘制主文本
                draw.text((x, y), watermark_text, font=font, fill=text_color)
                
                # 确保输出目录存在
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                
                # 保存图片
                if img.mode == 'RGBA':
                    # 如果输出格式不支持透明度，转换为RGB
                    if output_path.lower().endswith('.jpg') or output_path.lower().endswith('.jpeg'):
                        rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                        rgb_img.paste(img, mask=img.split()[-1])
                        rgb_img.save(output_path, quality=95)
                    else:
                        img.save(output_path)
                else:
                    img.save(output_path, quality=95)
                
                return True
                
        except Exception as e:
            print(f"处理图片 {image_path} 时出错: {e}")
            return False
    
    def process_directory(self, input_dir: str, font_size: int, color: str, 
                         position: str) -> Dict[str, int]:
        """处理目录中的所有图片"""
        input_path = Path(input_dir)
        if not input_path.exists() or not input_path.is_dir():
            print(f"错误: 路径 '{input_dir}' 不存在或不是目录")
            return {'processed': 0, 'skipped': 0, 'errors': 0}
        
        # 创建输出目录
        output_dir = input_path / f"{input_path.name}_watermark"
        output_dir.mkdir(exist_ok=True)
        
        stats = {'processed': 0, 'skipped': 0, 'errors': 0}
        
        # 遍历所有文件
        for file_path in input_path.rglob('*'):
            # 跳过输出目录中的文件
            if output_dir in file_path.parents or file_path == output_dir:
                continue
                
            if file_path.is_file() and file_path.suffix.lower() in self.supported_formats:
                print(f"正在处理: {file_path.name}")
                
                # 提取拍摄日期
                date_text = self.extract_date_from_exif(str(file_path))
                
                if date_text is None:
                    print(f"  跳过: 无法从 EXIF 中提取日期信息")
                    stats['skipped'] += 1
                    continue
                
                # 生成输出文件路径
                relative_path = file_path.relative_to(input_path)
                output_file = output_dir / relative_path
                
                # 确保输出子目录存在
                output_file.parent.mkdir(parents=True, exist_ok=True)
                
                # 添加水印
                success = self.add_watermark(
                    str(file_path), date_text, font_size, color, position, str(output_file)
                )
                
                if success:
                    print(f"  完成: 添加水印 '{date_text}'")
                    stats['processed'] += 1
                else:
                    stats['errors'] += 1
        
        return stats


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='为图片添加基于EXIF拍摄时间的水印')
    parser.add_argument('input_path', help='输入图片目录路径')
    parser.add_argument('--font-size', '-s', type=int, default=36, 
                       help='字体大小 (默认: 36)')
    parser.add_argument('--color', '-c', default='white',
                       help='文字颜色 (支持: white, black, red, blue, green, yellow 或十六进制 #RRGGBB，默认: white)')
    parser.add_argument('--position', '-p', default='bottom-right',
                       choices=['top-left', 'top-center', 'top-right',
                               'center-left', 'center', 'center-right', 
                               'bottom-left', 'bottom-center', 'bottom-right'],
                       help='水印位置 (默认: bottom-right)')
    
    args = parser.parse_args()
    
    # 创建水印处理器
    watermarker = ImageWatermarker()
    
    print(f"开始处理目录: {args.input_path}")
    print(f"设置 - 字体大小: {args.font_size}, 颜色: {args.color}, 位置: {args.position}")
    print("-" * 50)
    
    # 处理图片
    stats = watermarker.process_directory(
        args.input_path, args.font_size, args.color, args.position
    )
    
    print("-" * 50)
    print("处理完成!")
    print(f"成功处理: {stats['processed']} 张图片")
    print(f"跳过: {stats['skipped']} 张图片")
    print(f"错误: {stats['errors']} 张图片")
    
    if stats['processed'] > 0:
        output_dir = Path(args.input_path) / f"{Path(args.input_path).name}_watermark"
        print(f"输出目录: {output_dir}")


if __name__ == '__main__':
    main()