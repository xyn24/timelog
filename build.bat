@echo off
chcp 65001 > nul
echo Starting TimeLog Release Build...

:: 激活虚拟环境
call timelog_env\Scripts\activate.bat

:: 验证环境激活
echo Current Python: %VIRTUAL_ENV%
echo Python executable: 
python -c "import sys; print(sys.executable)"

:: 确保pyinstaller已安装
echo Checking PyInstaller installation...
pip show pyinstaller >nul 2>&1
if %errorlevel% neq 0 (
    echo Installing PyInstaller...
    pip install pyinstaller
)

:: 清理之前的构建文件
echo Cleaning previous build files...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

:: 使用PyInstaller打包
echo Building main executable...
pyinstaller timelog.spec

if %errorlevel% neq 0 (
    echo Build failed!
    pause
    exit /b 1
)

:: 创建deploy目录
echo Creating deploy directory...
if not exist deploy mkdir deploy
if not exist deploy\timelog mkdir deploy\timelog

:: 清理旧的部署文件
echo Cleaning old deployment files...
if exist deploy\timelog\timelog.exe del deploy\timelog\timelog.exe
if exist deploy\timelog\start_web.bat del deploy\timelog\start_web.bat
if exist deploy\timelog\timelog-start-web.bat del deploy\timelog\timelog-start-web.bat

:: 复制可执行文件到deploy目录
echo Creating deployment files...
copy dist\timelog.exe deploy\timelog\ >nul

:: 复制templates和static文件夹
echo Copying web assets...
xcopy /E /I templates deploy\timelog\templates >nul
xcopy /E /I static deploy\timelog\static >nul

:: 复制部署说明
copy README_RELEASE.md deploy\timelog\README.md >nul

:: 创建环境变量安装脚本
echo Creating environment variable scripts...
call :create_install_script
call :create_uninstall_script

:: 创建启动脚本
echo Creating launcher scripts...

(
echo @echo off
echo chcp 65001 ^> nul
echo cd /d "%%~dp0"
echo timelog.exe web
echo pause
) > deploy\timelog\timelog-start-web.bat

(
echo @echo off
echo chcp 65001 ^> nul
echo cd /d "%%~dp0"
echo timelog.exe %%*
) > deploy\timelog\timelog.bat

:: 删除临时构建文件
if exist build rmdir /s /q build 2>nul
if exist dist rmdir /s /q dist 2>nul

echo.
echo Build completed successfully!
echo Deployment files in deploy\timelog\ directory:
echo   timelog.exe               - Main executable
echo   timelog-start-web.bat     - Web interface launcher
echo   timelog-install.bat       - Add to system PATH
echo   timelog-uninstall.bat     - Remove from PATH
echo   README.md                 - Documentation
echo   templates\            - Web templates
echo   static\               - Web assets
echo.
echo Quick start:
echo   deploy\timelog\timelog-start-web.bat   - Start web interface
echo   deploy\timelog\timelog-install.bat     - Add to system PATH (recommended)
echo   deploy\timelog\timelog.exe --help      - Show help
echo   deploy\timelog\timelog.exe web         - Start web server
echo.
echo After installing to PATH, you can use 'timelog' from anywhere!
echo Ready for deployment - copy deploy\timelog\ folder to target computer!
pause

