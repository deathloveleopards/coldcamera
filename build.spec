# build.spec
block_cipher = None

a = Analysis(
    ['coldcamera/window.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('coldcamera/static/zoom.png', 'coldcamera/static'),
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
        "pedalboard",
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
    [],
    exclude_binaries=True,
    name='coldcamera',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,  # no UPX compression
    console=False,
    icon=None
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    name='coldcamera'
)
