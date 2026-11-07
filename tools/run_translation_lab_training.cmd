@echo off
setlocal
cd /d "%~dp0\.."
set "LAB_HOME=%LOCALAPPDATA%\SaylacianResearchLab"
set "TRAINING_PY=%LAB_HOME%\runtime\training-venv\Scripts\python.exe"
if not exist "%TRAINING_PY%" (
    echo Training runtime is missing. Run tools\setup_translation_training.cmd first.
    exit /b 2
)
"%TRAINING_PY%" tools\local_translation_lab.py --workspace "%LAB_HOME%" train --execute --config "%LAB_HOME%\config\active.toml" --experiment-id m2m100-smol-lora-20261031 %*
if errorlevel 1 exit /b %ERRORLEVEL%
"%TRAINING_PY%" tools\local_translation_lab.py --workspace "%LAB_HOME%" evaluate-candidate --config "%LAB_HOME%\config\active.toml" --experiment-id m2m100-smol-lora-20261031
exit /b %ERRORLEVEL%
