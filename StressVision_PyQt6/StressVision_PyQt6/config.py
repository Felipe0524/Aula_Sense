"""
⚙️ Configuración del Sistema StressVision
"""
from pathlib import Path

# Directorios
ROOT_DIR = Path(__file__).parent
DATA_DIR = ROOT_DIR / "data"
ENROLLMENTS_DIR = DATA_DIR / "enrollments"
OUTPUTS_DIR = DATA_DIR / "outputs"
LOGS_DIR = ROOT_DIR / "logs"
DB_PATH = DATA_DIR / "stressvision.db"

# Crear directorios si no existen
DATA_DIR.mkdir(exist_ok=True)
ENROLLMENTS_DIR.mkdir(exist_ok=True)
OUTPUTS_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)

# Detección Facial
FACE_DETECTION_BACKEND = "mediapipe"  # "mediapipe" o "opencv"
MIN_FACE_SIZE = 30  # píxeles
DETECTION_CONFIDENCE = 0.5

# Análisis Emocional
USE_ENSEMBLE = False  # Usar múltiples modelos
EMOTION_MODEL = "deepface"  # "deepface" o "fer"

# Reconocimiento Facial
RECOGNITION_THRESHOLD = 0.70  # Umbral de similitud (0-1)
ENROLLMENT_MIN_SAMPLES = 3
ENROLLMENT_QUALITY_THRESHOLD = 0.70

# Cálculo de Estrés
STRESS_WINDOW_SIZE = 30  # Número de emociones para calcular índice
STRESS_THRESHOLD = 50.0  # Umbral de alerta (0-100)

# Alertas
ALERT_THRESHOLD = 10  # Eventos de estrés para generar alerta
ALERT_WINDOW_MINUTES = 15  # Ventana de tiempo
ALERT_COOLDOWN_MINUTES = 60  # Tiempo entre alertas del mismo tipo

# Reportes
REPORT_INTERVAL_MINUTES = 15  # Frecuencia de reportes

# Video
CAMERA_INDEX = 0
VIDEO_WIDTH = 1280
VIDEO_HEIGHT = 720
VIDEO_FPS = 30
FRAME_SKIP = 3  # Analizar 1 de cada N frames

# Base de Datos
DB_MAX_DETECTIONS = 1000000  # Límite de detecciones en BD

# UI
UPDATE_METRICS_INTERVAL_MS = 1000  # Actualizar métricas cada segundo
UPDATE_DASHBOARD_INTERVAL_MS = 5000  # Actualizar dashboard cada 5 segundos
CHECK_ALERTS_INTERVAL_MS = 30000  # Verificar alertas cada 30 segundos

# Emociones Negativas (para cálculo de estrés)
NEGATIVE_EMOTIONS = [
    "angry", "fear", "sad", "disgust", "stress_high", "fatigue"
]

# Colores de Visualización
EMOTION_COLORS_BGR = {
    "neutral": (200, 200, 200),
    "happy": (0, 255, 0),
    "sad": (255, 0, 0),
    "angry": (0, 0, 255),
    "fear": (0, 165, 255),
    "surprise": (255, 0, 255),
    "disgust": (0, 255, 0),
    "stress_low": (255, 255, 0),
    "stress_high": (0, 0, 255),
    "fatigue": (128, 128, 128)
}

