@echo off
echo ============================================
echo    LEX VIRIDIS - Generador de Paquete Distribuible
echo ============================================
echo.

REM 1. Limpieza previa
call clean_build.bat

echo.
echo [2/2] Compilando INST_LEXVIRIDIS...
pyinstaller INST_LEXVIRIDIS.spec --noconfirm

if exist "dist\LEXVIRIDIS_V3.0.0_FR_2026\LEXVIRIDIS_V3.0.0_FR_2026.exe" (
    echo.
    echo ============================================
    echo    EXITO! Paquete generado en:
    echo    dist\LEXVIRIDIS_V3.0.0_FR_2026\LEXVIRIDIS_V3.0.0_FR_2026.exe
    echo ============================================
    echo.
    echo Nota: La carpeta 'assets' ya ha sido copiada internamente.
) else (
    echo.
    echo ERROR: Fallo la compilacion.
)

echo.
pause
