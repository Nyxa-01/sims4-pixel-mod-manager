# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for Sims 4 Pixel Mod Manager
Cross-platform build configuration for Windows, macOS, and Linux
"""

import platform
from pathlib import Path

# Project root directory
ROOT = Path(SPECPATH)

# Determine platform-specific settings
system = platform.system()

# Icon file based on platform
if system == 'Darwin':
    icon_file = str(ROOT / 'assets' / 'icons' / 'icon.icns')
elif system == 'Windows':
    icon_file = str(ROOT / 'assets' / 'icons' / 'icon.ico')
else:
    icon_file = str(ROOT / 'assets' / 'icons' / 'icon.png')

# Application name
APP_NAME = 'Sims4ModManager'

# Analysis configuration
a = Analysis(
    [str(ROOT / 'main.py')],
    pathex=[str(ROOT)],
    binaries=[],
    datas=[
        # Assets directory
        (str(ROOT / 'assets' / 'fonts'), 'assets/fonts'),
        (str(ROOT / 'assets' / 'icons'), 'assets/icons'),
        # VERSION file for runtime version checking
        (str(ROOT / 'VERSION'), '.'),
    ],
    hiddenimports=[
        # Tkinter and related
        'tkinter',
        'tkinter.ttk',
        'tkinter.messagebox',
        'tkinter.filedialog',
        'tkinter.scrolledtext',
        # Standard library modules used
        'json',
        'zipfile',
        'hashlib',
        'logging',
        'threading',
        'queue',
        'pathlib',
        'platform',
        'ctypes',
        'zlib',
        'ast',
        # Third-party
        'psutil',
        'requests',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclude test modules
        'pytest',
        'pytest_cov',
        'coverage',
        '_pytest',
        # Exclude development tools
        'black',
        'ruff',
        'mypy',
        'pylint',
        # Exclude unused tkinter themes
        'tkinter.tix',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

# Create PYZ archive
pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=None,
)

# Executable configuration
exe = EXE(
    pyz,
    a.scripts,
    [],  # No binaries in EXE for directory mode
    exclude_binaries=True,  # Directory mode (faster for development)
    name=APP_NAME,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # Windowed mode (no console)
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_file,
)

# Collect all files into distribution directory
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name=APP_NAME,
)

# macOS-specific: Create app bundle
if system == 'Darwin':
    app = BUNDLE(
        coll,
        name=f'{APP_NAME}.app',
        icon=icon_file,
        bundle_identifier='com.sims4modmanager.app',
        info_plist={
            'CFBundleName': 'Sims 4 Pixel Mod Manager',
            'CFBundleDisplayName': 'Sims 4 Pixel Mod Manager',
            'CFBundleVersion': '1.0.0',
            'CFBundleShortVersionString': '1.0.0',
            'CFBundleExecutable': APP_NAME,
            'CFBundleIdentifier': 'com.sims4modmanager.app',
            'CFBundlePackageType': 'APPL',
            'CFBundleSignature': 'S4MM',
            'LSMinimumSystemVersion': '10.13.0',
            'NSHighResolutionCapable': True,
            'NSRequiresAquaSystemAppearance': False,  # Support dark mode
        },
    )
