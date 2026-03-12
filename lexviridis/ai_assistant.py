import re


class LegalAIAssistant:
    """Asistente legal con RAG (Retrieval-Augmented Generation)."""

    def __init__(self, engine, gemini_client):
        self.engine = engine
        self.gemini = gemini_client
        self.history = []

    def answer_question(self, question: str) -> dict:
        """Responde una consulta legal usando contexto de la base de datos."""
        import logging

        logger = logging.getLogger(__name__)
        logger.info(f"IA: Procesando pregunta: {question}")

        # 1. Obtener contexto relevante
        results = self.engine.search_safe(question, page_size=5)
        logger.info(f"IA: Se encontraron {len(results.results)} documentos de contexto")
        context_docs = results.results

        # 2. Construir Prompt RAG
        context = ""
        for doc in context_docs:
            context += f"DOCUMENTO: {doc['file']}\n"
            context += f"CONTENIDO: {doc['context']}\n"  # En una impl real obtendríamos el texto completo
            context += "---\n"

        # 3. Incluir historial (últimos 3 mensajes)
        conv_history = "\n".join([f"{m['role'].upper()}: {m['content']}" for m in self.history[-3:]])

        prompt = f"""
Eres un asistente legal experto en Derecho Ambiental de Honduras (LEX VIRIDIS).
Tu objetivo es responder consultas con precisión citando artículos específicos.

HISTORIAL DE CONVERSACIÓN:
{conv_history}

CONTEXTO LEGAL RELEVANTE:
{context}

PREGUNTA: {question}

INSTRUCCIONES:
1. Responde basándote exclusivamente en el contexto y tus conocimientos del derecho hondureño.
2. Si la respuesta está en el contexto, CITA el artículo y la ley de forma explícita, ej: [Art. 10, Ley General del Ambiente].
3. Si no encuentras la respuesta exacta, indícalo pero ofrece orientación general basada en principios legales.
4. Usa un tono profesional, claro y pedagógico.
5. Sugiere 2 preguntas de seguimiento al final.

RESPUESTA:
"""
        # 4. Generar respuesta
        try:
            response_text = self.gemini.consultar(prompt)
        except Exception as e:
            response_text = f"Error al consultar la IA: {str(e)}"

        # 5. Extraer citas y fuentes
        citations = re.findall(r"\[Art\..*?\]", response_text)

        # Guardar en historial
        self.history.append({"role": "user", "content": question})
        self.history.append({"role": "assistant", "content": response_text})

        return {
            "answer": response_text,
            "sources": context_docs,
            "citations": citations,
            "followups": self._extract_followups(response_text),
        }

    def _extract_followups(self, text: str) -> list[str]:
        # Simple heurística para extraer preguntas de seguimiento si se incluyeron
        lines = text.split("\n")
        return [l.strip() for l in lines[-3:] if "?" in l]
