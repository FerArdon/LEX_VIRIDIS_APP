import logging
from typing import Any


class LibraryRepository:
    """
    Repository for accessing library data (Normas, Articulos).
    Abstracts direct SQL queries from the UI.
    """
    def __init__(self, db_manager):
        self.db_manager = db_manager

    def get_all_norms(self) -> list[dict[str, Any]]:
        """
        Retrieves all norms with their article count.
        """
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()

            # Optimized query to get all norms and their article counts
            cursor.execute("""
                SELECT id, tipo, titulo, archivo_pdf,
                       (SELECT COUNT(*) FROM articulos WHERE norma_id = normas.id) as num_articulos
                FROM normas
                ORDER BY tipo, titulo
            """)

            columns = [column[0] for column in cursor.description]
            results = []
            for row in cursor.fetchall():
                results.append(dict(zip(columns, row, strict=False)))

            conn.close()
            return results
        except Exception as e:
            logging.error(f"Error retrieving norms: {e}")
            return []

    def get_norms_grouped_by_type(self) -> dict[str, list[dict[str, Any]]]:
        """
        Retrieves all norms grouped by their type.
        """
        norms = self.get_all_norms()
        grouped = {}
        for norma in norms:
            tipo = norma.get('tipo', 'Otros') or 'Otros'
            if tipo not in grouped:
                grouped[tipo] = []
            grouped[tipo].append(norma)
        return grouped

    def get_norm_by_id(self, norm_id: int) -> dict[str, Any] | None:
        """Retrieves a specific norm by ID."""
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM normas WHERE id = ?", (norm_id,))
            row = cursor.fetchone()
            conn.close()

            if row:
                columns = [column[0] for column in cursor.description]
                return dict(zip(columns, row, strict=False))
            return None
        except Exception as e:
            logging.error(f"Error retrieving norm {norm_id}: {e}")
            return None