:create_install_script
(
echo @echo off
echo chcp 65001 ^> nul
echo echo TimeLog 环境变量安装脚本
echo echo ================================
echo.
echo :: 检查是否以管理员权限运行
echo net session ^>nul 2^>^&1
echo if %%errorlevel%% neq 0 ^(
echo     echo.
echo     echo 警告: 建议以管理员权限运行此脚本
echo     echo 这样可以为所有用户设置环境变量
echo     echo.
echo     echo 继续将为当前用户设置环境变量...
echo     echo.
echo     pause
echo     set "SCOPE=USER"
echo ^) else ^(
echo     echo 检测到管理员权限，将为所有用户设置环境变量
echo     set "SCOPE=MACHINE"
echo ^)
echo.
echo :: 获取当前目录
echo set "TIMELOG_DIR=%%~dp0"
echo set "TIMELOG_DIR=%%TIMELOG_DIR:~0,-1%%"
echo.
echo echo.
echo echo 当前 TimeLog 安装路径: %%TIMELOG_DIR%%
echo echo.
echo.
echo :: 检查timelog.exe是否存在
echo if not exist "%%TIMELOG_DIR%%\timelog.exe" ^(
echo     echo 错误: 在当前目录找不到 timelog.exe
echo     echo 请确保此脚本在 TimeLog 程序目录中运行
echo     pause
echo     exit /b 1
echo ^)
echo.
echo :: 获取当前PATH
echo if "%%SCOPE%%"=="MACHINE" ^(
echo     for /f "tokens=2*" %%%%a in ^('reg query "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Environment" /v PATH 2^^^>nul'^) do set "CURRENT_PATH=%%%%b"
echo ^) else ^(
echo     for /f "tokens=2*" %%%%a in ^('reg query "HKCU\Environment" /v PATH 2^^^>nul'^) do set "CURRENT_PATH=%%%%b"
echo ^)
echo.
echo :: 检查是否已经在PATH中
echo echo %%CURRENT_PATH%% ^| findstr /i "%%TIMELOG_DIR%%" ^>nul
echo if %%errorlevel%% equ 0 ^(
echo     echo TimeLog 目录已经在 PATH 环境变量中
echo     echo 当前路径: %%TIMELOG_DIR%%
echo     goto :test_command
echo ^)
echo.
echo :: 添加到PATH
echo echo 正在将 TimeLog 目录添加到 PATH 环境变量...
echo :: 检查PATH是否以分号结尾，避免双分号
echo if "%%SCOPE%%"=="MACHINE" ^(
echo     if "%%CURRENT_PATH:~-1%%"==";" ^(
echo         reg add "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Environment" /v PATH /t REG_EXPAND_SZ /d "%%CURRENT_PATH%%%%TIMELOG_DIR%%" /f ^>nul
echo     ^) else ^(
echo         reg add "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Environment" /v PATH /t REG_EXPAND_SZ /d "%%CURRENT_PATH%%;%%TIMELOG_DIR%%" /f ^>nul
echo     ^)
echo ^) else ^(
echo     if "%%CURRENT_PATH:~-1%%"==";" ^(
echo         reg add "HKCU\Environment" /v PATH /t REG_EXPAND_SZ /d "%%CURRENT_PATH%%%%TIMELOG_DIR%%" /f ^>nul
echo     ^) else ^(
echo         reg add "HKCU\Environment" /v PATH /t REG_EXPAND_SZ /d "%%CURRENT_PATH%%;%%TIMELOG_DIR%%" /f ^>nul
echo     ^)
echo ^)
echo.
echo if %%errorlevel%% equ 0 ^(
echo     echo ✓ 环境变量设置成功!
echo ^) else ^(
echo     echo ✗ 环境变量设置失败
echo     pause
echo     exit /b 1
echo ^)
echo.
echo :test_command
echo echo.
echo echo 正在测试命令...
echo.
echo :: 刷新环境变量（对当前会话）
echo set "PATH=%%PATH%%;%%TIMELOG_DIR%%"
echo.
echo :: 测试命令
echo timelog.exe --version ^>nul 2^>^&1
echo if %%errorlevel%% equ 0 ^(
echo     echo ✓ timelog 命令测试成功!
echo ^) else ^(
echo     echo ⚠ 当前会话中命令尚未生效，请重启命令提示符或重新登录
echo ^)
echo.
echo echo.
echo echo ================================
echo echo 安装完成!
echo echo.
echo echo 现在您可以在任何位置使用以下命令:
echo echo   timelog --help          查看帮助
echo echo   timelog start "任务名"   开始任务
echo echo   timelog stop            停止任务
echo echo   timelog status          查看状态
echo echo   timelog web             启动网页界面
echo echo.
echo echo 注意: 如果命令不生效，请重启命令提示符或重新登录
echo echo.
echo pause
) > deploy\timelog\timelog-install.bat
exit /b

