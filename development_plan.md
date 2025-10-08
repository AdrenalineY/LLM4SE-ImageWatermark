# Photo Watermark 2.0 开发计划与任务分解

## 开发策略概述

基于现有命令行版本的稳定核心功能，采用**渐进式开发**策略，确保每个阶段都有可运行的版本。优先实现基础功能，然后逐步添加高级特性。

## 技术选型建议

### GUI框架对比分析

| 框架 | 优势 | 劣势 | 推荐度 |
|------|------|------|--------|
| **tkinter** | 内置，无需额外依赖；打包体积小 | 界面较简陋；高级控件有限 | ⭐⭐⭐ |
| **PyQt5/6** | 界面美观；功能强大；跨平台好 | 学习曲线陡；许可证复杂 | ⭐⭐⭐⭐⭐ |
| **Kivy** | 现代化界面；触控支持好 | 桌面应用不常见；学习成本高 | ⭐⭐ |

**推荐选择**: **PyQt5** - 功能完整，界面美观，社区支持好

### 项目依赖管理

```python
# requirements_gui.txt
PyQt5==5.15.9
Pillow>=9.0.0
ExifRead>=3.0.0
PyInstaller>=5.0.0  # 用于打包
```

## 详细任务分解

### 第一阶段：基础功能实现 (4-5周)

#### Week 1: 项目架构与基础UI

**Task 1.1: 项目架构搭建** (2天)
```python
# 创建项目结构
photo_watermark_gui/
├── main.py
├── core/
│   ├── image_manager.py
│   ├── watermark_engine.py  # 继承命令行版本
│   └── config_manager.py
├── ui/
│   ├── main_window.py
│   ├── preview_widget.py
│   └── settings_panel.py
└── utils/
    ├── file_utils.py
    └── image_utils.py
```

**开发要点**:
- 设计清晰的模块接口
- 建立事件通信机制
- 继承现有的`ImageWatermarker`类

**Task 1.2: 主窗口框架** (3天)
- 创建主窗口布局（三栏式设计）
- 实现菜单栏基础结构
- 添加状态栏显示
- 设置窗口图标和标题

```python
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.setup_layout()
        self.setup_connections()
        
    def setup_ui(self):
        """设置用户界面"""
        self.setWindowTitle("Photo Watermark 2.0")
        self.setMinimumSize(1200, 800)
        
    def setup_layout(self):
        """设置布局"""
        # 三栏布局：文件列表 | 预览区 | 设置面板
        pass
```

#### Week 2: 文件管理与预览系统

**Task 2.1: 图片导入功能** (3天)
- 实现拖拽导入功能
- 文件/文件夹选择对话框
- 图片格式验证
- 缩略图生成和显示

```python
class ImageListWidget(QListWidget):
    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)
        self.setDragDropMode(QAbstractItemView.DropOnly)
        
    def dropEvent(self, event):
        """处理拖拽事件"""
        files = [url.toLocalFile() for url in event.mimeData().urls()]
        self.parent().load_images(files)
        
    def dragEnterEvent(self, event):
        """拖拽进入事件"""
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()
```

**Task 2.2: 预览系统** (2天)
- 图片预览窗口实现
- 预览图缩放算法
- 列表选择联动更新

```python
class PreviewWidget(QLabel):
    def __init__(self):
        super().__init__()
        self.setMinimumSize(400, 300)
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet("border: 1px solid gray;")
        
    def update_preview(self, image_path, watermark_settings=None):
        """更新预览显示"""
        # 加载图片
        # 应用水印预览
        # 缩放适配显示
        pass
```

#### Week 3: 基础水印功能

**Task 3.1: 水印引擎适配** (2天)
- 将命令行版本的水印功能适配为GUI版本
- 实现实时预览的水印应用
- 优化性能，避免重复计算

```python
class WatermarkEngine:
    def __init__(self):
        # 继承命令行版本的核心功能
        self.base_watermarker = ImageWatermarker()
        
    def apply_preview_watermark(self, image, settings):
        """应用水印用于预览（不保存文件）"""
        # 在内存中处理，返回PIL Image对象
        pass
        
    def batch_apply_watermark(self, image_list, settings, output_dir, progress_callback=None):
        """批量应用水印"""
        pass
```

