# -*- mode: python ; coding: utf-8 -*-
#
# PyInstaller spec for Spring Generator
# Produces a single self-contained executable that:
#   - bundles Flask, NumPy, and all other dependencies
#   - embeds the templates/ directory
#   - auto-opens the browser on launch (when frozen)
#
# Build:
#   cd spring_app
#   pyinstaller spring_generator.spec

from pathlib import Path

HERE = Path(SPECPATH)          # directory containing this .spec file

a = Analysis(
    [str(HERE / "app.py")],
    pathex=[str(HERE)],
    binaries=[],
    datas=[
        (str(HERE / "templates"), "templates"),   # HTML templates
    ],
    hiddenimports=[
        "spring_gen",
        "numpy",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="spring_generator",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,          # keep console visible so the URL is shown
    disable_windowed_traceback=False,
    argv_emulation=False,  # macOS: do not intercept Apple Events
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
