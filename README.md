# TimeLog - 时间记录工具

一个简洁高效的时间管理工具，支持命令行和网页界面双模式操作。

## 🌟 功能特色

- **双界面模式** - 命令行 + 网页界面，满足不同使用习惯
- **实时统计** - 任务时间分配和工作效率一目了然

数据存储在用户目录的 `.timelog.json` 文件中：查看时间分配和工作效率
- **智能分类** - 预设工作、学习、休息等类别，支持自定义
- **跨日任务** - 正确处理跨越日期的长时间任务
- **数据导出** - 支持CSV和JSON格式导出
- **完美中文** - 全中文界面，无编码问题
- **独立打包** - PyInstaller打包，无需Python环境

## 📁 项目结构

```
timelog/
├── timelog_simple.py      # 主程序入口
├── web_server.py          # Flask网页服务器
├── templates/             # 网页模板
│   ├── base.html
│   ├── index.html
│   ├── tasks.html
│   ├── stats.html
│   └── history.html
├── static/               # 静态资源
│   ├── style.css
│   ├── script.js
│   └── favicon.ico
├── build.bat            # 构建脚本
├── timelog.spec         # PyInstaller配置
├── README.md            # 项目主文档（本文件）
├── README_RELEASE.md    # 发布版用户文档
└── timelog_env/         # Python虚拟环境
```

## 📋 开发环境设置

### 1. 创建虚拟环境
```bash
python -m venv timelog_env
timelog_env\Scripts\activate
```

### 2. 安装依赖
```bash
pip install click flask pyinstaller
```

### 3. 运行开发版
```bash
# 命令行模式
python timelog_simple.py --help

# 网页模式
python timelog_simple.py web
```

## 📦 构建发布版

### 使用构建脚本
```bash
.\build.bat
```

构建后的文件位于 `deploy\timelog\` 目录，包含：
- `timelog.exe` - 独立可执行文件
- `start_web.bat` - 网页界面启动器
- `timelog.bat` - 命令行启动脚本
- `install_to_path.bat` - 环境变量安装脚本
- `uninstall_from_path.bat` - 环境变量卸载脚本
- `templates\` - 网页模板
- `static\` - 静态资源
- `README.md` - 用户文档（从README_RELEASE.md复制）

### ⚙️ 手动构建
```bash
# 激活虚拟环境
timelog_env\Scripts\activate

# 使用PyInstaller打包
pyinstaller timelog.spec
```

## 💻 使用方法

### 命令行界面
```bash
# 开始任务
timelog start "学习Python" -c study

# 查看状态
timelog status

# 停止任务
timelog stop

# 查看历史
timelog log

# 查看统计
timelog stats
```

### 网页界面
```bash
# 启动网页服务
timelog web

# 自定义端口
timelog web --port 8080

# 不自动打开浏览器
timelog web --no-browser
```

## 📊 数据格式

数据存储在用户目录的 `.timelog.json` 文件中：

```json
{
  "tasks": [
    {
      "id": "uuid",
      "name": "任务名称",
      "category": "work",
      "start_time": "2024-01-01T09:00:00",
      "end_time": "2024-01-01T10:30:00",
      "duration_minutes": 90
    }
  ],
  "current_task": null
}
```

## 🎯 预设类别

- **work** 💼 - 工作，项目，会议
- **study** 📚 - 学习，阅读，课程  
- **break** ☕ - 休息，吃饭，聊天
- **game** 🎮 - 游戏，娱乐
- **other** 📋 - 其他所有事项

## 🔧 技术栈

- **Python 3.7+** - 主要开发语言
- **Click** - 命令行界面框架
- **Flask** - 网页服务器框架
- **PyInstaller** - 可执行文件打包
- **HTML/CSS/JavaScript** - 网页前端

## 📝 开发笔记

### 动态导入处理
```python
# 为了支持PyInstaller打包，使用动态导入
if getattr(sys, 'frozen', False):
    # 打包后的环境
    spec = importlib.util.spec_from_file_location("web_server", 
        os.path.join(sys._MEIPASS, "web_server.py"))
else:
    # 开发环境
    spec = importlib.util.spec_from_file_location("web_server", "web_server.py")
```

### PyInstaller配置
关键配置项：
- `datas` - 包含templates和static文件夹
- `hiddenimports` - 确保web_server模块被包含
- `console=True` - 保持控制台模式

## 🚀 部署说明

1. 运行 `.\build.bat` 构建发布版
2. 将 `deploy\timelog\` 整个文件夹复制到目标电脑
3. 可选：运行 `install_to_path.bat` 添加到系统PATH
4. 用户可直接运行 `timelog.exe` 或双击 `start_web.bat`

## 许可证

本项目采用MIT许可证，更多信息请查看 [LICENSE](LICENSE) 文件。

## 🤝 贡献

欢迎提交问题和改进建议！

---

**开发者文档** - 如需用户使用说明，请查看 [README_RELEASE.md](README_RELEASE.md)