**Task 3.2: 文本水印UI控件** (3天)
- 文本输入框
- 字体大小滑块
- 颜色选择按钮
- 透明度滑块
- 九宫格位置选择

```python
class TextWatermarkPanel(QWidget):
    # 信号定义
    settings_changed = pyqtSignal(dict)
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.connect_signals()
        
    def setup_ui(self):
        """设置UI控件"""
        layout = QVBoxLayout()
        
        # 文本输入
        self.text_edit = QTextEdit()
        self.text_edit.setMaximumHeight(100)
        
        # 字体大小
        self.font_size_slider = QSlider(Qt.Horizontal)
        self.font_size_slider.setRange(12, 200)
        self.font_size_slider.setValue(36)
        
        # 添加到布局
        layout.addWidget(QLabel("水印文本:"))
        layout.addWidget(self.text_edit)
        # ... 其他控件
        
    def connect_signals(self):
        """连接信号槽"""
        self.text_edit.textChanged.connect(self.on_settings_changed)
        self.font_size_slider.valueChanged.connect(self.on_settings_changed)
        
    def on_settings_changed(self):
        """设置变更时发送信号"""
        settings = self.get_current_settings()
        self.settings_changed.emit(settings)
```

#### Week 4: 导出功能与配置管理

**Task 4.1: 导出功能** (3天)
- 输出目录选择
- 文件命名规则设置
- 格式选择（JPEG/PNG）
- 进度条显示
- 批量导出逻辑

```python
class ExportManager:
    def __init__(self):
        self.naming_rules = {
            'original': lambda name: name,
            'prefix': lambda name, prefix: f"{prefix}{name}",
            'suffix': lambda name, suffix: f"{name.stem}{suffix}{name.suffix}"
        }
        
    def export_images(self, image_list, settings, output_dir, progress_callback=None):
        """批量导出图片"""
        total = len(image_list)
        for i, image_path in enumerate(image_list):
            # 应用水印
            # 生成输出文件名
            # 保存文件
            if progress_callback:
                progress_callback(i + 1, total)
```

**Task 4.2: 基础配置管理** (2天)
- JSON配置文件读写
- 程序启动时加载设置
- 程序关闭时保存设置

```python
class ConfigManager:
    def __init__(self):
        self.config_path = Path.home() / '.photo_watermark_config.json'
        self.default_config = {
            'watermark': {
                'text': '',
                'font_size': 36,
                'color': 'white',
                'opacity': 100,
                'position': 'bottom-right'
            },
            'export': {
                'format': 'JPEG',
                'naming_rule': 'original',
                'output_dir': str(Path.home() / 'Desktop')
            }
        }
        
    def load_config(self):
        """加载配置"""
        if self.config_path.exists():
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return self.default_config.copy()
        
    def save_config(self, config):
        """保存配置"""
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
```

### 第二阶段：高级功能实现 (3-4周)

#### Week 5: 高级文本水印功能

**Task 5.1: 高级字体设置** (2天)
- 系统字体枚举和选择
- 粗体/斜体支持
- 字体预览功能

**Task 5.2: 高级颜色选择** (2天)
- 完整调色板实现
- RGB/HSV输入支持
- 颜色历史记录

**Task 5.3: 文字效果** (3天)
- 阴影效果实现
- 描边效果实现
- 效果预览优化

#### Week 6: 图片水印功能

**Task 6.1: 图片水印基础** (3天)
- 图片水印文件选择
- PNG透明度支持
- 水印图片预览

**Task 6.2: 图片水印调整** (2天)
- 缩放控制
- 透明度调节
- 位置调整

#### Week 7: 交互增强功能

**Task 7.1: 拖拽定位** (3天)
- 预览区域鼠标事件处理
- 水印拖拽实现
- 边界检测和限制

**Task 7.2: 旋转功能** (2天)
- 旋转角度控制
- 旋转预览效果
- 旋转算法优化

#### Week 8: 高级配置与优化

