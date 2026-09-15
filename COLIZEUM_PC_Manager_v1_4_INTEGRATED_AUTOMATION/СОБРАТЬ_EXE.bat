@echo off
chcp 65001 >nul
cd /d "%~dp0"

py -m pip install --upgrade pyinstaller
py -m PyInstaller --noconfirm --clean --onefile --windowed --name "COLIZEUM PC Manager" main.py

echo.
if exist "dist\COLIZEUM PC Manager.exe" (
  echo ГОТОВО:
  echo dist\COLIZEUM PC Manager.exe
) else (
  echo EXE не создан. Пришли ошибку выше.
)
pause
