# LEX VIRIDIS Web (PWA)

Esta es la versión web de LEX VIRIDIS, construida con React y FastAPI.

## Estructura

- `/backend`: API REST construida con FastAPI.
- `/frontend`: Aplicación SPA construida con React y Vite.

## Ejecución Local

### 1. Backend

```bash
cd backend
pip install -r requirements.txt
python main.py
```

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

## Características PWA

- **Manifest**: Archivo `manifest.json` incluido para permitir instalación.
- **Offline**: Preparado para implementación de Service Workers.
- **Responsive**: Diseño optimizado para móviles y escritorio.

## Despliegue con Docker

```bash
docker-compose up --build
```
