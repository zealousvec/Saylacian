# Run Saylacian

From the project root in PowerShell:

```powershell
.\.venv\Scripts\python.exe main.py
```

No activation or execution-policy change is needed. See the root `RUN.md` for original UI mode and optional website launch. The website is separate; Flask is not required to start the Kivy app.

Startup diagnostics are written locally to `<Kivy user data directory>/logs/diagnostics.log`. The log stores version/runtime metadata and exception type/code locations (filename, line and function only; no directory paths); it does not store translation text or exception messages. Translation failures show a generic message in the app. Review logs before sharing them. Current implementation and verification notes are in [project status](PROJECT_STATUS.md).
