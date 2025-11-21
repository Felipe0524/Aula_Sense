"""
🔖 Tipos y estructuras de datos compartidas
"""
from dataclasses import dataclass, field
from typing import Tuple, Dict, List, Optional
from datetime import datetime
from enum import Enum

# ============================================================================
# ENUMS
# ============================================================================

class EmotionType(str, Enum):
    """Tipos de emociones detectadas"""
    NEUTRAL = "neutral"
    HAPPY = "happy"
    SAD = "sad"
    ANGRY = "angry"
    FEAR = "fear"
    SURPRISE = "surprise"
    DISGUST = "disgust"
    # Emociones adicionales para estrés
    STRESS_LOW = "stress_low"
    STRESS_HIGH = "stress_high"
    FATIGUE = "fatigue"

class AlertType(str, Enum):
    """Tipos de alertas"""
    HIGH_STRESS_PROLONGED = "high_stress_prolonged"
    FATIGUE_DETECTED = "fatigue_detected"
    ANOMALY_DETECTED = "anomaly_detected"

class AlertSeverity(str, Enum):
    """Severidad de alertas"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class AlertStatus(str, Enum):
    """Estado de alertas"""
    PENDING = "pending"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"

# ============================================================================
# CONSTANTES
# ============================================================================

# Emociones negativas (para cálculo de estrés)
NEGATIVE_EMOTIONS = [
    EmotionType.ANGRY.value,
    EmotionType.FEAR.value,
    EmotionType.SAD.value,
    EmotionType.DISGUST.value,
    EmotionType.STRESS_HIGH.value,
    EmotionType.FATIGUE.value
]

# Emociones neutrales
NEUTRAL_EMOTIONS = [EmotionType.NEUTRAL.value]

# Emociones positivas
POSITIVE_EMOTIONS = [
    EmotionType.HAPPY.value,
    EmotionType.SURPRISE.value
]

# Mapeo de emociones a español
EMOTION_LABELS_ES = {
    EmotionType.NEUTRAL.value: "Neutral",
    EmotionType.HAPPY.value: "Alegría",
    EmotionType.SAD.value: "Tristeza",
    EmotionType.ANGRY.value: "Enojo",
    EmotionType.FEAR.value: "Miedo",
    EmotionType.SURPRISE.value: "Sorpresa",
    EmotionType.DISGUST.value: "Disgusto",
    EmotionType.STRESS_LOW.value: "Estrés Bajo",
    EmotionType.STRESS_HIGH.value: "Estrés Alto",
    EmotionType.FATIGUE.value: "Fatiga"
}

# Colores para visualización
EMOTION_COLORS = {
    EmotionType.NEUTRAL.value: (200, 200, 200),  # Gris
    EmotionType.HAPPY.value: (0, 255, 0),         # Verde
    EmotionType.SAD.value: (255, 0, 0),           # Azul
    EmotionType.ANGRY.value: (0, 0, 255),         # Rojo
    EmotionType.FEAR.value: (0, 165, 255),        # Naranja
    EmotionType.SURPRISE.value: (255, 0, 255),     # Magenta
    EmotionType.DISGUST.value: (0, 255, 0),        # Verde lima
    EmotionType.STRESS_LOW.value: (255, 255, 0),  # Amarillo
    EmotionType.STRESS_HIGH.value: (0, 0, 255),   # Rojo intenso
    EmotionType.FATIGUE.value: (128, 128, 128)    # Gris oscuro
}

# ============================================================================
# DATACLASSES
# ============================================================================

@dataclass
class FaceRegion:
    """Región facial detectada"""
    x: int
    y: int
    width: int
    height: int
    confidence: float = 0.0
    
    @property
    def bbox(self) -> Tuple[int, int, int, int]:
        """Retorna bounding box como tupla (x, y, w, h)"""
        return (self.x, self.y, self.width, self.height)
    
    @property
    def center(self) -> Tuple[int, int]:
        """Retorna centro del bounding box"""
        return (self.x + self.width // 2, self.y + self.height // 2)

@dataclass
class EmotionResult:
    """Resultado de análisis emocional"""
    emotion: str
    confidence: float
    probabilities: Dict[str, float] = field(default_factory=dict)
    timestamp: float = 0.0
    
    def __post_init__(self):
        if self.timestamp == 0.0:
            from time import time
            self.timestamp = time()

@dataclass
class DetectionResult:
    """Resultado completo de detección"""
    face_region: FaceRegion
    emotion: EmotionResult
    employee_id: Optional[str] = None
    recognition_confidence: float = 0.0
    track_id: Optional[int] = None
    age: Optional[int] = None
    gender: Optional[str] = None

@dataclass
class StressEvent:
    """Evento de estrés detectado"""
    timestamp: str
    stress_index: float
    emotion: str
    person_count: int
    employee_id: Optional[str] = None

@dataclass
class Alert:
    """Alerta generada por el sistema"""
    alert_id: int
    employee_id: Optional[str]
    alert_type: str
    severity: str
    stress_level: float
    timestamp: str
    status: str = AlertStatus.PENDING.value
    message: str = ""
    resolved_at: Optional[str] = None
    resolved_by: Optional[str] = None

@dataclass
class Employee:
    """Información de empleado"""
    employee_id: str
    name: str
    department: str
    shift: Optional[str] = None
    embedding: Optional[List[float]] = None
    consent_given: bool = False
    active: bool = True

@dataclass
class DetectionEvent:
    """Evento de detección almacenado en BD"""
    detection_id: Optional[int] = None
    session_id: Optional[str] = None
    employee_id: Optional[str] = None
    track_id: Optional[int] = None
    timestamp: Optional[str] = None
    emotion: Optional[str] = None
    confidence: float = 0.0
    stress_level: Optional[float] = None
    bounding_box: Optional[str] = None  # JSON string
    emotion_probabilities: Optional[str] = None  # JSON string
    processing_time_ms: Optional[int] = None

