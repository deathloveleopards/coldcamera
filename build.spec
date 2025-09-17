# build.spec
block_cipher = None

a = Analysis(
    ['application/window.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('application/static/zoom.png', 'application/static'),
    ],
    hiddenimports=[
        "PySide6",
        "PIL",
        "numpy",
        "loguru",
        "pyqtdarktheme",
        "moderngl",
        "cv2",
        "blend_modes",
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    cipher=block_cipher,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='coldcamera',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon=None
)
