@echo off
chcp 65001 > nul
echo TimeLog 环境变量卸载脚本
echo ================================

:: 检查是否以管理员权限运行
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo 将从当前用户环境变量中移除 TimeLog
    set "SCOPE=USER"
) else (
    echo 检测到管理员权限，将从系统环境变量中移除 TimeLog
    set "SCOPE=MACHINE"
)

:: 获取当前目录
set "TIMELOG_DIR=%~dp0"
set "TIMELOG_DIR=%TIMELOG_DIR:~0,-1%"

echo.
echo TimeLog 安装路径: %TIMELOG_DIR%
echo.

:: 获取当前PATH
if "%SCOPE%"=="MACHINE" (
    for /f "tokens=2*" %%a in ('reg query "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Environment" /v PATH 2^>nul') do set "CURRENT_PATH=%%b"
) else (
    for /f "tokens=2*" %%a in ('reg query "HKCU\Environment" /v PATH 2^>nul') do set "CURRENT_PATH=%%b"
)

:: 检查是否在PATH中
echo %CURRENT_PATH% | findstr /i "%TIMELOG_DIR%" >nul
if %errorlevel% neq 0 (
    echo TimeLog 目录不在 PATH 环境变量中
无需移除
    goto :end
)

:: 从PATH中移除

:: 使用PowerShell来精确处理PATH字符串
powershell -Command ^echo     "$current = '%CURRENT_PATH%'; " ^echo     "$toRemove = '%TIMELOG_DIR%'; " ^echo     "$paths = $current -split ';' ^| Where-Object { $_ -ne $toRemove -and $_ -notlike '*timelog*' -and $_ -ne '' }; " ^echo     "$newPath = $paths -join ';'; " ^echo     "Write-Output $newPath" > temp_path.txt

set /p NEW_PATH=<temp_path.txt
del temp_path.txt

:: 更新注册表
if "%SCOPE%"=="MACHINE" (
    reg add "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Environment" /v PATH /t REG_EXPAND_SZ /d "%NEW_PATH%" /f >nul
) else (
    reg add "HKCU\Environment" /v PATH /t REG_EXPAND_SZ /d "%NEW_PATH%" /f >nul
)

if %errorlevel% equ 0 (
    echo ✓ 环境变量移除成功!
) else (
    echo ✗ 环境变量移除失败
    pause
    exit /b 1
)

:end
echo.
echo ================================
echo 卸载完成!
echo.
echo TimeLog 已从系统 PATH 中移除
echo.
echo 如需完全删除 TimeLog，请手动删除程序文件夹
echo.
pause
