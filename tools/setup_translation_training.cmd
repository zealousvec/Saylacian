@echo off
setlocal
set "LAB_HOME=%LOCALAPPDATA%\SaylacianResearchLab"
set "TRAINING_PY=%LAB_HOME%\runtime\training-venv\Scripts\python.exe"
if not exist "%TRAINING_PY%" (
    py -3.12 -m venv "%LAB_HOME%\runtime\training-venv"
    if errorlevel 1 goto failed
)
"%TRAINING_PY%" -m pip install --upgrade pip
if errorlevel 1 goto failed
"%TRAINING_PY%" -m pip install torch==2.7.0 --index-url https://download.pytorch.org/whl/cu128
if errorlevel 1 goto failed
"%TRAINING_PY%" -m pip install -r "%~dp0..\requirements-training.txt"
if errorlevel 1 goto failed
"%TRAINING_PY%" -c "import torch, transformers, peft; print('Training runtime ready:', torch.__version__, transformers.__version__, peft.__version__); print('CUDA:', torch.cuda.is_available())"
if errorlevel 1 goto failed
echo Training runtime installed outside the application environment.
exit /b 0
:failed
echo Training setup failed. The Saylacian app environment was not changed.
exit /b 1
