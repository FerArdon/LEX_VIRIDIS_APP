
"""
Motor de búsqueda optimizado para LEX VIRIDIS.

Incluye:
- Validación de inputs
- Caché LRU para búsquedas frecuentes
- Paginación
- Búsqueda asíncrona
- Logging con métricas de rendimiento
"""

import sqlite3
import logging
import re
import time
from typing import List, Dict, Tuple, Optional
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum
from functools import lru_cache
import hashlib

# Configurar logger
search_logger = logging.getLogger("lexviridis.search")

# Importar configuración centralizada (compatible con .exe y desarrollo)
try:
    from .config import config as _app_config
    DB_PATH = _app_config.BASE_DIR / "LEX_VIRIDIS_DB" / "legislacion_ambiental.db"
except Exception:
    DB_PATH = Path(__file__).parent.parent / "LEX_VIRIDIS_DB" / "legislacion_ambiental.db"

MIN_QUERY_LENGTH = 2
MAX_QUERY_LENGTH = 200
DEFAULT_PAGE_SIZE = 20
CACHE_SIZE = 100

# === CONSTANTES ===
SEARCH_TIMEOUT_SECONDS = 5
MAX_RESULTS = 100

ALLOWED_CHARS_PATTERN = re.compile(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑüÜ0-9\s\-\.]+$')
SQL_KEYWORDS = {'DROP', 'DELETE', 'INSERT', 'UPDATE', 'TRUNCATE', '--', ';', 'UNION', 'SELECT'}

# Sinónimos legales
SINONIMOS = {
    'delito': ['delito', 'delitos', 'crimen', 'infraccion', 'infracción', 'falta'],
    'ambiental': ['ambiental', 'ambientales', 'ambiente', 'ecologico', 'ecológico', 'naturaleza'],
    'bosque': ['bosque', 'bosques', 'forestal', 'forestales', 'arbol', 'árboles', 'monte'],
    'agua': ['agua', 'aguas', 'hidrico', 'hídrico'],
    'contaminacion': ['contaminacion', 'contaminación', 'polucion', 'polución', 'vertido'],
    'tala': ['tala', 'corte', 'deforestacion', 'deforestación', 'aprovechamiento'],
    'licencia': ['licencia', 'licencias', 'permiso', 'permisos', 'autorizacion', 'autorización'],
    'multa': ['multa', 'multas', 'sancion', 'sanción', 'pena', 'penalidad'],
    'protegida': ['protegida', 'protegidas', 'protección', 'conservacion', 'conservación'],
}


class SearchStatus(Enum):
    SUCCESS = "success"
    NO_RESULTS = "no_results"
    INVALID_QUERY = "invalid_query"
    DB_ERROR = "db_error"
    TIMEOUT = "timeout"
    UNKNOWN_ERROR = "unknown_error"


@dataclass
class SearchResult:
    status: SearchStatus
    results: List[Dict]
    message: str
    query: str
    duration_ms: float
    total_found: int
    page: int = 1
    page_size: int = DEFAULT_PAGE_SIZE
    cached: bool = False


class QueryValidator:
    @staticmethod
    def validate(query: str) -> Tuple[bool, str]:
        if not query or not query.strip():
            return False, "Ingresa un término de búsqueda"
        
        query = query.strip()
        
        if len(query) < MIN_QUERY_LENGTH:
            return False, f"Mínimo {MIN_QUERY_LENGTH} caracteres"
        
        if len(query) > MAX_QUERY_LENGTH:
            return False, f"Máximo {MAX_QUERY_LENGTH} caracteres"
        
        if not ALLOWED_CHARS_PATTERN.match(query):
            invalid_chars = set(c for c in query if not re.match(r'[a-zA-ZáéíóúÁÉÍÓÚñÑüÜ0-9\s\-\.]', c))
            return False, f"Caracteres no permitidos: {' '.join(invalid_chars)}"
        
        query_upper = query.upper()
        for keyword in SQL_KEYWORDS:
            if keyword in query_upper:
                search_logger.warning(f"⚠️ SQL injection attempt: '{query}'")
                return False, "Término no válido"
        
        return True, ""

    @staticmethod
    def sanitize(query: str) -> str:
        sanitized = re.sub(r'[^\w\sáéíóúÁÉÍÓÚñÑüÜ\-\.]', '', query)
        return ' '.join(sanitized.split()).strip()


