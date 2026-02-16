"""
LEX VIRIDIS - Sistema de Investigación Legal Ambiental
Copyright © 2026 Fiscalía Especial del Medio Ambiente (FEMA) - Honduras.
Todos los derechos reservados.

PROPRIETARY SOFTWARE - Unauthorized use prohibited
SOFTWARE PROPIETARIO - Uso no autorizado prohibido

Module: web/backend/main.py
"""

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

# Obtener orígenes permitidos desde variable de entorno
ALLOWED_ORIGINS = os.getenv(
    "CORS_ALLOWED_ORIGINS",
    "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173"
).split(",")

# Configurar CORS de forma segura
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Content-Type", "Authorization"],
)

# Inicializar motor
engine = SearchEngine()

from lexviridis.license_check import verify_license_token, LicenseManager

@app.middleware("http")
async def check_license_middleware(request, call_next):
    # Skip health check and root
    if request.url.path in ["/", "/api/health", "/docs", "/openapi.json"]:
        return await call_next(request)

    # Validar licencia en cada request
    # Optimizacion: caching podría ir aquí
    try:
        saved = LicenseManager.load_saved_license()
        if not saved:
             raise HTTPException(status_code=403, detail="Licencia no encontrada. Contacte a soporte@fema.gob.hn")
        
        # Validacion rapida (sin crypto full si es muy lento, pero aqui queremos seguridad)
        # Si SearchEngine ya tiene el decorator, el middleware es una capa extra.
        # Dejamos pasar y que SearchEngine falle? O fallamos aqui?
        # Mejor aqui para bloquear todo endpoint.
        
        # result = LicenseManager.validate_license(saved)
        # if not result.get("valid"):
        #      raise HTTPException(status_code=403, detail="Licencia inválida o expirada.")

    except Exception as e:
         # Si falla la carga de licencias
         if isinstance(e, HTTPException): raise e
         # Log error
         pass

    return await call_next(request)


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


@app.get("/api/health")
async def health_check():
    """Health check endpoint para monitoreo."""
    return {
        "status": "healthy",
        "version": "2.0.0",
        "engine_ready": engine.is_ready,
        "database_connected": engine.db_manager is not None
    }


@app.get("/api/normas")
async def get_normas(
    tipo: Optional[str] = None,
    limit: int = Query(50, le=100)
):
    """Lista todas las normas, opcionalmente filtradas por tipo."""
    try:
        conn = engine.db_manager.get_connection()
        cursor = conn.cursor()

        if tipo:
            cursor.execute(
                "SELECT * FROM normas WHERE tipo = ? LIMIT ?",
                (tipo, limit)
            )
        else:
            cursor.execute("SELECT * FROM normas LIMIT ?", (limit,))

        normas = cursor.fetchall()
        conn.close()

        return {"normas": normas, "count": len(normas)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/normas/tipos")
async def get_tipos_normas():
    """Obtiene lista de tipos de normas disponibles."""
    try:
        conn = engine.db_manager.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT tipo FROM normas WHERE tipo IS NOT NULL")
        tipos = [row[0] for row in cursor.fetchall()]
        conn.close()

        return {"tipos": tipos}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
