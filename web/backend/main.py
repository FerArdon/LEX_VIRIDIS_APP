
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional, Dict
import sys
import os
from pathlib import Path

# Agregar el directorio raíz al path para importar lexviridis
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

try:
    from lexviridis.search_engine import SearchEngine, SearchStatus
except ImportError:
    # Si falla la importación, definiremos un mock o buscaremos otra forma
    # Pero debería funcionar si estamos en la estructura correcta
    pass

app = FastAPI(title="LEX VIRIDIS API", version="2.0.0")

# Configurar CORS para el frontend (Vite por defecto usa 5173)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # En producción limitar a dominios específicos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inicializar motor
engine = SearchEngine()

@app.get("/")
async def root():
    return {"message": "LEX VIRIDIS API v2.0 - Online", "status": "ready" if engine.is_ready else "error"}

@app.get("/api/search")
async def search(
    q: str = Query(..., min_length=2),
    page: int = 1,
    page_size: int = 20
):
    """Búsqueda de artículos legales."""
    if not engine.is_ready:
        raise HTTPException(status_code=500, detail="Motor de búsqueda no disponible")
    
    result = engine.search_safe(q, page=page, page_size=page_size)
    
    if result.status == SearchStatus.SUCCESS:
        return {
            "query": q,
            "page": page,
            "total_found": result.total_found,
            "duration_ms": result.duration_ms,
            "results": result.results
        }
    elif result.status == SearchStatus.NO_RESULTS:
        return {
            "query": q,
            "total_found": 0,
            "results": [],
            "message": "No se encontraron resultados"
        }
    else:
        raise HTTPException(status_code=400, detail=result.message)

@app.get("/api/documentos/{article_id}")
async def get_article(article_id: int):
    """Obtiene el detalle de un artículo específico."""
    article = engine.get_article_by_id(article_id)
    if not article:
        raise HTTPException(status_code=404, detail="Artículo no encontrado")
    
    # Registrar vista
    engine.log_article_view(article_id)
    
    return article

@app.get("/api/stats")
async def get_stats():
    """Obtiene estadísticas generales del sistema."""
    return engine.get_dashboard_stats()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
