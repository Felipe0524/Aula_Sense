"""
🚨 Gestor de Alertas Automáticas
Monitorea detecciones y genera alertas según patrones
"""
from typing import List, Optional, Dict
from datetime import datetime, timedelta
from collections import defaultdict
from core.utils.types import Alert, AlertType, AlertSeverity, AlertStatus
from core.database.database import Database
from core.services.stress_calculator import StressCalculator

class AlertManager:
    """
    Gestor de alertas automáticas
    """
    
    def __init__(
        self,
        database: Database,
        stress_calculator: StressCalculator,
        alert_threshold: int = 10,
        alert_window_minutes: int = 15,
        cooldown_minutes: int = 60
    ):
        """
        Inicializa el gestor de alertas
        
        Args:
            database: Instancia de Database
            stress_calculator: Instancia de StressCalculator
            alert_threshold: Número mínimo de eventos de estrés para alerta
            alert_window_minutes: Ventana de tiempo en minutos
            cooldown_minutes: Tiempo mínimo entre alertas del mismo tipo
        """
        self.db = database
        self.stress_calculator = stress_calculator
        self.alert_threshold = alert_threshold
        self.alert_window_minutes = alert_window_minutes
        self.cooldown_minutes = cooldown_minutes
        
        # Historial de alertas generadas (para cooldown)
        self.last_alert_times: Dict[str, datetime] = {}
    
    def check_and_generate_alerts(
        self,
        employee_id: Optional[str] = None
    ) -> List[Alert]:
        """
        Verifica condiciones y genera alertas si es necesario
        
        Args:
            employee_id: ID del empleado (None para global)
            
        Returns:
            Lista de alertas generadas
        """
        alerts = []
        
        # Obtener detecciones recientes
        window_start = datetime.now() - timedelta(minutes=self.alert_window_minutes)
        detections = self.db.get_detections(
            employee_id=employee_id,
            start_time=window_start.isoformat()
        )
        
        # Filtrar solo detecciones de estrés alto
        stress_detections = [
            d for d in detections
            if d.stress_level and d.stress_level > 0.7
        ]
        
        # Verificar umbral
        if len(stress_detections) >= self.alert_threshold:
            alert_key = f"high_stress_{employee_id or 'global'}"
            
            # Verificar cooldown
            if self._can_generate_alert(alert_key):
                alert = self._create_high_stress_alert(
                    employee_id=employee_id,
                    stress_detections=stress_detections
                )
                
                if alert:
                    alert_id = self.db.add_alert(alert)
                    if alert_id:
                        alert.alert_id = alert_id
                        alerts.append(alert)
                        self.last_alert_times[alert_key] = datetime.now()
        
        # Verificar fatiga
        fatigue_alert = self._check_fatigue(employee_id)
        if fatigue_alert:
            alerts.append(fatigue_alert)
        
        return alerts
    
    def _can_generate_alert(self, alert_key: str) -> bool:
        """Verifica si se puede generar una alerta (cooldown)"""
        if alert_key not in self.last_alert_times:
            return True
        
        last_time = self.last_alert_times[alert_key]
        elapsed = (datetime.now() - last_time).total_seconds() / 60.0
        
        return elapsed >= self.cooldown_minutes
    
    def _create_high_stress_alert(
        self,
        employee_id: Optional[str],
        stress_detections: List
    ) -> Optional[Alert]:
        """Crea alerta de estrés alto prolongado"""
        # Calcular nivel de estrés promedio
        avg_stress = sum(
            d.stress_level for d in stress_detections
            if d.stress_level
        ) / len(stress_detections)
        
        # Determinar severidad
        if avg_stress > 0.8:
            severity = AlertSeverity.HIGH.value
        elif avg_stress > 0.6:
            severity = AlertSeverity.MEDIUM.value
        else:
            severity = AlertSeverity.LOW.value
        
        # Crear mensaje
        if employee_id:
            message = f"Empleado {employee_id} muestra niveles altos de estrés prolongado"
        else:
            message = f"Se detectaron {len(stress_detections)} eventos de estrés alto en {self.alert_window_minutes} minutos"
        
        alert = Alert(
            alert_id=0,  # Se asignará al guardar
            employee_id=employee_id,
            alert_type=AlertType.HIGH_STRESS_PROLONGED.value,
            severity=severity,
            stress_level=avg_stress,
            timestamp=datetime.now().isoformat(),
            status=AlertStatus.PENDING.value,
            message=message
        )
        
        return alert
    
    def _check_fatigue(self, employee_id: Optional[str]) -> Optional[Alert]:
        """Verifica condiciones de fatiga"""
        distribution = self.stress_calculator.get_emotion_distribution(
            employee_id=employee_id,
            hours=1
        )
        
        fatigue_count = distribution.get('fatigue', 0)
        neutral_count = distribution.get('neutral', 0)
        
        # Si hay muchas detecciones de fatiga o neutral
        if fatigue_count >= 15 or (fatigue_count + neutral_count) >= 20:
            alert_key = f"fatigue_{employee_id or 'global'}"
            
            if self._can_generate_alert(alert_key):
                alert = Alert(
                    alert_id=0,
                    employee_id=employee_id,
                    alert_type=AlertType.FATIGUE_DETECTED.value,
                    severity=AlertSeverity.MEDIUM.value,
                    stress_level=0.5,
                    timestamp=datetime.now().isoformat(),
                    status=AlertStatus.PENDING.value,
                    message=f"Se detectó fatiga en {'empleado ' + employee_id if employee_id else 'múltiples personas'}"
                )
                
                alert_id = self.db.add_alert(alert)
                if alert_id:
                    alert.alert_id = alert_id
                    self.last_alert_times[alert_key] = datetime.now()
                    return alert
        
        return None
    
    def acknowledge_alert(self, alert_id: int, user_id: str) -> bool:
        """Reconoce una alerta"""
        return self.db.update_alert_status(
            alert_id=alert_id,
            status=AlertStatus.ACKNOWLEDGED.value,
            resolved_by=user_id
        )
    
    def resolve_alert(self, alert_id: int, user_id: str) -> bool:
        """Resuelve una alerta"""
        return self.db.update_alert_status(
            alert_id=alert_id,
            status=AlertStatus.RESOLVED.value,
            resolved_by=user_id
        )
    
    def get_pending_alerts(self, limit: int = 50) -> List[Alert]:
        """Obtiene alertas pendientes"""
        return self.db.get_alerts(
            status=AlertStatus.PENDING.value,
            limit=limit
        )

