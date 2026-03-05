from PyInstaller.utils.hooks import collect_submodules, collect_dynamic_libs

pedalboard_hidden = collect_submodules("pedalboard")
pedalboard_bins = collect_dynamic_libs("pedalboard")

block_cipher = None

a = Analysis(
    ['coldcamera/window.py'],
    pathex=[],
    binaries=pedalboard_bins,
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
    ] + pedalboard_hidden,
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    cipher=block_cipher,
)
