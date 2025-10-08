#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置管理器模块
负责应用程序配置的保存、加载和管理
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
from PyQt5.QtCore import QObject, pyqtSignal


class ConfigManager(QObject):
    """配置管理器"""
    
    # 信号定义
    config_loaded = pyqtSignal(dict)  # 配置加载完成
    config_saved = pyqtSignal()       # 配置保存完成
    
    def __init__(self):
        super().__init__()
        self.config_path = Path.home() / '.photo_watermark_gui_config.json'
        self.templates_path = Path.home() / '.photo_watermark_templates.json'
        
        # 默认配置
        self.default_config = {
            'window': {
                'geometry': None,  # 窗口几何信息
                'maximized': False,
                'splitter_sizes': None  # 分割器尺寸
            },
            'watermark': {
                'text': '',
                'font_size': 36,
                'font_family': 'Arial',
                'font_bold': False,
                'font_italic': False,
                'color': 'white',
                'opacity': 100,
                'position': 'bottom-right',
                'shadow_enabled': False,
                'shadow_offset': [2, 2],
                'shadow_color': 'black',
                'shadow_opacity': 50,
                'stroke_enabled': False,
                'stroke_width': 1,
                'stroke_color': 'black',
                'image_watermark_path': '',
                'image_scale': 1.0,
                'image_opacity': 100,
                'custom_position': None,
                'rotation': 0
            },
            'export': {
                'output_format': 'JPEG',
                'jpeg_quality': 95,
                'naming_rule': 'original',  # original, prefix, suffix
                'custom_prefix': 'wm_',
                'custom_suffix': '_watermarked',
                'output_dir': str(Path.home() / 'Desktop'),
                'preserve_exif': True
            },
            'ui': {
                'preview_size': 'fit',  # fit, actual, custom
                'show_thumbnails': True,
                'thumbnail_size': 64,
                'auto_preview': True,
                'theme': 'system'  # system, light, dark
            },
            'recent': {
                'directories': [],  # 最近使用的目录
                'templates': [],    # 最近使用的模板
                'max_recent': 10
            }
        }
        
        import copy
        self.current_config = copy.deepcopy(self.default_config)
        self.templates = {}  # 水印模板
    
    def load_config(self) -> Dict[str, Any]:
        """加载配置"""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    
                # 合并配置（保留默认值）
                self.current_config = self._merge_configs(self.default_config, loaded_config)
            else:
                self.current_config = self.default_config.copy()
            
            self.config_loaded.emit(self.current_config)
            return self.current_config
            
        except Exception as e:
            print(f"加载配置失败: {e}")
            self.current_config = self.default_config.copy()
            return self.current_config
    
    def save_config(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """保存配置"""
        try:
            if config:
                self.current_config = config
            
            # 确保目录存在
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.current_config, f, indent=2, ensure_ascii=False)
            
            self.config_saved.emit()
            return True
            
        except Exception as e:
            print(f"保存配置失败: {e}")
            return False
    
    def get_config(self, section: str, key: str = None, default=None):
        """获取配置值"""
        if key is None:
            return self.current_config.get(section, default)
        return self.current_config.get(section, {}).get(key, default)
    
    def set_config(self, section: str, key: str = None, value=None):
        """设置配置值"""
        if key is None:
            # 设置整个section
            self.current_config[section] = value
        else:
            # 设置特定key
            if section not in self.current_config:
                self.current_config[section] = {}
            self.current_config[section][key] = value
    
    def load_templates(self) -> Dict[str, Any]:
        """加载水印模板"""
        try:
            if self.templates_path.exists():
                with open(self.templates_path, 'r', encoding='utf-8') as f:
                    self.templates = json.load(f)
            else:
                self.templates = {}
            
            return self.templates
            
        except Exception as e:
            print(f"加载模板失败: {e}")
            self.templates = {}
            return self.templates
    
    def save_templates(self) -> bool:
        """保存水印模板"""
        try:
            self.templates_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.templates_path, 'w', encoding='utf-8') as f:
                json.dump(self.templates, f, indent=2, ensure_ascii=False)
            
            return True
            
        except Exception as e:
            print(f"保存模板失败: {e}")
            return False
    
    def add_template(self, name: str, template_data: Dict[str, Any]) -> bool:
        """添加水印模板"""
        try:
            self.templates[name] = {
                'data': template_data,
                'created_time': self._get_current_time(),
                'modified_time': self._get_current_time()
            }
            
            # 更新最近使用的模板列表
            recent_templates = self.current_config['recent']['templates']
            if name in recent_templates:
                recent_templates.remove(name)
            recent_templates.insert(0, name)
            
            # 限制最近模板数量
            max_recent = self.current_config['recent']['max_recent']
            self.current_config['recent']['templates'] = recent_templates[:max_recent]
            
            return self.save_templates()
            
        except Exception as e:
            print(f"添加模板失败: {e}")
            return False
    
    def get_template(self, name: str) -> Optional[Dict[str, Any]]:
        """获取水印模板"""
        return self.templates.get(name, {}).get('data')
    
    def remove_template(self, name: str) -> bool:
        """删除水印模板"""
        try:
            if name in self.templates:
                del self.templates[name]
                
                # 从最近使用列表中移除
                recent_templates = self.current_config['recent']['templates']
                if name in recent_templates:
                    recent_templates.remove(name)
                
                return self.save_templates()
            return False
            
        except Exception as e:
            print(f"删除模板失败: {e}")
            return False
    
    def get_template_list(self) -> list:
        """获取模板列表"""
        return [
            {
                'name': name,
                'created_time': info.get('created_time', ''),
                'modified_time': info.get('modified_time', '')
            }
            for name, info in self.templates.items()
        ]
    
    def add_recent_directory(self, directory: str):
        """添加最近使用的目录"""
        recent_dirs = self.current_config['recent']['directories']
        if directory in recent_dirs:
            recent_dirs.remove(directory)
        recent_dirs.insert(0, directory)
        
        # 限制最近目录数量
        max_recent = self.current_config['recent']['max_recent']
        self.current_config['recent']['directories'] = recent_dirs[:max_recent]
    
    def get_recent_directories(self) -> list:
        """获取最近使用的目录"""
        return self.current_config['recent']['directories']
    
    def reset_to_defaults(self, section: str = None) -> bool:
        """重置为默认配置"""
        try:
            import copy
            if section:
                self.current_config[section] = copy.deepcopy(self.default_config[section])
            else:
                self.current_config = copy.deepcopy(self.default_config)
            
            return self.save_config()
            
        except Exception as e:
            print(f"重置配置失败: {e}")
            return False
    
    def export_config(self, file_path: str) -> bool:
        """导出配置"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                export_data = {
                    'config': self.current_config,
                    'templates': self.templates,
                    'export_time': self._get_current_time()
                }
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            return True
            
        except Exception as e:
            print(f"导出配置失败: {e}")
            return False
    
    def import_config(self, file_path: str) -> bool:
        """导入配置"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                import_data = json.load(f)
            
            # 导入配置
            if 'config' in import_data:
                self.current_config = self._merge_configs(
                    self.default_config, import_data['config']
                )
            
            # 导入模板
            if 'templates' in import_data:
                self.templates.update(import_data['templates'])
                self.save_templates()
            
            return self.save_config()
            
        except Exception as e:
            print(f"导入配置失败: {e}")
            return False
    
    def _merge_configs(self, default: Dict[str, Any], loaded: Dict[str, Any]) -> Dict[str, Any]:
        """合并配置，保留默认值"""
        result = default.copy()
        
        for key, value in loaded.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key].update(value)
            else:
                result[key] = value
        
        return result
    
    def _get_current_time(self) -> str:
        """获取当前时间字符串"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    @property
    def config_file_exists(self) -> bool:
        """配置文件是否存在"""
        return self.config_path.exists()
    
    @property
    def templates_file_exists(self) -> bool:
        """模板文件是否存在"""
        return self.templates_path.exists()