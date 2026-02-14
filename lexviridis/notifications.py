
from datetime import datetime
from typing import List, Optional, Dict
import json

class NotificationType:
    NUEVA_LEY = "nueva_ley"
    MODIFICACION = "modificacion"
    DEROGACION = "derogacion"
    RECORDATORIO = "recordatorio"
    SISTEMA = "sistema"

class NotificationManager:
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.listeners = []

    def send_notification(self, tipo: str, titulo: str, mensaje: str, data: Dict = None, url: str = None):
        conn = self.db_manager.get_connection()
        try:
            data_str = json.dumps(data) if data else None
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO notificaciones (tipo, titulo, mensaje, data, accion_url)
                VALUES (?, ?, ?, ?, ?)
            """, (tipo, titulo, mensaje, data_str, url))
            notif_id = cursor.lastrowid
            conn.commit()
            
            # Notificar a listeners activos
            notif = {
                "id": notif_id,
                "tipo": tipo,
                "titulo": titulo,
                "mensaje": mensaje,
                "data": data,
                "fecha": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "leida": False,
                "url": url
            }
            for listener in self.listeners:
                listener(notif)
        finally:
            conn.close()

    def get_unread(self) -> List[Dict]:
        conn = self.db_manager.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM notificaciones WHERE leida = 0 ORDER BY fecha DESC")
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def mark_as_read(self, notif_id: int):
        conn = self.db_manager.get_connection()
        try:
            conn.execute("UPDATE notificaciones SET leida = 1 WHERE id = ?", (notif_id,))
            conn.commit()
        finally:
            conn.close()

    def subscribe(self, callback):
        self.listeners.append(callback)

    def create_reminder(self, titulo: str, mensaje: str, fecha_hora: datetime):
        import threading
        import time
        
        def _wait_and_send():
            delay = (fecha_hora - datetime.now()).total_seconds()
            if delay > 0:
                time.sleep(delay)
                self.send_notification(NotificationType.RECORDATORIO, titulo, mensaje)
        
        threading.Thread(target=_wait_and_send, daemon=True).start()
