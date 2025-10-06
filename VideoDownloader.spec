# -*- mode: python ; coding: utf-8 -*-

import os
import sys
from pathlib import Path

# Get the current directory
current_dir = Path.cwd()

# Define the main script
main_script = 'main_V3.py'

# Define data files to include
datas = [
    ('requirements.txt', '.'),
    ('README.md', '.'),
    ('LICENSE.txt', '.'),
    ('icon.ico', '.'),
    ('icon.png', '.'),
    ('RELEASE_NOTES.md', '.'),
    ('LICENSE_AGREEMENT.txt', '.'),
]

# Define hidden imports that PyInstaller might miss
hiddenimports = [
    'PyQt5.QtCore',
    'PyQt5.QtGui', 
    'PyQt5.QtWidgets',
    'PyQt5.sip',
    'yt_dlp',
    'yt_dlp.extractor',
    'yt_dlp.postprocessor',
    'yt_dlp.downloader',
    'yt_dlp.utils',
    'yt_dlp.compat',
    'yt_dlp.networking',
    'yt_dlp.cookies',
    'selenium',
    'selenium.webdriver',
    'selenium.webdriver.chrome',
    'selenium.webdriver.chrome.options',
    'selenium.webdriver.chrome.service',
    'selenium.webdriver.common.by',
    'selenium.webdriver.common.keys',
    'selenium.webdriver.common.action_chains',
    'selenium.webdriver.support',
    'selenium.webdriver.support.ui',
    'selenium.webdriver.support.expected_conditions',
    'browser_cookie3',
    'browser_cookie3.chrome',
    'browser_cookie3.firefox',
    'browser_cookie3.edge',
    'browser_cookie3.opera',
    'browser_cookie3.safari',
    'requests',
    'requests.adapters',
    'requests.auth',
    'requests.cookies',
    'requests.exceptions',
    'requests.models',
    'requests.sessions',
    'requests.utils',
    'urllib3',
    'urllib3.util',
    'urllib3.util.retry',
    'urllib3.util.connection',
    'urllib3.util.ssl_',
    'urllib3.util.timeout',
    'urllib3.util.url',
    'urllib3.poolmanager',
    'urllib3.exceptions',
    'certifi',
    'charset_normalizer',
    'idna',
    'sqlite3',
    'json',
    'tempfile',
    'threading',
    'subprocess',
    'shutil',
    'pathlib',
    'datetime',
    'logging',
    'base64',
    're',
    'os',
    'sys',
    'webbrowser',
    'platform',
    'ctypes',
    'ctypes.wintypes',
    'win32api',
    'win32con',
    'win32gui',
    'win32process',
    'pywintypes',
    'setup_helper',
    'enhanced_cookie_collector',
    'browser_cookie_helper',
    'secure_cookie_manager',
    'url_detector',
    'platform_login_manager',
    'captionsDownload',
    'mkvTomp4Converter',
    'command_toupload_to_github',
    'tokenize',
    'portalocker'
]

# Define binaries to include
binaries = []

# Analysis configuration
a = Analysis(
    [main_script],
    pathex=[str(current_dir)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

# Remove duplicate files
pyz = PYZ(a.pure, a.zipped_data, cipher=None)

# Create the executable
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='VideoDownloader',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Set to False for GUI application
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico',  # Use the icon file
    version_file=None,
)

# Create a directory distribution
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='VideoDownloader'
)