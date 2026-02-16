# Guía de Contribución - LEX VIRIDIS

¡Gracias por tu interés en contribuir a LEX VIRIDIS!

## 🚀 Setup para Desarrollo

```bash
# 1. Clonar repositorio
git clone <repository-url>
cd LEX_VIRIDIS_APP

# 2. Crear entorno virtual
python -m venv .venv
source .venv/Scripts/activate  # Windows
# source .venv/bin/activate    # Linux/macOS

# 3. Instalar dependencias de desarrollo
pip install -r requirements-dev.txt

# 4. Instalar pre-commit hooks
pre-commit install

# 5. Ejecutar tests
pytest tests/ -v
```

## 🔧 Herramientas de Calidad

### Linting y Formateo (Ruff)
```bash
# Verificar problemas
ruff check lexviridis/

# Corregir automáticamente
ruff check lexviridis/ --fix

# Formatear código
ruff format lexviridis/
```

### Type Checking (MyPy)
```bash
mypy lexviridis/
```

### Tests
```bash
# Ejecutar todos los tests
pytest tests/ -v

# Con cobertura
pytest tests/ --cov=lexviridis --cov-report=html

# Tests específicos
pytest tests/test_security.py -v
```

### Pre-commit Hooks
Los hooks se ejecutan automáticamente antes de cada commit. Para ejecutarlos manualmente:

```bash
pre-commit run --all-files
```

## 📝 Estándares de Código

### Python Style Guide
- Seguir PEP 8 (aplicado automáticamente por ruff)
- Longitud de línea: 120 caracteres
- Type hints en todas las funciones públicas
- Docstrings en formato Google

### Ejemplo de Docstring
```python
def search_articles(query: str, page: int = 1) -> SearchResult:
    """Busca artículos legales por término de búsqueda.

    Args:
        query: Término de búsqueda.
        page: Número de página (1-indexed).

    Returns:
        Resultado de búsqueda con artículos encontrados.

    Raises:
        ValueError: Si el query está vacío.
    """
    ...
```

### Commits
- Usar mensajes descriptivos en español
- Formato: `tipo: descripción breve`
- Tipos: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`

Ejemplos:
```
feat: agregar endpoint de favoritos a API
fix: corregir validación de queries vacías
refactor: extraer lógica de paginación a función
docs: actualizar README con nuevos endpoints
test: agregar tests para módulo de seguridad
```

## 🧪 Testing

### Escribir Tests
- Crear tests para todo código nuevo
- Mantener cobertura >80%
- Usar fixtures de `conftest.py`
- Nombrar tests descriptivamente: `test_<accion>_<condicion>_<resultado_esperado>`

### Ejemplo
```python
def test_search_empty_query_returns_invalid_status():
    """Búsqueda con query vacía debe retornar status INVALID."""
    engine = SearchEngine()
    result = engine.search_safe("")
    assert result.status == SearchStatus.INVALID
```

## 🔒 Seguridad

- **NUNCA** commitear API keys o secretos
- Usar `.env` para configuración sensible
- Validar entrada de usuarios
- Usar type hints para prevenir errores

## 📂 Estructura de Branches

```
main              # Producción (protegida)
├── develop       # Integración (protegida)
├── feature/*     # Nuevas características
├── fix/*         # Correcciones de bugs
└── refactor/*    # Refactorizaciones
```

## 🔄 Workflow de Contribución

1. **Crear branch** desde `develop`
   ```bash
   git checkout develop
   git pull origin develop
   git checkout -b feature/nombre-descriptivo
   ```

2. **Implementar cambios**
   - Escribir código
   - Agregar tests
   - Ejecutar `pytest` y `ruff`

3. **Commit**
   ```bash
   git add .
   git commit -m "feat: descripción del cambio"
   # Los pre-commit hooks se ejecutan automáticamente
   ```

4. **Push y Pull Request**
   ```bash
   git push origin feature/nombre-descriptivo
   ```
   - Crear PR en GitHub/GitLab
   - Describir cambios claramente
   - Esperar revisión de código

## ✅ Checklist antes de PR

- [ ] Tests pasan (`pytest tests/ -v`)
- [ ] Ruff sin errores (`ruff check lexviridis/`)
- [ ] MyPy sin errores críticos (`mypy lexviridis/`)
- [ ] Cobertura >80% mantenida
- [ ] Docstrings agregados
- [ ] `CHANGELOG.md` actualizado (si aplica)
- [ ] README actualizado (si aplica)

## 🐛 Reportar Bugs

Al reportar un bug, incluir:
- Descripción del problema
- Pasos para reproducir
- Comportamiento esperado vs actual
- Versión de Python y OS
- Stack trace (si aplica)

## 💡 Sugerir Features

Al sugerir un feature, incluir:
- Descripción clara del feature
- Caso de uso / problema que resuelve
- Propuesta de implementación (opcional)

## 📞 Contacto

Para preguntas sobre desarrollo, contactar al equipo de desarrollo de FEMA.

---

**¡Gracias por contribuir a LEX VIRIDIS!** 🌿
