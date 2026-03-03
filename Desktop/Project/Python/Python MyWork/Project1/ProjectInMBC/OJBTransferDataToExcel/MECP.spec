# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['C:\\Users\\12953 bao\\Desktop\\desktop\\work\\Project\\Python\\BasicLearnPython\\W3schools\\Python Tutorial\\ProjectInMBC\\Measurement equip connect\\MECP\\MECP.py'],
    pathex=[],
    binaries=[],
    datas=[('C:\\Users\\12953 bao\\Desktop\\desktop\\work\\Project\\Python\\BasicLearnPython\\W3schools\\data_form_config.txt', '.')],
    hiddenimports=[],
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
    a.datas,
    [],
    name='MECP',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
