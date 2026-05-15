import google.generativeai as genai
import os
import time
import logging
from typing import List, Dict, Tuple, Optional
import re
from pathlib import Path

# Configurar logger
logger = logging.getLogger("lexviridis.ai")

class ExecutionTimer:
    """Mide tiempo de ejecución para optimización."""
    def __init__(self, name: str):
        self.name = name
        self.start_time = None

    def __enter__(self):
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        elapsed = time.perf_counter() - self.start_time
        logger.info(f"[TIMER] {self.name}: {elapsed:.4f}s")

class GeminiClient:
    """Cliente wrapper para Google Gemini."""
    def __init__(self, api_key: str = None, model_name: str = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model_name = model_name or "gemini-2.0-flash"
        self.model = None
        if self.api_key:
            try:
                genai.configure(api_key=self.api_key)
                self.model = genai.GenerativeModel(self.model_name)
            except Exception as e:
                logger.error(f"Error configurando Gemini: {e}")

    def consultar(self, prompt: str) -> str:
        if not self.model:
            return "IA no configurada (falta API Key). Ve a Configuración para ingresar tu clave Gemini."
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            err_str = str(e)
            logger.error(f"Error en consulta Gemini: {err_str[:200]}")
            if "429" in err_str or "quota" in err_str.lower() or "rate" in err_str.lower():
                import re
                retry_match = re.search(r'retry[^\d]*(\d+)', err_str, re.IGNORECASE)
                wait = retry_match.group(1) if retry_match else "unos minutos"
                return (
                    f"⚠ Límite de cuota de API alcanzado.\n\n"
                    f"Tu plan gratuito de Gemini ha agotado las solicitudes por hoy. "
                    f"Intenta de nuevo en {wait} segundos, o considera actualizar tu plan en "
                    f"https://ai.dev/rate-limit"
                )
            if "API_KEY" in err_str or "api key" in err_str.lower() or "403" in err_str:
                return "⚠ Clave de API inválida. Verifica tu API Key en Configuración."
            return f"⚠ Error al consultar la IA: {err_str[:120]}"

class GroqClient:
    """Cliente wrapper para Groq (Llama, Mixtral, Gemma).
    Usa el SDK oficial si está disponible; cae en HTTP directo (urllib stdlib) si no.
    """
    _API_URL = "https://api.groq.com/openai/v1/chat/completions"

    def __init__(self, api_key: str = None, model_name: str = None):
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        self.model_name = model_name or "llama-3.3-70b-versatile"
        self.client = None
        self._use_http = False

        if self.api_key:
            try:
                from groq import Groq
                self.client = Groq(api_key=self.api_key)
                logger.info("GroqClient: usando SDK oficial")
            except Exception as e:
                logger.warning(f"Groq SDK no disponible ({e}), usando HTTP directo")
                self._use_http = True

    def _consultar_http(self, prompt: str) -> str:
        """Fallback: llama a la API de Groq mediante urllib (stdlib, siempre disponible)."""
        import urllib.request
        import json as _json

        payload = _json.dumps({
            "model": self.model_name,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 1024,
        }).encode("utf-8")

        req = urllib.request.Request(
            self._API_URL,
            data=payload,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=45) as resp:
                result = _json.loads(resp.read().decode("utf-8"))
                return result["choices"][0]["message"]["content"]
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="ignore")
            logger.error(f"Groq HTTP {e.code}: {body[:200]}")
            if e.code == 401:
                return "⚠ Clave de API de Groq inválida. Verifica tu API Key en Configuración."
            if e.code == 429:
                return "⚠ Límite de cuota de Groq alcanzado. Intenta de nuevo en unos momentos."
            return f"⚠ Error al consultar Groq ({e.code}): {body[:100]}"
        except Exception as e:
            logger.error(f"Error HTTP Groq: {e}")
            return f"⚠ Error al consultar Groq: {str(e)[:120]}"

    def consultar(self, prompt: str) -> str:
        if not self.api_key:
            return "IA no configurada (falta API Key). Ve a Configuración para ingresar tu clave de Groq."
        if self._use_http:
            return self._consultar_http(prompt)
        if not self.client:
            return "IA no configurada (falta API Key). Ve a Configuración para ingresar tu clave de Groq."
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1024,
            )
            return response.choices[0].message.content
        except Exception as e:
            err_str = str(e)
            logger.error(f"Error en consulta Groq: {err_str[:200]}")
            if "429" in err_str or "rate" in err_str.lower():
                return "⚠ Límite de cuota de Groq alcanzado. Intenta de nuevo en unos momentos."
            if "401" in err_str or "authentication" in err_str.lower() or "api_key" in err_str.lower() or "invalid_api_key" in err_str.lower():
                return "⚠ Clave de API de Groq inválida. Verifica tu API Key en Configuración."
            return f"⚠ Error al consultar Groq: {err_str[:120]}"

