# LEX VIRIDIS - Estado y pendientes

## Hecho (2026-10-02)
- Compatibilidad con Flet 0.82.x: `ft.Alignment.CENTER` (antes `ft.alignment.center`) y botones con `content=` (antes `text=`).
- `requirements.txt` fija `flet>=0.82.2,<0.83`.
- Arranque verificado: `python lexviridis/run_app.py` abre splash y login sin errores. 125 pruebas pasan.
- Limpieza de scripts de diagnostico sueltos.

## Pendientes
- Decidir la rama por defecto en GitHub: `origin/main` (foto vieja v3.2.0, mayo) no comparte historia con `master` (rama activa).
- Revisar y commitear `installer.iss` (reescrito, sin validar) y quitar `sqlite3` de `lexviridis/web/backend/requirements.txt`.
- Recompilar `dist/LEX_VIRIDIS.exe` (el actual es de febrero) y regenerar el instalador.
- Estandarizar versiones: `pyproject.toml` y logs dicen 3.0.0, `installer.iss` dice 3.1.1_2026, el ultimo release en `main` dice 3.2.0.