:create_uninstall_script
(
echo @echo off
echo chcp 65001 ^> nul
echo echo TimeLog 环境变量卸载脚本
echo echo ================================
echo.
echo :: 检查是否以管理员权限运行
echo net session ^>nul 2^>^&1
echo if %%errorlevel%% neq 0 ^(
echo     echo.
echo     echo 将从当前用户环境变量中移除 TimeLog
echo     set "SCOPE=USER"
echo ^) else ^(
echo     echo 检测到管理员权限，将从系统环境变量中移除 TimeLog
echo     set "SCOPE=MACHINE"
echo ^)
echo.
echo :: 获取当前目录
echo set "TIMELOG_DIR=%%~dp0"
echo set "TIMELOG_DIR=%%TIMELOG_DIR:~0,-1%%"
echo.
echo echo.
echo echo TimeLog 安装路径: %%TIMELOG_DIR%%
echo echo.
echo.
echo :: 获取当前PATH
echo if "%%SCOPE%%"=="MACHINE" ^(
echo     for /f "tokens=2*" %%%%a in ^('reg query "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Environment" /v PATH 2^^^>nul'^) do set "CURRENT_PATH=%%%%b"
echo ^) else ^(
echo     for /f "tokens=2*" %%%%a in ^('reg query "HKCU\Environment" /v PATH 2^^^>nul'^) do set "CURRENT_PATH=%%%%b"
echo ^)
echo.
echo :: 检查是否在PATH中
echo echo %%CURRENT_PATH%% ^| findstr /i "%%TIMELOG_DIR%%" ^>nul
echo if %%errorlevel%% neq 0 ^(
echo     echo TimeLog 目录不在 PATH 环境变量中
echo     echo 无需移除
echo     goto :end
echo ^)
echo.
echo :: 从PATH中移除
echo echo 正在从 PATH 环境变量中移除 TimeLog 目录...
echo.
echo :: 使用PowerShell来精确处理PATH字符串
echo powershell -Command ^^^
echo     "$current = '%%CURRENT_PATH%%'; " ^^^
echo     "$toRemove = '%%TIMELOG_DIR%%'; " ^^^
echo     "$paths = $current -split ';' ^| Where-Object { $_ -ne $toRemove -and $_ -notlike '*timelog*' -and $_ -ne '' }; " ^^^
echo     "$newPath = $paths -join ';'; " ^^^
echo     "Write-Output $newPath" ^> temp_path.txt
echo.
echo set /p NEW_PATH=^<temp_path.txt
echo del temp_path.txt
echo.
echo :: 更新注册表
echo if "%%SCOPE%%"=="MACHINE" ^(
echo     reg add "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Environment" /v PATH /t REG_EXPAND_SZ /d "%%NEW_PATH%%" /f ^>nul
echo ^) else ^(
echo     reg add "HKCU\Environment" /v PATH /t REG_EXPAND_SZ /d "%%NEW_PATH%%" /f ^>nul
echo ^)
echo.
echo if %%errorlevel%% equ 0 ^(
echo     echo ✓ 环境变量移除成功!
echo ^) else ^(
echo     echo ✗ 环境变量移除失败
echo     pause
echo     exit /b 1
echo ^)
echo.
echo :end
echo echo.
echo echo ================================
echo echo 卸载完成!
echo echo.
echo echo TimeLog 已从系统 PATH 中移除
echo echo 注意: 请重启命令提示符或重新登录以使更改生效
echo echo.
echo echo 如需完全删除 TimeLog，请手动删除程序文件夹
echo echo.
echo pause
) > deploy\timelog\timelog-uninstall.bat
exit /b
