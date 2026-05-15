"""
LEX VIRIDIS - Vista de Ayuda y Tutorial
Guía completa de uso de la aplicación, con ejemplos reales.
"""

import customtkinter as ctk
from .base_view import BaseView
from ..design_system_ctk import Colors, Typography


SECCIONES = [
    {
        "titulo": "¿Qué es LEX VIRIDIS?",
        "color": Colors.PRIMARY,
        "img": "manual_01.png",
        "pasos": [
            (
                "Plataforma de Gestión Legal Institucional",
                "legislación ambiental, forestal y conexa de Honduras. Permite buscar, "
                "consultar y exportar artículos de leyes, decretos, acuerdos y reglamentos "
                "de forma rápida, incluso sin conexión a internet (salvo el Asistente IA)."
            ),
            (
                "Módulos disponibles",
                "  1. Dashboard     — Estadísticas y actividad reciente\n"
                "  2. Buscador      — Búsqueda en 4 niveles + texto completo en todos los PDFs\n"
                "  3. Asistente IA  — Consultas en lenguaje natural (Groq / Gemini)\n"
                "  4. Biblioteca    — Catálogo de documentos, favoritos, importación\n"
                "  5. Configuración — API Key, licencia, rutas, usuario y contraseña\n"
                "  6. Ayuda         — Esta guía con exportación a PDF"
            ),
            (
                "Caso de Uso 1: Fiscal en Campo",
                "Un fiscal necesita verificar las sanciones aplicables por deforestación "
                "ilegal durante una inspección en sitio.\n\n"
                "Con LEX VIRIDIS, consulta la Ley Forestal en segundos desde su laptop, "
                "sin depender de internet ni cargar documentos físicos."
            ),
            (
                "Caso de Uso 2: Analista Técnico",
                "Un técnico ambiental necesita comparar disposiciones entre el Código Penal "
                "y la Ley General del Ambiente para preparar un informe.\n\n"
                "El Asistente IA extrae y contrasta los artículos relevantes de ambas normas "
                "en una sola consulta, ahorrando horas de revisión manual."
            ),
            (
                "Caso de Uso 3: Formación Profesional",
                "Un técnico nuevo en la institución necesita conocer la normativa ambiental "
                "hondureña para desempeñar su cargo.\n\n"
                "El compendio de 185+ documentos indexados funciona como base de conocimiento "
                "estructurada, con búsqueda inmediata y exportación para capacitación."
            ),
        ],
    },
    {
        "titulo": "🔐  Paso 1 — Activar tu Licencia",
        "color": "#7b1fa2",
        "img": "manual_02.png",
        "pasos": [
            (
                "¿Por qué necesito una licencia?",
                "LEX VIRIDIS es una herramienta institucional. La licencia identifica a tu "
                "institución y habilita el acceso completo a todos los módulos.\n\n"
                "Sin licencia activa, la app muestra la pantalla de activación al iniciar "
                "y no permite navegar a ningún módulo."
            ),
            (
                "Cómo activar la licencia",
                "1. Al iniciar la app por primera vez verás la pantalla de Activación\n"
                "2. Ingresa la clave de licencia proporcionada por el administrador del sistema\n"
                "3. Presiona 'Activar'\n"
                "4. Si la clave es válida, verás el badge verde '✓ Activa' y accederás a la app\n\n"
                "La clave se guarda automáticamente — solo necesitas ingresarla una vez."
            ),
            (
                "Verificar o renovar la licencia",
                "En cualquier momento puedes revisar el estado de tu licencia:\n\n"
                "  1. Ve al menú lateral → Configuración\n"
                "  2. Sección 'Licencia de Uso'\n"
                "  3. Verás: cliente, tipo de licencia y fecha de vencimiento\n\n"
                "Si la licencia está por vencer o ya venció, aparecerá el botón 'Renovar'. "
                "Contacta al administrador para obtener una nueva clave."
            ),
        ],
    },
    {
        "titulo": "🤖  Paso 2 — Configurar la API Key (Asistente IA)",
        "color": "#1d6b3a",
        "img": "manual_03.png",
        "pasos": [
            (
                "Obtener API Key de Groq (Recomendado — Gratis)",
                "1. Abre tu navegador y ve a: https://console.groq.com/keys\n"
                "2. Crea una cuenta gratuita (solo correo, sin tarjeta de crédito)\n"
                "3. Clic en 'Create API Key' → ponle un nombre (ej: LEX VIRIDIS)\n"
                "4. Copia la clave generada — comienza con 'gsk_...'\n\n"
                "Groq es completamente gratuito con ~14,400 consultas/día. "
                "Es la opción recomendada por velocidad y cuota."
            ),
            (
                "Guardar la clave en LEX VIRIDIS",
                "1. Ve al menú lateral → Configuración\n"
                "2. Sección 'Inteligencia Artificial'\n"
                "3. Selecciona 'Groq (Recomendado)' en el selector de proveedor\n"
                "4. Pega tu clave en el campo 'Groq API Key'\n"
                "5. Elige el modelo: llama-3.3-70b-versatile (recomendado)\n"
                "6. Presiona 'Guardar API Key'\n\n"
                "El estado cambiará a '✓ Activo'. A partir de aquí el Asistente IA "
                "está listo para responder consultas legales."
            ),
            (
                "Alternativa: Gemini de Google",
                "Si prefieres usar Google Gemini como respaldo:\n\n"
                "1. Ve a https://aistudio.google.com/ → inicia sesión con tu cuenta Google\n"
                "2. Clic en 'Get API Key' → 'Create API key'\n"
                "3. Copia la clave (comienza con 'AIza...')\n"
                "4. En Configuración → selecciona 'Gemini (Google)' → pega la clave → Guardar\n\n"
                "Puedes tener ambas claves guardadas y alternar entre proveedores "
                "en cualquier momento sin volver a ingresarlas."
            ),
        ],
    },
    {
        "titulo": "🔍  Paso 3 — Buscador Legal — Uso completo",
        "color": Colors.ACCENT_BLUE,
        "img": "manual_04.png",
        "pasos": [
            (
                "Búsqueda por palabra clave",
                "Escribe una o varias palabras y presiona Buscar o Enter.\n\n"
                "Ejemplos válidos:\n"
                "  • incendio\n"
                "  • tala ilegal\n"
                "  • biodiversidad\n"
                "  • licencia ambiental\n"
                "  • rondas forestales\n\n"
                "El sistema buscará en TODOS los documentos de la base de datos: "
                "artículos indexados, texto completo de PDFs y títulos de leyes."
            ),
            (
                "Búsqueda en lenguaje natural (frases completas)",
                "Puedes escribir preguntas como si le hablaras a una persona. "
                "El sistema extrae automáticamente las palabras clave relevantes y descarta "
                "palabras vacías (que, del, el, la, etc.).\n\n"
                "Ejemplos:\n"
                "  • que dice el artículo 325 del código penal\n"
                "  • cuál es la multa por contaminar un río\n"
                "  • qué dice la ley forestal sobre planes de manejo\n"
                "  • cuántos años de prisión por tala de bosque protegido"
            ),
            (
                "Resultados y relevancia",
                "Los resultados se ordenan por relevancia:\n"
                "  • Verde 'LEY ENCONTRADA' → coincide con el título del documento\n"
                "  • Número de relevancia alto → más coincidencias del término en el texto\n"
                "  • Se muestra el fragmento de texto donde aparece el término, con las "
                "    palabras buscadas resaltadas en negrita (**término**)."
            ),
            (
                "Abrir PDF con el término resaltado en amarillo",
                "Botón '📄 Abrir PDF': abre el documento con el término buscado resaltado "
                "en color amarillo en todas las páginas donde aparece — igual que cuando "
                "usas Ctrl+F en un lector PDF pero automático.\n\n"
                "  • Si el término aparece en varias páginas, todas quedan resaltadas\n"
                "  • Si la frase exacta no se encuentra, se resalta cada palabra por separado\n"
                "  • Si no hay coincidencias, se abre el PDF original sin modificar\n"
                "Requiere un lector PDF instalado (Adobe Reader, Microsoft Edge, etc.)."
            ),
            (
                "Ver detalle del artículo",
                "Botón '🔍 Ver Detalle': abre una ventana emergente con el texto completo "
                "del artículo encontrado, opción para abrirlo en PDF, marcarlo como "
                "favorito o exportarlo como TXT."
            ),
            (
                "Marcar como Favorito",
                "Botón '☆ Favorito' en cada resultado. Al presionarlo cambia a '★ Favorito' "
                "(azul). Los favoritos quedan guardados en la base de datos y se pueden ver "
                "en Biblioteca → pestaña ★ Favoritos, donde también puedes agregar notas "
                "personales."
            ),
            (
                "Exportar resultados",
                "Elige el formato en el menú desplegable (PDF / EXCEL / TXT) y presiona "
                "Exportar. Se guarda automáticamente en la carpeta de exportaciones.\n\n"
                "  • PDF  → documento formal con portada y resultados formateados\n"
                "  • EXCEL → hoja de cálculo con columnas: Ley, Artículo, Contenido, Página\n"
                "  • TXT  → texto plano para copiar/pegar"
            ),
            (
                "Sinónimos automáticos",
                "El buscador expande automáticamente los términos con sinónimos legales:\n"
                "  • bosque → forestal, forestales, árbol, monte\n"
                "  • delito → crimen, infracción, falta\n"
                "  • agua → aguas, hídrico\n"
                "  • tala → corte, deforestación, aprovechamiento\n"
                "  • multa → sanción, pena, penalidad"
            ),
        ],
    },
    {
        "titulo": "🤖  Paso 4 — Asistente IA — Consultas y uso avanzado",
        "color": "#1d6b3a",
        "img": "manual_05.png",
        "pasos": [
            (
                "Tipos de preguntas que puedes hacer",
                "El asistente tiene contexto de toda la legislación de Honduras:\n\n"
                "  • '¿Cuál es la multa máxima por contaminar un río?'\n"
                "  • '¿Qué dice el artículo 162 de la Ley Forestal?'\n"
                "  • '¿Cuántos años de cárcel por tala en área protegida?'\n"
                "  • '¿Qué requisitos necesito para un plan de manejo forestal?'\n"
                "  • 'Resume los artículos sobre biodiversidad marina'\n"
                "  • '¿Qué diferencia hay entre una licencia y un permiso ambiental?'"
            ),
            (
                "Selección de modelo Groq según necesidad",
                "  • llama-3.3-70b-versatile → Mayor calidad, respuestas profundas (RECOMENDADO)\n"
                "  • llama-3.1-8b-instant    → Ultra rápido, respuestas instantáneas\n"
                "  • mixtral-8x7b-32768      → Bueno para análisis largos y contexto amplio\n"
                "  • gemma2-9b-it            → Ligero, ideal para preguntas directas\n\n"
                "Si un modelo muestra 'cuota agotada', cambia a otro en Configuración."
            ),
            (
                "Errores comunes y soluciones",
                "  ⚠ 'IA no configurada' → Ve a Configuración y guarda tu API Key de Groq\n"
                "  ⚠ 'Límite de cuota'   → Espera unos minutos o cambia de modelo\n"
                "  ⚠ 'Clave inválida'    → Verifica que copiaste correctamente la clave gsk_...\n"
                "  ⚠ Sin respuesta       → Verifica tu conexión a internet"
            ),
        ],
    },
    {
        "titulo": "📚  Paso 5 — Biblioteca — Gestión de documentos",
        "color": "#7b4f12",
        "img": "manual_06.png",
        "pasos": [
            (
                "Catálogo Legal",
                "Muestra todos los documentos importados en la base de datos. "
                "Usa el campo 'Filtrar' para buscar por:\n"
                "  • Nombre del decreto o ley\n"
                "  • Número (ej: 098-2007)\n"
                "  • Tipo (Ley, Decreto, Acuerdo, Reglamento)"
            ),
            (
                "Agregar un nuevo PDF",
                "1. Clic en '+ Agregar PDF'\n"
                "2. Selecciona el archivo PDF desde tu computadora\n"
                "3. El sistema detecta automáticamente el título, tipo y número\n"
                "4. Revisa y corrige si es necesario\n"
                "5. Clic en 'Importar' → El PDF se copia a la biblioteca y se indexa"
            ),
            (
                "Sincronizar biblioteca",
                "Botón 'Sincronizar' re-procesa todos los PDFs de la carpeta "
                "Compendio Legal. Úsalo cuando:\n"
                "  • Agregues PDFs manualmente a esa carpeta\n"
                "  • Quieras actualizar documentos modificados\n"
                "  • La búsqueda no encuentre un documento que sí está en la carpeta"
            ),
            (
                "Favoritos guardados",
                "Pestaña ★ Favoritos: muestra todos los documentos o artículos "
                "que marcaste con ★ desde el Buscador.\n\n"
                "En cada favorito puedes:\n"
                "  • Ver el nombre del documento\n"
                "  • Abrir el PDF original\n"
                "  • Escribir una nota personal y guardarla\n"
                "  • Quitarlo de favoritos (botón rojo ✕)"
            ),
        ],
    },
    {
        "titulo": "📊  Paso 6 — Dashboard — Panel de control",
        "color": "#2c3e70",
        "img": "manual_07.png",
        "pasos": [
            (
                "Tarjetas de estadísticas",
                "Muestra en tiempo real:\n"
                "  • Total de normas legales en la base de datos\n"
                "  • Total de artículos indexados\n"
                "  • Documentos marcados como favoritos\n"
                "  • Total de búsquedas realizadas en el historial"
            ),
            (
                "Actividad reciente",
                "  • Gráfico de línea: búsquedas de los últimos 7 días\n"
                "  • Lista de documentos más consultados\n"
                "  • Distribución por tipo de norma (Ley, Decreto, Acuerdo...)"
            ),
        ],
    },
    {
        "titulo": "⚙  Paso 7 — Configuración — Opciones del sistema",
        "color": "#646464",
        "img": "manual_08.png",
        "pasos": [
            (
                "Inteligencia Artificial",
                "Selector de proveedor con dos opciones:\n\n"
                "  • Groq (Recomendado) — clave gratuita en console.groq.com/keys\n"
                "    Modelos: Llama 3.3 70B, Llama 3.1 8B, Mixtral, Gemma2\n"
                "  • Gemini (Google) — clave gratuita en aistudio.google.com\n"
                "    Modelos: gemini-2.0-flash, gemini-1.5-flash, gemini-1.5-pro\n\n"
                "Cada proveedor tiene su propio campo de clave y selector de modelos. "
                "Las claves de ambos se guardan en disco — puedes alternar entre proveedores "
                "en cualquier momento sin volver a ingresar las claves."
            ),
            (
                "Rutas de datos",
                "Muestra la ruta exacta donde está guardada la base de datos SQLite. "
                "Útil para hacer copias de seguridad: copia el archivo "
                "legislacion_ambiental.db a una ubicación segura."
            ),
            (
                "Licencia de uso",
                "Muestra el estado actual de la licencia con badge de color:\n"
                "  • Verde '✓ Activa' → cliente, tipo de licencia y fecha de vencimiento\n"
                "  • Naranja '⚠ Sin licencia' → botón para activar\n\n"
                "También incluye botón para renovar o cambiar la licencia en cualquier momento."
            ),
            (
                "Seguridad y acceso",
                "Cambia el nombre de usuario o la contraseña del sistema. "
                "Requiere ingresar la contraseña actual para confirmar el cambio."
            ),
            (
                "Tema visual (Light / Dark / System)",
                "Selector en la parte inferior del menú lateral. 'System' sigue el "
                "tema de Windows automáticamente (claro de día, oscuro de noche)."
            ),
            (
                "Historial de exportaciones",
                "Muestra los últimos documentos exportados (PDF, Excel, TXT) con "
                "fecha y nombre de archivo."
            ),
        ],
    },
    {
        "titulo": "⌨  Atajos de teclado y consejos rápidos",
        "color": "#555555",
        "img": "manual_09.png",
        "pasos": [
            ("Enter en Buscador",
             "Ejecuta la búsqueda directamente sin hacer clic en el botón Buscar."),
            ("Enter en Asistente IA",
             "Envía el mensaje al asistente."),
            ("Clic en logo LEX VIRIDIS",
             "Colapsa o expande el menú lateral para ganar más espacio en pantalla."),
            ("Filtro en Biblioteca",
             "El filtro del catálogo aplica con 300ms de espera automática "
             "(debounce), sin necesidad de presionar Enter."),
            ("Consejo: búsqueda exacta",
             "Para buscar una frase exacta, escríbela entre comillas:\n"
             "  • \"plan de manejo forestal\"\n"
             "  • \"artículo 325\"\n"
             "El sistema la buscará como una sola frase, no como palabras sueltas."),
            ("Consejo: copias de seguridad",
             "Haz copia del archivo:\n"
             "  LEX_VIRIDIS_DB/legislacion_ambiental.db\n"
             "Contiene todos los documentos, artículos, favoritos e historial."),
        ],
    },
    {
        "titulo": "📞  Soporte técnico",
        "color": Colors.PRIMARY,
        "img": "manual_10.png",
        "pasos": [
            (
                "Contacto",
                "ING. FERNANDO R. ARDON RODRIGUEZ\n"
                "EMAIL: frardonr@hotmail.com\n"
                "Transformación Digital — Gestión Técnica Institucional\n\n"
                "Desarrollado en colaboración con Antigravity, Gemini y Claude Opus 4.6.\n"
                "Ilustraciones generadas por Nano Banana AI."
            ),
            (
                "Versión actual",
                "LEX VIRIDIS v3.2.0.2026  (Marzo 2026)\n"
                "Plataforma de Gestión Legal Institucional\n\n"
                "Motor de búsqueda: 4 niveles — FTS5 + LIKE + texto completo PDF\n"
                "IA: Groq Llama 3.3 / Gemini (API externa, requiere internet)\n"
                "Exportación: PDF institucional, Excel, TXT\n"
                "Base legal: 194 documentos — leyes, decretos, acuerdos y reglamentos"
            ),
            (
                "Errores frecuentes y soluciones rápidas",
                "  • 'Base de datos no encontrada'  → Verifica la ruta en Configuración\n"
                "  • 'Buscador sin resultados'       → Usa Biblioteca → Sincronizar\n"
                "  • 'PDF no encontrado'             → El archivo puede haber sido movido;\n"
                "                                      reimportarlo desde Agregar PDF\n"
                "  • 'IA no responde'                → Verifica API Key y conexión a internet"
            ),
        ],
    },
    {
        "titulo": "★  Novedades — Versión 3.2.0 (Marzo 2026)",
        "color": "#b8860b",
        "img": "manual_11.png",
        "pasos": [
            (
                "Asistente IA: Groq como proveedor principal (gratis)",
                "Groq reemplaza a Google Gemini como opción recomendada para el Asistente IA.\n\n"
                "  • Modelo: Llama 3.3 70B — excelente en español y razonamiento legal\n"
                "  • Cuota: ~14,400 consultas/día (10× más que Gemini gratuito)\n"
                "  • Precio: completamente gratis, sin tarjeta de crédito\n"
                "  • Velocidad: sub-segundo (el más rápido disponible)\n\n"
                "Obtén tu clave gratuita en console.groq.com/keys con solo crear una cuenta."
            ),
            (
                "Configuración: Selector de proveedor IA (Groq / Gemini)",
                "La sección 'Inteligencia Artificial' en Configuración ahora incluye un selector "
                "con dos opciones:\n\n"
                "  • Groq (Recomendado) → API Key comienza con 'gsk_...'\n"
                "  • Gemini (Google)    → API Key comienza con 'AIza...' (respaldo)\n\n"
                "Cada proveedor tiene su propio campo de clave y selector de modelos. "
                "Puedes cambiar entre ellos en cualquier momento sin perder las claves guardadas."
            ),
            (
                "Motor de búsqueda completamente reescrito",
                "El Buscador ahora usa 4 niveles de búsqueda en cascada:\n"
                "  Nivel 1 → Título de la norma (coincidencia exacta)\n"
                "  Nivel 2 → Índice FTS5 sobre artículos indexados\n"
                "  Nivel 3 → Texto de artículos (búsqueda LIKE)\n"
                "  Nivel 4 → Texto completo de todos los PDFs (194 documentos)\n\n"
                "Esto garantiza resultados incluso cuando el índice FTS no tiene "
                "el documento. Palabras como 'rondas', 'fuego' o 'incendio' que antes "
                "daban 0 resultados, ahora devuelven 20 o más coincidencias."
            ),
            (
                "Búsqueda en lenguaje natural con filtro de palabras vacías",
                "Puedes escribir preguntas completas y el sistema extrae automáticamente "
                "las palabras clave, descartando: que, del, el, la, los, dice, según, "
                "artículo, cuál, etc.\n\n"
                "Ejemplo: 'que dice el artículo 325 del código penal'\n"
                "→ El sistema busca: 325, código, penal\n\n"
                "Esto evita búsquedas vacías o resultados irrelevantes por palabras comunes."
            ),
            (
                "PDFs que abren con el término buscado resaltado",
                "Al presionar '📄 Abrir PDF' en cualquier resultado, el documento se abre "
                "con el término de búsqueda resaltado en color amarillo en todas las páginas "
                "donde aparece. Ya no necesitas buscar manualmente en el documento.\n\n"
                "Si no se encuentra el término, se abre el PDF original sin modificar."
            ),
            (
                "Favoritos ahora muestran el nombre del documento",
                "Se corrigió el error donde los favoritos aparecían como 'Art. None — None'. "
                "Ahora cada favorito muestra correctamente el nombre de la ley o decreto "
                "de origen, incluso cuando el artículo proviene de una búsqueda en "
                "texto completo (no indexado por artículo)."
            ),
            (
                "Exportaciones en rutas relativas (listo para distribución)",
                "Se eliminó la ruta absoluta 'E:/LEX_VIRIDIS_APP/exports' que impedía "
                "instalar la app en otras computadoras. Las exportaciones ahora se guardan:\n"
                "  • En desarrollo: carpeta 'exports/' dentro del proyecto\n"
                "  • App instalada: Documentos\\LEX VIRIDIS\\Exportaciones\\\n\n"
                "Puedes cambiar la ubicación en el diálogo de guardado cada vez que exportas."
            ),
            (
                "Tutorial completo exportable como PDF",
                "Esta Ayuda ahora incluye el botón '📄 Exportar PDF' en la parte superior. "
                "Genera un manual institucional con:\n"
                "  • Portada con logo LEX VIRIDIS\n"
                "  • Índice con todas las secciones\n"
                "  • Barras de color por sección (igual que en la app)\n"
                "  • Badges numerados, subtítulos y descripciones detalladas\n"
                "  • Pie de página con versión y número de página"
            ),
        ],
    },
]


