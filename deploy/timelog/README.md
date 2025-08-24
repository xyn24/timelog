# TimeLog - 时间记录工具（发布版）

独立可执行文件版本 - 无需安装Python！

**这是即用发布版本 - 复制即可运行！**

## 📦 包含文件

```
timelog/
├── timelog.exe              # 主程序（包含所有功能）
├── start_web.bat            # 网页界面启动器
├── timelog.bat              # 命令行启动脚本
├── install_to_path.bat      # 环境变量安装脚本
├── uninstall_from_path.bat  # 环境变量卸载脚本
├── templates/               # 网页界面模板
│   ├── base.html
│   ├── index.html
│   ├── tasks.html
│   ├── stats.html
│   └── history.html
└── static/                 # 网页界面资源
    ├── style.css
    ├── script.js
    └── favicon.ico
```

## 🚀 快速开始

### 选项一：网页界面（推荐）
```cmd
# 方法1: 双击 start_web.bat
# 方法2: 在终端运行
timelog.exe web

# 浏览器会自动打开 http://localhost:5000
```

### 选项二：命令行
```cmd
# 方法1: 使用 timelog.bat 脚本
timelog start "学习英语" -c study

# 方法2: 直接运行可执行文件
timelog.exe start "学习英语" -c study

# 查看当前状态
timelog status
# 或
timelog.exe status

# 停止当前任务
timelog stop
# 或
timelog.exe stop

# 查看所有命令
timelog --help
# 或
timelog.exe --help
```

### 选项三：系统PATH（推荐高级用户）
```cmd
# 首次安装：右键以管理员身份运行
install_to_path.bat

# 安装后可在任何位置使用
timelog start "工作" -c work
timelog web
timelog status
```

## 🌟 功能特色

### 🌐 网页界面
- **实时仪表板** - 查看当前任务和每日进度
- **任务管理** - 一键开始/停止任务
- **快速启动按钮** - 为常用任务预配置
- **交互式图表** - 可视化时间分布和趋势
- **历史记录编辑器** - 编辑、创建、删除任务记录
- **智能导出** - CSV（Excel兼容）和JSON格式
- **跨日任务** - 正确处理过夜活动

### ⌨️ 命令行界面
- **即时命令** - 从终端快速切换任务
- **实时状态** - 无需打开浏览器即可查看进度
- **ASCII图表** - 在命令行中显示可视化统计
- **批量操作** - 非常适合自动化脚本

## 💾 数据和设置

- **数据位置**: `%USERPROFILE%\.timelog.json`
  - 示例: `C:\Users\您的用户名\.timelog.json`
- **自动备份**: 每次操作后自动保存数据
- **导出选项**: CSV（UTF-8/GBK）和JSON格式
- **跨设备**: 支持导出/导入进行数据迁移

## 🛠️ 部署指南

### 基础部署（适合所有用户）
1. 将整个 `timelog` 文件夹复制到所需位置
2. 双击 `start_web.bat` 启动网页界面
3. 或运行 `timelog.exe --help` 查看命令选项

### 高级部署（推荐经常使用的用户）
1. 复制文件夹到合适位置（如 `C:\Tools\timelog\`）
2. 右键以管理员身份运行 `install_to_path.bat`
3. 重启命令提示符后即可在任何位置使用 `timelog` 命令

### 多台电脑使用
1. 将文件夹复制到每台电脑
2. 使用导出/导入功能进行数据同步
3. 或将数据文件放在共享网络驱动器上

### 卸载
- 基础版：直接删除文件夹即可
- PATH版：先运行 `uninstall_from_path.bat`，再删除文件夹

### 系统要求
- Windows 10/11 (64位)
- 无需Python或其他软件
- ~50MB磁盘空间
- 无需网络连接

## 💡 使用技巧

### 快速任务切换
```cmd
# 使用完整路径（基础版）
timelog.exe start "阅读" -c study
timelog.exe start "休息" -c other

# 使用脚本（更简洁）
timelog start "阅读" -c study
timelog start "休息" -c other

# 安装到PATH后（最便捷）
timelog start "阅读" -c study  # 可在任何位置使用
```

### 启动方式选择
```cmd
# 网页界面
start_web.bat              # 最简单，双击即可
timelog web                 # 使用脚本
timelog.exe web             # 直接调用

# 命令行操作
timelog status              # 使用脚本
timelog.exe status          # 直接调用
```

### 日常工作流程
```cmd
# 上午（安装PATH版本示例）
timelog start "处理邮件" -c work

# 随时查看进度
timelog status

# 查看今日汇总
timelog stats -d today

# 晚上
timelog stop
```

### 网页界面技巧
- 双击 `start_web.bat` 是最简单的启动方式
- 使用快速启动按钮处理常见任务
- 编辑历史记录修正计时错误
- 定期导出数据进行备份
- 图表会自动更新

### 环境变量技巧
- 安装到PATH后可在任何目录使用 `timelog` 命令
- 适合经常使用命令行的用户
- 卸载前记得运行 `uninstall_from_path.bat`

## 🔧 故障排除

| 问题 | 解决方案 |
|---------|----------|
| 无法启动 | 检查Windows Defender/杀毒软件设置 |
| 网页无法加载 | 尝试不同端口: `timelog web --port 5001` |
| PATH命令无效 | 重启命令提示符或重新登录 |
| 中文文字乱码 | 程序会自动处理此问题 |
| 缺少模板 | 确保 `templates/` 文件夹存在 |
| 数据无法保存 | 检查用户文件夹的文件权限 |

### 常用命令
```cmd
# 帮助
timelog --help
# 或
timelog.exe --help

# 使用不同端口访问网页
timelog web --port 8080
# 或
timelog.exe web --port 8080

# 导出数据
timelog export backup.csv
# 或
timelog.exe export backup.csv

# 查看历史记录
timelog history
# 或
timelog.exe history
```

## 📊 了解您的数据

### 类别
- **work** 💼 - 工作，项目，会议
- **study** 📚 - 学习，阅读，课程
- **break** ☕ - 休息，吃饭，聊天
- **game** 🎮 - 游戏，娱乐
- **other** 📋 - 其他所有事项

### 时间跟踪
- 自动跟踪开始/停止时间
- 正确处理跨日任务
- 以小时和分钟显示持续时间
- 计算每日/每周总计

### 导出格式
- **CSV (UTF-8+BOM)** - 最适合Windows上的Excel
- **CSV (GBK)** - 中文编码替代方案
- **JSON** - 包含元数据的完整数据

## 🎯 为什么选择TimeLog？

✅ **无需安装** - 复制即可运行  
✅ **双重界面** - 网页 + 命令行  
✅ **完美中文** - 无编码问题  
✅ **智能分析** - 自动洞察  
✅ **便携数据** - 随处可用  
✅ **实时更新** - 实时进度跟踪  

---

**准备好高效地跟踪您的时间吗？**

🚀 **简单开始**：双击 `start_web.bat`  
⚡ **高级用户**：运行 `install_to_path.bat` 后使用 `timelog web`  
📱 **命令行**：直接运行 `timelog.exe --help` 查看所有选项
