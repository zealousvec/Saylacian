@echo off
setlocal
cd /d "%~dp0\.."

set "LAB_HOME=%LOCALAPPDATA%\SaylacianResearchLab"
set "APP_PY=.venv\Scripts\python.exe"
set "TRAINING_PY=%LAB_HOME%\runtime\training-venv\Scripts\python.exe"
set "CONFIG=%LAB_HOME%\config\active.toml"
if not defined SAYLACIAN_DATASET_ID set "SAYLACIAN_DATASET_ID=opus-infopankki-en-so"
if not defined SAYLACIAN_EXPERIMENT_ID for /f %%i in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMddTHHmmss"') do set "SAYLACIAN_EXPERIMENT_ID=m2m100-somali-%%i"

if not exist "%APP_PY%" (
    echo Project virtual environment is missing. Install the project requirements first.
    exit /b 2
)
if not exist "%TRAINING_PY%" (
    echo Isolated training runtime is missing. Run tools\setup_translation_training.cmd first.
    exit /b 2
)
if not exist "%CONFIG%" (
    echo Private lab config is missing. Initialize the research lab first.
    exit /b 2
)

"%APP_PY%" -c "import pyarrow.parquet" >nul 2>nul
if errorlevel 1 (
    echo Parquet support is missing. Install requirements-research-parquet.txt in .venv.
    exit /b 2
)

"%APP_PY%" tools\local_translation_lab.py --workspace "%LAB_HOME%" download --approved --config "%CONFIG%"
if errorlevel 1 exit /b %ERRORLEVEL%

"%APP_PY%" tools\local_translation_lab.py --workspace "%LAB_HOME%" prepare --source google-smol-en-so
if errorlevel 1 exit /b %ERRORLEVEL%
"%APP_PY%" tools\local_translation_lab.py --workspace "%LAB_HOME%" prepare --source opus-paracrawl-en-so
if errorlevel 1 exit /b %ERRORLEVEL%
"%APP_PY%" tools\local_translation_lab.py --workspace "%LAB_HOME%" prepare --source opus-infopankki-en-so
if errorlevel 1 exit /b %ERRORLEVEL%

"%TRAINING_PY%" tools\local_translation_lab.py --workspace "%LAB_HOME%" train --execute --config "%CONFIG%" --dataset-id "%SAYLACIAN_DATASET_ID%" --experiment-id "%SAYLACIAN_EXPERIMENT_ID%"
if errorlevel 1 exit /b %ERRORLEVEL%

"%TRAINING_PY%" tools\local_translation_lab.py --workspace "%LAB_HOME%" evaluate-candidate --config "%CONFIG%" --dataset-id "%SAYLACIAN_DATASET_ID%" --evaluation-dataset-id google-smol-en-so --experiment-id "%SAYLACIAN_EXPERIMENT_ID%"
if errorlevel 1 exit /b %ERRORLEVEL%
"%TRAINING_PY%" tools\local_translation_lab.py --workspace "%LAB_HOME%" evaluate-candidate --config "%CONFIG%" --dataset-id "%SAYLACIAN_DATASET_ID%" --evaluation-dataset-id "%SAYLACIAN_DATASET_ID%" --experiment-id "%SAYLACIAN_EXPERIMENT_ID%"
exit /b %ERRORLEVEL%
