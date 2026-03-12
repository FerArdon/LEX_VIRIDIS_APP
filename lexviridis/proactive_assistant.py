import flet as ft


class UserBehaviorAnalyzer:
    """Analiza el comportamiento del usuario para personalización."""

    def __init__(self, db_manager):
        self.db_manager = db_manager

    def analyze_search_patterns(self, user_id: int) -> dict:
        conn = self.db_manager.get_connection()
        try:
            cursor = conn.cursor()
            # Búsquedas más frecuentes (extraer 'query' del JSON en properties)
            cursor.execute(
                """
                SELECT json_extract(properties, '$.query') as query, COUNT(*) as frequency
                FROM analytics_events
                WHERE user_id = ? AND event_type = 'search_executed'
                  AND json_extract(properties, '$.query') IS NOT NULL
                GROUP BY json_extract(properties, '$.query')
                ORDER BY frequency DESC
                LIMIT 10
            """,
                (user_id,),
            )
            patterns = cursor.fetchall()

            # Categorías de interés
            categories = {}
            for row in patterns:
                query = row[0] if row[0] else ""
                freq = row[1]
                cat = self._classify_query(query)
                categories[cat] = categories.get(cat, 0) + freq

            return {"frequent_queries": [(row[0], row[1]) for row in patterns], "interest_categories": categories}
        except Exception:
            # Si hay error (ej. tabla vacía), devolver patrones vacíos
            return {"frequent_queries": [], "interest_categories": {}}
        finally:
            conn.close()

    def _classify_query(self, query: str) -> str:
        keywords = {
            "forestal": ["bosque", "tala", "forestal", "árbol", "madera"],
            "agua": ["agua", "río", "cuenca", "hídrico"],
            "penal": ["delito", "multa", "sanción", "pena"],
            "licencia": ["licencia", "permiso", "autorización"],
            "protección": ["área protegida", "parque", "reserva"],
        }
        q = query.lower()
        for cat, terms in keywords.items():
            if any(t in q for t in terms):
                return cat
        return "general"


class ProactiveSuggestions:
    """Genera sugerencias proactivas basadas en análisis."""

    def __init__(self, analyzer):
        self.analyzer = analyzer

    def get_suggestions(self, user_id: int, context: dict = None) -> list[dict]:
        patterns = self.analyzer.analyze_search_patterns(user_id)
        suggestions = []

        # Sugerencia: Búsqueda frecuente
        if patterns["frequent_queries"]:
            top_q = patterns["frequent_queries"][0][0]
            suggestions.append(
                {
                    "type": "save_search",
                    "title": "Acceso Rápido",
                    "message": f'¿Quieres guardar "{top_q}" como búsqueda rápida?',
                    "data": top_q,
                    "priority": 5,
                }
            )

        # Sugerencia: Categoría dominante
        cats = patterns["interest_categories"]
        if cats:
            top_cat = max(cats, key=cats.get)
            if top_cat != "general":
                suggestions.append(
                    {
                        "type": "new_legislation",
                        "title": "Área de Interés",
                        "message": f"Hemos detectado interés en temas de {top_cat}. ¿Deseas ver novedades?",
                        "data": top_cat,
                        "priority": 8,
                    }
                )

        return sorted(suggestions, key=lambda x: x["priority"], reverse=True)[:3]


class SmartShortcuts:
    """Genera atajos inteligentes."""

    @staticmethod
    def get_shortcuts(user_id: int, analyzer) -> list[dict]:
        patterns = analyzer.analyze_search_patterns(user_id)
        shortcuts = []
        for q, _ in patterns["frequent_queries"][:4]:
            shortcuts.append({"label": q, "icon": ft.Icons.SEARCH, "action": q})
        return shortcuts
