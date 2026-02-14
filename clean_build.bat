@echo off
echo ==========================================
echo LIMPIANDO CARPETAS DE COMPILACION (BUILD/DIST)
echo ==========================================

if exist "build" (
    echo Eliminando carpeta "build"...
    rmdir /s /q "build"
) else (
    echo Carpeta "build" no encontrada.
)

if exist "dist" (
    echo Eliminando carpeta "dist"...
    rmdir /s /q "dist"
) else (
    echo Carpeta "dist" no encontrada.
)

echo.
echo Limpieza completada. Listo para compilar.
echo ==========================================
timeout /t 3 >nul
