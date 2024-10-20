# -*- mode: python ; coding: utf-8 -*-


block_cipher = None


a = Analysis(['ACRN_pyside.py'],
             pathex=[],
             binaries=[],
             datas=[],
             hiddenimports=[],
             hookspath=[],
             hooksconfig={},
             runtime_hooks=[],
             excludes=[
             'matplotlib',
             'tkinter',
             'hdf5',
             'h5py',
             'MySQLdb',
             'scipy',
             ],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)

Key = ['mkl','d3dcompiler_47','opengl32sw','Qt5DBus','Qt5Quick','Qt5WebSockets','Qt5VirtualKeyboard','Qt5Test','Qt5OpenGL','libGLESv2','libEGL']#'libopenblas',


def remove_from_list(input, keys):
    outlist = []
    for item in input:
        name, _, _ = item
        flag = 0
        for key_word in keys:
            if name.find(key_word) > -1:
                flag = 1
        if flag != 1:
            outlist.append(item)
    return outlist


exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,  
          [],
          name='ACRN_pyside',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=False,
          disable_windowed_traceback=False,
          target_arch=None,
          codesign_identity=None,
          entitlements_file=None,
          icon="ACRN_ICON.ico")
