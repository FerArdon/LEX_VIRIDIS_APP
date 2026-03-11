# PROMPT PARA ANTIGRAVITY - Creación de Ejecutable LEX VIRIDIS

## CONTEXTO
Eres un asistente especializado en Python y PyInstaller. Tu tarea es crear un ejecutable (.exe) para la aplicación LEX VIRIDIS v3.0.0, una aplicación desktop de gestión de legislación ambiental construida con Python 3.11.9 y Flet.

## UBICACIÓN DEL PROYECTO
- **Directorio de trabajo**: `C:\LEX_VIRIDIS_APP`
- **Entorno virtual**: `C:\LEX_VIRIDIS_APP\.venv`
- **Python**: 3.11.9
- **Sistema Operativo**: Windows 11

## PASO 1: VERIFICAR DEPENDENCIAS Y CREAR build.spec

### 1.1 Verificar que PyInstaller está instalado
Ejecuta en el directorio `C:\LEX_VIRIDIS_APP`:
```bash
.venv\Scripts\activate
pip install pyinstaller
```

### 1.2 Crear archivo build.spec
Crea el archivo `C:\LEX_VIRIDIS_APP\build.spec` con el siguiente contenido:

```python
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=['C:\\LEX_VIRIDIS_APP'],
    binaries=[],
    datas=[
        ('assets', 'assets'),
        ('COMPENDIO LEYES FEMA', 'COMPENDIO LEYES FEMA'),
        ('data', 'data'),
        ('LEX_VIRIDIS_DB', 'LEX_VIRIDIS_DB'),
        ('.env.example', '.'),
    ],
    hiddenimports=[
        'flet',
        'flet.core',
        'flet.fastapi',
        'sqlite3',
        'PyPDF2',
        'cryptography',
        'cryptography.fernet',
        'cryptography.hazmat',
        'cryptography.hazmat.primitives',
        'cryptography.hazmat.backends',
        'PIL',
        'PIL.Image',
        'dateutil',
        'dateutil.parser',
        'pkg_resources',
        'pkg_resources.py2_warn',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'pytest',
        'pytest-cov',
        'mypy',
        'ruff',
        'black',
        'isort',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='LexViridis',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # Sin consola para app desktop
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets\\lux_viridis_2.ico'  # Icono de la aplicación
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='LexViridis'
)
```

## PASO 2: VERIFICAR ESTRUCTURA DE ARCHIVOS

### 2.1 Verificar que existen estos directorios y archivos críticos:
```
C:\LEX_VIRIDIS_APP\
├── main.py                          ✓ Punto de entrada
├── assets\
│   ├── lux_viridis_2.ico           ✓ Icono principal
│   ├── logo_luxviridis.png         ✓ Logo
│   └── hero_search.png             ✓ Banner
├── COMPENDIO LEYES FEMA\           ✓ PDFs de legislación
├── data\                            ✓ Datos de usuario
├── LEX_VIRIDIS_DB\
│   └── legislacion_ambiental.db    ✓ Base de datos SQLite
├── lexviridis\
│   ├── __init__.py
│   ├── ui_v2.py                    ✓ Interfaz principal
│   ├── config.py                   ✓ Configuración
│   ├── security.py                 ✓ Autenticación
│   ├── search_engine.py            ✓ Motor de búsqueda
│   ├── app\
│   │   └── dependencies.py         ✓ Inyección de dependencias
│   ├── repositories\
│   │   └── casos_repository.py     ✓ Repositorio de casos
│   └── views\
│       ├── casos.py                ✓ Vista de casos
│       ├── caso_detail.py          ✓ Detalle de caso
│       └── ... (otras 6 vistas)
└── .env.example                     ✓ Ejemplo de configuración
```

### 2.2 Si falta el icono, usar PNG como alternativa
Si `assets\lux_viridis_2.ico` no existe, modifica en `build.spec`:
```python
icon='assets\\logo_luxviridis.png'  # Fallback a PNG
```

## PASO 3: COMPILAR EL EJECUTABLE

### 3.1 Limpiar builds previos (si existen)
```bash
cd C:\LEX_VIRIDIS_APP
rmdir /s /q build
rmdir /s /q dist
```

### 3.2 Ejecutar PyInstaller
```bash
.venv\Scripts\activate
pyinstaller build.spec --clean --noconfirm
```

### 3.3 Monitorear la compilación
**Observa estos mensajes clave:**
- ✓ "Building Analysis" - Analizando dependencias
- ✓ "Building PYZ" - Comprimiendo módulos Python
- ✓ "Building EXE" - Creando ejecutable
- ✓ "Building COLLECT" - Recolectando archivos

