import logging
import re

logger = logging.getLogger(__name__)

# Palabras de relleno y de pregunta que no ayudan a encontrar articulos
STOPWORDS = {
    "cual",
    "cuál",
    "cuales",
    "cuáles",
    "que",
    "qué",
    "quien",
    "quién",
    "quienes",
    "quiénes",
    "como",
    "cómo",
    "cuando",
    "cuándo",
    "donde",
    "dónde",
    "cuanto",
    "cuánto",
    "cuantos",
    "cuántos",
    "por",
    "para",
    "con",
    "sin",
    "del",
    "los",
    "las",
    "una",
    "uno",
    "unos",
    "unas",
    "son",
    "hay",
    "debe",
    "deben",
    "puede",
    "pueden",
    "existe",
    "existen",
    "tiene",
    "tienen",
    "sobre",
    "ante",
    "entre",
    "este",
    "esta",
    "esto",
    "estos",
    "estas",
    "ese",
    "esa",
    "eso",
    "ser",
    "fue",
    "era",
    "mas",
    "más",
    "muy",
    "también",
    "hondureño",
    "honduras",
}

MAX_FUENTES = 5
MAX_CHARS_POR_FUENTE = 1800

SIN_FUENTES = (
    "No encontré en el compendio disposiciones que respondan a tu consulta, así que prefiero no "
    "contestar de memoria: podría citarte artículos que no existen.\n\n"
    "Prueba con términos más específicos, por ejemplo «multa tala ilegal» o «licencia ambiental requisitos»."
)


def _etiqueta(numero) -> str:
    numero = str(numero or "").strip()
    return f"Art. {numero}" if numero[:1].isdigit() else (numero or "Art.")


class LegalAIAssistant:
    """Asistente legal con RAG (Retrieval-Augmented Generation)."""

    def __init__(self, engine, gemini_client):
        self.engine = engine
        self.gemini = gemini_client
        self.history = []

    @staticmethod
    def _consulta_de_busqueda(pregunta: str) -> str:
        """Convierte la pregunta en palabras clave (sin signos ni palabras de relleno)."""
        palabras = [w for w in re.findall(r"\w+", pregunta.lower()) if len(w) > 2 and w not in STOPWORDS]
        return " ".join(palabras[:8]) or " ".join(re.findall(r"\w+", pregunta))

    def _recuperar_fuentes(self, pregunta: str) -> list[dict]:
        """Busca en el compendio y devuelve los articulos COMPLETOS (no solo un fragmento)."""
        resultado = self.engine.search_safe(self._consulta_de_busqueda(pregunta), page_size=MAX_FUENTES)
        fuentes = []
        for doc in resultado.results:
            articulo = self.engine.get_article_by_id(doc["id"]) if doc.get("id") else None
            if articulo and articulo.get("contenido"):
                # Se conserva el formato de resultado de busqueda (la interfaz lo usa) y se agrega el texto completo
                fuentes.append(
                    {
                        **doc,
                        "contenido_completo": articulo["contenido"],
                        "norma_titulo": articulo["norma_titulo"],
                        "numero_articulo": articulo["numero_articulo"],
                    }
                )
        return fuentes

    @staticmethod
    def _armar_contexto(fuentes: list[dict]) -> str:
        bloques = []
        for i, f in enumerate(fuentes, 1):
            texto = " ".join(str(f["contenido_completo"]).split())[:MAX_CHARS_POR_FUENTE]
            bloques.append(
                f"FUENTE {i}: {f['norma_titulo']} — {_etiqueta(f['numero_articulo'])} (pág. {f.get('page') or 1})\n"
                f"TEXTO: {texto}"
            )
        return "\n---\n".join(bloques)

    @staticmethod
    def _citas_no_verificadas(citas: list[str], fuentes: list[dict]) -> list[str]:
        """Citas del tipo [Art. 168, ...] cuyo numero de articulo no aparece en ninguna fuente."""
        presentes = {str(f["numero_articulo"]).strip().upper() for f in fuentes}
        dudosas = []
        for cita in citas:
            m = re.search(r"Art(?:\.|ículo)?\s*(\d+(?:\s*-\s*[A-Za-z])?)", cita, re.IGNORECASE)
            if m and m.group(1).replace(" ", "").upper() not in presentes:
                dudosas.append(cita)
        return dudosas

    def answer_question(self, question: str) -> dict:
        """Responde una consulta legal usando SOLO los articulos recuperados del compendio."""
        logger.info(f"IA: Procesando pregunta: {question}")

        # 1. Recuperar articulos relevantes (texto completo)
        fuentes = self._recuperar_fuentes(question)
        logger.info(f"IA: {len(fuentes)} fuentes recuperadas")

        # Sin fuentes no se consulta a la IA: contestaria de memoria e inventaria citas.
        if not fuentes:
            return {"answer": SIN_FUENTES, "sources": [], "citations": [], "followups": []}

        # 2. Construir prompt RAG
        contexto = self._armar_contexto(fuentes)
        conv_history = "\n".join([f"{m['role'].upper()}: {m['content']}" for m in self.history[-3:]])

        prompt = f"""
Eres un asistente legal experto en Derecho Ambiental de Honduras (LEX VIRIDIS).
Respondes consultas citando con precisión, y SOLO con base en las FUENTES que se te entregan.

HISTORIAL DE CONVERSACIÓN:
{conv_history}

FUENTES (texto de la legislación recuperado del compendio):
{contexto}

PREGUNTA: {question}

INSTRUCCIONES:
1. Responde exclusivamente con lo que dicen las FUENTES. No uses conocimiento propio para completar datos.
2. Cita únicamente artículos que aparezcan en las FUENTES, copiando número y norma tal como figuran, ej: [Art. 166, Ley Forestal]. Nunca inventes artículos, penas, montos ni plazos.
3. Si las FUENTES no responden la pregunta, o solo en parte, dilo claramente e indica qué falta; no lo rellenes.
4. Si dos fuentes parecen contradecirse (por ejemplo, distintas versiones o numeración de una misma ley), señálalo.
5. Tono profesional, claro y pedagógico.
6. Termina sugiriendo 2 preguntas de seguimiento.

RESPUESTA:
"""
        # 3. Generar respuesta
        try:
            response_text = self.gemini.consultar(prompt)
        except Exception as e:
            response_text = f"Error al consultar la IA: {str(e)}"

        # 4. Extraer citas y avisar de las que no estan respaldadas por las fuentes
        citations = re.findall(r"\[Art\..*?\]", response_text)
        dudosas = self._citas_no_verificadas(citations, fuentes)
        if dudosas:
            response_text += (
                "\n\n⚠️ Verifica estas citas: su número de artículo no aparece en las fuentes consultadas: "
                + "; ".join(dudosas)
            )

        # Guardar en historial
        self.history.append({"role": "user", "content": question})
        self.history.append({"role": "assistant", "content": response_text})

        return {
            "answer": response_text,
            "sources": fuentes,
            "citations": citations,
            "followups": self._extract_followups(response_text),
        }

    def _extract_followups(self, text: str) -> list[str]:
        # Simple heurística para extraer preguntas de seguimiento si se incluyeron
        lines = text.split("\n")
        return [l.strip() for l in lines[-3:] if "?" in l]
