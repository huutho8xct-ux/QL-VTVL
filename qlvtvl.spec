# -*- mode: python ; coding: utf-8 -*-
# Đóng gói: pyinstaller qlvtvl.spec --noconfirm
block_cipher = None

EXCLUDES = [
    "tkinter", "unittest", "pydoc_data", "PySide6.QtWebEngineCore", "PySide6.QtWebEngineWidgets",
    "PySide6.QtQml", "PySide6.QtQuick", "PySide6.Qt3DCore", "PySide6.QtMultimedia", "PySide6.QtPdf",
    "PySide6.QtCharts", "PySide6.QtDataVisualization", "PySide6.QtBluetooth", "PySide6.QtSql",
]

a = Analysis(
    ["run.py"],
    pathex=[],
    binaries=[],
    datas=[("qlvtvl/assets", "qlvtvl/assets")],
    hiddenimports=["docx", "openpyxl"],
    hookspath=[],
    runtime_hooks=[],
    excludes=EXCLUDES,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="QL-VTVL",
    debug=False,
    strip=False,
    upx=False,
    console=False,
    icon="qlvtvl/assets/app.ico",
    version="installer/version_info.txt",
)
coll = COLLECT(exe, a.binaries, a.zipfiles, a.datas, strip=False, upx=False, name="QL-VTVL")
