"""
📊 Calculadora de Índice de Estrés
Mantiene historial y calcula métricas de estrés por colaborador
"""
from collections import deque
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from core.utils.types import (
    EmotionResult, StressEvent, NEGATIVE_EMOTIONS,
    EmotionType
)
import time

class StressCalculator:
    """
    Calculadora de índice de estrés con historial temporal
    """
    
    def __init__(self, max_history: int = 100, window_size: int = 30):
        """
        Inicializa el calculador
        
        Args:
            max_history: Máximo número de emociones en historial
            window_size: Tamaño de ventana para cálculo de estrés
        """
        self.max_history = max_history
        self.window_size = window_size
        
        # Historial por empleado: {employee_id: deque}
        self.employee_histories: Dict[str, deque] = {}
        
        # Historial global
        self.global_history: deque = deque(maxlen=max_history)
        
        # Eventos de estrés
        self.stress_events: List[StressEvent] = []
        
        # Métricas agregadas
        self.metrics: Dict[str, Dict] = {}
    
    def add_emotion(
        self,
        emotion: str,
        employee_id: Optional[str] = None,
        confidence: float = 0.0
    ):
        """
        Agrega una emoción al historial
        
        Args:
            emotion: Emoción detectada
            employee_id: ID del empleado (opcional)
            confidence: Confianza de la detección
        """
        timestamp = time.time()
        
        # Agregar a historial global
        self.global_history.append({
            'emotion': emotion,
            'timestamp': timestamp,
            'confidence': confidence
        })
        
        # Agregar a historial del empleado
        if employee_id:
            if employee_id not in self.employee_histories:
                self.employee_histories[employee_id] = deque(maxlen=self.max_history)
            
            self.employee_histories[employee_id].append({
                'emotion': emotion,
                'timestamp': timestamp,
                'confidence': confidence
            })
    
    def calculate_stress_index(
        self,
        employee_id: Optional[str] = None,
        window: Optional[int] = None
    ) -> float:
        """
        Calcula índice de estrés basado en ventana temporal
        
        Args:
            employee_id: ID del empleado (None para global)
            window: Tamaño de ventana (None usa self.window_size)
            
        Returns:
            Índice de estrés (0-100)
        """
        window = window or self.window_size
        
        # Seleccionar historial
        if employee_id and employee_id in self.employee_histories:
            history = list(self.employee_histories[employee_id])
        else:
            history = list(self.global_history)
        
        if len(history) < 5:
            return 0.0
        
        # Obtener últimas N emociones
        recent_emotions = history[-window:]
        
        # Contar emociones negativas
        negative_count = sum(
            1 for e in recent_emotions
            if e['emotion'] in NEGATIVE_EMOTIONS
        )
        
        # Calcular porcentaje
        total = len(recent_emotions)
        if total == 0:
            return 0.0
        
        stress_index = (negative_count / total) * 100.0
        return round(stress_index, 2)
    
    def check_stress_threshold(
        self,
        threshold: float = 50.0,
        employee_id: Optional[str] = None
    ) -> bool:
        """
        Verifica si se superó el umbral de estrés
        
        Args:
            threshold: Umbral de estrés (0-100)
            employee_id: ID del empleado (None para global)
            
        Returns:
            True si se superó el umbral
        """
        stress_index = self.calculate_stress_index(employee_id)
        
        if stress_index > threshold:
            # Obtener última emoción
            if employee_id and employee_id in self.employee_histories:
                history = list(self.employee_histories[employee_id])
            else:
                history = list(self.global_history)
            
            last_emotion = history[-1]['emotion'] if history else 'unknown'
            
            # Crear evento de estrés
            event = StressEvent(
                timestamp=datetime.now().isoformat(),
                stress_index=stress_index,
                emotion=last_emotion,
                person_count=1,
                employee_id=employee_id
            )
            
            self.stress_events.append(event)
            return True
        
        return False
    
    def get_emotion_distribution(
        self,
        employee_id: Optional[str] = None,
        hours: int = 24
    ) -> Dict[str, int]:
        """
        Obtiene distribución de emociones
        
        Args:
            employee_id: ID del empleado (None para global)
            hours: Horas hacia atrás a considerar
            
        Returns:
            Diccionario con conteo de cada emoción
        """
        cutoff_time = time.time() - (hours * 3600)
        
        # Seleccionar historial
        if employee_id and employee_id in self.employee_histories:
            history = list(self.employee_histories[employee_id])
        else:
            history = list(self.global_history)
        
        # Filtrar por tiempo
        recent = [e for e in history if e['timestamp'] >= cutoff_time]
        
        # Contar emociones
        distribution = {}
        for entry in recent:
            emotion = entry['emotion']
            distribution[emotion] = distribution.get(emotion, 0) + 1
        
        return distribution
    
    def get_metrics(self, employee_id: Optional[str] = None) -> Dict:
        """
        Obtiene métricas agregadas
        
        Args:
            employee_id: ID del empleado (None para global)
            
        Returns:
            Diccionario con métricas
        """
        stress_index = self.calculate_stress_index(employee_id)
        distribution = self.get_emotion_distribution(employee_id)
        
        total_detections = sum(distribution.values())
        negative_count = sum(
            distribution.get(e, 0) for e in NEGATIVE_EMOTIONS
        )
        
        # Emoción predominante
        predominant_emotion = max(
            distribution.items(),
            key=lambda x: x[1]
        )[0] if distribution else EmotionType.NEUTRAL.value
        
        return {
            'stress_index': stress_index,
            'total_detections': total_detections,
            'negative_count': negative_count,
            'negative_percentage': (negative_count / total_detections * 100) if total_detections > 0 else 0,
            'predominant_emotion': predominant_emotion,
            'emotion_distribution': distribution,
            'stress_events_count': len([
                e for e in self.stress_events
                if e.employee_id == employee_id or employee_id is None
            ])
        }
    
    def clear_history(self, employee_id: Optional[str] = None):
        """Limpia el historial"""
        if employee_id:
            if employee_id in self.employee_histories:
                self.employee_histories[employee_id].clear()
        else:
            self.global_history.clear()
            self.employee_histories.clear()

