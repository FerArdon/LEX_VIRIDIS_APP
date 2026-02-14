"""
Fixtures compartidos para la suite de pruebas de LEX VIRIDIS.
"""

import sqlite3
import pytest
from pathlib import Path


@pytest.fixture
def tmp_db(tmp_path):
    """Crea una base de datos SQLite temporal con el esquema completo de LEX VIRIDIS."""
    db_path = tmp_path / "test_legislacion.db"
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Tabla principal de normas
    cursor.execute("""
        CREATE TABLE normas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT NOT NULL,
            tipo TEXT,
            archivo_pdf TEXT,
            resumen TEXT,
            fecha_publicacion TEXT
        )
    """)

    # Tabla de articulos
    cursor.execute("""
        CREATE TABLE articulos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            norma_id INTEGER NOT NULL,
            numero_articulo TEXT,
            contenido TEXT,
            pagina INTEGER,
            FOREIGN KEY (norma_id) REFERENCES normas(id)
        )
    """)

    # FTS5 para busqueda de texto completo (standalone, sin content sync)
    cursor.execute("""
        CREATE VIRTUAL TABLE busqueda_fts USING fts5(
            articulo_id UNINDEXED,
            titulo_norma,
            numero_articulo
        )
    """)

    # Tablas de historial y favoritos
    cursor.execute("""
        CREATE TABLE historial_busquedas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            query TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE articulos_vistos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            articulo_id INTEGER,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (articulo_id) REFERENCES articulos(id)
        )
    """)
    cursor.execute("""
        CREATE TABLE favoritos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            articulo_id INTEGER UNIQUE,
            nota TEXT,
            fecha_agregado DATETIME DEFAULT CURRENT_TIMESTAMP,
            fecha_modificado DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (articulo_id) REFERENCES articulos(id)
        )
    """)
    cursor.execute("""
        CREATE TABLE favoritos_tags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            favorito_id INTEGER,
            tag TEXT NOT NULL,
            FOREIGN KEY (favorito_id) REFERENCES favoritos(id)
        )
    """)
    cursor.execute("""
        CREATE TABLE historial_exportaciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo TEXT,
            items_count INTEGER,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Tablas de usuarios y sesiones
    cursor.execute("""
        CREATE TABLE usuarios (
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
    cursor.execute("""
        CREATE TABLE sesiones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            token TEXT UNIQUE NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            expires_at DATETIME NOT NULL,
            FOREIGN KEY (user_id) REFERENCES usuarios(id)
        )
    """)
    cursor.execute("""
        CREATE TABLE usuarios_roles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            role TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES usuarios(id)
        )
    """)

    # Tablas de notificaciones y analytics
    cursor.execute("""
        CREATE TABLE notificaciones (
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
    cursor.execute("""
        CREATE TABLE analytics_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_type TEXT NOT NULL,
            properties TEXT,
            user_id INTEGER,
            session_id TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES usuarios(id)
        )
    """)

    # Insertar datos de prueba
    cursor.execute("""
        INSERT INTO normas (titulo, tipo, archivo_pdf, resumen, fecha_publicacion)
        VALUES ('Ley General del Ambiente', 'Decreto Legislativo', '01-DL_104-1993.pdf',
                'Ley marco de proteccion ambiental de Honduras', '1993-06-27')
    """)
    cursor.execute("""
        INSERT INTO normas (titulo, tipo, archivo_pdf, resumen, fecha_publicacion)
        VALUES ('Ley Forestal', 'Decreto Legislativo', '02-DL_156-2007.pdf',
                'Regulacion del sector forestal hondureno', '2007-09-13')
    """)
    cursor.execute("""
        INSERT INTO normas (titulo, tipo, archivo_pdf, resumen, fecha_publicacion)
        VALUES ('Reglamento de Licencias Ambientales', 'Acuerdo Ejecutivo', '03-AE_109-1993.pdf',
                'Reglamento para otorgamiento de licencias ambientales', '1993-12-20')
    """)

    # Articulos de prueba
    cursor.execute("""
        INSERT INTO articulos (norma_id, numero_articulo, contenido, pagina)
        VALUES (1, '1', 'La proteccion del ambiente y los recursos naturales es de interes publico y social.', 1)
    """)
    cursor.execute("""
        INSERT INTO articulos (norma_id, numero_articulo, contenido, pagina)
        VALUES (1, '5', 'Los bosques y aguas son recursos protegidos por el Estado.', 2)
    """)
    cursor.execute("""
        INSERT INTO articulos (norma_id, numero_articulo, contenido, pagina)
        VALUES (2, '10', 'La tala ilegal de bosques constituye un delito ambiental.', 5)
    """)
    cursor.execute("""
        INSERT INTO articulos (norma_id, numero_articulo, contenido, pagina)
        VALUES (3, '3', 'La licencia ambiental es el permiso otorgado por la autoridad competente.', 1)
    """)

    # Insertar en FTS5
    for art_id in [1, 2, 3, 4]:
        cursor.execute("SELECT a.id, n.titulo, a.numero_articulo FROM articulos a JOIN normas n ON a.norma_id = n.id WHERE a.id = ?", (art_id,))
        row = cursor.fetchone()
        cursor.execute(
            "INSERT INTO busqueda_fts (articulo_id, titulo_norma, numero_articulo) VALUES (?, ?, ?)",
            (row[0], row[1], row[2])
        )

    conn.commit()
    conn.close()
    return db_path


@pytest.fixture
def db_manager(tmp_db):
    """Crea un DatabaseManager apuntando a la BD temporal."""
    from lexviridis.search_engine import DatabaseManager

    # Resetear singleton para que use la BD temporal
    DatabaseManager._instance = None
    manager = DatabaseManager(tmp_db)
    yield manager
    # Limpiar singleton despues de cada test
    DatabaseManager._instance = None


@pytest.fixture
def search_engine(db_manager):
    """Crea un SearchEngine con la BD temporal."""
    from lexviridis.search_engine import SearchEngine, DB_PATH
    import lexviridis.search_engine as se_module

    # Guardar el DB_PATH original y reemplazar temporalmente
    original_db_path = se_module.DB_PATH
    se_module.DB_PATH = db_manager.db_path

    # Resetear singleton para que use la BD temporal
    from lexviridis.search_engine import DatabaseManager
    DatabaseManager._instance = None

    engine = SearchEngine()
    yield engine

    # Restaurar
    se_module.DB_PATH = original_db_path
    DatabaseManager._instance = None
