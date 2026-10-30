# SPDX-License-Identifier: AGPL-3.0-or-later
# -*- mode: python ; coding: utf-8 -*-
# Builds the Windows app bundle; verified language packs install separately after setup.
from PyInstaller.utils.hooks import collect_all

datas = [
    ("app/main.kv", "app"),
    ("app/original.kv", "app"),
    ("assets/BoramaChart-Regular.ttf", "assets"),
    ("assets/KaddareChart-Regular.ttf", "assets"),
    ("assets/NotoSansCoptic-Regular.ttf", "assets"),
    ("assets/NotoSansOsmanya.ttf", "assets"),
    ("assets/OFL-Coptic.txt", "assets"),
    ("assets/OFL-Osmanya.txt", "assets"),
    ("assets/research/Borama_Alphabet_Chart.jpg", "assets/research"),
    ("assets/research/Kaddare_Alphabet_Chart.jpg", "assets/research"),
    ("notices", "notices"),
    ("saylacian/core/data", "saylacian/core/data"),
]
binaries = []
hiddenimports = ["app.acceptance", "app.original_compat"]
tmp_ret = collect_all("kivymd")
datas += tmp_ret[0]
binaries += tmp_ret[1]
hiddenimports += tmp_ret[2]
tmp_ret = collect_all("ctranslate2")
datas += tmp_ret[0]
binaries += tmp_ret[1]
hiddenimports += tmp_ret[2]
tmp_ret = collect_all("sentencepiece")
datas += tmp_ret[0]
binaries += tmp_ret[1]
hiddenimports += tmp_ret[2]
tmp_ret = collect_all("py3langid")
datas += tmp_ret[0]
binaries += tmp_ret[1]
hiddenimports += tmp_ret[2]
a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["kivy.core.audio.audio_gstplayer", "kivy.lib.gstplayer"],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="Saylacian",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="Saylacian",
)
