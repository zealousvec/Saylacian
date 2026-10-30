# Real Windows clipboard acceptance

`tools/test_windows_clipboard.ps1` publishes all three Saylacian payloads, then reads them from a separate WinForms PowerShell process. This exercises the actual Windows clipboard formats and a different consumer process.

The Windows clipboard is shared by applications in the same interactive session. It cannot be safely isolated by launching a second process. Therefore the test now refuses to run unless explicitly marked as inside a disposable Windows VM and the clipboard is empty. It never clears or restores clipboard data. Reset the VM to its clean snapshot between runs. Disable host/guest clipboard sharing before starting the VM; otherwise the VM may expose the host clipboard.

Inside the disposable VM, set `SAYLACIAN_CLIPBOARD_TEST_ENV=disposable-vm`, then run:

```powershell
$env:SAYLACIAN_CLIPBOARD_TEST_ENV = 'disposable-vm'
.\.venv\Scripts\pwsh.exe -NoProfile -File tools\test_windows_clipboard.ps1 -InDisposableWindowsVm
```

Use the VM's actual PowerShell executable path if `pwsh.exe` is elsewhere. The script writes evidence under the VM's temporary directory. Do not run this against the everyday Windows desktop. Unit tests and Kivy acceptance use in-memory clipboard doubles and verify the payload without changing the system clipboard; they do not substitute for this external-process acceptance.

The real external-consumer check remains unverified until run in such an isolated environment.
