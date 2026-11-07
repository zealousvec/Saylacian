@echo off
setlocal
cd /d "%~dp0\.."

call tools\run_somali_marian_experiment.cmd
if errorlevel 1 exit /b %ERRORLEVEL%

set "LAB_HOME=%LOCALAPPDATA%\SaylacianResearchLab"
set "TRAINING_PY=%LAB_HOME%\runtime\training-venv\Scripts\python.exe"
if not exist "%TRAINING_PY%" (
    echo Isolated training runtime is missing. Run tools\setup_translation_training.cmd first.
    exit /b 2
)

"%TRAINING_PY%" -m tools.translation_lab.somali_reverse_screen --train-mixture
exit /b %ERRORLEVEL%
