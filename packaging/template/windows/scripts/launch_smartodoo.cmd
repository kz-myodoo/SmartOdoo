@echo off
setlocal

for %%I in ("%~dp0..") do set "APP_DIR=%%~fI"
set "VENV_PYTHONW=%LOCALAPPDATA%\SmartOdoo\venv\Scripts\pythonw.exe"
set "VENV_PYTHON=%LOCALAPPDATA%\SmartOdoo\venv\Scripts\python.exe"
set "POST_INSTALL_PS1=%APP_DIR%\scripts\post_install.ps1"

if not exist "%VENV_PYTHON%" (
    echo [INFO] SmartOdoo Python environment is missing. Bootstrapping now...
    if not exist "%POST_INSTALL_PS1%" (
        echo [ERROR] Missing bootstrap script: %POST_INSTALL_PS1%
        pause
        exit /b 1
    )

    powershell -NoProfile -ExecutionPolicy Bypass -File "%POST_INSTALL_PS1%" -AppDir "%APP_DIR%"
    if errorlevel 1 (
        echo [ERROR] Failed to bootstrap SmartOdoo Python environment.
        echo [INFO] Check Python installation and internet connectivity for pip.
        pause
        exit /b 1
    )
)

if exist "%VENV_PYTHONW%" (
    start "" "%VENV_PYTHONW%" "%APP_DIR%\app\core\smartodoo_gui.py"
    exit /b 0
)

if exist "%VENV_PYTHON%" (
    "%VENV_PYTHON%" "%APP_DIR%\app\core\smartodoo_gui.py"
    exit /b %errorlevel%
)

echo [ERROR] SmartOdoo Python environment was not found.
echo [INFO] Re-run installer to rebuild environment.
pause
exit /b 1
