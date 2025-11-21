# 🎯 StressVision - Sistema de Detección de Estrés Laboral

Sistema completo de detección de emociones y estrés en tiempo real con interfaz gráfica PyQt6.

## 📋 Características Principales

- ✅ **Detección Multi-Rostro**: Detecta hasta 20 personas simultáneamente
- ✅ **Reconocimiento Facial**: Sistema de enrollment y reconocimiento de colaboradores
- ✅ **Análisis de 7 Emociones**: Neutral, Alegría, Tristeza, Enojo, Estrés Bajo, Estrés Alto, Fatiga
- ✅ **Sistema de Alertas Automáticas**: Genera alertas ante patrones de estrés prolongado
- ✅ **Reportes Periódicos**: Genera reportes cada 15 minutos automáticamente
- ✅ **Dashboard en Tiempo Real**: Visualización de métricas y estadísticas
- ✅ **Base de Datos Local**: Almacenamiento SQLite para historial completo
- ✅ **100% Tiempo Real**: Procesamiento asíncrono con threading

## 🚀 Instalación

### Requisitos Previos

- Python 3.8 o superior
- Cámara web o dispositivo de captura de video
- Windows 10/11, Linux o macOS

### Pasos de Instalación

1. **Clonar o descargar el proyecto**

```bash
cd StressVision_PyQt6
```

2. **Crear entorno virtual (recomendado)**

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

3. **Instalar dependencias**

```bash
pip install -r requirements.txt
```

**Nota**: Si tienes GPU NVIDIA y quieres aceleración, instala TensorFlow-GPU:

```bash
pip uninstall tensorflow
pip install tensorflow-gpu==2.13.0
```

4. **Verificar instalación**

```bash
python main.py
```

## 📖 Uso

### Inicio Rápido

1. **Ejecutar la aplicación**

```bash
python main.py
```

2. **Iniciar Monitoreo**

   - Haz clic en "▶ Iniciar Monitoreo"
   - Selecciona el índice de cámara (0 por defecto)
   - El sistema comenzará a detectar rostros y analizar emociones

3. **Ver Métricas**

   - **Tab Tiempo Real**: Visualización de video con detecciones en vivo
   - **Tab Dashboard**: Métricas agregadas y estadísticas
   - **Tab Alertas**: Gestión de alertas generadas
   - **Tab Empleados**: Lista de empleados registrados

### Enrollment de Empleados

Para registrar nuevos empleados, necesitarás usar el sistema de enrollment:

1. **Preparar muestras faciales** (mínimo 3-10 imágenes)
2. **Usar el módulo de enrollment** (a implementar en futuras versiones)
3. **Los embeddings se guardan en `data/enrollments/`**

### Configuración

El sistema se configura automáticamente, pero puedes ajustar:

- **Cámara**: Selecciona el índice de cámara en la barra de herramientas
- **Frame Skip**: Modifica `frame_skip` en `VideoThread` para ajustar rendimiento
- **Umbrales de Alerta**: Ajusta en `AlertManager` según necesidades

## 🏗️ Estructura del Proyecto

```
StressVision_PyQt6/
├── main.py                 # Punto de entrada
├── requirements.txt        # Dependencias
├── README.md              # Este archivo
│
├── app/                    # Interfaz gráfica
│   ├── main_window.py     # Ventana principal PyQt6
│   └── __init__.py
│
├── core/                  # Lógica de negocio
│   ├── detectors/         # Detectores
│   │   ├── face_detector.py      # Detección facial
│   │   ├── emotion_analyzer.py   # Análisis emocional
│   │   └── face_recognizer.py    # Reconocimiento facial
│   │
│   ├── services/          # Servicios
│   │   ├── stress_calculator.py  # Cálculo de estrés
│   │   ├── alert_manager.py      # Gestión de alertas
│   │   └── report_generator.py   # Generación de reportes
│   │
│   ├── database/          # Base de datos
│   │   └── database.py    # Gestor SQLite
│   │
│   └── utils/             # Utilidades
│       └── types.py       # Tipos y constantes
│
└── data/                  # Datos
    ├── enrollments/       # Embeddings de empleados
    ├── stressvision.db    # Base de datos SQLite
    └── outputs/           # Reportes y exportaciones
```