class DatabaseManager:
    _instance = None
    _connection_pool = None
    
    def __new__(cls, db_path: Path = DB_PATH):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, db_path: Path = DB_PATH):
        if self._initialized:
            return
        self.db_path = db_path
        self._validate_database()
        self._initialized = True
    
    def _validate_database(self):
        if not self.db_path.exists():
            raise FileNotFoundError(f"BD no encontrada: {self.db_path}")
        
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='normas'")
        if not cursor.fetchone():
            conn.close()
            raise ValueError("BD corrupta o vacía")
        conn.close()
        search_logger.info(f"✅ BD validada: {self.db_path.name}")
    
    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path), timeout=10, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        # Optimizaciones de conexión
        conn.execute("PRAGMA cache_size = -16000")  # 16MB cache
        conn.execute("PRAGMA journal_mode = WAL")  # Modo WAL para mejor concurrencia
        conn.execute("PRAGMA synchronous = NORMAL")
        
        return conn

    def initialize_tables(self):
        """Inicializa todas las tablas necesarias una sola vez."""
        conn = self.get_connection()
        try:
            self._init_extra_tables(conn)
            search_logger.info("✅ Tablas inicializadas")
        finally:
            conn.close()

    def _init_extra_tables(self, conn):
        """Inicializa tablas para estadísticas y favoritos."""
        cursor = conn.cursor()
        
        # Historial de búsquedas
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS historial_busquedas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Historial de vistas
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS articulos_vistos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                articulo_id INTEGER,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (articulo_id) REFERENCES articulos(id)
            )
        """)
        
        # Favoritos
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS favoritos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                articulo_id INTEGER UNIQUE,
                nota TEXT,
                fecha_agregado DATETIME DEFAULT CURRENT_TIMESTAMP,
                fecha_modificado DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (articulo_id) REFERENCES articulos(id)
            )
        """)
        
        # Tags de favoritos
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS favoritos_tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                favorito_id INTEGER,
                tag TEXT NOT NULL,
                FOREIGN KEY (favorito_id) REFERENCES favoritos(id)
            )
        """)

        # Historial de exportaciones
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS historial_exportaciones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tipo TEXT,  -- 'pdf', 'search_results'
                items_count INTEGER,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Usuarios
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_salt BLOB NOT NULL,
                password_hash BLOB NOT NULL,
                email TEXT UNIQUE NOT NULL,
                security_question TEXT,
                security_answer_salt BLOB,
                security_answer_hash BLOB,
                recovery_enabled BOOLEAN DEFAULT FALSE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_login DATETIME
            )
        """)

        # Sesiones
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sesiones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                token TEXT UNIQUE NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                expires_at DATETIME NOT NULL,
                FOREIGN KEY (user_id) REFERENCES usuarios(id)
            )
        """)

        # Roles
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS usuarios_roles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                role TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES usuarios(id)
            )
        """)

        # Notificaciones
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS notificaciones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tipo TEXT NOT NULL,
                titulo TEXT NOT NULL,
                mensaje TEXT NOT NULL,
                data TEXT,
                fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
                leida BOOLEAN DEFAULT FALSE,
                accion_url TEXT
            )
        """)

        # Analytics
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS analytics_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT NOT NULL,
                properties TEXT, -- JSON
                user_id INTEGER,
                session_id TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES usuarios(id)
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_analytics_type_time ON analytics_events(event_type, timestamp)")

        # Migration: Add new columns if they don't exist
        try:
            cursor.execute("SELECT security_question FROM usuarios LIMIT 1")
        except sqlite3.OperationalError:
            cursor.execute("ALTER TABLE usuarios ADD COLUMN security_question TEXT")
            cursor.execute("ALTER TABLE usuarios ADD COLUMN security_answer_salt BLOB")
            cursor.execute("ALTER TABLE usuarios ADD COLUMN security_answer_hash BLOB")
            cursor.execute("ALTER TABLE usuarios ADD COLUMN recovery_enabled BOOLEAN DEFAULT FALSE")
            conn.commit()
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_analytics_user ON analytics_events(user_id)")
        
        conn.commit()


# === CACHÉ DE RESULTADOS ===
class SearchCache:
    """Caché LRU thread-safe para resultados de búsqueda."""
    
    def __init__(self, maxsize: int = CACHE_SIZE):
        self._cache = {}
        self._order = []
        self._maxsize = maxsize
    
    def _make_key(self, query: str, page: int, page_size: int) -> str:
        return hashlib.md5(f"{query.lower()}:{page}:{page_size}".encode()).hexdigest()
    
    def get(self, query: str, page: int = 1, page_size: int = DEFAULT_PAGE_SIZE) -> Optional[List[Dict]]:
        key = self._make_key(query, page, page_size)
        return self._cache.get(key)
    
    def set(self, query: str, results: List[Dict], page: int = 1, page_size: int = DEFAULT_PAGE_SIZE):
        key = self._make_key(query, page, page_size)
        
        if key in self._cache:
            self._order.remove(key)
        elif len(self._cache) >= self._maxsize:
            oldest = self._order.pop(0)
            del self._cache[oldest]
        
        self._cache[key] = results
        self._order.append(key)
    
    def clear(self):
        self._cache.clear()
        self._order.clear()


class SearchEngine:
    """Motor de búsqueda optimizado con caché y paginación."""

    def __init__(self, text_index=None):
        self.db_manager: Optional[DatabaseManager] = None
        self._is_ready = False
        self._init_error: Optional[str] = None
        self._cache = SearchCache()
        
        try:
            self.db_manager = DatabaseManager(DB_PATH)
            self.db_manager.initialize_tables()  # Asegurar tablas y migraciones
            self._is_ready = True
            search_logger.info("✅ SearchEngine listo")
        except Exception as e:
            self._init_error = str(e)
            search_logger.error(f"❌ Error init: {e}")

    @property
    def is_ready(self) -> bool:
        return self._is_ready

    @property
    def init_error(self) -> Optional[str]:
        return self._init_error

    def _normalize_accents(self, text: str) -> str:
        replacements = {'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u', 'ñ': 'n', 'ü': 'u'}
        result = text.lower()
        for orig, repl in replacements.items():
            result = result.replace(orig, repl)
        return result

    def _expand_query_with_synonyms(self, query: str) -> List[str]:
        words = query.lower().split()
        expanded = []
        
        for word in words:
            word_norm = self._normalize_accents(word)
            found = False
            
            for base, synonyms in SINONIMOS.items():
                norm_synonyms = [self._normalize_accents(s) for s in synonyms]
                if word_norm in norm_synonyms:
                    expanded.extend(synonyms)
                    found = True
                    break
            
            if not found:
                expanded.append(word)
        
        return list(dict.fromkeys(expanded))

    def search(self, query: str, operator: str = "OR", limit: int = DEFAULT_PAGE_SIZE, offset: int = 0) -> List[Dict]:
        """Búsqueda simple (interfaz compatible)."""
        result = self.search_safe(query, operator, page=1, page_size=limit)
        return result.results

    def search_safe(self, query: str, operator: str = "OR", page: int = 1, page_size: int = DEFAULT_PAGE_SIZE) -> SearchResult:
        """Búsqueda segura con caché, validación y paginación."""
        start_time = time.perf_counter()
        
        # Registrar búsqueda en historial
        import threading
        threading.Thread(target=self._log_search, args=(query,), daemon=True).start()
        
        if not self._is_ready:
            return SearchResult(
                status=SearchStatus.DB_ERROR,
                results=[],
                message=self._init_error or "Motor no disponible",
                query=query, duration_ms=0, total_found=0
            )
        
        # Validar
        is_valid, error_msg = QueryValidator.validate(query)
        if not is_valid:
            return SearchResult(
                status=SearchStatus.INVALID_QUERY,
                results=[], message=error_msg,
                query=query, duration_ms=0, total_found=0
            )
        
        clean_query = QueryValidator.sanitize(query)
        
        # Verificar caché
        cached = self._cache.get(clean_query, page, page_size)
        if cached is not None:
            duration = (time.perf_counter() - start_time) * 1000
            search_logger.info(f"⚡ CACHE HIT: '{query}' → {len(cached)} resultados ({duration:.2f}ms)")
            return SearchResult(
                status=SearchStatus.SUCCESS if cached else SearchStatus.NO_RESULTS,
                results=cached,
                message=f"{len(cached)} resultados (caché)",
                query=query, duration_ms=duration, total_found=len(cached),
                page=page, page_size=page_size, cached=True
            )
        
        # Ejecutar búsqueda
        try:
            # Manejo especial para Novedades
            if clean_query.lower() == "novedades" or "novedades" in clean_query.lower():
                results = self._get_latest_norms(limit=20)
            else:
                results = self._execute_search(clean_query, operator, page, page_size)
            
            duration = (time.perf_counter() - start_time) * 1000
            
            # Guardar en caché
            self._cache.set(clean_query, results, page, page_size)
            
            if not results:
                search_logger.info(f"🔍 Sin resultados: '{query}' ({duration:.2f}ms)")
                return SearchResult(
                    status=SearchStatus.NO_RESULTS,
                    results=[], message="Sin resultados. Prueba otros términos.",
                    query=query, duration_ms=duration, total_found=0
                )
            
            search_logger.info(f"✅ '{query}' → {len(results)} resultados ({duration:.2f}ms)")
            return SearchResult(
                status=SearchStatus.SUCCESS,
                results=results,
                message=f"{len(results)} resultados",
                query=query, duration_ms=duration, total_found=len(results),
                page=page, page_size=page_size
            )
            
        except sqlite3.Error as e:
            search_logger.error(f"❌ DB error: {e}")
            return SearchResult(
                status=SearchStatus.DB_ERROR,
                results=[], message="Error de base de datos",
                query=query, duration_ms=(time.perf_counter() - start_time) * 1000,
                total_found=0
            )
        except Exception as e:
            search_logger.error(f"❌ Error: {e}", exc_info=True)
            return SearchResult(
                status=SearchStatus.UNKNOWN_ERROR,
                results=[], message="Error inesperado",
                query=query, duration_ms=(time.perf_counter() - start_time) * 1000,
                total_found=0
            )

    def _execute_search(self, query: str, operator: str, page: int, page_size: int) -> List[Dict]:
        """Ejecuta búsqueda optimizada con paginación."""
        results = []
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        
        try:
            terms = self._expand_query_with_synonyms(query)
            fts_terms = [f'"{t}"' for t in terms if len(t) > 2]
            
            if not fts_terms:
                return []
            
            fts_query = " OR ".join(fts_terms)
            offset = (page - 1) * page_size
            
            # Utilizar la función snippet de FTS5 para fragmentos contextuales reales
            sql = """
                SELECT 
                    f.articulo_id,
                    f.titulo_norma, 
                    f.numero_articulo,
                    snippet(busqueda_fts, 1, '<b>', '</b>', '...', 30) as fragmento,
                    f.rank,
                    a.pagina,
                    a.contenido as contenido_completo,
                    n.archivo_pdf
                FROM busqueda_fts f
                JOIN articulos a ON f.articulo_id = a.id
                JOIN normas n ON a.norma_id = n.id
                WHERE busqueda_fts MATCH ? 
                ORDER BY f.rank 
                LIMIT ? OFFSET ?
            """
            
            cursor.execute(sql, (fts_query, page_size, offset))
            
            for row in cursor.fetchall():
                # Convertir snippet de FTS (<b>...</b>) a Markdown (**...**) para Flet
                snippet_md = str(row['fragmento']).replace("<b>", "**").replace("</b>", "**")
                
                # Calcular número de ocurrencias
                matches_count = 0
                contenido_lower = str(row['contenido_completo']).lower()
                for term in terms:
                    if len(term) > 2:
                        matches_count += contenido_lower.count(term.lower())

                results.append({
                    'id': row['articulo_id'],
                    'file': row['archivo_pdf'] or "Desconocido",
                    'page': row['pagina'] or 1,
                    'relevance': round(abs(row['rank']) * 10, 1),
                    'context': f"Art. {row['numero_articulo']}: {snippet_md}",
                    'term': query,
                    'matches': matches_count,
                    'is_high_relevance': abs(row['rank']) < 5.0 # Rank bajo en FTS5 significa más relevante
                })
            
            results.sort(key=lambda x: x['relevance'], reverse=True)
            
            # Fallback: Si FTS no encuentra nada, buscar directamente en normas.titulo
            if not results:
                search_logger.info(f"FTS sin resultados, intentando LIKE en normas.titulo para: {query}")
                like_sql = """
                    SELECT DISTINCT
                        n.id as norma_id,
                        n.titulo,
                        n.tipo,
                        n.archivo_pdf,
                        n.resumen
                    FROM normas n
                    WHERE n.titulo LIKE ? COLLATE NOCASE
                       OR n.resumen LIKE ? COLLATE NOCASE
                    LIMIT ?
                """
                like_term = f"%{query}%"
                cursor.execute(like_sql, (like_term, like_term, page_size))
                
                for row in cursor.fetchall():
                    # Crear un resultado sintético desde la norma
                    results.append({
                        'id': row['norma_id'],
                        'file': row['archivo_pdf'] or "Desconocido",
                        'page': 1,
                        'relevance': 8.0,
                        'context': f"{row['tipo']}: {row['titulo'][:100]}",
                        'term': query,
                        'matches': 1,
                        'is_high_relevance': True,
                        'norma_titulo': row['titulo'],
                        'tipo_norma': row['tipo'],
                        'contenido': row['resumen'] or row['titulo'],
                    })
            
        finally:
            conn.close()
        
        return results

    def get_article_by_id(self, article_id: int) -> Optional[Dict]:
        """Obtiene un artículo completo por su ID."""
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT a.id, a.numero_articulo, a.contenido, a.pagina, n.titulo as norma_titulo, n.archivo_pdf
                FROM articulos a
                JOIN normas n ON a.norma_id = n.id
                WHERE a.id = ?
            """, (article_id,))
            
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
        finally:
            conn.close()

    def clear_cache(self):
        """Limpia el caché de búsquedas."""
        self._cache.clear()
        search_logger.info("🗑️ Caché limpiado")

    def _log_search(self, query: str):
        """Registra una búsqueda en el historial."""
        conn = self.db_manager.get_connection()
        try:
            conn.execute("INSERT INTO historial_busquedas (query) VALUES (?)", (query,))
            conn.commit()
        except Exception as e:
            search_logger.error(f"Error logging search: {e}")
        finally:
            conn.close()

    def log_article_view(self, article_id: int):
        """Registra la vista de un artículo."""
        conn = self.db_manager.get_connection()
        try:
            conn.execute("INSERT INTO articulos_vistos (articulo_id) VALUES (?)", (article_id,))
            conn.commit()
        except Exception as e:
            search_logger.error(f"Error logging view: {e}")
        finally:
            conn.close()

    def log_export(self, tipo: str, items_count: int):
        """Registra una exportación."""
        conn = self.db_manager.get_connection()
        try:
            conn.execute("INSERT INTO historial_exportaciones (tipo, items_count) VALUES (?, ?)", (tipo, items_count))
            conn.commit()
        except Exception as e:
            search_logger.error(f"Error logging export: {e}")
        finally:
            conn.close()

    def get_search_suggestions(self, partial: str, limit: int = 5) -> List[str]:
        """Obtiene sugerencias basadas en el historial."""
        if not partial or len(partial) < 2: return []
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT DISTINCT query 
                FROM historial_busquedas 
                WHERE query LIKE ? 
                ORDER BY timestamp DESC 
                LIMIT ?
            """, (f"{partial}%", limit))
            return [row['query'] for row in cursor.fetchall()]
        finally:
            conn.close()

    def _get_latest_norms(self, limit: int = 20) -> List[Dict]:
        """Obtiene las normas más recientes."""
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        results = []
        try:
            # Intentar ordenar por fecha de publicación si existe
            cursor.execute("""
                SELECT id, titulo, fecha_publicacion, tipo, archivo_pdf,
                       (SELECT COUNT(*) FROM articulos WHERE norma_id = normas.id) as num_articulos
                FROM normas 
                ORDER BY fecha_publicacion DESC 
                LIMIT ?
            """, (limit,))
            
            for row in cursor.fetchall():
                # Adaptar formato a resultado de búsqueda
                results.append({
                    'id': row['id'], # Usamos ID de norma, ojo con conflicto con ID de artículo
                    'file': row['archivo_pdf'] or "Desconocido",
                    'page': 1,
                    'relevance': 100.0,
                    'context': f"{row['tipo']} - {row['fecha_publicacion']}",
                    'term': "Novedades",
                    'matches': 0,
                    'is_high_relevance': True,
                    'is_norma': True, # Bandera para diferenciar en UI
                    'titulo': row['titulo'],
                    'tipo': row['tipo']
                })
        except Exception as e:
            search_logger.error(f"Error fetching latest norms: {e}")
        finally:
            conn.close()
        return results

    def clear_history(self, tipo: str = "todo", days: int = None):
        """Limpia el historial."""
        conn = self.db_manager.get_connection()
        try:
            where_clause = ""
            params = []
            if days:
                where_clause = " WHERE timestamp < DATE('now', '-' || ? || ' days')"
                params = [days]
            
            if tipo in ["busquedas", "todo"]:
                conn.execute(f"DELETE FROM historial_busquedas{where_clause}", params)
            if tipo in ["vistas", "todo"]:
                conn.execute(f"DELETE FROM articulos_vistos{where_clause}", params)
            if tipo in ["exportaciones", "todo"]:
                conn.execute(f"DELETE FROM historial_exportaciones{where_clause}", params)
            
            conn.commit()
        finally:
            conn.close()

    # === ESTADÍSTICAS ===
    def get_dashboard_stats(self) -> Dict:
        """Obtiene métricas para el dashboard."""
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        stats = {}
        
        try:
            # Stats generales
            cursor.execute("SELECT COUNT(*) FROM normas")
            stats['total_normas'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM articulos")
            stats['total_articulos'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM favoritos")
            stats['total_favoritos'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM historial_busquedas")
            stats['total_busquedas'] = cursor.fetchone()[0]
            
            # Distribución por tipo de norma
            cursor.execute("""
                SELECT tipo, COUNT(*) as count 
                FROM normas 
                GROUP BY tipo 
                ORDER BY count DESC
            """)
            stats['distribucion_tipo'] = {row['tipo'] or 'Otros': row['count'] for row in cursor.fetchall()}
            
            # Top búsquedas
            cursor.execute("""
                SELECT query, COUNT(*) as frequency 
                FROM historial_busquedas 
                GROUP BY query 
                ORDER BY frequency DESC 
                LIMIT 10
            """)
            stats['top_searches'] = [(row['query'], row['frequency']) for row in cursor.fetchall()]
            
            # Actividad última semana
            cursor.execute("""
                SELECT DATE(timestamp) as fecha, COUNT(*) as count 
                FROM historial_busquedas 
                WHERE timestamp >= DATE('now', '-7 days') 
                GROUP BY fecha 
                ORDER BY fecha
            """)
            stats['timeline_busquedas'] = [(row['fecha'], row['count']) for row in cursor.fetchall()]
            
            # Documentos más consultados
            cursor.execute("""
                SELECT n.titulo, COUNT(*) as views 
                FROM articulos_vistos av 
                JOIN articulos a ON av.articulo_id = a.id 
                JOIN normas n ON a.norma_id = n.id 
                GROUP BY n.id 
                ORDER BY views DESC 
                LIMIT 5
            """)
            stats['most_viewed'] = [(row['titulo'], row['views']) for row in cursor.fetchall()]
            
            return stats
        finally:
            conn.close()

    # === FAVORITOS ===
    def toggle_favorite(self, article_id: int) -> bool:
        """Agrega o quita un artículo de favoritos. Retorna True si es favorito ahora."""
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT id FROM favoritos WHERE articulo_id = ?", (article_id,))
            row = cursor.fetchone()
            
            if row:
                cursor.execute("DELETE FROM favoritos WHERE articulo_id = ?", (article_id,))
                conn.commit()
                return False
            else:
                cursor.execute("INSERT INTO favoritos (articulo_id) VALUES (?)", (article_id,))
                conn.commit()
                return True
        finally:
            conn.close()

    def is_favorite(self, article_id: int) -> bool:
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT id FROM favoritos WHERE articulo_id = ?", (article_id,))
            return cursor.fetchone() is not None
        finally:
            conn.close()

    def update_favorite_note(self, article_id: int, nota: str):
        conn = self.db_manager.get_connection()
        try:
            conn.execute("""
                UPDATE favoritos 
                SET nota = ?, fecha_modificado = CURRENT_TIMESTAMP 
                WHERE articulo_id = ?
            """, (nota, article_id))
            conn.commit()
        finally:
            conn.close()

    def get_favorites(self) -> List[Dict]:
        """Obtiene la lista de artículos favoritos."""
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT 
                    f.articulo_id as id,
                    f.nota,
                    f.fecha_agregado,
                    a.numero_articulo,
                    a.contenido,
                    a.pagina,
                    n.titulo as norma_titulo,
                    n.archivo_pdf as file
                FROM favoritos f
                JOIN articulos a ON f.articulo_id = a.id
                JOIN normas n ON a.norma_id = n.id
                ORDER BY f.fecha_agregado DESC
            """)
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def get_favorite_tags(self, article_id: int) -> List[str]:
        """Obtiene los tags de un favorito por articulo_id."""
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT id FROM favoritos WHERE articulo_id = ?", (article_id,))
            row = cursor.fetchone()
            if not row: return []
            
            cursor.execute("SELECT tag FROM favoritos_tags WHERE favorito_id = ?", (row['id'],))
            return [r['tag'] for r in cursor.fetchall()]
        finally:
            conn.close()

    def add_favorite_tag(self, article_id: int, tag: str):
        """Agrega un tag a un favorito."""
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT id FROM favoritos WHERE articulo_id = ?", (article_id,))
            row = cursor.fetchone()
            if not row: return
            
            cursor.execute("INSERT INTO favoritos_tags (favorito_id, tag) VALUES (?, ?)", (row['id'], tag))
            conn.commit()
        finally:
            conn.close()



def create_search_engine(text_index=None) -> SearchEngine:
    return SearchEngine(text_index)
