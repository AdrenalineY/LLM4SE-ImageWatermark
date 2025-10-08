#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Photo Watermark 2.0 - GUI Application
基于EXIF拍摄时间信息为图片添加水印的桌面应用程序
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from ui.main_window import MainWindow


def main():
    """主函数"""
    # 设置高DPI支持（必须在创建QApplication之前）
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    # 创建应用程序实例
    app = QApplication(sys.argv)
    
    # 设置应用程序属性
    app.setApplicationName("Photo Watermark 2.0")
    app.setApplicationVersion("2.0.0")
    app.setOrganizationName("LLM4SE Project")
    app.setOrganizationDomain("github.com/AdrenalineY/LLM4SE-ImageWatermark")
    
    # 设置应用程序图标（如果存在）
    icon_path = project_root / "resources" / "icon.ico"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))
    
    # 创建主窗口
    main_window = MainWindow()
    
    # 检查是否为测试模式
    if '--test' in sys.argv:
        print("GUI应用程序测试启动成功!")
        main_window.close()
        return 0
    
    main_window.show()
    
    # 启动事件循环
    return app.exec_()


if __name__ == "__main__":
    sys.exit(main())