@echo off
setlocal
cd /d "%~dp0"
set "EULER_PYTHON=%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
if exist "%EULER_PYTHON%" goto iniciar
set "EULER_PYTHON=%~dp0.venv\Scripts\python.exe"
if exist "%EULER_PYTHON%" goto iniciar
set "EULER_PYTHON=python"
:iniciar
echo Abrindo a instalacao atual da EULER...
"%EULER_PYTHON%" "%~dp0scripts\abrir_local.py" %*
if errorlevel 1 (
  echo Nao foi possivel abrir. Veja a mensagem acima.
  pause
  exit /b 1
)
exit /b 0
