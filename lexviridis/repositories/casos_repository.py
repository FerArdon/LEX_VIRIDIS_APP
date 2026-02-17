"""Repository para gestión de casos y expedientes legales."""

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional


class CasosRepository:
    """Repositorio para gestionar casos legales y expedientes."""

    def __init__(self, db_path: Path | str):
        """Inicializa el repositorio de casos."""
        self.db_path = Path(db_path)
        self._init_tables()

    def _init_tables(self):
        """Crea las tablas necesarias para casos si no existen."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Tabla principal de casos
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS casos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                numero_expediente TEXT UNIQUE NOT NULL,
                titulo TEXT NOT NULL,
                descripcion TEXT,
                fecha_inicio TEXT NOT NULL,
                fecha_cierre TEXT,
                estado TEXT DEFAULT 'ABIERTO',
                prioridad TEXT DEFAULT 'MEDIA',
                categoria TEXT,
                responsable TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Tabla para vincular artículos a casos
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS caso_articulos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                caso_id INTEGER NOT NULL,
                articulo_id INTEGER NOT NULL,
                relevancia TEXT DEFAULT 'MEDIA',
                notas TEXT,
                vinculado_en TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (caso_id) REFERENCES casos(id) ON DELETE CASCADE,
                UNIQUE(caso_id, articulo_id)
            )
        """)

        # Tabla para notas y anotaciones por caso
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS caso_notas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                caso_id INTEGER NOT NULL,
                tipo TEXT DEFAULT 'NOTA',
                titulo TEXT NOT NULL,
                contenido TEXT NOT NULL,
                autor TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (caso_id) REFERENCES casos(id) ON DELETE CASCADE
            )
        """)

        # Tabla para búsquedas vinculadas a casos
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS caso_busquedas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                caso_id INTEGER NOT NULL,
                query TEXT NOT NULL,
                resultados_count INTEGER DEFAULT 0,
                fecha_busqueda TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (caso_id) REFERENCES casos(id) ON DELETE CASCADE
            )
        """)

        # Índices para mejorar rendimiento
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_casos_estado
            ON casos(estado)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_casos_prioridad
            ON casos(prioridad)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_caso_articulos_caso
            ON caso_articulos(caso_id)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_caso_notas_caso
            ON caso_notas(caso_id)
        """)

        conn.commit()
        conn.close()

    def crear_caso(
        self,
        numero_expediente: str,
        titulo: str,
        descripcion: str = "",
        estado: str = "ABIERTO",
        prioridad: str = "MEDIA",
        categoria: str = "",
        responsable: str = ""
    ) -> int:
        """
        Crea un nuevo caso.

        Returns:
            ID del caso creado
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        fecha_inicio = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute("""
            INSERT INTO casos (
                numero_expediente, titulo, descripcion, fecha_inicio,
                estado, prioridad, categoria, responsable
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            numero_expediente, titulo, descripcion, fecha_inicio,
            estado, prioridad, categoria, responsable
        ))

        caso_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return caso_id

    def obtener_casos(
        self,
        estado: Optional[str] = None,
        prioridad: Optional[str] = None,
        categoria: Optional[str] = None,
        limit: int = 100
    ) -> list[dict]:
        """Obtiene lista de casos con filtros opcionales."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        query = "SELECT * FROM casos WHERE 1=1"
        params = []

        if estado:
            query += " AND estado = ?"
            params.append(estado)

        if prioridad:
            query += " AND prioridad = ?"
            params.append(prioridad)

        if categoria:
            query += " AND categoria = ?"
            params.append(categoria)

        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)

        cursor.execute(query, params)
        casos = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return casos

    def obtener_caso(self, caso_id: int) -> Optional[dict]:
        """Obtiene un caso por ID."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM casos WHERE id = ?", (caso_id,))
        row = cursor.fetchone()
        conn.close()

        return dict(row) if row else None

    def actualizar_caso(
        self,
        caso_id: int,
        titulo: Optional[str] = None,
        descripcion: Optional[str] = None,
        estado: Optional[str] = None,
        prioridad: Optional[str] = None,
        categoria: Optional[str] = None,
        responsable: Optional[str] = None
    ) -> bool:
        """Actualiza un caso existente."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        updates = []
        params = []

        if titulo is not None:
            updates.append("titulo = ?")
            params.append(titulo)

        if descripcion is not None:
            updates.append("descripcion = ?")
            params.append(descripcion)

        if estado is not None:
            updates.append("estado = ?")
            params.append(estado)
            if estado == "CERRADO":
                updates.append("fecha_cierre = ?")
                params.append(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

        if prioridad is not None:
            updates.append("prioridad = ?")
            params.append(prioridad)

        if categoria is not None:
            updates.append("categoria = ?")
            params.append(categoria)

        if responsable is not None:
            updates.append("responsable = ?")
            params.append(responsable)

        if not updates:
            conn.close()
            return False

        updates.append("updated_at = ?")
        params.append(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        params.append(caso_id)

        query = f"UPDATE casos SET {', '.join(updates)} WHERE id = ?"
        cursor.execute(query, params)

        success = cursor.rowcount > 0
        conn.commit()
        conn.close()

        return success

    def eliminar_caso(self, caso_id: int) -> bool:
        """Elimina un caso y todas sus vinculaciones."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("DELETE FROM casos WHERE id = ?", (caso_id,))

        success = cursor.rowcount > 0
        conn.commit()
        conn.close()

        return success

    def vincular_articulo(
        self,
        caso_id: int,
        articulo_id: int,
        relevancia: str = "MEDIA",
        notas: str = ""
    ) -> bool:
        """Vincula un artículo a un caso."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO caso_articulos (caso_id, articulo_id, relevancia, notas)
                VALUES (?, ?, ?, ?)
            """, (caso_id, articulo_id, relevancia, notas))

            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            # Ya existe la vinculación
            conn.close()
            return False

    def desvincular_articulo(self, caso_id: int, articulo_id: int) -> bool:
        """Desvincula un artículo de un caso."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            DELETE FROM caso_articulos
            WHERE caso_id = ? AND articulo_id = ?
        """, (caso_id, articulo_id))

        success = cursor.rowcount > 0
        conn.commit()
        conn.close()

        return success

    def obtener_articulos_caso(self, caso_id: int) -> list[dict]:
        """Obtiene todos los artículos vinculados a un caso."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                ca.*,
                a.numero_articulo,
                a.contenido_completo,
                n.titulo as norma_titulo,
                n.archivo_pdf
            FROM caso_articulos ca
            JOIN articulos a ON ca.articulo_id = a.id
            JOIN normas n ON a.norma_id = n.id
            WHERE ca.caso_id = ?
            ORDER BY ca.vinculado_en DESC
        """, (caso_id,))

        articulos = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return articulos

    def agregar_nota(
        self,
        caso_id: int,
        titulo: str,
        contenido: str,
        tipo: str = "NOTA",
        autor: str = ""
    ) -> int:
        """Agrega una nota a un caso."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO caso_notas (caso_id, tipo, titulo, contenido, autor)
            VALUES (?, ?, ?, ?, ?)
        """, (caso_id, tipo, titulo, contenido, autor))

        nota_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return nota_id

    def obtener_notas_caso(self, caso_id: int) -> list[dict]:
        """Obtiene todas las notas de un caso."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM caso_notas
            WHERE caso_id = ?
            ORDER BY created_at DESC
        """, (caso_id,))

        notas = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return notas

    def eliminar_nota(self, nota_id: int) -> bool:
        """Elimina una nota."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("DELETE FROM caso_notas WHERE id = ?", (nota_id,))

        success = cursor.rowcount > 0
        conn.commit()
        conn.close()

        return success

    def obtener_estadisticas(self) -> dict:
        """Obtiene estadísticas generales de casos."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        stats = {}

        # Total de casos
        cursor.execute("SELECT COUNT(*) FROM casos")
        stats['total_casos'] = cursor.fetchone()[0]

        # Casos por estado
        cursor.execute("""
            SELECT estado, COUNT(*)
            FROM casos
            GROUP BY estado
        """)
        stats['por_estado'] = {row[0]: row[1] for row in cursor.fetchall()}

        # Casos por prioridad
        cursor.execute("""
            SELECT prioridad, COUNT(*)
            FROM casos
            GROUP BY prioridad
        """)
        stats['por_prioridad'] = {row[0]: row[1] for row in cursor.fetchall()}

        conn.close()
        return stats