**Errores comunes y soluciones:**

#### Error: "ModuleNotFoundError: No module named 'X'"
**Solución**: Agregar el módulo a `hiddenimports` en build.spec:
```python
hiddenimports=[
    # ... existentes
    'nombre_del_modulo_faltante',
]
```

#### Error: "FileNotFoundError: [Errno 2] No such file or directory: 'assets'"
**Solución**: Verificar que la carpeta assets existe y tiene los archivos necesarios.

#### Error: Icon not found
**Solución**: Cambiar a PNG en build.spec o verificar ruta del icono.

## PASO 4: VERIFICAR Y PROBAR EL EJECUTABLE

### 4.1 Verificar la estructura de salida
Después de compilar, deberías tener:
```
C:\LEX_VIRIDIS_APP\dist\LexViridis\
├── LexViridis.exe              ✓ Ejecutable principal
├── assets\                      ✓ Recursos copiados
├── COMPENDIO LEYES FEMA\       ✓ PDFs copiados
├── data\                        ✓ Datos copiados
├── LEX_VIRIDIS_DB\             ✓ Base de datos copiada
├── _internal\                   ✓ Dependencias de Python
└── ... (archivos DLL y dependencias)
```

### 4.2 Prueba básica del ejecutable
```bash
cd C:\LEX_VIRIDIS_APP\dist\LexViridis
LexViridis.exe
```

### 4.3 Checklist de funcionalidad
**Verifica que funcione:**
- [ ] La aplicación inicia sin errores
- [ ] Aparece la ventana de login centrada
- [ ] El login funciona con credenciales válidas
- [ ] El logo y banner se muestran correctamente
- [ ] La búsqueda de artículos funciona
- [ ] La vista de casos carga correctamente
- [ ] Se pueden crear nuevos casos
- [ ] Los PDFs se pueden abrir

### 4.4 Verificar logs en caso de error
Si el ejecutable falla, revisa los logs en:
```
C:\Users\frard\AppData\Local\Temp\LEX_VIRIDIS\logs\
```

## PASO 5: REPORTAR RESULTADOS

### 5.1 Si la compilación fue EXITOSA
Reporta:
```
✅ COMPILACIÓN EXITOSA

Ubicación del ejecutable:
C:\LEX_VIRIDIS_APP\dist\LexViridis\LexViridis.exe

Tamaño del ejecutable: [tamaño en MB]
Tamaño total del directorio: [tamaño en MB]

Pruebas realizadas:
✓ [Lista de funcionalidades probadas]

Siguiente paso sugerido:
Crear instalador con Inno Setup o NSIS
```

### 5.2 Si hubo ERRORES
Reporta:
```
❌ ERROR EN COMPILACIÓN

Error principal:
[Copiar el mensaje de error completo]

Logs relevantes:
[Copiar últimas 20 líneas de la salida de PyInstaller]

Archivos verificados:
[Lista de archivos que existen/faltan]

Acción requerida:
[Descripción del problema y posible solución]
```

## NOTAS IMPORTANTES

### Credenciales de prueba
- Usuario: `admin`
- Contraseña: `admin123`

### Configuración de la aplicación
- La app usa SQLite (no requiere servidor de base de datos)
- Los logs se guardan en `C:\Users\frard\AppData\Local\Temp\LEX_VIRIDIS\logs\`
- La configuración se lee de `.env` (si existe) o usa valores por defecto

### Problemas conocidos
1. **Flet requiere recursos**: Asegúrate de incluir carpeta `assets` completa
2. **SQLite necesita permisos**: El ejecutable debe poder escribir en su directorio
3. **Antivirus**: Puede marcar falsos positivos, agregar excepción si es necesario

### Optimizaciones opcionales
- **UPX compression**: Ya habilitado en build.spec (reduce tamaño ~30%)
- **One-file mode**: NO recomendado para esta app (demasiado lento al iniciar)
- **Console mode**: Mantener `console=False` para app profesional

## COMANDO FINAL RESUMIDO

```bash
# 1. Activar entorno
cd C:\LEX_VIRIDIS_APP
.venv\Scripts\activate

# 2. Instalar PyInstaller
pip install pyinstaller

# 3. Limpiar builds previos
rmdir /s /q build dist

# 4. Compilar
pyinstaller build.spec --clean --noconfirm

# 5. Probar
cd dist\LexViridis
LexViridis.exe
```

---

**IMPORTANTE**: Ejecuta estos pasos en orden y reporta cualquier error que encuentres con el mensaje completo y el contexto. Si todo funciona, prepara el ejecutable para distribución.
