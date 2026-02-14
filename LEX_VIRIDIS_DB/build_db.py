
import sqlite3
import datetime
from pathlib import Path

DB_PATH = Path(r"c:\Users\frard\OneDrive\LEX_VIRIDIS_APP\LEX_VIRIDIS_DB\legislacion_ambiental.db")

SCHEMA_SCRIPT = """
-- Habilitar claves foráneas
PRAGMA foreign_keys = ON;

-- 1. Tabla Maestra de Instituciones
CREATE TABLE IF NOT EXISTS instituciones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL UNIQUE,
    siglas TEXT,
    tipo TEXT -- 'Congreso', 'Ejecutivo', 'Municipalidad', 'Internacional'
);

-- 2. Tabla Principal de Normas (Leyes, Decretos, Acuerdos)
CREATE TABLE IF NOT EXISTS normas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tipo TEXT NOT NULL,          -- 'Ley', 'Decreto', 'Acuerdo', 'Reglamento', 'Tratado'
    numero TEXT,                 -- Ej: '104-93', '98-2007'
    titulo TEXT NOT NULL,
    fecha_publicacion DATE,
    fecha_vigencia DATE,
    estado TEXT DEFAULT 'VIGENTE', -- 'VIGENTE', 'DEROGADA', 'REFORMADA'
    institucion_id INTEGER,
    categoria TEXT,              -- 'Forestal', 'Agua', 'Minas', 'General', 'Penal'
    resumen TEXT,
    texto_completo TEXT,         -- Para búsquedas simples si no se usa FTS
    archivo_pdf TEXT,            -- Ruta al PDF original
    FOREIGN KEY (institucion_id) REFERENCES instituciones(id)
);

-- 3. Tabla de Artículos (Desglose granular para búsqueda precisa)
CREATE TABLE IF NOT EXISTS articulos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    norma_id INTEGER NOT NULL,
    numero_articulo TEXT,        -- Ej: '1', '32-A'
    titulo_articulo TEXT,        -- Ej: 'Definiciones'
    contenido TEXT NOT NULL,
    estado TEXT DEFAULT 'VIGENTE',
    FOREIGN KEY (norma_id) REFERENCES normas(id) ON DELETE CASCADE
);

-- 4. Índice Full-Text Search (FTS5) para búsquedas ultra-rápidas
CREATE VIRTUAL TABLE IF NOT EXISTS busqueda_fts USING fts5(
    titulo_norma,
    contenido_articulo,
    tags,
    tokenize='porter' -- Stemming básico
);

-- 5. Relaciones (Modificaciones, Derogaciones)
CREATE TABLE IF NOT EXISTS relaciones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    norma_origen_id INTEGER,    -- La norma que modifica
    norma_destino_id INTEGER,   -- La norma modificada
    tipo_relacion TEXT,         -- 'REFORMA', 'DEROGA', 'REGLAMENTA'
    descripcion TEXT,
    FOREIGN KEY (norma_origen_id) REFERENCES normas(id),
    FOREIGN KEY (norma_destino_id) REFERENCES normas(id)
);

-- 6. Glosario Ambiental
CREATE TABLE IF NOT EXISTS glosario (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    termino TEXT NOT NULL UNIQUE,
    definicion TEXT NOT NULL,
    fuente_norma_id INTEGER,
    FOREIGN KEY (fuente_norma_id) REFERENCES normas(id)
);

-- TRIGGERS PARA MANTENER FTS ACTUALIZADO
CREATE TRIGGER IF NOT EXISTS insert_articulo_fts AFTER INSERT ON articulos
BEGIN
    INSERT INTO busqueda_fts(titulo_norma, contenido_articulo, tags)
    SELECT n.titulo, new.contenido, n.categoria
    FROM normas n WHERE n.id = new.norma_id;
END;
"""

def init_db():
    print(f"📦 Creando base de datos en: {DB_PATH}")
    try:
        if DB_PATH.exists():
            print("⚠️ La base de datos ya existe. Creando backup...")
            # Aquí podríamos renombrarla, pero por ahora solo avisamos
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.executescript(SCHEMA_SCRIPT)
        
        conn.commit()
        conn.close()
        print("✅ Esquema creado exitosamente.")
        return True
    except Exception as e:
        print(f"❌ Error creando base de datos: {e}")
        return False

# DATOS SEMILLA (Seed Data)
# Lista curada de las leyes más importantes
SEED_DATA = [
    # INSTITUCIONES
    ("Congreso Nacional", "CN", "Congreso"),
    ("Secretaría de Recursos Naturales y Ambiente", "SERNA", "Ejecutivo"),
    ("Instituto de Conservación Forestal", "ICF", "Ejecutivo"),
    
    # NORMAS (Muestras representativas)
    {
        "tipo": "Ley", "numero": "104-93", "titulo": "Ley General del Ambiente",
        "fecha": "1993-06-30", "inst": "Congreso Nacional", "cat": "General",
        "resumen": "Marco general para la protección, conservación y restauración del ambiente y los recursos naturales."
    },
    {
        "tipo": "Ley", "numero": "98-2007", "titulo": "Ley Forestal, Áreas Protegidas y Vida Silvestre",
        "fecha": "2007-09-20", "inst": "Congreso Nacional", "cat": "Forestal",
        "resumen": "Regula el régimen legal de los bosques, áreas protegidas y vida silvestre."
    },
     {
        "tipo": "Ley", "numero": "181-2009", "titulo": "Ley General de Aguas",
        "fecha": "2009-12-14", "inst": "Congreso Nacional", "cat": "Agua",
        "resumen": "Establece los principios y regulaciones para la gestión del recurso hídrico."
    },
    {
        "tipo": "Decreto", "numero": "130-2017", "titulo": "Código Penal de Honduras (Título XVI)",
        "fecha": "2019-05-10", "inst": "Congreso Nacional", "cat": "Penal",
        "resumen": "Título XVI dedicado exclusivamente a los Delitos contra el Medio Ambiente."
    }
]

def seed_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    print("\n🌱 Sembrando datos iniciales...")
    
    # 1. Instituciones
    inst_map = {} # nombre -> id
    for nombre, siglas, tipo in [d for d in SEED_DATA if isinstance(d, tuple)]:
        try:
            c.execute("INSERT OR IGNORE INTO instituciones (nombre, siglas, tipo) VALUES (?, ?, ?)", (nombre, siglas, tipo))
            # Obtener ID
            c.execute("SELECT id FROM instituciones WHERE nombre = ?", (nombre,))
            inst_map[nombre] = c.fetchone()[0]
        except Exception as e:
            print(f"Error insertando {nombre}: {e}")
            
    # 2. Normas
    for item in [d for d in SEED_DATA if isinstance(d, dict)]:
        try:
            inst_id = inst_map.get(item["inst"])
            c.execute("""
                INSERT INTO normas (tipo, numero, titulo, fecha_publicacion, institucion_id, categoria, resumen)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (item["tipo"], item["numero"], item["titulo"], item["fecha"], inst_id, item["cat"], item["resumen"]))
            print(f"   ➕ Norma agregada: {item['titulo']}")
        except Exception as e:
            print(f"Error insertando norma {item['titulo']}: {e}")

    conn.commit()
    conn.close()
    print("✅ Datos iniciales cargados.")

if __name__ == "__main__":
    if init_db():
        seed_db()
