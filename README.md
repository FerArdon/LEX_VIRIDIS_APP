# LEX VIRIDIS 🌿

**Compendio Legal Ambiental Inteligente para Honduras**

Sistema profesional de investigación legal ambiental desarrollado para la Fiscalía Especial del Medio Ambiente (FEMA) de Honduras.

---

## 📋 Características

### Core Features

- 🔍 **Motor de Búsqueda Avanzado**: FTS5 (Full-Text Search) con soporte para sinónimos y búsqueda semántica
- 🤖 **Asistente IA con Gemini**: Consultas en lenguaje natural sobre legislación ambiental
- 📚 **Biblioteca Digital**: 185+ documentos legales en PDF con metadata completa
- ⭐ **Sistema de Favoritos**: Organización personal de artículos y normas
- 📖 **Sistema de Estudio**: Flashcards con repetición espaciada para aprendizaje
- 📊 **Analytics**: Dashboard con estadísticas y métricas de uso
- 🔐 **Seguridad**: Autenticación robusta, cifrado de datos sensibles, gestión de sesiones

### Arquitectura

- **Desktop App**: Python 3.11 + Flet (UI moderna y responsive)
- **Web App**: React + FastAPI (en desarrollo)
- **Base de Datos**: SQLite con FTS5 para búsqueda full-text
- **IA**: Google Gemini 1.5 Flash para procesamiento de lenguaje natural

---

## 🚀 Instalación

### Requisitos Previos

- Python 3.11+
- Git
- Windows 10/11 (recomendado) o Linux/macOS

### Setup Rápido

```bash
# 1. Clonar repositorio
git clone <repository-url>
cd LEX_VIRIDIS_APP

# 2. Crear entorno virtual
python -m venv .venv

# 3. Activar entorno virtual
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

# 4. Instalar dependencias
pip install -r requirements.txt
pip install -r requirements-dev.txt  # Para desarrollo

# 5. Configurar variables de entorno (opcional)
cp .env.example .env
# Editar .env y agregar tu GEMINI_API_KEY

# 6. Ejecutar aplicación
python run_modern_ui.py
```

---

## 🧪 Testing

El proyecto cuenta con **125 tests automatizados** con alta cobertura:

```bash
# Ejecutar todos los tests
pytest tests/ -v

# Con cobertura
pytest tests/ --cov=lexviridis --cov-report=term-missing

# Solo tests de seguridad
pytest tests/test_security.py -v

# Solo tests del motor de búsqueda
pytest tests/test_search_engine.py -v
```

---

## 🏗️ Estructura del Proyecto

```
LEX_VIRIDIS_APP/
├── lexviridis/              # Código fuente principal
│   ├── app/                 # Arquitectura de aplicación
│   │   ├── dependencies.py  # Inyección de dependencias
│   │   └── navigation.py    # Gestor de navegación
│   ├── views/               # Vistas modulares (Fase 3)
│   │   ├── dashboard.py
│   │   ├── search.py
│   │   ├── ai_chat.py
│   │   ├── favorites.py
│   │   ├── library.py
│   │   ├── study.py
│   │   └── settings.py
│   ├── services/            # Capa de servicios
│   ├── config.py            # Configuración inmutable
│   ├── search_engine.py     # Motor de búsqueda FTS5
│   ├── security.py          # Autenticación y cifrado
│   ├── secure_config.py     # Gestor de config segura (Fase 5)
│   ├── constants.py         # Constantes centralizadas (Fase 4)
│   └── ui_v2.py             # Shell principal (239 líneas, antes 2,891)
├── tests/                   # 125 tests automatizados
├── web/                     # Aplicación web (React + FastAPI)
├── LEX_VIRIDIS_DB/          # Base de datos SQLite
├── COMPENDIO LEYES FEMA/    # PDFs de legislación
└── pyproject.toml           # Configuración de herramientas
```

---

## 📊 Refactorización Completada

### Fase 1: Limpieza y Cimientos ✅

- Eliminación de archivos duplicados
- Organización de scripts de diagnóstico
- Configuración de herramientas de calidad (ruff, mypy, pytest)
- Inicialización de Git

### Fase 2: Infraestructura de Pruebas ✅

- **125 tests automatizados** con >80% de cobertura
- Fixtures compartidos en `conftest.py`
- Tests para: búsqueda, config, persistencia, seguridad, citas, utils, traducciones

### Fase 3: Descomponer God Class ✅

- **ui_v2.py reducido de 2,891 → 239 líneas** (-92%)
- 8 vistas modulares en `lexviridis/views/`
- Arquitectura limpia con DependencyContainer y NavigationManager
- Separación de responsabilidades

### Fase 4: Calidad de Código ✅

- Corrección de 15+ bare exceptions con logging específico
- Creación de `constants.py` para números mágicos
- **1,466 problemas corregidos automáticamente** con ruff
- Modernización de type hints (PEP 585/604)

### Fase 5: Seguridad ✅

- **Cifrado de API key de Gemini** con `SecureConfigManager`
- **CORS configurado** en FastAPI con orígenes específicos
- **Thread safety** con `threading.Lock` en `DependencyContainer`
- Todos los tests de seguridad pasando

### Fases 6-8: Próximos Pasos 📋

- **Fase 6**: Expandir API FastAPI + React frontend
- **Fase 7**: Documentación técnica + CI/CD + pre-commit hooks
- **Fase 8**: Pruebas de integración + optimización de rendimiento

---

## 🔧 Herramientas de Calidad

```bash
# Linting y formateo
ruff check lexviridis/
ruff check lexviridis/ --fix  # Corregir automáticamente

# Type checking
mypy lexviridis/

# Cobertura de tests
pytest --cov=lexviridis --cov-report=html
```

---

## 🔒 Seguridad

- **Autenticación**: PBKDF2 con 600,000 iteraciones
- **Cifrado**: Fernet (AES-128) para datos sensibles
- **Sesiones**: Tokens seguros con expiración de 30 días
- **SQL Injection**: Protección con validación de queries
- **API Keys**: Almacenamiento cifrado con `EncryptionManager`

---

## 📝 Configuración

### Variables de Entorno

```bash
# .env
GEMINI_API_KEY=tu-api-key-aqui
CORS_ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000
DEBUG=False
```

### Credenciales por Defecto

```
Usuario: admin
Contraseña: admin123
```

⚠️ **Cambiar en producción**

---

## 📄 Licencia

**PROPIEDAD DE FEMA HONDURAS - USO RESTRINGIDO**

Este software es propiedad exclusiva de la Fiscalía Especial del Medio Ambiente (FEMA) de Honduras.
Su uso, copia, modificación o distribución no autorizada está estrictamente prohibida.

Consulte el archivo `LICENSE` para los términos completos.

---

## 📞 Soporte

- **Institucional**: Fiscalía Especial del Medio Ambiente (FEMA)
- **Email**: <soporte@fema.gob.hn>
- **Técnico**: Ing. Fer Ardón (`fer.ardon@fema.gob.hn`)

---

## 🎯 Métricas del Proyecto

- **Líneas de código**: ~15,000
- **Tests**: 125 (100% pasando)
- **Cobertura**: >80%
- **Documentos legales**: 185+
- **Artículos indexados**: 5,000+
- **Tiempo de búsqueda**: <100ms promedio

---

**Desarrollado para FEMA Honduras**

*Última actualización: Febrero 2026*
