@echo off

set /p script_path=Enter the full path to your Python script (.py): 
set /p requirements_path=Enter the full path to your requirements.txt: 
set /p venv_name=Enter a name for your virtual environment (e.g., venv): 
set /p batch_name=Enter the name for your batch file (e.g., run_my_script.bat): 

:: Get base directory of the Python script
for %%i in ("%script_path%") do set BASE_DIR=%%~dpi
set BASE_DIR=%BASE_DIR:~0,-1%

set VENV_PATH=%BASE_DIR%\%venv_name%

echo.
echo 📁 Project directory: %BASE_DIR%

:: Step 1: Create virtual environment if it doesn't exist
if not exist "%VENV_PATH%" (
    echo 🔧 Creating virtual environment...
    python -m venv "%VENV_PATH%"
) else (
    echo ✅ Virtual environment already exists
)

:: Step 2: Activate and install dependencies
call "%VENV_PATH%\Scripts\activate.bat"

echo ⬆️ Upgrading pip...
pip install --upgrade pip

echo 📦 Installing requirements...
pip install -r "%requirements_path%"

echo 🌐 Installing Playwright browsers...
playwright install

:: Step 3: Create executable batch script with runtime safety
echo @echo off > "%batch_name%"
echo. >> "%batch_name%"

:: Existing logic (kept)
echo set BASE_DIR=%BASE_DIR% >> "%batch_name%"

:: 🔥 NEW: detect actual script location at runtime
echo set SCRIPT_DIR=%%~dp0 >> "%batch_name%"

:: 🔥 NEW: ensure execution happens from script location
echo cd /d "%%SCRIPT_DIR%%" >> "%batch_name%"

:: Activate venv
echo call "%%BASE_DIR%%\%venv_name%\Scripts\activate.bat" >> "%batch_name%"

:: Debug info
echo echo Running from: %%SCRIPT_DIR%% >> "%batch_name%"
echo echo Using Python: %%VIRTUAL_ENV%% >> "%batch_name%"

:: 🔥 NEW: pass runtime directory to Python
echo set RUN_BASE_DIR=%%SCRIPT_DIR%% >> "%batch_name%"

:: Existing logic (kept)
echo python "%script_path%" %%* >> "%batch_name%"

echo pause >> "%batch_name%"

echo.
echo ✅ DONE! Your script "%batch_name%" is ready.
echo 👉 Run it by double-clicking or from terminal

pause