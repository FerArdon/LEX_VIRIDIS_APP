# 🌿 LEX VIRIDIS - Compendio Legal Ambiental de Honduras

Sistema de búsqueda inteligente para normativa ambiental hondureña con IA integrada.

## 🚀 Inicio Rápido

```bash
# Activar entorno virtual
.venv\Scripts\activate

# Ejecutar aplicación
python run_modern_ui.py
```

## 📁 Estructura del Proyecto

```
LEX_VIRIDIS_APP/
├── 📁 lexviridis/           # Módulo principal de la aplicación
│   ├── config.py            # Configuración centralizada
│   ├── indexer.py           # Indexador de PDFs
│   ├── search_engine.py     # Motor de búsqueda SQLite FTS5
│   ├── ia_gemini.py         # Integración con Google Gemini
│   ├── main_flet.py         # UI principal (versión clásica)
│   ├── ui_v2.py             # UI moderna (versión 2.0)
│   └── pdf_viewer_fixed.py  # Visor de PDFs con resaltado
│
├── 📁 LEX_VIRIDIS_DB/       # Base de datos SQLite
│   └── legislacion_ambiental.db
│
├── 📄 lexviridis/license_system.py  # Sistema de licenciamiento (la clave de firma NO va en el repo)
│
├── 📁 COMPENDIO LEYES FEMA/ # PDFs de normativa (185 documentos)
│
├── 📁 assets/               # Recursos (iconos, imágenes)
├── 📁 data/                 # Índices y datos de la app
├── 📁 logs/                 # Logs de la aplicación
│
├── run_modern_ui.py         # ⭐ Script para ejecutar UI moderna
├── run_lexviridis.py        # Script para ejecutar UI clásica
├── requirements.txt         # Dependencias Python
└── README.md                # Este archivo
```

## ✨ Características

- 🔍 **Búsqueda Inteligente**: Motor FTS5 con sinónimos legales
- 🤖 **Asistente IA**: Integración con Google Gemini
- 📄 **Visor PDF**: Resaltado automático de términos buscados
- 📊 **185+ Documentos**: Leyes, decretos y reglamentos ambientales
- 🎨 **UI Moderna**: Interfaz profesional con Material Design

## 🔧 Requisitos

- Python 3.11+
- Windows 10/11

## 📦 Instalación

```bash
# Crear entorno virtual
python -m venv .venv

# Activar
.venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt
```

## 📞 Soporte

Desarrollado para la Fiscalía Especial del Medio Ambiente (FEMA) de Honduras.

---
**Versión**: 2.0.0 | **Última actualización**: Febrero 2026
