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

class ExecutionTimer:
    """Mide tiempo de ejecución para optimización."""
    def __init__(self, name: str):
        self.name = name
        self.start_time = None

    def __enter__(self):
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        elapsed = time.perf_counter() - self.start_time
        search_logger.info(f"[TIMER] {self.name}: {elapsed:.4f}s")

class Formatter:
    """Centraliza las reglas de formato."""
    @staticmethod
    def number(value: float, decimals: int = 0) -> str:
        if value is None: return "0"
        return "{:,.{}f}".format(value, decimals)

# Importar configuración centralizada (compatible con .exe y desarrollo)
try:
    from .config import config as _app_config
    DB_PATH = _app_config.DB_DIR / "legislacion_ambiental.db"
except Exception:
    DB_PATH = Path(__file__).parent.parent / "LEX_VIRIDIS_DB" / "legislacion_ambiental.db"

MIN_QUERY_LENGTH = 2
MAX_QUERY_LENGTH = 200
DEFAULT_PAGE_SIZE = 20
CACHE_SIZE = 100

# === CONSTANTES ===
SEARCH_TIMEOUT_SECONDS = 5
MAX_RESULTS = 100

ALLOWED_CHARS_PATTERN = re.compile(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑüÜ0-9\s\-\."\',\:\;\?\¡\!\(\)]+$')
SQL_KEYWORDS = {'DROP', 'DELETE', 'INSERT', 'UPDATE', 'TRUNCATE', '--', ';', 'UNION', 'SELECT'}

# Palabras vacías en español que no aportan a la búsqueda
STOP_WORDS = {
    'que', 'de', 'del', 'el', 'la', 'los', 'las', 'un', 'una', 'unos', 'unas',
    'en', 'a', 'por', 'con', 'para', 'se', 'su', 'es', 'son', 'al', 'lo',
    'como', 'mas', 'o', 'y', 'pero', 'sobre', 'tambien', 'tanto', 'asi',
    'ante', 'bajo', 'este', 'esta', 'estos', 'estas', 'ese', 'esa', 'esos',
    'esas', 'mi', 'me', 'nos', 'le', 'les', 'ser', 'dice', 'diga', 'dicho',
    'articulo', 'articulos', 'segun', 'cuando', 'donde', 'cual', 'cuales',
    'hay', 'tiene', 'tienen', 'debe', 'deben', 'puede', 'pueden', 'sido',
    'han', 'haya', 'todo', 'todos', 'toda', 'todas', 'cada', 'entre', 'sin',
}

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
            invalid_chars = set(c for c in query if not re.match(r'[a-zA-ZáéíóúÁÉÍÓÚñÑüÜ0-9\s\-\."\',\:\;\?\¡\!\(\)]', c))
            return False, f"Caracteres no permitidos: {' '.join(invalid_chars)}"
        
        query_upper = query.upper()
        for keyword in SQL_KEYWORDS:
            if keyword in query_upper:
                search_logger.warning(f"⚠️ SQL injection attempt: '{query}'")
                return False, "Término no válido"
        
        return True, ""

    @staticmethod
    def sanitize(query: str) -> str:
        # Preserve quotes and common punctuation so sentences remain intact
        sanitized = re.sub(r'[^\w\sáéíóúÁÉÍÓÚñÑüÜ\-\.\"\',\:\;\?\¡\!\(\)]', '', query)
        # Normalize whitespace
        sanitized = re.sub(r'\s+', ' ', sanitized).strip()
        return sanitized

class DatabaseManager:
    _instance = None
    
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
        # 1. Asegurar persistencia: Si no existe en AppData (destinatario final), copiar de la instalación (semilla)
        if not self.db_path.exists():
            try:
                seed_path = _app_config.SEED_DB_DIR / self.db_path.name
                if seed_path.exists():
                    search_logger.info(f"💾 Copiando BD maestra ({seed_path.name}) a AppData...")
                    import shutil
                    shutil.copy2(seed_path, self.db_path)
                    search_logger.info("✅ BD clonada exitosamente")
                else:
                    raise FileNotFoundError(f"BD maestra no encontrada en: {seed_path}")
            except Exception as e:
                search_logger.error(f"❌ Error al migrar base de datos: {e}")
                raise FileNotFoundError(f"BD no encontrada y fallo al clonar: {e}")

        # 2. Validar esquema: tabla normas existe, tiene columnas requeridas y datos
        REQUIRED_COLUMNS = {"id", "titulo", "texto_completo"}
        conn = sqlite3.connect(str(self.db_path))
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='normas'")
            if not cursor.fetchone():
                raise ValueError("BD corrupta: tabla 'normas' no encontrada")

            cursor.execute("PRAGMA table_info(normas)")
            cols = {row[1] for row in cursor.fetchall()}
            missing = REQUIRED_COLUMNS - cols
            if missing:
                raise ValueError(f"BD incompleta: columnas faltantes en 'normas': {missing}")

            cursor.execute("SELECT COUNT(*) FROM normas")
            count = cursor.fetchone()[0]
            if count == 0:
                search_logger.warning("⚠️ La tabla 'normas' existe pero está vacía")
            else:
                search_logger.info(f"✅ BD validada: {self.db_path.name} ({count} normas)")
        finally:
            conn.close()
    
    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path), timeout=10, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA cache_size = -16000")
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA synchronous = NORMAL")
        return conn

    def initialize_tables(self):
        conn = self.get_connection()
        try:
            self._init_extra_tables(conn)
            search_logger.info("✅ Tablas inicializadas")
        finally:
            conn.close()

    def _init_extra_tables(self, conn):
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS historial_busquedas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS articulos_vistos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                articulo_id INTEGER,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS favoritos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                articulo_id INTEGER UNIQUE,
                nota TEXT,
                fecha_agregado DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS favoritos_tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                favorito_id INTEGER,
                tag TEXT NOT NULL
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS historial_exportaciones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tipo TEXT,
                items_count INTEGER,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_salt BLOB NOT NULL,
                password_hash BLOB NOT NULL,
                email TEXT UNIQUE NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_login DATETIME
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sesiones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                token TEXT UNIQUE NOT NULL,
                expires_at DATETIME NOT NULL
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS usuarios_roles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                role TEXT NOT NULL
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS notificaciones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tipo TEXT NOT NULL,
                titulo TEXT NOT NULL,
                mensaje TEXT NOT NULL,
                leida BOOLEAN DEFAULT FALSE
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS analytics_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT NOT NULL,
                properties TEXT,
                user_id INTEGER,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_analytics ON analytics_events(event_type, timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_historial_timestamp ON historial_busquedas(timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_historial_query ON historial_busquedas(query)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_articulos_vistos ON articulos_vistos(articulo_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_favoritos_articulo ON favoritos(articulo_id)")
        
        # Migración: Preguntas de seguridad dinámicas
        try:
            cursor.execute("SELECT security_question FROM usuarios LIMIT 1")
        except sqlite3.OperationalError:
            search_logger.info("Migrando tabla usuarios para preguntas de seguridad...")
            cursor.execute("ALTER TABLE usuarios ADD COLUMN security_question TEXT")
            cursor.execute("ALTER TABLE usuarios ADD COLUMN security_answer_salt BLOB")
            cursor.execute("ALTER TABLE usuarios ADD COLUMN security_answer_hash BLOB")
            cursor.execute("ALTER TABLE usuarios ADD COLUMN recovery_enabled BOOLEAN DEFAULT FALSE")
        
        conn.commit()


class SearchCache:
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

    def invalidate(self):
        """Invalida todo el caché. Llamar después de importar nuevos PDFs."""
        self.clear()
        search_logger.info("🔄 Caché de búsqueda invalidado")


class SearchEngine:
    def __init__(self, text_index=None):
        self.db_manager = DatabaseManager(DB_PATH)
        self.db_manager.initialize_tables()
        self._is_ready = True
        self._cache = SearchCache()
        search_logger.info("✅ SearchEngine listo")

    @property
    def is_ready(self) -> bool:
        return self._is_ready

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

    def _tokenize_query(self, query: str) -> List[str]:
        # Extrae frases entre comillas como tokens únicos y palabras sueltas
        # Improved: Handle nested punctuation, better splitting
        pattern = re.compile(r'"([^"]+)"|' + r"'([^']+)'|([^\s""\']+)", re.IGNORECASE)
        tokens = []
        for m in pattern.findall(query):
            token = (m[0] or m[1] or m[2]).strip(' ,.?!:;-')
            if token and len(token) >= 2:
                tokens.append(token)
        return tokens

    def search(self, query: str, operator: str = "OR", limit: int = DEFAULT_PAGE_SIZE, offset: int = 0) -> List[Dict]:
        result = self.search_safe(query, operator, page=1, page_size=limit)
        return result.results

    def search_safe(self, query: str, operator: str = "OR", page: int = 1, page_size: int = DEFAULT_PAGE_SIZE) -> 'SearchResult':
        start_time = time.perf_counter()
        
        is_valid, error_msg = QueryValidator.validate(query)
        if not is_valid:
            return SearchResult(SearchStatus.INVALID_QUERY, [], error_msg, query, 0, 0)
        
        clean_query = QueryValidator.sanitize(query)
        cached = self._cache.get(clean_query, page, page_size)
        if cached is not None:
            duration = (time.perf_counter() - start_time) * 1000
            return SearchResult(SearchStatus.SUCCESS, cached, f"{len(cached)} resultados (caché)", query, duration, len(cached), page, page_size, True)
        
        try:
            results = self._execute_search(clean_query, operator, page, page_size)
            duration = (time.perf_counter() - start_time) * 1000
            self._cache.set(clean_query, results, page, page_size)
            
            status = SearchStatus.SUCCESS if results else SearchStatus.NO_RESULTS
            message = f"{len(results)} resultados" if results else "Sin resultados. Prueba otros términos."
            
            return SearchResult(status, results, message, query, duration, len(results), page, page_size)
        except Exception as e:
            duration = (time.perf_counter() - start_time) * 1000
            search_logger.error(f"Error búsqueda: {e}")
            return SearchResult(SearchStatus.UNKNOWN_ERROR, [], str(e), query, duration, 0)

    def _extract_search_words(self, query: str) -> List[str]:
        """Extrae palabras clave de una consulta en lenguaje natural, filtrando stop words."""
        # Quitar comillas, puntuación extra
        clean = query.replace('"', '').replace("'", "").strip()
        raw_words = re.split(r'\s+', clean)
        # Filtrar stop words, palabras muy cortas y números solos (excepto con más de 2 dígitos)
        key_words = []
        for w in raw_words:
            w_lower = w.lower().strip('.,;:?!')
            if not w_lower:
                continue
            if len(w_lower) < 2:
                continue
            if w_lower in STOP_WORDS:
                continue
            key_words.append(w_lower)
        return list(dict.fromkeys(key_words))  # deduplicar conservando orden

    def _snippet_from_texto(self, texto: str, search_words: List[str], max_len: int = 250) -> str:
        """Extrae un fragmento del texto_completo centrado en la primera coincidencia."""
        if not texto:
            return ""
        texto_lower = texto.lower()
        best_pos = len(texto)
        for w in search_words:
            pos = texto_lower.find(w.lower())
            if pos != -1 and pos < best_pos:
                best_pos = pos
        start = max(0, best_pos - 60)
        end = min(len(texto), start + max_len)
        snippet = texto[start:end]
        if start > 0:
            snippet = "..." + snippet
        if end < len(texto):
            snippet = snippet + "..."
        return snippet

    def _execute_search(self, query: str, operator: str, page: int, page_size: int) -> List[Dict]:
        import os as _os
        results = []
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()

        try:
            offset = (page - 1) * page_size

            # ── MODO FRASE EXACTA: query entre comillas → FTS5 phrase search ─────────
            phrase_match = re.match(r'^["\u201c\u201d](.+)["\u201c\u201d]$', query.strip())
            if phrase_match:
                phrase = phrase_match.group(1).strip()
                # FTS5 interpreta "word1 word2 word3" como frase exacta consecutiva
                fts_phrase = f'"{phrase}"'
                rows = []
                try:
                    rows.extend(self._run_fts_query(cursor, fts_phrase, page_size * 2, offset))
                except Exception as e:
                    search_logger.debug(f"Phrase FTS error: {e}")

                # Fallback LIKE frase exacta si FTS no devuelve nada
                if not rows:
                    try:
                        cursor.execute("""
                            SELECT a.id AS articulo_id, n.titulo AS titulo_norma,
                                   a.numero_articulo, a.contenido AS fragmento,
                                   -1.0 AS rank, a.pagina,
                                   a.contenido AS contenido_completo, n.archivo_pdf
                            FROM articulos a JOIN normas n ON a.norma_id = n.id
                            WHERE a.contenido LIKE ?
                            LIMIT ? OFFSET ?
                        """, (f'%{phrase}%', page_size, offset))
                        rows.extend(cursor.fetchall())
                    except Exception as e:
                        search_logger.debug(f"Phrase LIKE error: {e}")

                key_words = phrase.split()
                search_terms = key_words
                return self._build_results(rows, search_terms, key_words)

            # 1. Extraer palabras clave (sin stop words)
            key_words = self._extract_search_words(query)
            if not key_words:
                # Si solo había stop words, tomar todas las palabras de > 2 chars
                key_words = [w for w in re.split(r'\s+', query.strip()) if len(w) > 2]

            # Expandir con sinónimos solo para palabras individuales
            expanded_terms = []
            for w in key_words:
                if ' ' not in w:
                    expanded_terms.extend(self._expand_query_with_synonyms(w))
                else:
                    expanded_terms.append(w)
            search_terms = list(dict.fromkeys([t.strip() for t in expanded_terms if t.strip()]))

            rows = []

            # ── NIVEL 1: Búsqueda en títulos de normas (ANY keyword) ────────────────
            try:
                title_conds = ' OR '.join('n.titulo LIKE ?' for _ in key_words[:6])
                title_params = [f'%{w}%' for w in key_words[:6]]
                title_params.append(30)
                cursor.execute(f"""
                    SELECT n.id AS articulo_id, n.titulo AS titulo_norma,
                           '' AS numero_articulo,
                           n.titulo AS fragmento,
                           -2.0 AS rank, 1 AS pagina,
                           n.titulo AS contenido_completo, n.archivo_pdf
                    FROM normas n
                    WHERE {title_conds}
                    LIMIT ?
                """, title_params)
                rows.extend(cursor.fetchall())
            except Exception as e:
                search_logger.debug(f"Title search error: {e}")

            # ── NIVEL 2: FTS sobre artículos (requiere FTS válida) ──────────────────
            fts_terms = [f'"{t.replace(chr(34), "")}"' for t in search_terms if t]
            if fts_terms:
                try:
                    fts_q_and = ' AND '.join(fts_terms[:4])
                    # Contar solo filas FTS (no títulos de normas) para decidir fallback OR
                    fts_rows = list(self._run_fts_query(cursor, fts_q_and, page_size, offset))
                    if len(fts_rows) < 5:
                        fts_q_or = ' OR '.join(fts_terms[:6])
                        # OR con doble límite para capturar artículos con terminología diferente
                        fts_rows.extend(self._run_fts_query(cursor, fts_q_or, page_size * 2, offset))
                    rows.extend(fts_rows)
                except Exception as e:
                    search_logger.debug(f"FTS error: {e}")

            # ── NIVEL 3: LIKE sobre articulos.contenido ──────────────────────────────
            if len(rows) < 5 and key_words:
                try:
                    art_conds = ' OR '.join(
                        '(a.contenido LIKE ? OR n.titulo LIKE ?)' for _ in key_words[:5]
                    )
                    art_params = []
                    for w in key_words[:5]:
                        art_params.extend([f'%{w}%', f'%{w}%'])
                    art_params.extend([page_size, offset])
                    cursor.execute(f"""
                        SELECT a.id AS articulo_id, n.titulo AS titulo_norma,
                               a.numero_articulo,
                               a.contenido AS fragmento,
                               -1.0 AS rank, a.pagina,
                               a.contenido AS contenido_completo, n.archivo_pdf
                        FROM articulos a JOIN normas n ON a.norma_id = n.id
                        WHERE {art_conds}
                        LIMIT ? OFFSET ?
                    """, art_params)
                    rows.extend(cursor.fetchall())
                except Exception as e:
                    search_logger.debug(f"Articulos LIKE error: {e}")

            # ── NIVEL 4: LIKE sobre normas.texto_completo (fuente principal) ─────────
            if len(rows) < 10 and key_words:
                try:
                    txt_conds = ' OR '.join(
                        '(n.texto_completo LIKE ? OR n.titulo LIKE ?)' for _ in key_words[:5]
                    )
                    txt_params = []
                    for w in key_words[:5]:
                        txt_params.extend([f'%{w}%', f'%{w}%'])
                    txt_params.extend([page_size, offset])
                    cursor.execute(f"""
                        SELECT n.id AS articulo_id, n.titulo AS titulo_norma,
                               'Texto completo' AS numero_articulo,
                               n.texto_completo AS fragmento,
                               -0.8 AS rank, 1 AS pagina,
                               n.texto_completo AS contenido_completo, n.archivo_pdf
                        FROM normas n
                        WHERE n.texto_completo IS NOT NULL AND ({txt_conds})
                        LIMIT ? OFFSET ?
                    """, txt_params)
                    rows.extend(cursor.fetchall())
                except Exception as e:
                    search_logger.debug(f"Normas texto_completo LIKE error: {e}")

            return self._build_results(rows, search_terms, key_words)

        finally:
            conn.close()

    def _build_results(self, rows: List, search_terms: List[str], key_words: List[str]) -> List[Dict]:
        """Deduplica filas y construye la lista de resultados con snippets resaltados."""
        import os as _os
        seen = set()
        unique_rows = []
        for r in rows:
            try:
                key = (r['titulo_norma'], r['numero_articulo'])
            except Exception:
                key = str(r)
            if key not in seen:
                unique_rows.append(r)
                seen.add(key)

        results = []
        for row in unique_rows:
            try:
                raw_frag = row['fragmento']
                if not raw_frag:
                    raw_frag = row['contenido_completo'] or ""
            except Exception:
                raw_frag = ""

            raw_frag = str(raw_frag)

            if "</b>" in raw_frag:
                snippet_md = raw_frag.replace("<b>", "**").replace("</b>", "**")
            else:
                snippet_raw = self._snippet_from_texto(raw_frag, search_terms or key_words)
                if not snippet_raw:
                    snippet_raw = raw_frag[:200] + ("..." if len(raw_frag) > 200 else "")
                snippet_md = snippet_raw
                for term in (search_terms or key_words):
                    if len(term) > 2:
                        snippet_md = re.compile(re.escape(term), re.IGNORECASE).sub(
                            f"**{term}**", snippet_md
                        )

            pdf_entry = row['archivo_pdf'] or ""
            if ":" in pdf_entry or "\\" in pdf_entry or "/" in pdf_entry:
                pdf_filename = _os.path.basename(pdf_entry)
            else:
                pdf_filename = pdf_entry

            num_art = row['numero_articulo'] or ""
            ctx = f"Art. {num_art}: {snippet_md}" if num_art and num_art not in ('', 'Texto completo') else snippet_md

            results.append({
                'id': row['articulo_id'],
                'file': pdf_filename,
                'page': row['pagina'] or 1,
                'relevance': abs(row['rank'] or 0) * 10 if row['rank'] else 0,
                'context': ctx,
                'norma_titulo': row['titulo_norma'],
                'numero_articulo': num_art,
            })

        results.sort(key=lambda x: x['relevance'], reverse=True)
        return results

    def _run_fts_query(self, cursor, fts_query: str, limit: int, offset: int) -> List:
        """Helper para ejecutar consultas FTS5 sobre artículos indexados."""
        try:
            cursor.execute("""
                SELECT
                    f.articulo_id,
                    f.titulo_norma,
                    f.numero_articulo,
                    snippet(busqueda_fts, 1, '<b>', '</b>', '...', 30) AS fragmento,
                    f.rank,
                    a.pagina,
                    a.contenido AS contenido_completo,
                    n.archivo_pdf
                FROM busqueda_fts f
                JOIN articulos a ON f.articulo_id = a.id
                JOIN normas n ON a.norma_id = n.id
                WHERE busqueda_fts MATCH ?
                ORDER BY rank
                LIMIT ? OFFSET ?
            """, (fts_query, limit, offset))
            return cursor.fetchall()
        except Exception as e:
            search_logger.debug(f"FTS query skipped: {e}")
            return []

    def get_article_by_id(self, article_id: int) -> Optional[Dict]:
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

    def get_search_suggestions(self, prefix: str, limit: int = 5) -> List[str]:
        """Obtiene sugerencias de búsqueda basadas en el prefijo ingresado."""
        if not prefix or len(prefix.strip()) < 2:
            return []
        
        prefix = prefix.strip().lower()
        suggestions = []
        
        # Expandir con sinónimos
        expanded = self._expand_query_with_synonyms(prefix)
        suggestions.extend(expanded[:limit])
        
        # Agregar términos del historial que coincidan
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT DISTINCT query 
                FROM historial_busquedas 
                WHERE LOWER(query) LIKE ? 
                ORDER BY timestamp DESC 
                LIMIT ?
            """, (f"{prefix}%", limit - len(suggestions)))
            
            for row in cursor.fetchall():
                suggestions.append(row['query'])
        finally:
            conn.close()
        
        return suggestions[:limit]

    def is_favorite(self, article_id: int) -> bool:
        """Verifica si un artículo está en favoritos."""
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT COUNT(*) as count FROM favoritos WHERE articulo_id = ?", (article_id,))
            result = cursor.fetchone()
            return result['count'] > 0 if result else False
        finally:
            conn.close()

    def toggle_favorite(self, article_id: int, nota: str = "") -> bool:
        """
        Alterna favorito de un artículo.
        Retorna True si ahora está en favoritos, False si fue removido.
        """
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        try:
            # Verificar si ya es favorito
            cursor.execute("SELECT id FROM favoritos WHERE articulo_id = ?", (article_id,))
            result = cursor.fetchone()
            
            if result:
                # Remover de favoritos
                cursor.execute("DELETE FROM favoritos WHERE articulo_id = ?", (article_id,))
                conn.commit()
                search_logger.info(f"Artículo {article_id} removido de favoritos")
                return False
            else:
                # Agregar a favoritos
                cursor.execute("INSERT INTO favoritos (articulo_id, nota) VALUES (?, ?)", (article_id, nota))
                conn.commit()
                search_logger.info(f"Artículo {article_id} agregado a favoritos")
                return True
        except Exception as e:
            search_logger.error(f"Error toggleando favorito: {e}")
            return False
        finally:
            conn.close()

    def add_favorite(self, article_id: int, nota: str = "") -> bool:
        """Agrega un artículo a favoritos."""
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT OR IGNORE INTO favoritos (articulo_id, nota) VALUES (?, ?)", (article_id, nota))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            search_logger.error(f"Error agregando favorito: {e}")
            return False
        finally:
            conn.close()

    def remove_favorite(self, article_id: int) -> bool:
        """Remueve un artículo de favoritos."""
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM favoritos WHERE articulo_id = ?", (article_id,))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            search_logger.error(f"Error removiendo favorito: {e}")
            return False
        finally:
            conn.close()

    def get_favorites(self) -> List[Dict]:
        """Obtiene todos los favoritos del usuario.

        Funciona tanto si articulo_id es un id de articulos como de normas,
        ya que el buscador puede guardar ambos tipos según el nivel de búsqueda.
        """
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT f.id, f.articulo_id, f.nota, f.fecha_agregado,
                       a.numero_articulo,
                       a.contenido,
                       a.pagina,
                       COALESCE(na.titulo, nd.titulo)       AS norma_titulo,
                       COALESCE(na.archivo_pdf, nd.archivo_pdf) AS archivo_pdf
                FROM favoritos f
                -- intento 1: articulo_id es realmente un id de articulo
                LEFT JOIN articulos a  ON f.articulo_id = a.id
                LEFT JOIN normas    na ON a.norma_id    = na.id
                -- intento 2: articulo_id es en realidad un id de norma
                LEFT JOIN normas    nd ON f.articulo_id = nd.id
                ORDER BY f.fecha_agregado DESC
            """)
            rows = []
            for row in cursor.fetchall():
                d = dict(row)
                # Si el título sigue siendo NULL, buscar por norma directamente
                if not d.get('norma_titulo'):
                    cursor2 = conn.cursor()
                    cursor2.execute(
                        "SELECT titulo, archivo_pdf FROM normas WHERE id=?",
                        (d['articulo_id'],)
                    )
                    nr = cursor2.fetchone()
                    if nr:
                        d['norma_titulo'] = nr['titulo']
                        d['archivo_pdf']  = nr['archivo_pdf']
                    else:
                        d['norma_titulo'] = 'Documento desconocido'
                rows.append(d)
            return rows
        except Exception as e:
            search_logger.error(f"Error obteniendo favoritos: {e}")
            return []
        finally:
            conn.close()

    def get_favorite_tags(self, favorito_id: int) -> List[str]:
        """Retorna la lista de tags de un favorito."""
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT tag FROM favoritos_tags WHERE favorito_id = ?", (favorito_id,))
            return [row['tag'] for row in cursor.fetchall()]
        except Exception as e:
            search_logger.error(f"Error obteniendo tags de favorito {favorito_id}: {e}")
            return []
        finally:
            conn.close()

    def add_favorite_tag(self, favorito_id: int, tag: str) -> bool:
        """Agrega un tag a un favorito."""
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO favoritos_tags (favorito_id, tag) VALUES (?, ?)", (favorito_id, tag.strip()))
            conn.commit()
            return True
        except Exception as e:
            search_logger.error(f"Error agregando tag al favorito {favorito_id}: {e}")
            return False
        finally:
            conn.close()

    def update_favorite_note(self, favorito_id: int, note: str) -> bool:
        """Actualiza la nota personal de un favorito."""
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("UPDATE favoritos SET nota = ? WHERE id = ?", (note, favorito_id))
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            search_logger.error(f"Error actualizando nota del favorito {favorito_id}: {e}")
            return False
        finally:
            conn.close()

def create_search_engine(text_index=None) -> 'SearchEngine':
    return SearchEngine(text_index)