class LegalAIAssistant:
    """Asistente legal con RAG (Retrieval-Augmented Generation)."""
    
    def __init__(self, engine, gemini_client):
        self.engine = engine
        self.gemini = gemini_client
        self.history = []

    # Palabras genéricas de preguntas legales que no aportan al buscador
    _QUERY_STOP = {
        'que', 'cual', 'cuales', 'como', 'donde', 'cuando', 'quien', 'quienes',
        'dice', 'diga', 'establece', 'define', 'indica', 'menciona', 'refiere',
        'articulo', 'articulos', 'art', 'ley', 'codigo', 'norma', 'decreto',
        'el', 'la', 'los', 'las', 'un', 'una', 'del', 'de', 'en', 'a', 'por',
        'con', 'para', 'se', 'su', 'es', 'son', 'al', 'lo', 'mas', 'o', 'y',
        'pero', 'sobre', 'ante', 'bajo', 'este', 'esta', 'ese', 'esa', 'mi',
        'hay', 'tiene', 'tienen', 'debe', 'deben', 'puede', 'pueden', 'sido',
        'especificamente', 'especifica', 'especifico', 'hondureno', 'hondurena',
        'honduras', 'segun', 'respecto', 'acerca', 'trata', 'habla', 'relativo',
        'relativa', 'delito', 'infraccion', 'penal', 'civil', 'ambiente',
        # preposiciones y conjunciones no filtradas antes
        'entre', 'hacia', 'desde', 'hasta', 'seran', 'sera', 'siendo',
        'mediante', 'cuanto', 'tanto', 'tal', 'tales', 'dicho', 'dichos',
        'mismo', 'misma', 'mismos', 'mismas', 'todo', 'toda', 'todos', 'todas',
    }

    def _build_search_query(self, question: str) -> str:
        """
        Extrae términos clave de la pregunta para mejorar el retrieval.
        Combina: número de artículo (si hay) + nombre de ley + tema sustantivo.
        """
        import unicodedata

        def normalize(s):
            return unicodedata.normalize('NFD', s).encode('ascii', 'ignore').decode().lower()

        q_norm = normalize(question)

        # 1. Número de artículo explícito
        art_match = re.search(r'art[íi]?culo\.?\s*(\d+)|art\.\s*(\d+)', q_norm)
        art_num = (art_match.group(1) or art_match.group(2)) if art_match else None

        # 2. Nombre de ley / código
        law_keywords = []
        law_patterns = [
            (r'codigo\s+penal',              'codigo penal'),
            (r'codigo\s+civil',              'codigo civil'),
            (r'codigo\s+procesal',           'codigo procesal'),
            (r'codigo\s+de\s+trabajo',       'codigo trabajo'),
            (r'ley\s+general\s+del?\s+amb',  'ley general ambiente'),
            (r'ley\s+forestal',              'ley forestal'),
            (r'ley\s+de\s+pesca',            'ley pesca'),
            (r'ley\s+de\s+aguas?',           'ley agua'),
            (r'ley\s+(general\s+de|de)\s+mineria', 'ley mineria'),
            (r'ley\s+de\s+municipalidades',  'ley municipalidades'),
            (r'ley\s+de\s+biodiversidad',    'ley biodiversidad'),
            (r'ley\s+de\s+ordenamiento',     'ley ordenamiento'),
            (r'reglamento\s+general',        'reglamento general'),
            (r'reglamento\s+(de|del?)\s+ley\s+forestal', 'reglamento ley forestal'),
        ]
        for pattern, keyword in law_patterns:
            if re.search(pattern, q_norm):
                law_keywords.append(keyword)

        # 3. Palabras sustantivas del tema (lo que queda tras filtrar stop words)
        tokens = re.split(r'\s+', re.sub(r'[^\w\s]', ' ', q_norm))
        topic_words = [
            t for t in tokens
            if t and len(t) > 2 and t not in self._QUERY_STOP
        ]

        # Palabras tan genéricas que deben excluirse del query de búsqueda
        # (aparecen en miles de artículos y arruinan el ranking FTS)
        _GENERIC = {
            'distancias', 'distancia', 'minimas', 'minimo', 'minima',
            'proteccion', 'proteger', 'protege', 'establecen', 'establecer',
            'respetarse', 'cumplirse', 'cumplimiento', 'aplicarse', 'aplicar',
            'deben', 'requieren', 'exigen', 'disposiciones', 'disposicion',
            'regulacion', 'regulaciones', 'normas', 'normativa', 'regulan',
            'general', 'generales', 'especial', 'especiales', 'nacional',
        }
        # 3b. Expansión de sinónimos jurídicos específicos por dominio
        #     Cuando el usuario usa terminología coloquial que difiere del lenguaje legal
        _topic_set = set(topic_words)
        _law_str_tmp = ' '.join(law_keywords)
        if 'mineria' in _law_str_tmp or 'minera' in _topic_set:
            expansion = []
            # "fuentes de agua / agua potable" → en ley minería = "zonas productoras"
            if 'agua' in _topic_set or 'fuentes' in _topic_set or 'potable' in _topic_set:
                expansion += ['productoras', 'exclusion']
            # "asentamientos / comunidades / zona urbana" → "exclusion"
            if 'asentamientos' in _topic_set or 'comunidades' in _topic_set:
                if 'exclusion' not in expansion:
                    expansion.append('exclusion')
            # Prepend expansion terms so they rank first in unique_topics
            if expansion:
                topic_words = list(dict.fromkeys(expansion + topic_words))

        # Recalcular filtered DESPUÉS de la expansión de sinónimos
        topic_words_filtered = [t for t in topic_words if t not in _GENERIC]

        # 4. Combinar según estrategia:
        #    - Con número de artículo: "325 codigo penal"   (número + ley)
        #    - Con ley identificada: "mineria" + términos tema (max 4)
        #      → la ley ancla el resultado al documento correcto
        #    - Solo tema sustantivo: términos filtrados (si no se detectó ley)
        if art_num:
            parts = [art_num] + law_keywords
        elif law_keywords and topic_words_filtered:
            # Combinar ley + términos temáticos únicos (sin variantes de law_keywords)
            law_str = ' '.join(law_keywords)
            unique_topics = [t for t in topic_words_filtered if t not in law_str][:5]
            parts = law_keywords + unique_topics
        elif law_keywords:
            parts = law_keywords
        elif topic_words_filtered:
            parts = topic_words_filtered
        else:
            parts = topic_words          # fallback sin filtro genérico

        return ' '.join(parts) if parts else question

    def answer_question(self, question: str) -> Dict:
        """Responde una consulta legal usando contexto de la base de datos."""
        logger.info(f"IA: Procesando pregunta: {question}")

        # Guard temprano fuera del timer para retorno limpio
        if not self.engine:
            logger.error("IA: Error - Motor de búsqueda no inicializado (engine is None)")
            return {
                "answer": "⚠ Error: El motor de búsqueda no está disponible. No puedo consultar la base de datos legal.",
                "sources": [],
                "citations": [],
                "followups": []
            }

        with ExecutionTimer(f"IA Query: {question[:30]}..."):
            # 1. Obtener contexto relevante — búsqueda con términos clave extraídos
            search_query = self._build_search_query(question)
            logger.info(f"IA: Query de búsqueda: '{search_query}'")
            results = self.engine.search_safe(search_query, page_size=6)
            logger.info(f"IA: Se encontraron {len(results.results)} documentos de contexto")
            context_docs = results.results

            # 1b. Búsqueda alternativa con términos cortos/directos de la pregunta
            #     para capturar artículos que el query largo puede haber perdido.
            import unicodedata
            def _norm(s):
                return unicodedata.normalize('NFD', s).encode('ascii', 'ignore').decode().lower()
            q_norm2 = _norm(question)
            short_terms = [w for w in re.split(r'\s+', re.sub(r'[^\w\s]', ' ', q_norm2))
                           if len(w) > 3 and w not in self._QUERY_STOP]
            # Tomar los términos más específicos (los más largos o al final de la pregunta)
            alt_terms = short_terms[-5:] if len(short_terms) > 5 else short_terms
            if alt_terms:
                alt_query = ' '.join(alt_terms)
                alt_results = self.engine.search_safe(alt_query, page_size=4)
                seen_ids = {r['id'] for r in context_docs}
                added = 0
                for r in alt_results.results:
                    if r['id'] not in seen_ids:
                        context_docs.append(r)
                        seen_ids.add(r['id'])
                        added += 1
                if added:
                    logger.info(f"IA: Búsqueda alternativa '{alt_query}' añadió {added} docs")

            # 2. Construir Prompt RAG
            context = ""
            total_chars = 0
            MAX_CONTEXT_CHARS = 12000  # Límite de seguridad para el contexto RAG

            for i, doc in enumerate(context_docs, 1):
                article = self.engine.get_article_by_id(doc['id'])
                full_content = article['contenido'] if article else doc.get('context', '')

                # Truncar artículos individuales si son masivos (> 4000 chars)
                if len(full_content) > 4000:
                    full_content = full_content[:3950] + "... [CONTENIDO TRUNCADO POR LONGITUD]"

                estado = (article.get('estado') or 'VIGENTE') if article else 'VIGENTE'
                doc_name = doc.get('norma_titulo') or doc.get('file', 'Documento sin título')
                art_num  = doc.get('numero_articulo') or doc.get('articulo', '')
                ref = f"Art. {art_num}, {doc_name}" if art_num else doc_name
                estado_tag = f" ⚠ DEROGADA" if estado == 'DEROGADA' else " ✓ VIGENTE"

                doc_text = f"[FUENTE {i}]{estado_tag} — {ref}\n{full_content}\n---\n"

                if total_chars + len(doc_text) > MAX_CONTEXT_CHARS:
                    logger.warning(f"IA: Límite de contexto alcanzado. Omitiendo fuentes restantes.")
                    break

                context += doc_text
                total_chars += len(doc_text)

            if not context.strip():
                context = "(No se encontraron documentos relevantes para esta consulta)"

            # 3. Incluir historial (últimos 3 mensajes)
            conv_history = "\n".join([f"{m['role'].upper()}: {m['content']}" for m in self.history[-3:]])

            prompt = f"""
Eres un asistente legal del sistema LEX VIRIDIS, especializado en legislación ambiental de Honduras.

REGLA FUNDAMENTAL — LEE ESTO ANTES DE RESPONDER:
Responde ÚNICAMENTE con información que aparezca textualmente en el CONTEXTO LEGAL proporcionado.
ESTÁ PROHIBIDO inventar, suponer o citar artículos, leyes o datos que no estén en el contexto.
Si el contexto no contiene la respuesta, responde exactamente: "No encontré información sobre este tema en los documentos disponibles."

ALERTA SOBRE VIGENCIA:
Cada fuente del contexto está marcada con ✓ VIGENTE o ⚠ DEROGADA.
- Si una fuente dice ⚠ DEROGADA: NO la cites como ley aplicable. Puedes mencionarla solo como referencia histórica, indicando claramente que está derogada.
- Si una fuente dice ✓ VIGENTE: puedes citarla con normalidad.
- Si el mismo artículo aparece en una fuente DEROGADA y otra VIGENTE, usa SOLO la VIGENTE.
- Nunca presentes como vigente un artículo marcado como DEROGADA.

HISTORIAL DE CONVERSACIÓN:
{conv_history}

CONTEXTO LEGAL RELEVANTE (estos son los únicos documentos en los que puedes basar tu respuesta):
{context}

PREGUNTA: {question}

GUÍA DE INTERPRETACIÓN JURÍDICA (terminología legal hondureña):
Cuando el usuario use estos términos coloquiales, búscalos en el contexto con los equivalentes legales:
- "distancias mínimas", "área de protección", "zona de amortiguamiento" en minería
  → busca: "Zonas de Exclusión" (Art. 48), "zonas productoras de agua", "áreas de reserva" (Arts. 46-49)
- "moratoria minería a cielo abierto"
  → busca: PCM-020-2022, Decreto Ejecutivo, moratoria, suspensión concesiones
- "daño ambiental minero", "obligaciones empresa minera"
  → busca: "Obligaciones Ambientales" (Art. 78), Plan de Manejo Ambiental, EIA (Art. 50)
- "permiso minero", "concesión", "licencia minera"
  → busca: "Concesión Minera" (Arts. 7, 46), derechos mineros, Dirección General de Minas
- "impacto ambiental", "estudio ambiental" en proyectos
  → busca: EIA, Estudio de Impacto Ambiental (Art. 50), SERNA, Secretaría de Recursos Naturales

INSTRUCCIONES:
1. Usa SOLO la información del CONTEXTO LEGAL de arriba. Nada más.
2. Cuando cites un artículo, debe aparecer literalmente en el contexto. Formato: [Art. X, Nombre de la Ley].
3. Si el contexto no tiene la respuesta, di: "No encontré información sobre este tema en los documentos disponibles." — NO inventes ni completes con conocimiento propio.
4. Tono profesional, claro y directo.
5. Si respondiste con información del contexto, sugiere 2 preguntas de seguimiento al final.

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
                "followups": self._extract_followups(response_text)
            }

    def _extract_followups(self, text: str) -> List[str]:
        # Simple heurística para extraer preguntas de seguimiento si se incluyeron
        lines = text.split("\n")
        return [l.strip() for l in lines[-3:] if "?" in l]
