import logging
from typing import Any


class StatsRepository:
    """
    Repository for accessing system statistics and analytics.
    """
    def __init__(self, db_manager):
        self.db_manager = db_manager

    def get_dashboard_stats(self) -> dict[str, Any]:
        """
        Retrieves aggregated stats for the dashboard.
        Based on logic extracted from SearchEngine.get_dashboard_stats/ui_v2.
        """
        stats = {
            'total_normas': 0,
            'total_articulos': 0,
            'total_favoritos': 0,
            'total_busquedas': 0,
            'distribucion_tipo': {},
            'top_searches': [],
            'most_viewed': [],
            'timeline_busquedas': []
        }

        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()

            # Basic counts
            cursor.execute("SELECT COUNT(*) FROM normas")
            stats['total_normas'] = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM articulos")
            stats['total_articulos'] = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM favoritos")
            stats['total_favoritos'] = cursor.fetchone()[0]

            # Search stats
            try:
                cursor.execute("SELECT COUNT(*) FROM search_logs")
                stats['total_busquedas'] = cursor.fetchone()[0]
            except Exception:
                pass  # Table might not exist yet

            # Distribution by type
            cursor.execute("SELECT tipo, COUNT(*) FROM normas GROUP BY tipo")
            for row in cursor.fetchall():
                stats['distribucion_tipo'][row[0] or 'Otros'] = row[1]

            # Top searches
            try:
                cursor.execute("""
                    SELECT query, COUNT(*) as c
                    FROM search_logs
                    GROUP BY query
                    ORDER BY c DESC
                    LIMIT 5
                """)
                stats['top_searches'] = cursor.fetchall()
            except Exception:
                pass

            # Timeline (Last 7 days)
            try:
                cursor.execute("""
                    SELECT date(timestamp), COUNT(*)
                    FROM search_logs
                    WHERE timestamp >= date('now', '-7 days')
                    GROUP BY date(timestamp)
                    ORDER BY date(timestamp)
                """)
                stats['timeline_busquedas'] = cursor.fetchall()
            except Exception:
                pass

            conn.close()
        except Exception as e:
            logging.error(f"Error retrieving dashboard stats: {e}")

        return stats

    def reset_stats(self) -> bool:
        """Resets all statistical data."""
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM search_logs")
            cursor.execute("DELETE FROM view_history")
            cursor.execute("DELETE FROM user_activity")
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logging.error(f"Error resetting stats: {e}")
            return False
