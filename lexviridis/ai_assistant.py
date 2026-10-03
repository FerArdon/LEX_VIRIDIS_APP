import logging
import re
import unicodedata

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

# Si la pregunta es sobre multas, tambien se busca el regimen de multas y sanciones administrativas del mismo tema
PALABRAS_MULTA = {"multa", "multas", "sancion", "sanción", "sanciones", "penalidad"}
TEMAS = {
    **dict.fromkeys(
        ("tala", "talar", "madera", "bosque", "bosques", "forestal", "forestales", "aprovechamiento"), "forestal"
    ),
    **dict.fromkeys(("incendio", "incendios", "quema"), "forestal"),
    **dict.fromkeys(("agua", "aguas", "vertido", "vertidos"), "aguas"),
    **dict.fromkeys(("pesca", "acuicultura"), "pesca"),
    **dict.fromkeys(("fauna", "caza", "vida", "silvestre"), "silvestre"),
}

MAX_FUENTES = 8
MAX_CHARS_POR_FUENTE = 1800

SIN_FUENTES = (
    "No encontré en el compendio disposiciones que respondan a tu consulta, así que prefiero no "
    "contestar de memoria: podría citarte artículos que no existen.\n\n"
    "Prueba con términos más específicos, por ejemplo «multa tala ilegal» o «licencia ambiental requisitos»."
)


def _huella(texto: str) -> str:
    """Identifica un articulo copiado en varios documentos (ignora acentos, mayusculas y el encabezado 'ARTICULO N')."""
    t = unicodedata.normalize("NFD", str(texto).lower())
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    t = re.sub(r"^\s*articulo\s*\d+[\w-]*\s*[.\-:]*\s*", "", t)
    return re.sub(r"[^a-z0-9]+", " ", t).strip()[:100]


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

    @classmethod
    def _consultas(cls, pregunta: str) -> list[str]:
        """La consulta completa y versiones con una palabra menos.

        Pedir TODAS las palabras deja fuera articulos clave que no repiten alguna (p. ej. "multa tala ilegal"
        no encuentra el articulo de multas administrativas porque no dice "ilegal").
        """
        completa = cls._consulta_de_busqueda(pregunta)
        palabras = completa.split()
        consultas = [completa]
        if 3 <= len(palabras) <= 6:
            consultas += [" ".join(palabras[:i] + palabras[i + 1 :]) for i in range(len(palabras))]
        if PALABRAS_MULTA & set(palabras):
            tema = next((TEMAS[p] for p in palabras if p in TEMAS), None)
            if tema:
                consultas.append(f"multas sanciones administrativas {tema}")
        return list(dict.fromkeys(consultas))

    def _recuperar_fuentes(self, pregunta: str) -> list[dict]:
        """Busca en el compendio y devuelve los articulos COMPLETOS (no solo un fragmento)."""
        # Una lista de candidatos por consulta; se reparten los cupos por turnos para que ninguna acapare
        listas = [self.engine.search_safe(q, page_size=MAX_FUENTES * 3).results for q in self._consultas(pregunta)]
        candidatos = [lista[i] for i in range(MAX_FUENTES * 3) for lista in listas if i < len(lista)]
        fuentes = []
        huellas: dict[str, dict] = {}
        ids_vistos: set = set()
        for doc in candidatos:
            if len(fuentes) >= MAX_FUENTES:
                break
            if not doc.get("id") or doc["id"] in ids_vistos:
                continue
            ids_vistos.add(doc["id"])
            articulo = self.engine.get_article_by_id(doc["id"])
            if articulo and articulo.get("contenido"):
                huella = _huella(articulo["contenido"])
                if huella in huellas:  # copia de un articulo ya incluido: no ocupa cupo
                    huellas[huella]["also_in"].append(articulo["norma_titulo"])
                    continue
                # Se conserva el formato de resultado de busqueda (la interfaz lo usa) y se agrega el texto completo
                fuente = {
                    **doc,
                    "contenido_completo": articulo["contenido"],
                    "norma_titulo": articulo["norma_titulo"],
                    "numero_articulo": articulo["numero_articulo"],
                    "also_in": [],
                }
                huellas[huella] = fuente
                fuentes.append(fuente)
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
        # Un bloque puede traer varios articulos seguidos (p. ej. el 172 con el 173 pegado): tambien cuentan
        for f in fuentes:
            for n in re.findall(r"ART[ÍI]CULO\s*(\d+(?:-[A-Za-z])?)", str(f["contenido_completo"]), re.IGNORECASE):
                presentes.add(n.upper())
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
