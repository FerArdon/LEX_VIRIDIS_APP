#!/usr/bin/env python3
"""
Script para crear el instalador de LEX VIRIDIS usando Inno Setup
Automatiza todo el proceso de generación del instalador profesional
"""

import os
import subprocess
import sys
from pathlib import Path


def find_inno_setup():
    """Busca la instalación de Inno Setup en el sistema."""
    possible_paths = [
        r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
        r"C:\Program Files\Inno Setup 6\ISCC.exe",
        r"C:\Program Files (x86)\Inno Setup 5\ISCC.exe",
        r"C:\Program Files\Inno Setup 5\ISCC.exe",
    ]

    for path in possible_paths:
        if Path(path).exists():
            return Path(path)

    return None

def check_prerequisites():
    """Verifica que todos los archivos necesarios estén presentes."""

    print("🔍 Verificando prerequisitos...")

    required_files = [
        "dist/LEX_VIRIDIS.exe",
        "LEX_VIRIDIS_Setup.iss",
        "LICENSE.txt",
        "README_INSTALACION.txt",
        "INSTRUCCIONES_USO.txt",
        "assets/lux_viridis_2.ico.ico"
    ]

    missing_files = []

    for file in required_files:
        if not Path(file).exists():
            missing_files.append(file)
            print(f"❌ Falta: {file}")
        else:
            print(f"✅ Encontrado: {file}")

    if missing_files:
        print(f"\n❌ Faltan {len(missing_files)} archivos necesarios:")
        for file in missing_files:
            print(f"   - {file}")
        return False

    print("✅ Todos los archivos necesarios están presentes")
    return True

def create_installer_directory():
    """Crea el directorio para el instalador."""
    installer_dir = Path("installer")
    installer_dir.mkdir(exist_ok=True)
    print(f"📁 Directorio del instalador: {installer_dir.absolute()}")
    return installer_dir

def create_readme_md():
    """Crea un archivo README.md si no existe."""
    readme_path = Path("README.md")
    if not readme_path.exists():
        print("📝 Creando README.md...")
        readme_content = """# LEX VIRIDIS v1.1.0

## Buscador Jurídico Ambiental de Honduras

LEX VIRIDIS es una aplicación especializada en la búsqueda y consulta de legislación ambiental hondureña.

### Características principales:
- Motor de búsqueda avanzado con más de 52,745 términos indexados
- Visor de PDF integrado con resaltado automático
- Base de datos completa con 164 documentos legales
- Interfaz moderna y profesional
- Sistema de caché inteligente

### Requisitos del sistema:
- Windows 10 (64-bit) o superior
- 4 GB de RAM mínimo
- 3 GB de espacio libre en disco

### Instalación:
1. Descargue el instalador LEX_VIRIDIS_v1.1.0_Setup.exe
2. Ejecute el instalador como administrador
3. Siga las instrucciones del asistente de instalación

### Uso:
1. Inicie LEX VIRIDIS desde el menú Inicio o escritorio
2. Escriba términos de búsqueda en el campo principal
3. Haga doble clic en los resultados para abrir los PDFs
4. Los términos aparecerán resaltados automáticamente

### Soporte:
Para soporte técnico, consulte la documentación incluida o visite www.lexviridis.hn

---
Copyright (C) 2025 LEX VIRIDIS Development Team
"""
        readme_path.write_text(readme_content, encoding='utf-8')
        print("✅ README.md creado")
    else:
        print("✅ README.md ya existe")