class HelpView(BaseView):
    def __init__(self, master, app):
        super().__init__(master, app)
        self.setup_ui()

    def setup_ui(self):
        self._section_frames = []   # referencias a cada grupo para scroll-to
        # ── Encabezado ──────────────────────────────────────────────────────
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=30, pady=(25, 5))

        ctk.CTkLabel(
            hdr,
            text="Ayuda y Tutorial",
            font=Typography.get_font(22, "bold"),
            text_color=Colors.PRIMARY, anchor="w"
        ).pack(side="left")

        # Botón exportar (más a la derecha)
        ctk.CTkButton(
            hdr, text="📄 Exportar PDF",
            command=self._export_help_pdf,
            fg_color=Colors.PRIMARY, hover_color=Colors.SECONDARY,
            height=34, corner_radius=8, font=Typography.bold()
        ).pack(side="right", padx=(10, 0))

        ctk.CTkLabel(
            hdr,
            text="Guía completa de uso · LEX VIRIDIS v3.2.0.2026",
            font=Typography.caption(),
            text_color=Colors.TEXT_SECONDARY, anchor="e"
        ).pack(side="right")

        # ── Índice de navegación rápida ─────────────────────────────────────
        nav_frame = ctk.CTkScrollableFrame(
            self, fg_color=Colors.SURFACE_LIGHT, height=48,
            orientation="horizontal", corner_radius=8
        )
        nav_frame.pack(fill="x", padx=20, pady=(0, 8))

        # Los botones se crean después de renderizar las secciones
        # para poder pasar la referencia al frame destino (idx)
        self._nav_buttons = []
        for i, sec in enumerate(SECCIONES):
            titulo_corto = sec["titulo"].split("—")[0].strip()
            btn = ctk.CTkButton(
                nav_frame, text=titulo_corto,
                height=30, corner_radius=6,
                fg_color="transparent",
                border_width=1, border_color=Colors.BORDER,
                text_color=Colors.TEXT_SECONDARY,
                font=Typography.caption(),
                hover_color=Colors.BORDER,
                command=lambda idx=i: self._scroll_to_section(idx),
            )
            btn.pack(side="left", padx=4, pady=6)
            self._nav_buttons.append(btn)

        # ── Contenido scrollable ─────────────────────────────────────────────
        self._scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self._scroll.pack(fill="both", expand=True, padx=20, pady=5)

        for sec in SECCIONES:
            self._render_seccion(self._scroll, sec)

    # ── Navegación rápida ────────────────────────────────────────────────────
    def _scroll_to_section(self, idx: int):
        """Desplaza el CTkScrollableFrame hasta el frame de la sección idx."""
        if idx >= len(self._section_frames):
            return
        target = self._section_frames[idx]
        canvas = self._scroll._parent_canvas

        def _do_scroll():
            # Coordenada Y del frame destino relativa al canvas interior
            target.update_idletasks()
            canvas.update_idletasks()
            target_y  = target.winfo_y()
            total_h   = canvas.winfo_height()
            scroll_h  = self._scroll._parent_frame.winfo_height()
            if scroll_h <= total_h:
                return
            fraction = target_y / scroll_h
            canvas.yview_moveto(max(0.0, min(fraction, 1.0)))

        self.after(10, _do_scroll)

    # ── Renderer de sección ──────────────────────────────────────────────────
    def _render_seccion(self, parent, sec: dict):
        group = ctk.CTkFrame(parent, corner_radius=12,
                             border_width=1, border_color=Colors.BORDER)
        group.pack(fill="x", pady=8, padx=4)
        self._section_frames.append(group)   # registrar para navegación

        # Barra de título coloreada
        title_bar = ctk.CTkFrame(group, fg_color=sec.get("color", Colors.PRIMARY),
                                  corner_radius=10, height=42)
        title_bar.pack(fill="x")
        title_bar.pack_propagate(False)

        ctk.CTkLabel(
            title_bar, text=f"  {sec['titulo']}",
            font=Typography.get_font(13, "bold"),
            text_color="white", anchor="w"
        ).pack(fill="x", padx=12, pady=10)

        # Pasos numerados
        for i, (subtitulo, descripcion) in enumerate(sec["pasos"]):
            bg = (Colors.SURFACE_LIGHT, "#2b2b2b") if i % 2 == 0 else "transparent"
            paso = ctk.CTkFrame(group, fg_color=bg, corner_radius=0)
            paso.pack(fill="x")

            inner = ctk.CTkFrame(paso, fg_color="transparent")
            inner.pack(fill="x", padx=16, pady=8)

            # Número
            num_bg = ctk.CTkFrame(inner, fg_color=sec.get("color", Colors.PRIMARY),
                                   width=26, height=26, corner_radius=13)
            num_bg.pack(side="left", anchor="n", padx=(0, 12), pady=2)
            num_bg.pack_propagate(False)
            ctk.CTkLabel(num_bg, text=str(i + 1),
                         font=Typography.get_font(10, "bold"),
                         text_color="white").place(relx=0.5, rely=0.5, anchor="center")

            # Texto
            txt_col = ctk.CTkFrame(inner, fg_color="transparent")
            txt_col.pack(side="left", fill="x", expand=True)

            ctk.CTkLabel(
                txt_col, text=subtitulo,
                font=Typography.bold(), anchor="w",
                text_color=sec.get("color", Colors.PRIMARY)
            ).pack(anchor="w")

            ctk.CTkLabel(
                txt_col, text=descripcion,
                font=Typography.body(),
                text_color=Colors.TEXT_SECONDARY,
                anchor="w", justify="left",
                wraplength=850
            ).pack(anchor="w", pady=(3, 0))

        # Espacio inferior
        ctk.CTkFrame(group, height=8, fg_color="transparent").pack()

    # ── EXPORTACIÓN PDF ─────────────────────────────────────────────────────

    def _export_help_pdf(self):
        """Abre diálogo de guardado y lanza la generación del PDF en un hilo."""
        from tkinter import filedialog
        from datetime import datetime
        from ..config import config

        file_path = filedialog.asksaveasfilename(
            initialdir=str(config.EXPORT_DIR),
            initialfile=f"LEX_VIRIDIS_Tutorial_{datetime.now().strftime('%Y%m%d')}.pdf",
            defaultextension=".pdf",
            filetypes=[("Documento PDF", "*.pdf")],
            title="Guardar Tutorial como PDF"
        )
        if not file_path:
            return

        self.show_toast("Generando PDF...", "info")
        self.run_in_thread(self._generate_help_pdf, (file_path,))

    def _generate_help_pdf(self, file_path: str):
        """Genera el PDF del tutorial con formato visual institucional."""
        try:
            import re
            from fpdf import FPDF
            from datetime import datetime
            from ..config import config
            from ..utils.export_manager import ExportLogManager

            def _c(text: str) -> str:
                """Limpia emojis/unicode no soportado por la fuente Helvetica."""
                return text.encode("latin-1", errors="ignore").decode("latin-1")

            def _hex_rgb(hex_color: str):
                """Convierte #RRGGBB → (R, G, B). Fallback teal si falla."""
                try:
                    h = hex_color.lstrip("#")
                    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
                except Exception:
                    return (0, 102, 102)

            pdf = FPDF()
            pdf.set_auto_page_break(auto=True, margin=18)

            # ── PORTADA ──────────────────────────────────────────────────
            pdf.add_page()

            logo_path = config.BASE_DIR / "assets" / "LEXVIRIDIS_WHITE_BG.png"
            if logo_path.exists():
                pdf.image(str(logo_path), x=83, y=18, w=44)
                pdf.ln(52)
            else:
                pdf.ln(20)

            # Eliminado título duplicado (ya está en el logo)
            pdf.ln(10)

            pdf.set_font("helvetica", "", 15)
            pdf.set_text_color(60, 60, 60)
            pdf.cell(0, 9, "Manual de Usuario y Tutorial Completo", 0, 1, "C")
            pdf.ln(3)

            pdf.set_draw_color(0, 102, 102)
            pdf.set_line_width(0.8)
            pdf.line(30, pdf.get_y(), 180, pdf.get_y())
            pdf.ln(7)

            pdf.set_font("helvetica", "", 11)
            pdf.set_text_color(110, 110, 110)
            pdf.cell(0, 6, "Plataforma de Gestion Legal Institucional", 0, 1, "C")
            pdf.cell(0, 6, "Version 3.2.0.2026", 0, 1, "C")
            pdf.cell(0, 6, f"Generado el {datetime.now().strftime('%d/%m/%Y a las %H:%M')}", 0, 1, "C")
            pdf.ln(14)

            # Índice
            pdf.set_fill_color(240, 248, 248)
            pdf.set_font("helvetica", "B", 12)
            pdf.set_text_color(0, 102, 102)
            pdf.cell(0, 9, "  Contenido", 0, 1, "L", fill=True)
            pdf.ln(2)

            for i, sec in enumerate(SECCIONES, 1):
                pdf.set_font("helvetica", "", 11)
                pdf.set_text_color(60, 60, 60)
                color_hex = sec.get("color", "#006666")
                if not (isinstance(color_hex, str) and color_hex.startswith("#")):
                    color_hex = "#006666"
                r, g, b = _hex_rgb(color_hex)
                pdf.set_fill_color(r, g, b)
                # Punto de color
                pdf.cell(5, 7, "", 0, 0)
                pdf.set_font("helvetica", "B", 11)
                pdf.set_text_color(r, g, b)
                pdf.cell(10, 7, f"{i}.", 0, 0)
                pdf.set_text_color(60, 60, 60)
                pdf.set_font("helvetica", "", 11)
                titulo_limpio = _c(re.sub(r"[^\x20-\x7E\xC0-\xFF]", "", sec["titulo"]).strip())
                pdf.cell(0, 7, titulo_limpio[:80], 0, 1)

            # ── SECCIONES ────────────────────────────────────────────────
            for sec in SECCIONES:
                pdf.add_page()

                color_hex = sec.get("color", "#006666")
                if not (isinstance(color_hex, str) and color_hex.startswith("#")):
                    color_hex = "#006666"
                r, g, b = _hex_rgb(color_hex)

                # Barra de título coloreada
                pdf.set_fill_color(r, g, b)
                pdf.set_text_color(255, 255, 255)
                pdf.set_font("helvetica", "B", 13)
                titulo_limpio = _c(re.sub(r"[^\x20-\x7E\xC0-\xFF]", "", sec["titulo"]).strip())
                pdf.cell(0, 12, f"  {titulo_limpio}", 0, 1, "L", fill=True)
                pdf.ln(2)

                # --- IMAGEN DE SECCIÓN ---
                if "img" in sec:
                    img_path = config.BASE_DIR / "assets" / "manual_images" / sec["img"]
                    if img_path.exists():
                        # Centrar imagen: ancho 110mm, x = (210-110)/2 = 50
                        # Aumentamos el margen superior para la imagen
                        pdf.ln(5)
                        pdf.image(str(img_path), x=50, y=pdf.get_y(), w=110)
                        # Las imágenes cuadradas de AI ocuparán ~110mm de alto. 
                        # Dejamos 115mm de espacio para el texto.
                        pdf.ln(115)
                    else:
                        pdf.ln(4)
                else:
                    pdf.ln(4)

                # Pasos
                for i, (subtitulo, descripcion) in enumerate(sec["pasos"]):
                    # Badge numérico (cuadro de color)
                    pdf.set_fill_color(r, g, b)
                    pdf.set_text_color(255, 255, 255)
                    pdf.set_font("helvetica", "B", 10)
                    badge_y = pdf.get_y()
                    pdf.cell(9, 9, f" {i+1}", 0, 0, "C", fill=True)

                    # Subtítulo en color
                    pdf.set_text_color(r, g, b)
                    pdf.set_font("helvetica", "B", 11)
                    sub_limpio = _c(subtitulo)
                    pdf.cell(0, 9, f"  {sub_limpio}", 0, 1, "L")

                    # Descripción
                    pdf.set_x(14)
                    pdf.set_text_color(80, 80, 80)
                    pdf.set_font("helvetica", "", 10)
                    desc_limpio = _c(descripcion)
                    pdf.multi_cell(175, 5.2, desc_limpio, align="L")

                    # Separador entre pasos
                    if i < len(sec["pasos"]) - 1:
                        pdf.set_draw_color(220, 220, 220)
                        pdf.set_line_width(0.2)
                        pdf.line(10, pdf.get_y() + 1.5, 200, pdf.get_y() + 1.5)
                    pdf.ln(5)

            # ── PIE DE PÁGINA (todas las páginas) ────────────────────────
            class _Footer(FPDF):
                pass  # placeholder; pie ya integrado por auto_page_break

            # Pie en última página
            pdf.set_y(-14)
            pdf.set_font("helvetica", "I", 8)
            pdf.set_text_color(160, 160, 160)
            pdf.cell(0, 5,
                     f"LEX VIRIDIS v3.2.0.2026  |  Manual de Usuario  |  Pagina {pdf.page_no()}",
                     0, 0, "C")

            pdf.output(file_path)
            ExportLogManager.add_log(file_path, "PDF")
            self.update_ui(self.show_export_success_dialog, file_path)

        except Exception as e:
            import traceback
            traceback.print_exc()
            self.update_ui(self.show_toast, f"Error al exportar: {e}", "error")
