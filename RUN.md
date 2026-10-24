# Run Saylacian

Open this project folder in VS Code, then run from PowerShell without activating the virtual environment:

```powershell
.\.venv\Scripts\python.exe main.py
```

The app is Python + Kivy/KivyMD. Flask is not part of the Kivy runtime install. For the optional legacy website, install its separate dependency and run it from the project root:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-website.txt
.\.venv\Scripts\python.exe run_website.py
```

To view the recovered original interface through the compatibility adapter:

```powershell
.\.venv\Scripts\python.exe main.py --original-ui
```

## Fresh Windows source install

Requires 64-bit Python 3.12. This installs the runtime, not translation model weights:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-runtime-lock.txt
.\.venv\Scripts\python.exe main.py
```

In Saylacian, select the download icon, then download a pack. Current pinned downloads:

- Somali / English: about 300 MiB (314,460,609 bytes)
- French / English: about 166 MiB (174,530,568 bytes)

The app verifies each downloaded asset against its manifest size and SHA-256, stages the files, then activates a versioned pack. Translation uses installed local models without an account, network connection, provider quota, or per-request fee. Packs live in `%LOCALAPPDATA%\Saylacian\model-packs`; remove a pack in the same screen to reclaim its storage. During an update, older versions remain recoverable until the user removes the pack.

The Somali pack uses multilingual OPUS translation checkpoints in both directions. The experimental synthetic English-to-Somali checkpoint is not offered as a download because a pinned preconverted artifact is unavailable. Existing source installs can continue to use that model if it is present locally. Somali quality remains machine-generated and needs fluent-speaker evaluation.

On desktop, press **Ctrl+Shift+M** to switch between translation and script conversion, and **Ctrl+P** to open offline packs. Press **Ctrl+L** to return to the translator and focus the text editor. Press **Ctrl+K** to search/select a target language or script, and **Ctrl+Shift+K** to choose a source. Use **Up/Down** to move through matches, **Enter** to select and **Esc** to return.

Developers can download the pinned source model assets with `tools\prepare_models.py --download` or verify installed assets without network access with `tools\prepare_models.py --verify-only`. The Windows package excludes model weights; packs are downloaded on demand. See [third-party notices](docs/THIRD_PARTY_NOTICES.md) for licensing notes and [backup and restore](docs/BACKUP_AND_RESTORE.md) to recover preserved source copies.

The existing unsigned development executable was blocked by Windows Application Control. Run the source application with the command above; do not weaken Windows security settings. See [online translation](docs/ONLINE_TRANSLATION.md) for the optional, user-enabled remote-provider configuration.

For measured Somali model comparisons and current quality limitations, see [Somali translation quality](docs/SOMALI_TRANSLATION_QUALITY.md).
