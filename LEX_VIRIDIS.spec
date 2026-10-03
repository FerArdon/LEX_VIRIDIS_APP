# -*- mode: python ; coding: utf-8 -*-
"""
LEX VIRIDIS - PyInstaller Spec File
Genera ejecutable portable con todos los recursos incluidos.
"""

import os
from pathlib import Path

# Rutas base
# Utilizar dinámicamente el directorio actual para soportar ejecución en cualquier ubicación
BASE_DIR = Path(os.path.abspath(os.getcwd()))
ASSETS_DIR = BASE_DIR / "assets"
DATA_DIR = BASE_DIR / "data"
DB_DIR = BASE_DIR / "LEX_VIRIDIS_DB"

# La clave de firma de licencias NO esta en el repositorio. Sin ella la app compilada
# no podria validar ninguna licencia: abortar en vez de producir un .exe inservible.
if not (BASE_DIR / "lexviridis_license_secret.py").exists():
    raise SystemExit("Falta lexviridis_license_secret.py en la raiz (clave de licencias, no versionada). Copiela de la carpeta privada del generador antes de compilar.")

block_cipher = None

# Archivos de datos a incluir
datas = [
    # Assets (iconos, imágenes hero)
    (str(ASSETS_DIR), 'assets'),
    # Base de datos
    (str(DB_DIR / "legislacion_ambiental.db"), 'LEX_VIRIDIS_DB'),
    # Archivos de configuración
    (str(BASE_DIR / "config.py"), '.'),
    # Traducciones i18n
    (str(BASE_DIR / "lexviridis" / "i18n"), os.path.join('lexviridis', 'i18n')),
]

# Incluir icons.json de Flet (requerido para ft.Icons.* en modo frozen)
import flet as _flet
_flet_dir = os.path.dirname(_flet.__file__)
_icons_json = os.path.join(_flet_dir, 'controls', 'material', 'icons.json')
if os.path.exists(_icons_json):
    datas.append((_icons_json, os.path.join('flet', 'controls', 'material')))

# Agregar data folder si existe
if DATA_DIR.exists():
    for f in DATA_DIR.glob("*.db"):
        datas.append((str(f), 'data'))

# Módulos ocultos que PyInstaller no detecta automáticamente
hiddenimports = [
    'flet',
    'flet_core',
    'flet_runtime',
    'sqlite3',
    'reportlab',
    'reportlab.lib',
    'reportlab.lib.colors',
    'reportlab.lib.units',
    'reportlab.lib.pagesizes',
    'reportlab.platypus',
    'reportlab.pdfgen',
    'google.generativeai',
    'PIL',
    'PIL.Image',
    'pathlib',
    'logging',
    'json',
    'hashlib',
    'hmac',
    'base64',
    'uuid',
    'threading',
    'datetime',
    'lexviridis',
    'lexviridis.ui_v2',
    'lexviridis.design_system',
    'lexviridis.search_engine',
    'lexviridis.indexer',
    'lexviridis.ia_gemini',
    'lexviridis.security',
    'lexviridis.notifications',
    'lexviridis.ai_assistant',
    'lexviridis.analytics',
    'lexviridis.theme_manager',
    'lexviridis.accessibility',
    'lexviridis.translations',
    'lexviridis.cloud_sync',
    'lexviridis.proactive_assistant',
    'lexviridis.citations',
    'lexviridis.study_system',
    'lexviridis.license_ui',
    'lexviridis.license_system',
    'lexviridis.pdf_exporter',
    'lexviridis.pdf_exporter',
    'flet_desktop',
    'flet_desktop.app',
    'flet_charts',
    'lexviridis_license_secret',
]

a = Analysis(
    ['run_modern_ui.py'],
    pathex=[str(BASE_DIR)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['matplotlib', 'numpy', 'pandas', 'scipy', 'PyQt5', 'PyQt6', 'PySide2', 'PySide6', 'tkinter'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# Incluir binarios de flet_desktop explícitamente
try:
    import flet_desktop
    flet_bin = os.path.join(os.path.dirname(flet_desktop.__file__), 'app')
    a.datas += Tree(flet_bin, prefix='flet_desktop/app')
except ImportError:
    pass

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='LEX_VIRIDIS',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Sin ventana de consola (los errores de arranque van a %APPDATA%\LEX VIRIDIS\error_arranque.log)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(ASSETS_DIR / "LEXVIRIDIS_WHITE_BG.ico"),  # Icono del ejecutable
    version='version_info.txt',  # Información de versión (opcional)
)
