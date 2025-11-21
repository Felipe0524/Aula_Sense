"""
📊 Generador de Reportes Periódicos
Genera reportes cada 15 minutos con estadísticas agregadas
"""
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from core.database.database import Database
from core.services.stress_calculator import StressCalculator

class ReportGenerator:
    """
    Generador de reportes periódicos
    """
    
    def __init__(
        self,
        database: Database,
        stress_calculator: StressCalculator,
        report_interval_minutes: int = 15
    ):
        """
        Inicializa el generador de reportes
        
        Args:
            database: Instancia de Database
            stress_calculator: Instancia de StressCalculator
            report_interval_minutes: Intervalo de generación en minutos
        """
        self.db = database
        self.stress_calculator = stress_calculator
        self.report_interval_minutes = report_interval_minutes
        self.last_report_time: Optional[datetime] = None
    
    def generate_report(self) -> Optional[Dict]:
        """
        Genera un reporte periódico
        
        Returns:
            Diccionario con datos del reporte o None si no hay datos
        """
        # Calcular ventana de tiempo
        end_time = datetime.now()
        start_time = end_time - timedelta(minutes=self.report_interval_minutes)
        
        # Obtener detecciones del período
        detections = self.db.get_detections(
            start_time=start_time.isoformat(),
            end_time=end_time.isoformat(),
            limit=10000
        )
        
        if not detections:
            return None
        
        # Calcular estadísticas
        total_detections = len(detections)
        
        # Empleados únicos detectados
        employees_detected = set(
            d.employee_id for d in detections
            if d.employee_id
        )
        num_employees_detected = len(employees_detected)
        
        # Nivel de estrés promedio
        stress_levels = [
            d.stress_level for d in detections
            if d.stress_level is not None
        ]
        avg_stress_level = sum(stress_levels) / len(stress_levels) if stress_levels else 0.0
        
        # Distribución de emociones
        emotion_distribution = {}
        for detection in detections:
            emotion = detection.emotion or 'unknown'
            emotion_distribution[emotion] = emotion_distribution.get(emotion, 0) + 1
        
        # Alertas generadas en el período
        alerts = self.db.get_alerts(
            limit=1000
        )
        alerts_in_period = [
            a for a in alerts
            if start_time <= datetime.fromisoformat(a.timestamp) <= end_time
        ]
        alerts_generated = len(alerts_in_period)
        
        # Crear reporte
        report_data = {
            'timestamp': end_time.isoformat(),
            'period_start': start_time.isoformat(),
            'period_end': end_time.isoformat(),
            'total_detections': total_detections,
            'employees_detected': num_employees_detected,
            'avg_stress_level': round(avg_stress_level, 2),
            'emotion_distribution': emotion_distribution,
            'alerts_generated': alerts_generated,
            'employee_details': self._get_employee_details(employees_detected, detections)
        }
        
        # Guardar en base de datos
        self._save_report(report_data)
        
        return report_data
    
    def _get_employee_details(
        self,
        employee_ids: set,
        detections: List
    ) -> Dict:
        """Obtiene detalles por empleado"""
        details = {}
        
        for employee_id in employee_ids:
            employee_detections = [
                d for d in detections
                if d.employee_id == employee_id
            ]
            
            if employee_detections:
                stress_levels = [
                    d.stress_level for d in employee_detections
                    if d.stress_level
                ]
                
                emotions = [d.emotion for d in employee_detections if d.emotion]
                predominant_emotion = max(
                    set(emotions),
                    key=emotions.count
                ) if emotions else 'unknown'
                
                details[employee_id] = {
                    'detection_count': len(employee_detections),
                    'avg_stress_level': sum(stress_levels) / len(stress_levels) if stress_levels else 0.0,
                    'predominant_emotion': predominant_emotion
                }
        
        return details
    
    def _save_report(self, report_data: Dict):
        """Guarda el reporte en la base de datos"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO reports_15min
                    (timestamp, total_detections, employees_detected,
                     avg_stress_level, emotion_distribution, alerts_generated,
                     report_data)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    report_data['timestamp'],
                    report_data['total_detections'],
                    report_data['employees_detected'],
                    report_data['avg_stress_level'],
                    json.dumps(report_data['emotion_distribution']),
                    report_data['alerts_generated'],
                    json.dumps(report_data)
                ))
        except Exception as e:
            print(f"⚠️ Error guardando reporte: {e}")
    
    def should_generate_report(self) -> bool:
        """Verifica si es momento de generar un reporte"""
        if self.last_report_time is None:
            return True
        
        elapsed = (datetime.now() - self.last_report_time).total_seconds() / 60.0
        return elapsed >= self.report_interval_minutes
    
    def get_latest_report(self) -> Optional[Dict]:
        """Obtiene el último reporte generado"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT report_data FROM reports_15min
                    ORDER BY timestamp DESC LIMIT 1
                """)
                
                row = cursor.fetchone()
                if row:
                    return json.loads(row['report_data'])
        except Exception as e:
            print(f"⚠️ Error obteniendo último reporte: {e}")
        
        return None

