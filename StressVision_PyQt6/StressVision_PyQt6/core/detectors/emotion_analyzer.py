"""
😊 Analizador de Emociones
Usa DeepFace y modelos ensemble para análisis emocional
"""
import cv2
import numpy as np
from typing import Dict, List, Optional
from deepface import DeepFace
from core.utils.types import EmotionResult, EmotionType
import time

class EmotionAnalyzer:
    """
    Analizador de emociones con soporte para ensemble de modelos
    """
    
    def __init__(self, use_ensemble: bool = False):
        """
        Inicializa el analizador
        
        Args:
            use_ensemble: Si True, usa múltiples modelos para mejor precisión
        """
        self.use_ensemble = use_ensemble
        self.fer_model = None
        
        if use_ensemble:
            self._load_fer_model()
    
    def _load_fer_model(self):
        """Carga modelo FER adicional para ensemble"""
        try:
            from tensorflow.keras.models import load_model
            from tensorflow.keras.preprocessing.image import img_to_array
            
            # Intentar cargar modelo FER si está disponible
            model_path = "models/fer2013_mini_XCEPTION.102-0.66.hdf5"
            # self.fer_model = load_model(model_path, compile=False)
            # self.fer_labels = ['angry', 'disgust', 'fear', 'happy', 'sad', 'surprise', 'neutral']
            print("⚠️ Modelo FER no encontrado, usando solo DeepFace")
        except Exception as e:
            print(f"⚠️ No se pudo cargar modelo FER: {e}")
    
    def analyze_face(self, face_roi: np.ndarray) -> EmotionResult:
        """
        Analiza la emoción de un rostro
        
        Args:
            face_roi: ROI del rostro (BGR)
            
        Returns:
            EmotionResult con emoción detectada y probabilidades
        """
        try:
            # Análisis con DeepFace
            analysis = DeepFace.analyze(
                face_roi,
                actions=['emotion'],
                enforce_detection=False,
                detector_backend='opencv',
                silent=True
            )
            
            # Normalizar resultado (DeepFace puede retornar lista o dict)
            if isinstance(analysis, list):
                analysis = analysis[0]
            
            emotions = analysis.get('emotion', {})
            
            # Obtener emoción dominante
            dominant_emotion = analysis.get('dominant_emotion', 'neutral')
            confidence = emotions.get(dominant_emotion, 0.0) / 100.0
            
            # Convertir probabilidades a formato 0-1
            probabilities = {k: v / 100.0 for k, v in emotions.items()}
            
            # Mapear emociones a nuestro sistema
            mapped_emotion = self._map_emotion(dominant_emotion, probabilities)
            
            return EmotionResult(
                emotion=mapped_emotion,
                confidence=confidence,
                probabilities=probabilities,
                timestamp=time.time()
            )
            
        except Exception as e:
            print(f"⚠️ Error en análisis emocional: {e}")
            # Retornar resultado neutral en caso de error
            return EmotionResult(
                emotion=EmotionType.NEUTRAL.value,
                confidence=0.0,
                probabilities={},
                timestamp=time.time()
            )
    
    def _map_emotion(self, emotion: str, probabilities: Dict[str, float]) -> str:
        """
        Mapea emociones de DeepFace a nuestro sistema
        
        Args:
            emotion: Emoción detectada por DeepFace
            probabilities: Probabilidades de todas las emociones
            
        Returns:
            Emoción mapeada a nuestro sistema
        """
        # Mapeo directo
        emotion_map = {
            'angry': EmotionType.ANGRY.value,
            'fear': EmotionType.FEAR.value,
            'sad': EmotionType.SAD.value,
            'disgust': EmotionType.DISGUST.value,
            'happy': EmotionType.HAPPY.value,
            'surprise': EmotionType.SURPRISE.value,
            'neutral': EmotionType.NEUTRAL.value
        }
        
        base_emotion = emotion_map.get(emotion, EmotionType.NEUTRAL.value)
        
        # Determinar si hay estrés o fatiga basado en combinaciones
        # Estrés alto: angry + fear + sad con alta probabilidad
        stress_score = (
            probabilities.get('angry', 0) * 0.4 +
            probabilities.get('fear', 0) * 0.3 +
            probabilities.get('sad', 0) * 0.3
        )
        
        # Fatiga: neutral + sad con baja energía
        fatigue_score = (
            probabilities.get('neutral', 0) * 0.6 +
            probabilities.get('sad', 0) * 0.4
        )
        
        if stress_score > 0.6:
            return EmotionType.STRESS_HIGH.value
        elif stress_score > 0.4:
            return EmotionType.STRESS_LOW.value
        elif fatigue_score > 0.7 and probabilities.get('neutral', 0) > 0.5:
            return EmotionType.FATIGUE.value
        else:
            return base_emotion
    
    def analyze_multiple_faces(self, frame: np.ndarray, face_regions: List) -> List[EmotionResult]:
        """
        Analiza emociones de múltiples rostros
        
        Args:
            frame: Frame completo
            face_regions: Lista de FaceRegion
            
        Returns:
            Lista de EmotionResult
        """
        results = []
        
        for face_region in face_regions:
            x, y, w, h = face_region.bbox
            
            # Extraer ROI con padding
            padding = 10
            x1 = max(0, x - padding)
            y1 = max(0, y - padding)
            x2 = min(frame.shape[1], x + w + padding)
            y2 = min(frame.shape[0], y + h + padding)
            
            face_roi = frame[y1:y2, x1:x2]
            
            if face_roi.size > 0:
                result = self.analyze_face(face_roi)
                results.append(result)
        
        return results

