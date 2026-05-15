# TODO FIXES LEX VIRIDIS - Plan de 14 correcciones
Estado: Pendiente ⏳ | Completado ✅ | Error ❌

## 🎯 ORDEN DE EJECUCIÓN (Priorizado por dependencias)

### 🔴 FASE 1: Core Engine (30min)
- [ ] 1. **Unificar search_engine.py** ← Merge fixed.py + eliminar duplicado
- [ ] 2. **Fix threading Flet** main_flet.py/ui_v2.py (run_task)
- [ ] 3. **Validate paths/DB** config.py + search_engine.py

### 🟡 FASE 2: UI/UX Fixes (45min)
- [ ] 4. **PDF viewer portable** pdf_viewer_fixed.py (webbrowser)
- [ ] 5. **Gemini fallback** ia_gemini.py + UI prompt
- [ ] 6. **Dashboard stats** verificar get_dashboard_stats()

### 🟢 FASE 3: Robustez/Mantenimiento (30min)
- [ ] 7. **Logging rotación** __init__.py RotatingFileHandler
- [ ] 8. **Assets cleanup** eliminar duplicados
- [ ] 9. **Auto-venv** run_app.py + activate.bat
- [ ] 10. **DB migrations** versioning table
- [ ] 11. **Licencias JSON** license_system.py
- [ ] 12. **Web stub** backend/main.py opcional
- [ ] 13. **gitignore assets**
- [ ] 14. **TODO.md update** marcar original + tests

## 🧪 TESTS POST-FIX
```
1. python run_app.py → Startup OK (no crash threading)
2. Search "licencia" → Results + dashboard stats
3. Open PDF → No tkinter error
4. AI sin key → Graceful prompt
5. pyinstaller build → .exe paths OK
6. Logs → logs/lexviridis.log rotado >10MB
```

## 🚀 COMANDOS ÚTILES
```bash
# Test completo
python run_app.py

# Build exe  
pyinstaller --onedir --add-data "lexviridis/assets;lexviridis/assets" main.py

# Cleanup
rmdir /s assets\assets
git clean -fd
```

**Progreso actual: 0/14**  
*Actualizar checkbox al completar cada paso*
