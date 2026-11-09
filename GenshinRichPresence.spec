# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['webview_launcher.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=['webview', 'bottle', 'pythonnet', 'clr_loader', 'proxy_tools'],
    hookspath=[''],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # The GUI is forced to the EdgeChromium backend (webview_launcher.py);
        # pywebview's optional Qt/Tk/EFL backends are dead weight.
        'PyQt5', 'tkinter',
    ],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='GenshinRichPresence',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon='resources/assets/images/app-specific/ApplicationIcon.ico',
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
    name='GenshinRichPresence',
)
