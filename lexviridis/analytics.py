
import json
from enum import Enum
from datetime import datetime
from typing import Dict, List, Optional

class EventType(Enum):
    SEARCH_EXECUTED = "search_executed"
    SEARCH_RESULT_CLICKED = "search_result_clicked"
    PAGE_VIEW = "page_view"
    SECTION_OPENED = "section_opened"
    FAVORITE_ADDED = "favorite_added"
    DOCUMENT_EXPORTED = "document_exported"
    ERROR_OCCURRED = "error_occurred"
    SEARCH_NO_RESULTS = "search_no_results"

class AnalyticsTracker:
    """Rastreador de eventos de usuario."""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager

    def track_event(self, event_type: EventType, properties: Dict = None, user_id: int = None, session_id: str = None):
        """Registra un evento en la base de datos."""
        conn = self.db_manager.get_connection()
        try:
            conn.execute("""
                INSERT INTO analytics_events (event_type, properties, user_id, session_id)
                VALUES (?, ?, ?, ?)
            """, (event_type.value, json.dumps(properties or {}), user_id, session_id))
            conn.commit()
        finally:
            conn.close()

    def track_search(self, query: str, results_count: int, user_id: int = None):
        self.track_event(EventType.SEARCH_EXECUTED, {
            'query': query,
            'results_count': results_count,
            'has_results': results_count > 0
        }, user_id)

class AnalyticsReporter:
    """Genera reportes y métricas de uso."""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager

    def get_kpis(self, start_date: str, end_date: str) -> Dict:
        conn = self.db_manager.get_connection()
        try:
            cursor = conn.cursor()
            metrics = {}
            
            # Búsquedas totales
            cursor.execute("SELECT COUNT(*) FROM analytics_events WHERE event_type = ? AND timestamp BETWEEN ? AND ?", 
                         (EventType.SEARCH_EXECUTED.value, start_date, end_date))
            metrics['total_searches'] = cursor.fetchone()[0]
            
            # Usuarios únicos
            cursor.execute("SELECT COUNT(DISTINCT user_id) FROM analytics_events WHERE timestamp BETWEEN ? AND ?", 
                         (start_date, end_date))
            metrics['active_users'] = cursor.fetchone()[0]
            
            return metrics
        finally:
            conn.close()

    def get_funnel(self) -> Dict:
        conn = self.db_manager.get_connection()
        try:
            cursor = conn.cursor()
            # Simplificado para demo
            cursor.execute("SELECT COUNT(*) FROM analytics_events WHERE event_type = ?", (EventType.SEARCH_EXECUTED.value,))
            searches = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM analytics_events WHERE event_type = ?", (EventType.SEARCH_RESULT_CLICKED.value,))
            clicks = cursor.fetchone()[0]
            
            return {
                'searches': searches,
                'clicks': clicks,
                'conversion': (clicks/searches*100) if searches > 0 else 0
            }
        finally:
            conn.close()

    def get_heatmap(self) -> List[List[int]]:
        conn = self.db_manager.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    CAST(strftime('%w', timestamp) AS INTEGER) as day,
                    CAST(strftime('%H', timestamp) AS INTEGER) as hour,
                    COUNT(*) as count
                FROM analytics_events
                WHERE timestamp >= DATE('now', '-30 days')
                GROUP BY day, hour
            """)
            data = cursor.fetchall()
            heatmap = [[0]*24 for _ in range(7)]
            for day, hour, count in data:
                heatmap[day][hour] = count
            return heatmap
        finally:
            conn.close()
