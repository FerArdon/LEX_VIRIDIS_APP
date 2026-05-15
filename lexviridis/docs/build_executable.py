#!/usr/bin/env python3
"""
Script para crear ejecutable de LEX VIRIDIS
Genera un archivo .exe autoejecutable con icono personalizado
"""

import os
import sys
import subprocess
from pathlib import Path

def create_executable():
    """Crea el ejecutable de LEX VIRIDIS usando PyInstaller"""
    
    print("🚀 CREANDO EJECUTABLE DE LEX VIRIDIS")
    print("=" * 50)
    
    # Verificar archivos necesarios
    main_script = Path("run_lexviridis.py")
    icon_file = Path("assets/lux_viridis_2.ico.ico")
    
    if not main_script.exists():
        print(f"❌ Error: No se encontró {main_script}")
        return False
    
    if not icon_file.exists():
        print(f"❌ Error: No se encontró el icono {icon_file}")
        return False
    
    print(f"✅ Script principal: {main_script}")
    print(f"✅ Icono: {icon_file}")
    
    # Configuración de PyInstaller
    pyinstaller_args = [
        "pyinstaller",
        "--onefile",                    # Crear un solo archivo ejecutable
        "--windowed",                   # Sin ventana de consola
        f"--icon={icon_file}",          # Icono personalizado
        "--name=LEX_VIRIDIS",           # Nombre del ejecutable
        "--distpath=dist",              # Directorio de salida
        "--workpath=build",             # Directorio de trabajo temporal
        "--specpath=.",                 # Directorio para el archivo .spec
        "--clean",                      # Limpiar cache antes de construir
        "--noconfirm",                  # No pedir confirmación
        
        # Incluir directorios de datos
        "--add-data=assets;assets",
        "--add-data=lexviridis;lexviridis",
        "--add-data=COMPENDIO LEYES FEMA;COMPENDIO LEYES FEMA",
        "--add-data=cache;cache",
        "--add-data=data;data",
        
        # Módulos ocultos que PyInstaller podría no detectar
        "--hidden-import=tkinter",
        "--hidden-import=tkinter.ttk",
        "--hidden-import=ttkbootstrap",
        "--hidden-import=fitz",
        "--hidden-import=PIL",
        "--hidden-import=psutil",
        "--hidden-import=numpy",
        "--hidden-import=ollama",
        "--hidden-import=tempfile",
        "--hidden-import=shutil",
        "--hidden-import=sys",
        
        # Script principal
        str(main_script)
    ]
    
    print("\n📦 Ejecutando PyInstaller...")
    print("Comando:", " ".join(pyinstaller_args))
    print("\n⏳ Esto puede tomar varios minutos...")
    
    try:
        # Ejecutar PyInstaller
        result = subprocess.run(
            pyinstaller_args,
            capture_output=True,
            text=True,
            cwd=os.getcwd()
        )
        
        if result.returncode == 0:
            print("\n✅ ¡EJECUTABLE CREADO EXITOSAMENTE!")
            
            # Verificar que el ejecutable se creó
            exe_path = Path("dist/LEX_VIRIDIS.exe")
            if exe_path.exists():
                size_mb = exe_path.stat().st_size / (1024 * 1024)
                print(f"📁 Ubicación: {exe_path.absolute()}")
                print(f"📏 Tamaño: {size_mb:.1f} MB")
                print(f"🎯 Icono: {icon_file}")
                
                # Crear acceso directo en el escritorio (opcional)
                create_desktop_shortcut(exe_path)
                
                return True
            else:
                print("❌ Error: El ejecutable no se encontró en la ubicación esperada")
                return False
        else:
            print("❌ Error durante la creación del ejecutable:")
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ Error ejecutando PyInstaller: {e}")
        return False

def create_desktop_shortcut(exe_path):
    """Crea un acceso directo en el escritorio (Windows)"""
    try:
        import winshell
        from win32com.client import Dispatch
        
        desktop = winshell.desktop()
        shortcut_path = os.path.join(desktop, "LEX VIRIDIS.lnk")
        
        shell = Dispatch('WScript.Shell')
        shortcut = shell.CreateShortCut(shortcut_path)
        shortcut.Targetpath = str(exe_path.absolute())
        shortcut.WorkingDirectory = str(exe_path.parent.absolute())
        shortcut.IconLocation = str(Path("assets/lux_viridis_2.ico.ico").absolute())
        shortcut.Description = "LEX VIRIDIS - Buscador Jurídico Ambiental de Honduras"
        shortcut.save()
        
        print(f"🖥️  Acceso directo creado en el escritorio: {shortcut_path}")
        
    except ImportError:
        print("⚠️  Para crear acceso directo, instala: pip install winshell pywin32")
    except Exception as e:
        print(f"⚠️  No se pudo crear acceso directo: {e}")

def main():
    """Función principal"""
    print("🔧 GENERADOR DE EJECUTABLE LEX VIRIDIS")
    print("=" * 60)
    print(f"Python: {sys.version}")
    print(f"Directorio: {os.getcwd()}")
    print()
    
    # Crear ejecutable
    success = create_executable()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 ¡PROCESO COMPLETADO EXITOSAMENTE!")
        print("✅ LEX VIRIDIS.exe está listo para usar")
        print("📂 Ubicación: dist/LEX_VIRIDIS.exe")
        print("\n💡 Instrucciones:")
        print("1. Navega a la carpeta 'dist'")
        print("2. Ejecuta 'LEX_VIRIDIS.exe'")
        print("3. ¡Disfruta del buscador jurídico ambiental!")
    else:
        print("❌ PROCESO FALLÓ")
        print("Revisa los errores arriba para más detalles")
    
    return success

if __name__ == "__main__":
    success = main()
    input("\nPresiona Enter para salir...")
    sys.exit(0 if success else 1)
