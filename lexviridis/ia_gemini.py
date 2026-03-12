"""
Módulo de integración con Google Gemini AI para LEX VIRIDIS.

Este módulo reemplaza la IA local (Ollama) por una integración en la nube con Gemini,
incluyendo un generador de prompts especializado para normativa ambiental.
"""

import logging
import os
import socket

import google.generativeai as genai

# Configurar logger
logger = logging.getLogger(__name__)


class PromptGenerator:
    """Generador de prompts especializado para el ámbito legal ambiental."""

    @staticmethod
    def generar_resumen(texto: str) -> str:
        """Genera un prompt para resumir texto legal."""
        return f"""
        Actúa como un experto en derecho ambiental de Honduras.
        Analiza el siguiente texto legal extraído del 'COMPENDIO DE LEYES FEMA':

        "{texto}"

        Genera un resumen ejecutivo que destaque:
        1. El objeto principal de la norma.
        2. Las obligaciones o prohibiciones clave.
        3. Las sanciones mencionadas (si las hay).

        Mantén un tono formal y jurídico pero claro.
        """

    @staticmethod
    def generar_explicacion(texto: str) -> str:
        """Genera un prompt para explicar texto legal en lenguaje sencillo."""
        return f"""
        Actúa como un asistente legal pedagógico.
        Explica el siguiente fragmento jurídico a un ciudadano sin formación legal:

        "{texto}"

        Usa analogías si es necesario, pero mantén la precisión técnica.
        Evita la jerga legal innecesaria.
        """

    @staticmethod
    def generar_analisis_caso(consulta: str, contexto_legal: list[str]) -> str:
        """
        Genera un prompt para analizar una consulta específica basada en leyes encontradas.
        """
        contexto_str = "\n---\n".join(contexto_legal[:3])  # Usar los top 3 fragmentos

        return f"""
        CONTEXTO LEGAL (Normativa Ambiental de Honduras - FEMA):
        {contexto_str}

        CONSULTA DEL USUARIO:
        "{consulta}"

        TAREA:
        Basado ÚNICAMENTE en el contexto legal proporcionado arriba, responde a la consulta del usuario.
        Si la información no está en el contexto, indícalo claramente.
        Cita la norma específica (nombre del archivo o artículo) cuando hagas afirmaciones.
        """


class GeminiClient:
    """Cliente wrapper para Google Gemini."""

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.http_client = None
        self.model = None
        self._setup()

    def _setup(self):
        """Configura el cliente de Gemini e intenta conectar con un modelo válido."""
        if not self.api_key:
            logger.warning("No se encontró GEMINI_API_KEY. La IA estará deshabilitada.")
            return

        try:
            genai.configure(api_key=self.api_key)

            # Lista de modelos candidatos en orden de preferencia
            candidates = ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-pro", "gemini-1.0-pro"]

            self.model = None

            # Estrategia: Listar modelos disponibles para esta API Key
            try:
                # Obtener lista, filtrando los que soportan generateContent
                all_models = list(genai.list_models())
                available = []
                for m in all_models:
                    if "generateContent" in m.supported_generation_methods:
                        name = m.name.replace("models/", "")
                        available.append(name)

                logger.info(f"Modelos disponibles: {available}")

                # 1. Buscar coincidencia exacta con candidatos
                for cand in candidates:
                    if cand in available:
                        logger.info(f"✅ Usando modelo: {cand}")
                        self.model = genai.GenerativeModel(cand)
                        return

                # 2. Si no, buscar cualquier 'gemini'
                for m in available:
                    if "gemini" in m:
                        logger.info(f"⚠️ Usando modelo alternativo: {m}")
                        self.model = genai.GenerativeModel(m)
                        return

                # 3. Fallback ciego
                logger.warning(
                    "No se encontraron modelos compatibles en la lista. Intentando 'gemini-1.5-flash' por defecto."
                )
                self.model = genai.GenerativeModel("gemini-1.5-flash")

            except Exception as e:
                logger.error(f"Error listando modelos: {e}. Usando fallback 'gemini-pro'.")
                self.model = genai.GenerativeModel("gemini-pro")

        except Exception as e:
            logger.error(f"Error configurando Gemini: {e}")
            self.model = None

    def check_connection(self) -> bool:
        """Verifica si hay conexión a internet y acceso a Gemini."""
        try:
            # Check simple de internet
            socket.create_connection(("www.google.com", 80), timeout=3)
            return True if self.model else False
        except OSError:
            return False

    def consultar(self, prompt: str) -> str:
        """
        Envía una consulta a Gemini.

        Args:
            prompt: El texto del prompt a enviar.

        Returns:
            La respuesta de texto generada.
        """
        if not self.check_connection():
            return "⚠️ No hay conexión a internet o la API key no es válida. La IA no está disponible."

        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            error_str = str(e)
            logger.error(f"Error consultando Gemini: {error_str}")

            # Manejo específico de errores comunes
            if "429" in error_str or "quota" in error_str.lower():
                return "⚠️ Has excedido tu cuota gratuita de uso de IA (Rate Limit). Por favor espera un minuto antes de intentar nuevamente."

            if "403" in error_str or "key" in error_str.lower():
                return "⚠️ Error de autenticación. Verifica que tu API Key sea correcta en Configuración."

            return f"⚠️ Error detallado con Gemini: {error_str}"

    def set_api_key(self, key: str):
        """Permite configurar la API key en tiempo de ejecución."""
        self.api_key = key
        self._setup()
