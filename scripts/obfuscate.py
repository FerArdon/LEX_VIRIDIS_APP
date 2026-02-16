
import os
import shutil
import subprocess
import sys
from pathlib import Path

def main():
    print("🔒 Iniciando ofuscación de código con PyArmor...")
    
    # 1. Verificar PyArmor
    try:
        subprocess.run(["pyarmor", "--version"], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ PyArmor no encontrado. Instalando...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyarmor"], check=True)

    # 2. Directorios
    BASE_DIR = Path.cwd()
    SRC_DIR = BASE_DIR / "lexviridis"
    DIST_DIR = BASE_DIR / "dist_obfuscated"
    
    if DIST_DIR.exists():
        shutil.rmtree(DIST_DIR)
    DIST_DIR.mkdir()

    # 3. Ejecutar PyArmor
    # Usamos modo 'gen' para generar paquete ofuscado
    # -O: Output dir
    # -r: Recursive
    # --exclude: Excluir tests o venv si estuvieran dentro (no deberian)
    try:
        cmd = [
            "pyarmor", "gen",
            "-O", str(DIST_DIR),
            "-r",
            str(SRC_DIR)
        ]
        print(f"Running: {' '.join(cmd)}")
        subprocess.run(cmd, check=True)
        
        print(f"✅ Código ofuscado generado en: {DIST_DIR}")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error durante ofuscación: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
