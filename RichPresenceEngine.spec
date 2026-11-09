# -*- mode: python ; coding: utf-8 -*-
#
# GenshinEngine - windowed (console-less) OCR engine exe.
#
# Bundles main.py plus all third-party dependencies (RapidOCR, ONNX Runtime
# DirectML, OpenCV, NumPy, pypresence, pywin32...). Application code that
# lives in plain files next to the exe (core/, CONFIG.py) is EXCLUDED from
# the bundle and imported from disk at runtime - main.py inserts its own
# folder at sys.path[0] when frozen. This keeps every __file__-based path
# in core/ working unchanged.

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    # RapidOCR reads config.yaml and its .onnx models relative to its own
    # package dir (__file__), which PyInstaller doesn't bundle automatically.
    datas=[
        ('python3.12.8_embedded/Lib/site-packages/rapidocr_onnxruntime/config.yaml',
         'rapidocr_onnxruntime'),
        ('python3.12.8_embedded/Lib/site-packages/rapidocr_onnxruntime/models',
         'rapidocr_onnxruntime/models'),
    ],
    # core/ is excluded from analysis below, so PyInstaller never sees its
    # third-party imports - they must be listed here explicitly.
    hiddenimports=[
        'watchdog', 'watchdog.observers',
        'pypresence', 'psutil',
        'numpy', 'PIL',
        'rapidocr_onnxruntime', 'onnxruntime', 'cv2',
        'win32.win32gui', 'win32.win32process', 'win32.win32api', 'pywintypes',
        'win32.lib.win32con',
    ],
    hookspath=[''],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Provided as plain folders/files next to the exe
        'core', 'gui', 'tools', 'CONFIG',
        # Unused GUI-toolkit backends
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
    name='RichPresenceEngine',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,          # <- never spawns a terminal window
    icon='resources/assets/images/app-specific/Icon_Distributors.ico',
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
    name='RichPresenceEngine',
)
