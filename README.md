# 图片水印工具 (Image Watermark Tool)

基于EXIF拍摄时间信息为图片批量添加水印的Python命令行工具。

## 功能特点

- 🖼️ **自动读取EXIF信息**: 从图片文件中提取拍摄日期信息
- 📅 **日期水印**: 将拍摄日期（年-月-日格式）作为水印添加到图片上
- 🎨 **自定义样式**: 支持自定义字体大小、颜色和位置
- 📁 **批量处理**: 一次处理整个目录中的所有图片
- 💾 **智能保存**: 保持原目录结构，输出到新的子目录
- 🔧 **多格式支持**: 支持 JPG、PNG、TIFF、BMP 等常见图片格式

## 安装

### 1. 克隆项目
```bash
git clone <repository-url>
cd LLM4SE-ImageWatermark
```

### 2. 安装依赖
```bash
pip install -r requirements.txt
```

或手动安装：
```bash
pip install Pillow>=9.0.0 ExifRead>=3.0.0
```

## 使用方法

### 基本用法
```bash
python image_watermark.py <图片目录路径>
```

### 完整参数
```bash
python image_watermark.py <图片目录路径> [选项]
```

### 参数说明

| 参数 | 简写 | 类型 | 默认值 | 说明 |
|------|------|------|--------|------|
| `input_path` | - | 字符串 | 必需 | 输入图片目录路径 |
| `--font-size` | `-s` | 整数 | 36 | 字体大小 |
| `--color` | `-c` | 字符串 | white | 文字颜色 |
| `--position` | `-p` | 字符串 | bottom-right | 水印位置 |

### 颜色选项
- 预定义颜色: `white`, `black`, `red`, `blue`, `green`, `yellow`
- 十六进制颜色: `#RRGGBB` (如 `#FF0000` 表示红色)

### 位置选项
```
top-left        top-center        top-right
center-left     center            center-right  
bottom-left     bottom-center     bottom-right
```

## 使用示例

### 示例1: 基本使用
```bash
python image_watermark.py "C:\Photos\Vacation2023"
```
使用默认设置处理指定目录中的所有图片。

### 示例2: 自定义字体大小和颜色
```bash
python image_watermark.py "C:\Photos\Vacation2023" --font-size 48 --color red
```

### 示例3: 设置水印位置
```bash
python image_watermark.py "C:\Photos\Vacation2023" --position top-left --color "#FFD700"
```

### 示例4: 完整自定义
```bash
python image_watermark.py "D:\Pictures\Events" -s 32 -c blue -p center
```

## 输出结构

程序会在输入目录下创建一个名为 `原目录名_watermark` 的子目录，保存处理后的图片：

```
原目录/
├── photo1.jpg
├── photo2.png
├── subfolder/
│   └── photo3.jpg
└── 原目录_watermark/          # 输出目录
    ├── photo1.jpg             # 带水印的图片
    ├── photo2.png
    └── subfolder/
        └── photo3.jpg
```

## 工作原理

1. **扫描目录**: 递归扫描输入目录中的所有支持格式的图片文件
2. **读取EXIF**: 尝试从每张图片的EXIF信息中提取拍摄日期
3. **生成水印**: 将日期格式化为 "YYYY-MM-DD" 格式作为水印文本
4. **添加水印**: 根据指定的样式和位置在图片上绘制水印
5. **保存文件**: 将处理后的图片保存到输出目录，保持原有的目录结构

## 注意事项

- 仅处理包含有效EXIF拍摄时间信息的图片
- 如果图片没有EXIF信息或无法读取日期，将被跳过
- 输出图片质量设置为95%，平衡文件大小和图片质量
- 支持透明度的格式（PNG）会添加半透明阴影效果
- JPG格式输出时会自动处理透明度兼容性

## 系统要求

- Python 3.7+
- Windows/macOS/Linux
- 足够的磁盘空间存储输出图片

## 故障排除

### 常见问题

1. **"缺少必需的库"错误**
   ```bash
   pip install Pillow exifread
   ```

2. **字体显示问题**
   - Windows: 程序会自动寻找系统字体（黑体、微软雅黑等）
   - 其他系统: 使用默认字体

3. **图片无法处理**
   - 检查图片格式是否支持
   - 确认图片包含有效的EXIF信息
   - 检查文件权限

4. **输出目录权限问题**
   - 确保对输入目录有写权限
   - 检查磁盘空间是否充足

## 许可证

MIT License

## 贡献

欢迎提交问题报告和功能请求！
