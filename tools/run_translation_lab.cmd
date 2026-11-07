@echo off
setlocal
cd /d "%~dp0\.."
set PYTHONUTF8=1
set "LAB_HOME=%LOCALAPPDATA%\SaylacianResearchLab"
set "LAB_CONFIG=%LAB_HOME%\config\active.toml"
if exist ".venv\Scripts\python.exe" (
    set "PYTHON=.venv\Scripts\python.exe"
) else (
    set "PYTHON=py -3.12"
)
%PYTHON% tools\local_translation_lab.py init
if errorlevel 1 goto failed
%PYTHON% tools\local_translation_lab.py doctor
if errorlevel 1 goto failed
echo.
echo Starting local data, transliteration, and offline translation checks.
echo Training runs only when its approved data, checkpoint, and trainer are ready.
%PYTHON% tools\local_translation_lab.py overnight --config "%LAB_CONFIG%"
set RESULT=%ERRORLEVEL%
echo.
echo Research runner exited with code %RESULT%. Use status, report, or resume to continue.
pause
exit /b %RESULT%
:failed
echo Lab setup or preflight failed. Confirm Python 3.12 and the development dependencies are installed.
pause
exit /b 1