def build_installer():
    """Construye el instalador usando Inno Setup."""

    print("\n🚀 CREANDO INSTALADOR DE LEX VIRIDIS")
    print("=" * 50)

    # Verificar prerequisitos
    if not check_prerequisites():
        return False

    # Buscar Inno Setup
    inno_setup_path = find_inno_setup()
    if not inno_setup_path:
        print("❌ Error: Inno Setup no está instalado")
        print("Descargue e instale Inno Setup desde: https://jrsoftware.org/isinfo.php")
        return False

    print(f"✅ Inno Setup encontrado: {inno_setup_path}")

    # Crear directorio del instalador
    installer_dir = create_installer_directory()

    # Crear README.md si no existe
    create_readme_md()

    # Construir el instalador
    script_path = Path("LEX_VIRIDIS_Setup.iss").absolute()

    print("\n📦 Compilando instalador...")
    print(f"Script: {script_path}")

    try:
        # Ejecutar Inno Setup Compiler
        result = subprocess.run([
            str(inno_setup_path),
            str(script_path)
        ], capture_output=True, text=True, cwd=os.getcwd())

        if result.returncode == 0:
            print("\n✅ ¡INSTALADOR CREADO EXITOSAMENTE!")

            # Buscar el instalador generado
            installer_files = list(installer_dir.glob("*.exe"))
            if installer_files:
                installer_file = installer_files[0]
                size_mb = installer_file.stat().st_size / (1024 * 1024)

                print(f"📁 Ubicación: {installer_file.absolute()}")
                print(f"📏 Tamaño: {size_mb:.1f} MB")
                print(f"📅 Fecha: {installer_file.stat().st_mtime}")

                # Mostrar información adicional
                print("\n💡 Información del instalador:")
                print("   - Nombre: LEX_VIRIDIS_v1.1.0_Setup.exe")
                print("   - Versión: 1.1.0")
                print("   - Plataforma: Windows 64-bit")
                print("   - Tipo: Instalador profesional con Inno Setup")

                return True
            else:
                print("❌ Error: No se encontró el archivo del instalador")
                return False
        else:
            print("❌ Error durante la compilación del instalador:")
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
            return False

    except Exception as e:
        print(f"❌ Error ejecutando Inno Setup: {e}")
        return False

def show_instructions():
    """Muestra instrucciones para distribuir el instalador."""

    print("\n" + "=" * 60)
    print("🎉 ¡INSTALADOR COMPLETADO EXITOSAMENTE!")
    print("=" * 60)

    print("\n📋 INSTRUCCIONES PARA DISTRIBUCIÓN:")
    print("1. El instalador está en la carpeta 'installer/'")
    print("2. Pruebe el instalador en un sistema limpio")
    print("3. Distribuya el archivo .exe a los usuarios finales")
    print("4. Los usuarios deben ejecutar como administrador")

    print("\n🔧 CARACTERÍSTICAS DEL INSTALADOR:")
    print("✅ Instalación profesional con asistente")
    print("✅ Detección automática de requisitos del sistema")
    print("✅ Creación de accesos directos")
    print("✅ Registro en Windows")
    print("✅ Desinstalador incluido")
    print("✅ Soporte para instalación silenciosa")

    print("\n📦 CONTENIDO DEL INSTALADOR:")
    print("✅ LEX VIRIDIS.exe (289.5 MB)")
    print("✅ Base de datos legal completa")
    print("✅ Documentación y licencias")
    print("✅ Recursos gráficos")
    print("✅ Archivos de configuración")

    print("\n🎯 PRÓXIMOS PASOS:")
    print("1. Probar el instalador")
    print("2. Crear documentación de distribución")
    print("3. Preparar canal de distribución")
    print("4. Configurar sistema de actualizaciones")

def main():
    """Función principal."""

    print("🔧 GENERADOR DE INSTALADOR LEX VIRIDIS")
    print("=" * 60)
    print(f"Python: {sys.version}")
    print(f"Directorio: {os.getcwd()}")
    print()

    # Construir instalador
    success = build_installer()

    if success:
        show_instructions()
    else:
        print("\n❌ PROCESO FALLÓ")
        print("Revise los errores arriba para más detalles")

    return success

if __name__ == "__main__":
    success = main()
    input("\nPresiona Enter para salir...")
    sys.exit(0 if success else 1)
