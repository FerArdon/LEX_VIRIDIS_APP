@echo off
setlocal enabledelayedexpansion

echo ============================================================
echo           LEX VIRIDIS - Build System (V3 CTk)
echo ============================================================
echo.

:: 1. Activar Entorno Virtual
echo [1/5] Verificando entorno virtual...
if exist ".venv\Scripts\activate.bat" (
    echo    Activando .venv...
    call .venv\Scripts\activate.bat
) else (
    echo    ADVERTENCIA: No se encontro .venv. Usando Python global.
)

:: 2. Instalar Dependencias
echo.
echo [2/5] Actualizando dependencias...
pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo ERROR: No se pudieron instalar las dependencias.
    pause
    exit /b 1
)

:: 3. Limpieza de Builds Anteriores
echo.
echo [3/5] Limpiando residuos previos...
if exist "build" rmdir /s /q build
if exist "dist" rmdir /s /q dist
echo    Limpieza completada.

:: 4. Ejecutar PyInstaller usando el spec file actualizado
echo.
echo [4/5] Compilando ejecutable con PyInstaller (usando LEX_VIRIDIS_2.spec)...
pyinstaller --noconfirm --clean docs\LEX_VIRIDIS_2.spec

if errorlevel 1 (
    echo ERROR: Fallo la compilacion del ejecutable.
    pause
    exit /b 1
)

echo    Ejecutable generado en dist\LEX_VIRIDIS_2\LEX_VIRIDIS_2.exe

:: 5. Generar Instalador (Opcional)
echo.
echo [5/5] Buscando Inno Setup para generar instalador...
set ISCC=""
if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" (
    set ISCC="C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
) else if exist "C:\Program Files\Inno Setup 6\ISCC.exe" (
    set ISCC="C:\Program Files\Inno Setup 6\ISCC.exe"
)

if not %ISCC% == "" (
    echo    Generando instalador...
    if not exist "installer" mkdir installer
    %ISCC% tools\installer.iss
    if errorlevel 0 (
        echo    EXITO: Instalador creado en installer\
    )
) else (
    echo    AVISO: Inno Setup no encontrado. El ejecutable esta en dist\LEX_VIRIDIS_2\
)

echo.
echo ============================================================
echo           PROCESO DE CONSTRUCCION FINALIZADO
echo ============================================================
echo.
pause
