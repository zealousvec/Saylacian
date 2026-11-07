@echo off
setlocal
cd /d "%~dp0\.."
set "PYTHONUTF8=1"
set "LAB_HOME=%LOCALAPPDATA%\SaylacianResearchLab"
set "LAB_CONFIG=%LAB_HOME%\config\active.toml"
set "TRAINING_PY=%LAB_HOME%\runtime\training-venv\Scripts\python.exe"

if exist ".venv\Scripts\python.exe" (
    set "PYTHON=.venv\Scripts\python.exe"
) else (
    set "PYTHON=py -3.12"
)

%PYTHON% tools\local_translation_lab.py init
if errorlevel 1 goto failed
%PYTHON% tools\local_translation_lab.py doctor
if errorlevel 1 goto failed
%PYTHON% tools\local_translation_lab.py overnight --config "%LAB_CONFIG%"
if errorlevel 1 goto failed

%PYTHON% -c "import pathlib,sys,tomllib; c=tomllib.loads(pathlib.Path(r'%LAB_CONFIG%').read_text()); sys.exit(0 if c.get('training_enabled') and 'google-smol-en-so' in c.get('approved_source_ids',[]) else 1)"
if errorlevel 1 (
    echo Training is not enabled for the approved Google SMOL source in the active config.
    echo No training packages were installed and no training was started.
    exit /b 2
)

if not exist "%TRAINING_PY%" (
    call tools\setup_translation_training.cmd
    if errorlevel 1 goto failed
)

set "EXPERIMENT_ID=m2m100-smol-lora-%RANDOM%-%RANDOM%"
call tools\run_translation_lab_training.cmd --experiment-id %EXPERIMENT_ID%
if errorlevel 1 goto failed
echo.
echo Research and evaluation campaign completed. Nothing was promoted or published.
exit /b 0

:failed
set "RESULT=%ERRORLEVEL%"
echo.
echo Campaign stopped with exit code %RESULT%. Review the local report and resolve the stated gate.
exit /b %RESULT%
