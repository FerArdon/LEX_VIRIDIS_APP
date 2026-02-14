
import json
import random
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Optional
import sqlite3

@dataclass
class Flashcard:
    id: Optional[int]
    pregunta: str
    respuesta: str
    categoria: str
    dificultad: int
    veces_vista: int = 0
    veces_correcta: int = 0
    ultima_revision: Optional[datetime] = None
    proxima_revision: Optional[datetime] = None

class StudyManager:
    """Gestor del sistema de estudio (Flashcards y Repetición Espaciada)."""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager

    def save_flashcard(self, user_id: int, fc: Flashcard):
        conn = self.db_manager.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO flashcards (user_id, pregunta, respuesta, categoria, dificultad)
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, fc.pregunta, fc.respuesta, fc.categoria, fc.dificultad))
            conn.commit()
        finally:
            conn.close()

    def get_due_flashcards(self, user_id: int, limit: int = 20) -> List[Flashcard]:
        conn = self.db_manager.get_connection()
        try:
            cursor = conn.cursor()
            # Seleccionar pendientes o nuevas
            cursor.execute("""
                SELECT id, pregunta, respuesta, categoria, dificultad, veces_vista, veces_correcta, ultima_revision, proxima_revision
                FROM flashcards
                WHERE user_id = ? 
                AND (proxima_revision IS NULL OR proxima_revision <= CURRENT_TIMESTAMP)
                ORDER BY RANDOM()
                LIMIT ?
            """, (user_id, limit))
            rows = cursor.fetchall()
            return [Flashcard(
                id=r[0], pregunta=r[1], respuesta=r[2], categoria=r[3], 
                dificultad=r[4], veces_vista=r[5], veces_correcta=r[6],
                ultima_revision=datetime.fromisoformat(r[7]) if r[7] else None,
                proxima_revision=datetime.fromisoformat(r[8]) if r[8] else None
            ) for r in rows]
        finally:
            conn.close()

    def delete_all_flashcards(self, user_id: int):
        """Elimina todas las flashcards y el progreso del usuario."""
        conn = self.db_manager.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM flashcards WHERE user_id = ?", (user_id,))
            conn.commit()
        finally:
            conn.close()

    def update_flashcard_stats(self, fc_id: int, correct: bool):
        """Implementación simple del algoritmo SM-2 para repetición espaciada."""
        conn = self.db_manager.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT veces_correcta, veces_vista FROM flashcards WHERE id = ?", (fc_id,))
            row = cursor.fetchone()
            if not row: return
            
            veces_correcta, veces_vista = row
            veces_vista += 1
            if correct:
                veces_correcta += 1
                # Algoritmo de intervalo simple
                days = (veces_correcta * 2) if veces_correcta > 1 else 1
            else:
                days = 1 # Repetir mañana
            
            proxima = datetime.now() + timedelta(days=days)
            cursor.execute("""
                UPDATE flashcards 
                SET veces_vista = ?, veces_correcta = ?, ultima_revision = CURRENT_TIMESTAMP, proxima_revision = ?
                WHERE id = ?
            """, (veces_vista, veces_correcta, proxima.isoformat(), fc_id))
            conn.commit()
        finally:
            conn.close()

    def generate_flashcards_from_text(self, text: str, category: str, ai_client=None) -> List[Flashcard]:
        """Generador de flashcards (Híbrido: AI + Heurística)."""
        cards = []
        
        # 1. Intentar generación con IA si está disponible
        if ai_client and ai_client.check_connection():
            try:
                prompt = f"""
                Actúa como un profesor de derecho experto.
                Analiza el siguiente texto legal de Honduras y genera 3 preguntas de estudio clave (Flashcards).
                
                TEXTO: "{text[:1500]}"
                
                FORMATO DE RESPUESTA (Solo JSON):
                [
                    {{"pregunta": "¿Qué define el artículo X?", "respuesta": "Define Y como..."}},
                    ...
                ]
                
                Las preguntas deben ser conceptuales y las respuestas precisas.
                """
                response = ai_client.consultar(prompt)
                
                # Limpiar markdown de código si existe
                response = response.replace('```json', '').replace('```', '').strip()
                
                data = json.loads(response)
                for item in data:
                    cards.append(Flashcard(
                        None, 
                        item.get('pregunta', 'Pregunta'), 
                        item.get('respuesta', 'Respuesta'), 
                        category, 
                        2
                    ))
                
                if cards: return cards

            except Exception as e:
                print(f"Error generando cards con IA: {e}")
                # Fallback a heurística

        # 2. Fallback: Generador heurístico (Regex)
        import re
        # Buscar definiciones: "X es Y" o "Se entiende por X..."
        defs = re.findall(r'([A-Z][^.]{2,40}?)\s+es\s+([^.]{5,200})', text)
        for term, desc in defs:
            cards.append(Flashcard(None, f"¿Qué es {term.strip()}?", desc.strip(), category, 2))
        
        # Si no hay mucho, crear una general del párrafo
        if not cards and len(text) > 50:
            cards.append(Flashcard(None, "¿De qué trata este apartado?", text[:100] + "...", category, 3))
        
        return cards

class QuizEngine:
    """Motor de cuestionarios dinámicos."""
    
    @staticmethod
    def generate_quiz(articulo: dict) -> List[dict]:
        """Genera un mini-quiz de un artículo."""
        options = [
            articulo['contenido'][:100] + "...",
            "Regula las sanciones penales de tráfico",
            "Establece el presupuesto nacional",
            "Define la estructura del sistema judicial"
        ]
        correct = options[0]
        random.shuffle(options)
        
        return {
            'pregunta': f"¿Cuál es el propósito del Artículo {articulo.get('numero_articulo', '')}?",
            'opciones': options,
            'correcta_idx': options.index(correct),
            'explicacion': articulo['contenido']
        }