**Task 8.1: 模板系统** (3天)
- 模板保存/加载
- 模板管理界面
- 模板预览功能

**Task 8.2: 性能优化** (2天)
- 预览更新性能优化
- 内存使用优化
- 多线程处理导出

### 第三阶段：打包发布 (1-2周)

#### Week 9: 打包与测试

**Task 9.1: 应用程序打包** (3天)
```python
# build_windows.py
import PyInstaller.__main__

PyInstaller.__main__.run([
    'main.py',
    '--onefile',
    '--windowed',
    '--icon=resources/icon.ico',
    '--name=PhotoWatermark',
    '--add-data=resources;resources',
    '--clean'
])
```

**Task 9.2: 跨平台测试** (2天)
- Windows 10/11测试
- macOS测试（如有条件）
- 不同分辨率适配测试

**Task 9.3: 用户文档** (2天)
- 用户使用手册
- 安装说明
- 常见问题解答

## 风险控制与质量保证

### 主要风险点

1. **性能风险**: 大图片预览可能导致界面卡顿
   - **解决方案**: 多线程处理，预览图缩放限制

2. **兼容性风险**: 不同系统的字体和颜色显示差异
   - **解决方案**: 提供字体回退机制，颜色标准化

3. **用户体验风险**: 复杂功能可能影响易用性
   - **解决方案**: 提供默认设置，渐进式功能展示

### 测试策略

#### 单元测试重点
```python
# 测试核心功能
def test_watermark_engine():
    """测试水印引擎功能"""
    pass

def test_image_processing():
    """测试图片处理功能"""
    pass

def test_config_management():
    """测试配置管理功能"""
    pass
```

#### 集成测试重点
- 完整工作流程测试
- 异常情况处理测试
- 边界条件测试

#### 用户验收测试
- 新手用户易用性测试
- 高级用户功能完整性测试
- 不同场景应用测试

## 开发环境配置

### 开发工具链
```bash
# 创建虚拟环境
python -m venv photo_watermark_env
source photo_watermark_env/bin/activate  # Linux/Mac
# or
photo_watermark_env\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements_gui.txt

# 开发工具
pip install pytest  # 单元测试
pip install black   # 代码格式化
pip install flake8  # 代码检查
```

### IDE配置建议
推荐使用 **PyCharm** 或 **VS Code**：
- 配置自动代码格式化
- 启用类型检查
- 配置调试环境
- 集成版本控制

## Git提交规范

### 提交信息格式
```
<type>(<scope>): <subject>

<body>

<footer>
```

### 提交类型
- `feat`: 新功能
- `fix`: Bug修复
- `docs`: 文档更新
- `style`: 代码格式调整
- `refactor`: 代码重构
- `test`: 测试相关
- `build`: 构建相关

### 示例提交
```
feat(ui): add image drag-and-drop support

- Implement drag and drop functionality for main window
- Add visual feedback during drag operations
- Support both single files and directories
- Add file format validation

Closes #12
```

## 发布计划

### 版本规划
- **v2.0.0-alpha**: 基础功能完成
- **v2.0.0-beta**: 高级功能完成
- **v2.0.0**: 正式发布版本

### GitHub Release内容
```markdown
## Photo Watermark v2.0.0

### 新增功能
- 🖼️ 直观的GUI界面
- 📁 支持拖拽导入图片/文件夹
- 👁️ 实时预览水印效果
- 🎨 丰富的文本水印设置
- 📐 九宫格位置快速设置
- 💾 配置自动保存/恢复

### 下载
- [Windows 64位](releases/download/v2.0.0/PhotoWatermark-v2.0.0-win64.exe)
- [macOS](releases/download/v2.0.0/PhotoWatermark-v2.0.0-macos.dmg)

### 系统要求
- Windows 10/11 或 macOS 10.14+
- 至少2GB可用内存
- 100MB可用磁盘空间
```

这个开发计划提供了详细的任务分解和时间安排，确保项目能够按时完成并达到预期的质量标准。每个任务都包含了具体的代码示例和实现要点，便于开发过程中的参考和执行。