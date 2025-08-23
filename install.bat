@echo off
chcp 65001 >nul
echo ==========================================
echo     TimeLog 时间记录工具 - 自动安装
echo ==========================================
echo.

echo 🌟 1. 创建虚拟环境...
if not exist "timelog_env" (
    echo 🔧 正在创建虚拟环境...
    python -m venv timelog_env
    if %errorlevel% neq 0 (
        echo ❌ 虚拟环境创建失败！请检查Python安装
        pause
        exit /b 1
    )
    echo ✅ 虚拟环境创建成功
) else (
    echo ✅ 虚拟环境已存在
)

echo.
echo 📦 2. 安装依赖包...

REM 在虚拟环境中安装依赖
echo 🔧 正在安装 click 和 flask...
timelog_env\Scripts\pip.exe install click flask
if %errorlevel% neq 0 (
    echo ❌ 依赖安装失败！请检查网络连接
    pause
    exit /b 1
) else (
    echo ✅ 依赖安装完成
)

echo.
echo 🛠️  3. 配置环境变量...

REM 获取当前目录（去掉最后的反斜杠）
set "CURRENT_DIR=%~dp0"
set "CURRENT_DIR=%CURRENT_DIR:~0,-1%"

echo 安装路径: %CURRENT_DIR%

REM 检查当前目录是否已在PATH中
echo %PATH% | findstr /I /C:"%CURRENT_DIR%" >nul
if %errorlevel% equ 0 (
    echo ✅ 路径已在环境变量中
    goto :skip_path
)

echo � 正在添加到用户环境变量...

REM 获取当前用户的PATH变量
for /f "usebackq tokens=2*" %%A in (`reg query "HKCU\Environment" /v PATH 2^>nul`) do set "USER_PATH=%%B"

REM 如果用户PATH为空，直接设置
if "%USER_PATH%"=="" (
    echo 设置新的用户PATH...
    reg add "HKCU\Environment" /v PATH /t REG_EXPAND_SZ /d "%CURRENT_DIR%" /f >nul 2>&1
) else (
    echo 添加到现有PATH...
    reg add "HKCU\Environment" /v PATH /t REG_EXPAND_SZ /d "%USER_PATH%;%CURRENT_DIR%" /f >nul 2>&1
)

if %errorlevel% equ 0 (
    echo ✅ 已自动添加到用户环境变量
    echo 📌 环境变量已设置，新开的命令行窗口将生效
    
    REM 刷新当前会话的环境变量
    set "PATH=%PATH%;%CURRENT_DIR%"
    echo ✅ 当前会话环境变量已更新
) else (
    echo ❌ 自动配置失败，请手动添加到PATH：
    echo %CURRENT_DIR%
)

:skip_path

echo.
echo 🎯 4. 创建全局命令...

REM 创建不带扩展名的timelog命令文件（用于全局调用）
if not exist "%CURRENT_DIR%\timelog.cmd" (
    echo @echo off > "%CURRENT_DIR%\timelog.cmd"
    echo chcp 65001 ^>nul >> "%CURRENT_DIR%\timelog.cmd"
    echo cd /d "%CURRENT_DIR%" >> "%CURRENT_DIR%\timelog.cmd"
    echo. >> "%CURRENT_DIR%\timelog.cmd"
    echo REM 检查虚拟环境是否存在 >> "%CURRENT_DIR%\timelog.cmd"
    echo if exist "timelog_env\Scripts\python.exe" ^( >> "%CURRENT_DIR%\timelog.cmd"
    echo     timelog_env\Scripts\python.exe timelog_simple.py %%* >> "%CURRENT_DIR%\timelog.cmd"
    echo ^) else ^( >> "%CURRENT_DIR%\timelog.cmd"
    echo     echo ❌ 虚拟环境未找到，请运行 install.bat 重新安装 >> "%CURRENT_DIR%\timelog.cmd"
    echo     pause >> "%CURRENT_DIR%\timelog.cmd"
    echo ^) >> "%CURRENT_DIR%\timelog.cmd"
    echo ✅ 已创建全局命令 timelog.cmd
)

echo.
echo 🧪 5. 测试安装...
call "%CURRENT_DIR%\timelog.bat" --help >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ 工具正常工作！
) else (
    echo ⚠️  工具可能有问题，请检查Python环境
)

echo.
echo 🎉 安装完成！
echo.
echo 📖 使用方法：
echo.
echo 方法1 - 直接使用:
echo   .\timelog.bat start "学习任务" -c study
echo   .\timelog.bat stop
echo   .\timelog.bat stats
echo.
echo 方法2 - 全局使用（推荐）:
echo   timelog start "学习任务" -c study
echo   timelog stop  
echo   timelog stats
echo.
echo 注意：如果方法2不可用，请重新打开命令行窗口
echo.
echo 📝 查看 README.md 了解更多用法
echo.
pause
