# Web App – Lector de Estados de Cuenta Bancarios

Aplicación web desarrollada como evolución del proyecto Bancos Reader, diseñada para procesar estados de cuenta bancarios desde un entorno backend escalable.

El sistema permite cargar archivos PDF bancarios y generar automáticamente reportes estructurados en Excel listos para análisis financiero.

Este proyecto representa la migración de procesamiento local a una arquitectura moderna basada en backend con Python.

---

## Objetivo
Crear una plataforma web capaz de automatizar la lectura de estados de cuenta bancarios, centralizando el procesamiento y facilitando la generación de archivos descargables.

---

## Funcionalidades actuales
- Carga de estados de cuenta bancarios en PDF  
- Procesamiento automático desde backend  
- Extracción de movimientos financieros  
- Generación de archivos Excel descargables  
- API preparada para múltiples bancos  
- Arquitectura lista para integración de OCR  

---

## Enfoque técnico
El sistema funciona mediante:

1. Subida de archivos PDF desde frontend  
2. Procesamiento del documento en backend (FastAPI)  
3. Extracción estructurada de movimientos  
4. Generación dinámica de Excel  
5. Descarga directa del archivo procesado  

---

## Tecnologías
- Python  
- FastAPI  
- Pandas  
- SQLAlchemy  
- HTML / CSS  
- JavaScript  
- Uvicorn  

---

## Contenerización con Docker

La aplicación fue preparada para ejecutarse en un entorno completamente contenedorizado utilizando Docker Desktop y Docker Compose.

Esto permite:

- Levantar backend y base de datos automáticamente  
- Mantener dependencias aisladas  
- Replicar fácilmente el entorno en cualquier máquina  
- Simular un despliegue real de producción  

---

### Servicios levantados con Docker

| Servicio | Función |
|---------|---------|
| API FastAPI | Procesamiento de PDFs y generación de Excel |
| PostgreSQL | Almacenamiento de resultados y metadatos |
| Storage Volume | Persistencia de archivos cargados |

---

### Ejecución local

```bash
docker compose up --build
```


## Arquitectura del proyecto
```
bank-statement-webapp/
├── backend/
│ ├── app/
│ ├── routers/
│ ├── services/
│ ├── storage/
│ └── main.py
├── frontend/
│ ├── static/
│ └── templates/
└── requirements.txt
```

---

## Escalabilidad
El sistema está preparado para:
- Integrar nuevos bancos fácilmente  
- Implementar lectura OCR para PDFs escaneados  
- Manejo multiusuario  
- Convertirse en plataforma SaaS  

---

Proyecto desarrollado como migración de automatización financiera a entorno web utilizando backend en Python.

