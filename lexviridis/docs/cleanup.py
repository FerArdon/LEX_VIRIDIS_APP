
"""
🧹 LEX VIRIDIS - Script de Limpieza y Reorganización
Ejecutar desde la raíz del proyecto.
"""

import shutil
from datetime import datetime, timedelta
from pathlib import Path

BASE_DIR = Path(r"c:\Users\frard\OneDrive\LEX_VIRIDIS_APP")

# === ARCHIVOS BASURA A ELIMINAR ===
BASURA_PATTERNS = [
    "**/__pycache__",
    "**/*.pyc",
    "**/*.pyo",
    "**/*.bak",
    "**/*~",
    "**/Thumbs.db",
    "**/desktop.ini",
    "**/.DS_Store",
]

# === ARCHIVOS ESPECÍFICOS A ELIMINAR ===
ARCHIVOS_ELIMINAR = [
    # Scripts de diagnóstico temporales
    "diag_324.py",
    "fix_art324.py",
    "test_busqueda.py",

    # Duplicados de requirements
    "requirements_updated.txt",

    # Archivos de instalación extraños en lexviridis/
    "lexviridis/InstallationLog.txt",
    "lexviridis/components.xml",
    "lexviridis/installer.dat",
    "lexviridis/maintenancetool.dat",
    "lexviridis/maintenancetool.exe",
    "lexviridis/maintenancetool.ini",
    "lexviridis/network.xml",
    "lexviridis/gpt4all-32.png",
    "lexviridis/gpt4all-48.png",
    "lexviridis/gpt4all.ico",

    # Visor duplicado
    "lexviridis/pdf_viewer.py",  # Usar solo pdf_viewer_fixed.py
]

# === CARPETAS A ELIMINAR ===
CARPETAS_ELIMINAR = [
    "lexviridis/bin",              # Binarios de gpt4all (enorme)
    "lexviridis/lib",              # Librerías de gpt4all
    "lexviridis/installerResources",
    "lexviridis/Licenses",         # Licencias de gpt4all
    "build",                       # Build artifacts
    "dist",                        # Distribution artifacts
    "cache",                       # Cache
    "installer",                   # Instalador viejo
    "backups",                     # Backups viejos
    "temp_pdfs",                   # PDFs temporales
]

def limpiar_pycache():
    """Elimina todos los __pycache__ y .pyc"""
    print("\n🗑️ Eliminando __pycache__ y archivos .pyc...")
    count = 0
    for pattern in ["**/__pycache__", "**/*.pyc"]:
        for path in BASE_DIR.glob(pattern):
            try:
                if path.is_dir():
                    shutil.rmtree(path)
                else:
                    path.unlink()
                count += 1
            except Exception as e:
                print(f"   ⚠️ No se pudo eliminar {path}: {e}")
    print(f"   ✅ Eliminados {count} items de cache")

def limpiar_archivos_especificos():
    """Elimina archivos específicos innecesarios"""
    print("\n🗑️ Eliminando archivos innecesarios...")
    for archivo in ARCHIVOS_ELIMINAR:
        path = BASE_DIR / archivo
        if path.exists():
            try:
                path.unlink()
                print(f"   ✅ Eliminado: {archivo}")
            except Exception as e:
                print(f"   ⚠️ Error con {archivo}: {e}")

def limpiar_carpetas():
    """Elimina carpetas innecesarias"""
    print("\n🗑️ Eliminando carpetas innecesarias...")
    for carpeta in CARPETAS_ELIMINAR:
        path = BASE_DIR / carpeta
        if path.exists():
            try:
                shutil.rmtree(path)
                print(f"   ✅ Eliminada carpeta: {carpeta}")
            except Exception as e:
                print(f"   ⚠️ Error con {carpeta}: {e}")

def limpiar_logs_viejos():
    """Elimina logs con más de 7 días"""
    print("\n🗑️ Limpiando logs viejos (>7 días)...")
    logs_dir = BASE_DIR / "logs"
    if logs_dir.exists():
        limite = datetime.now() - timedelta(days=7)
        count = 0
        for log in logs_dir.glob("*.log"):
            if datetime.fromtimestamp(log.stat().st_mtime) < limite:
                log.unlink()
                count += 1
        print(f"   ✅ Eliminados {count} logs viejos")

def crear_gitignore():
    """Crea un .gitignore apropiado"""
    print("\n📄 Creando .gitignore...")
    gitignore_content = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
dist/
*.egg-info/
.eggs/

# Virtual Environment
.venv/
venv/
ENV/

# IDE
.vscode/
.idea/
*.swp
*.swo

# LEX VIRIDIS Específico
temp_pdfs/
cache/
logs/*.log
*.bak
*~

# Windows
Thumbs.db
desktop.ini

# Datos sensibles
.env
*.pem
*.key

# Base de datos (opcional, quitar si quieres versionar)
# LEX_VIRIDIS_DB/*.db

# Documentos PDF (muy grandes para Git)
COMPENDIO LEYES FEMA/
"""

    gitignore_path = BASE_DIR / ".gitignore"
    gitignore_path.write_text(gitignore_content, encoding='utf-8')
    print("   ✅ .gitignore creado")

def mostrar_resumen():
    """Muestra resumen final"""
    print("\n" + "=" * 60)
    print("📊 RESUMEN FINAL")
    print("=" * 60)

    # Contar archivos en raíz
    archivos_raiz = [f for f in BASE_DIR.iterdir() if f.is_file()]
    carpetas_raiz = [f for f in BASE_DIR.iterdir() if f.is_dir()]

    print(f"   Archivos en raíz: {len(archivos_raiz)}")
    print(f"   Carpetas en raíz: {len(carpetas_raiz)}")

    print("\n   📁 Estructura actual:")
    for item in sorted(BASE_DIR.iterdir()):
        if item.name.startswith('.'):
            continue
        tipo = "📁" if item.is_dir() else "📄"
        print(f"      {tipo} {item.name}")

if __name__ == "__main__":
    print("=" * 60)
    print("🧹 LEX VIRIDIS - LIMPIEZA DEL PROYECTO")
    print("=" * 60)

    limpiar_pycache()
    limpiar_archivos_especificos()
    limpiar_carpetas()
    limpiar_logs_viejos()
    crear_gitignore()
    mostrar_resumen()

    print("\n✨ ¡Limpieza completada!")
