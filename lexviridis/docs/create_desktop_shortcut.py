#!/usr/bin/env python3
"""
Script para crear acceso directo de LEX VIRIDIS en el escritorio
"""

import os
import sys
from pathlib import Path

def create_desktop_shortcut():
    """Crea un acceso directo en el escritorio"""
    try:
        import winshell
        from win32com.client import Dispatch
        
        # Rutas
        exe_path = Path("dist/LEX_VIRIDIS.exe").absolute()
        icon_path = Path("assets/lux_viridis_2.ico.ico").absolute()
        
        if not exe_path.exists():
            print(f"❌ Error: No se encontró el ejecutable en {exe_path}")
            return False
        
        if not icon_path.exists():
            print(f"❌ Error: No se encontró el icono en {icon_path}")
            return False
        
        # Crear acceso directo
        desktop = winshell.desktop()
        shortcut_path = os.path.join(desktop, "LEX VIRIDIS - Buscador Jurídico Ambiental.lnk")
        
        shell = Dispatch('WScript.Shell')
        shortcut = shell.CreateShortCut(shortcut_path)
        shortcut.Targetpath = str(exe_path)
        shortcut.WorkingDirectory = str(exe_path.parent)
        shortcut.IconLocation = str(icon_path)
        shortcut.Description = "LEX VIRIDIS - Buscador Jurídico Ambiental de Honduras v1.1.0"
        shortcut.save()
        
        print("✅ ¡ACCESO DIRECTO CREADO EXITOSAMENTE!")
        print(f"📍 Ubicación: {shortcut_path}")
        print(f"🎯 Ejecutable: {exe_path}")
        print(f"🖼️  Icono: {icon_path}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creando acceso directo: {e}")
        return False

def main():
    """Función principal"""
    print("🖥️  CREADOR DE ACCESO DIRECTO - LEX VIRIDIS")
    print("=" * 50)
    
    success = create_desktop_shortcut()
    
    if success:
        print("\n🎉 ¡PROCESO COMPLETADO!")
        print("✅ Acceso directo creado en el escritorio")
        print("✅ Puedes ejecutar LEX VIRIDIS desde el escritorio")
    else:
        print("\n❌ PROCESO FALLÓ")
    
    return success

if __name__ == "__main__":
    success = main()
    input("\nPresiona Enter para salir...")
    sys.exit(0 if success else 1)
