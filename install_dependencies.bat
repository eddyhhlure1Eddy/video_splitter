@echo off
echo 正在检查Python环境...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未找到Python，请安装Python后再运行此脚本。
    pause
    exit /b 1
)

echo 正在更新pip...
python -m pip install --upgrade pip

echo 正在安装依赖项，请稍候...
python -m pip install -r requirements.txt

if %errorlevel% equ 0 (
    echo.
    echo [成功] 所有依赖项已成功安装！
) else (
    echo.
    echo [错误] 安装依赖项时出现问题，请检查错误信息。
)

pause 