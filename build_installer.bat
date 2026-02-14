@echo off
echo ============================================
echo    LEX VIRIDIS - Generador de Instalador
echo ============================================
echo.

REM Verificar que existe el ejecutable
if not exist "dist\LEX_VIRIDIS.exe" (
    echo ERROR: No se encontro dist\LEX_VIRIDIS.exe
    echo Primero ejecute: build_exe.bat
    pause
    exit /b 1
)

REM Buscar Inno Setup
set ISCC=""
if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" (
    set ISCC="C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
) else if exist "C:\Program Files\Inno Setup 6\ISCC.exe" (
    set ISCC="C:\Program Files\Inno Setup 6\ISCC.exe"
) else (
    echo ERROR: No se encontro Inno Setup 6
    echo Descarguelo de: https://jrsoftware.org/isdl.php
    pause
    exit /b 1
)

echo Creando directorio de salida...
if not exist "installer" mkdir installer

echo.
echo Compilando instalador con Inno Setup...
%ISCC% installer.iss

if exist "installer\LEX_VIRIDIS_Setup_v3.0.exe" (
    echo.
    echo ============================================
    echo    EXITO! Instalador generado en:
    echo    installer\LEX_VIRIDIS_Setup_v3.0.exe
    echo ============================================
    
    echo.
    echo Tamanio del instalador:
    for %%A in (installer\LEX_VIRIDIS_Setup_v3.0.exe) do echo    %%~zA bytes
    
    explorer installer
) else (
    echo.
    echo ERROR: No se pudo generar el instalador.
)

echo.
pause
