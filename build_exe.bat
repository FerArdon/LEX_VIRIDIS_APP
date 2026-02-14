@echo off
echo ============================================
echo    LEX VIRIDIS - Generador de Instalador
echo ============================================
echo.

REM Activar entorno virtual si existe
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
)

REM Verificar PyInstaller
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo Instalando PyInstaller...
    pip install pyinstaller
)

echo.
echo [1/3] Limpiando builds anteriores...
rmdir /s /q build 2>nul
rmdir /s /q dist 2>nul

echo.
echo [2/3] Generando ejecutable...
pyinstaller LEX_VIRIDIS.spec --clean --noconfirm

echo.
echo [3/3] Verificando resultado...
if exist "dist\LEX_VIRIDIS.exe" (
    echo.
    echo ============================================
    echo    EXITO! Ejecutable generado en:
    echo    dist\LEX_VIRIDIS.exe
    echo ============================================
    
    REM Copiar assets necesarios
    echo Copiando recursos adicionales...
    xcopy /E /I /Y assets dist\assets >nul 2>&1
    xcopy /E /I /Y LEX_VIRIDIS_DB dist\LEX_VIRIDIS_DB >nul 2>&1
    if exist "LEX_VIRIDIS_LICENCIA" xcopy /E /I /Y LEX_VIRIDIS_LICENCIA dist\LEX_VIRIDIS_LICENCIA >nul 2>&1
    
    echo.
    echo Tamanio del ejecutable:
    for %%A in (dist\LEX_VIRIDIS.exe) do echo    %%~zA bytes
    
    echo.
    echo Para crear el instalador, ejecute:
    echo    build_installer.bat
) else (
    echo.
    echo ERROR: No se pudo generar el ejecutable.
    echo Revise los logs de PyInstaller arriba.
)

echo.
pause
