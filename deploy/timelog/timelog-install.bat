@echo off
chcp 65001 > nul
echo TimeLog 环境变量安装脚本
echo ================================

:: 检查是否以管理员权限运行
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo 警告: 建议以管理员权限运行此脚本
    echo.
    echo 继续将为当前用户设置环境变量...
    echo.
    pause
    set "SCOPE=USER"
) else (
    echo 检测到管理员权限，将为所有用户设置环境变量
    set "SCOPE=MACHINE"
)

:: 获取当前目录
set "TIMELOG_DIR=%~dp0"
set "TIMELOG_DIR=%TIMELOG_DIR:~0,-1%"

echo.
echo 当前 TimeLog 安装路径: %TIMELOG_DIR%
echo.

:: 检查timelog.exe是否存在
if not exist "%TIMELOG_DIR%\timelog.exe" (
    echo 错误: 在当前目录找不到 timelog.exe
    echo 请确保此脚本在 TimeLog 程序目录中运行
    pause
    exit /b 1
)

:: 获取当前PATH
if "%SCOPE%"=="MACHINE" (
    for /f "tokens=2*" %%a in ('reg query "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Environment" /v PATH 2^>nul') do set "CURRENT_PATH=%%b"
) else (
    for /f "tokens=2*" %%a in ('reg query "HKCU\Environment" /v PATH 2^>nul') do set "CURRENT_PATH=%%b"
)

:: 检查是否已经在PATH中
echo %CURRENT_PATH% | findstr /i "%TIMELOG_DIR%" >nul
if %errorlevel% equ 0 (
    echo TimeLog 目录已经在 PATH 环境变量中
当前路径: %TIMELOG_DIR%
    goto :test_command
)

:: 添加到PATH
echo 正在将 TimeLog 目录添加到 PATH 环境变量...
if "%SCOPE%"=="MACHINE" (
    reg add "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Environment" /v PATH /t REG_EXPAND_SZ /d "%CURRENT_PATH%;%TIMELOG_DIR%" /f >nul
) else (
    reg add "HKCU\Environment" /v PATH /t REG_EXPAND_SZ /d "%CURRENT_PATH%;%TIMELOG_DIR%" /f >nul
)

if %errorlevel% equ 0 (
    echo ✓ 环境变量设置成功!
) else (
    echo ✗ 环境变量设置失败
    pause
    exit /b 1
)

:test_command
echo.
echo 正在测试命令...

:: 刷新环境变量（对当前会话）
set "PATH=%PATH%;%TIMELOG_DIR%"

:: 测试命令
timelog.exe --version >nul 2>&1
if %errorlevel% equ 0 (
    echo ✓ timelog 命令测试成功!
) else (
    echo ⚠ 当前会话中命令尚未生效，请重启命令提示符或重新登录
)

echo.
echo ================================
echo 安装完成!
echo.
echo 现在您可以在任何位置使用以下命令:
echo   timelog --help          查看帮助
echo   timelog start "任务名"   开始任务
echo   timelog status          查看状态
echo.
echo 注意: 如果命令不生效，请重启命令提示符或重新登录
echo.
pause
