@echo off
echo ============================================================
echo           LEX VIRIDIS - Project Cleanup Script
echo ============================================================
echo.
echo CUIDADO: Este script eliminara archivos y carpetas obsoletos.
echo Se han preservado: lexviridis.db, assets/, data/, etc.
echo.
set /p confirm="¿Desea continuar con la purga? (S/N): "
if /i not "%confirm%"=="S" exit /b

echo.
echo [1/3] Eliminando residuos de Flet y archivos de depuracion...
del /q check_flet.py 2>nul
del /q inspect_flet.py 2>nul
del /q test_flet_stability.py 2>nul
del /q main_flet.py 2>nul
del /q main_new.py 2>nul
del /q run_app.py 2>nul
del /q build_final.log 2>nul
del /q build_venv3.log 2>nul
del /q build_venv4.log 2>nul
del /q output_log.txt 2>nul
del /q inspect_tabs.txt 2>nul
del /q README_USB.md 2>nul
del /q _ul 2>nul

echo.
echo [2/3] Eliminando antiguos scripts de build y specs...
del /q build_dist.bat 2>nul
del /q build_exe.bat 2>nul
del /q build_installer.bat 2>nul
del /q INST_LEXVIRIDIS.spec 2>nul
del /q LEX_VIRIDIS.spec 2>nul

echo.
echo [3/3] Eliminando carpetas temporales y entornos obsoletos...
if exist "web" rmdir /s /q web
if exist "dist" rmdir /s /q dist
if exist "build" rmdir /s /q build
if exist "env" rmdir /s /q env
if exist "__pycache__" rmdir /s /q __pycache__
if exist ".ruff_cache" rmdir /s /q .ruff_cache

:: Limpiar pycache recursivo
for /d /r . %%d in (__pycache__) do @if exist "%%d" rmdir /s /q "%%d"

echo.
echo ============================================================
echo           PURGA COMPLETADA EXITOSAMENTE
echo ============================================================
echo.
pause