## 🎯 Funcionalidades Detalladas

### RF-04: Detección Facial en Tiempo Real

- ✅ Detecta hasta 20 rostros simultáneamente
- ✅ Usa MediaPipe o OpenCV como backend
- ✅ Procesa mínimo 8-15 FPS
- ✅ Tamaño mínimo de rostro: 30x30 píxeles

### RF-06: Detección de Emociones

- ✅ Clasifica 7 emociones con DeepFace
- ✅ Accuracy: ≥85%
- ✅ Latencia: ≤150ms por rostro
- ✅ Retorna vector de probabilidades

### RF-10: Cálculo de Resumen de Estrés

- ✅ Agrega detecciones de últimas 24 horas
- ✅ Calcula promedio de nivel de estrés
- ✅ Cuenta eventos de estrés alto
- ✅ Identifica emoción predominante

### RF-11: Generación Automática de Alertas

- ✅ Monitorea detecciones en tiempo real
- ✅ Trigger: ≥10 eventos de estrés en 15 minutos
- ✅ Severidad según confianza
- ✅ Cooldown de 1 hora para evitar duplicados

### RF-14: Generación de Reportes Periódicos

- ✅ Frecuencia: cada 15 minutos (configurable)
- ✅ Incluye: total detecciones, empleados, estrés promedio
- ✅ Distribución de emociones
- ✅ Guarda en base de datos

### RF-15: Dashboard de Métricas en Tiempo Real

- ✅ Total de empleados activos
- ✅ Detecciones de última hora
- ✅ Nivel de estrés general
- ✅ Alertas pendientes
- ✅ Actualización automática cada 5 segundos

## 🔧 Solución de Problemas

### La cámara no se abre

- Verifica que la cámara no esté siendo usada por otra aplicación
- Prueba diferentes índices de cámara (0, 1, 2...)
- En Windows, asegúrate de tener permisos de cámara

### FPS muy bajos

- Reduce `frame_skip` en `VideoThread` (aumenta procesamiento)
- Usa backend OpenCV en lugar de MediaPipe (más rápido)
- Considera usar GPU si está disponible

### Errores de DeepFace

- Asegúrate de tener conexión a internet la primera vez (descarga modelos)
- Los modelos se guardan en `~/.deepface/weights/`
- Verifica que tengas suficiente espacio en disco

### Base de datos bloqueada

- Cierra otras instancias de la aplicación
- Verifica permisos de escritura en `data/`

## 📊 Requisitos del Sistema

### Mínimos

- CPU: Intel i5 o equivalente (4 cores)
- RAM: 8 GB
- GPU: Integrada (opcional)
- Cámara: USB 2.0 o superior
- Resolución: 640x480 o superior

### Recomendados

- CPU: Intel i7 o equivalente (8 cores)
- RAM: 16 GB
- GPU: NVIDIA con CUDA (para aceleración)
- Cámara: USB 3.0, 1080p
- Resolución: 1280x720 o superior

## 🛠️ Desarrollo

### Agregar Nueva Emoción

1. Editar `core/utils/types.py`:
   - Agregar a `EmotionType` enum
   - Agregar a `EMOTION_LABELS_ES`
   - Agregar a `EMOTION_COLORS`

2. Actualizar `emotion_analyzer.py` para mapear la nueva emoción

### Agregar Nuevo Backend de Detección

1. Crear nueva clase en `core/detectors/`
2. Implementar método `detect_faces(frame) -> List[FaceRegion]`
3. Agregar opción en `FaceDetector.__init__()`

## 📝 Licencia

Este proyecto es desarrollado para Gloria S.A.

## 👥 Soporte

Para problemas o preguntas:
- Revisa la documentación en `docs/`
- Verifica los logs en `logs/`
- Contacta al equipo de desarrollo

---

**Versión**: 1.0  
**Fecha**: Noviembre 2024  
**Desarrollado para**: Gloria S.A.

