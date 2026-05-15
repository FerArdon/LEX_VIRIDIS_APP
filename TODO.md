# Fix Search Engine - Soporte Completo Frases y Palabras Individuales

## Status: En Progreso

### Paso 1: [x] Crear/Actualizar TODO.md con plan detallado
### Paso 2: [] Editar lexviridis/search_engine.py
   - Relajar QueryValidator: agregar chars / * # ( ) , ; : ? ! +, MIN_QUERY_LENGTH=1
   - Mejorar sanitize: mantener más puntuación para frases legales
   - Potenciar _tokenize_query: manejar "art. 325", números, mixed quotes
   - FTS en _execute_search: usar NEAR/5 para multi-term, AND para frase única
   - Fallback LIKE: SIEMPRE OR palabras individuales después de sanitize
   - Logs debug: FTS query, rows FTS vs LIKE, trigger fallback
### Paso 3: [] Probar fixes
   - Test frase: "que dice el articulo 325 del codigo penal"
   - Test palabras: "daños al ecosistema", "incendio forestal"
   - Comando: python -c "from lexviridis.search_engine import *; engine = create_search_engine(); print(engine.search_safe('articulo 325'))"
   - Limpiar cache engine._cache.clear()
### Paso 4: [] Verificar FTS DB
   - sqlite3 LEX_VIRIDIS_DB/legislacion_ambiental.db "SELECT count(*) FROM busqueda_fts;"
### Paso 5: [] Actualizar TODO.md como completado
### Paso 6: [] Probar en app completa

**Tests pendientes:**
- Limpiar cache
- Verificar integridad FTS
- Probar términos con chars especiales: "art. 25", "ley 123/2007"

**Archivos afectados:** lexviridis/search_engine.py
