"""
💾 Base de Datos SQLite
Gestión de datos locales del sistema
"""
import sqlite3
import json
from pathlib import Path
from typing import List, Optional, Dict
from datetime import datetime
from contextlib import contextmanager
from core.utils.types import (
    Employee, DetectionEvent, Alert, AlertStatus, AlertType, AlertSeverity
)

class Database:
    """
    Gestor de base de datos SQLite
    """
    
    def __init__(self, db_path: str = "data/stressvision.db"):
        """
        Inicializa la base de datos
        
        Args:
            db_path: Ruta al archivo de base de datos
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
    
    @contextmanager
    def get_connection(self):
        """Context manager para conexiones a la BD"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def _init_database(self):
        """Inicializa las tablas de la base de datos"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Tabla de empleados
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS employees (
                    employee_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    department TEXT,
                    shift TEXT,
                    consent_given INTEGER DEFAULT 0,
                    active INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Tabla de sesiones
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    device_id TEXT,
                    location TEXT,
                    start_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    end_timestamp TIMESTAMP,
                    status TEXT DEFAULT 'active',
                    total_detections INTEGER DEFAULT 0
                )
            """)
            
            # Tabla de detecciones
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS detection_events (
                    detection_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT,
                    employee_id TEXT,
                    track_id INTEGER,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    emotion TEXT,
                    confidence REAL,
                    stress_level REAL,
                    bounding_box TEXT,
                    emotion_probabilities TEXT,
                    processing_time_ms INTEGER,
                    FOREIGN KEY (employee_id) REFERENCES employees(employee_id),
                    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
                )
            """)
            
            # Tabla de alertas
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS alerts (
                    alert_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    employee_id TEXT,
                    alert_type TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    stress_level REAL NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'pending',
                    message TEXT,
                    resolved_at TIMESTAMP,
                    resolved_by TEXT,
                    FOREIGN KEY (employee_id) REFERENCES employees(employee_id)
                )
            """)
            
            # Tabla de reportes periódicos
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS reports_15min (
                    report_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    total_detections INTEGER,
                    employees_detected INTEGER,
                    avg_stress_level REAL,
                    emotion_distribution TEXT,
                    alerts_generated INTEGER,
                    report_data TEXT
                )
            """)
            
            # Tabla de resumen de estrés por empleado
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS employee_stress_summary (
                    summary_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    employee_id TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    avg_stress_level REAL,
                    high_stress_count INTEGER DEFAULT 0,
                    predominant_emotion TEXT,
                    total_detections INTEGER DEFAULT 0,
                    FOREIGN KEY (employee_id) REFERENCES employees(employee_id)
                )
            """)
            
            # Índices para mejor rendimiento
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_detections_employee_timestamp
                ON detection_events(employee_id, timestamp)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_detections_session
                ON detection_events(session_id)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_alerts_status
                ON alerts(status, timestamp)
            """)
            
            conn.commit()
    
    # ========================================================================
    # EMPLEADOS
    # ========================================================================
    
    def add_employee(self, employee: Employee) -> bool:
        """Agrega un nuevo empleado"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO employees
                    (employee_id, name, department, shift, consent_given, active)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    employee.employee_id,
                    employee.name,
                    employee.department,
                    employee.shift,
                    1 if employee.consent_given else 0,
                    1 if employee.active else 0
                ))
            return True
        except Exception as e:
            print(f"⚠️ Error agregando empleado: {e}")
            return False
    
    def get_employee(self, employee_id: str) -> Optional[Employee]:
        """Obtiene un empleado por ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM employees WHERE employee_id = ?
            """, (employee_id,))
            
            row = cursor.fetchone()
            if row:
                return Employee(
                    employee_id=row['employee_id'],
                    name=row['name'],
                    department=row['department'],
                    shift=row['shift'],
                    consent_given=bool(row['consent_given']),
                    active=bool(row['active'])
                )
        return None
    
    def get_all_employees(self, active_only: bool = True) -> List[Employee]:
        """Obtiene todos los empleados"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            query = "SELECT * FROM employees"
            if active_only:
                query += " WHERE active = 1"
            query += " ORDER BY name"
            
            cursor.execute(query)
            return [
                Employee(
                    employee_id=row['employee_id'],
                    name=row['name'],
                    department=row['department'],
                    shift=row['shift'],
                    consent_given=bool(row['consent_given']),
                    active=bool(row['active'])
                )
                for row in cursor.fetchall()
            ]
    
    # ========================================================================
    # DETECCIONES
    # ========================================================================
    
    def add_detection(self, detection: DetectionEvent) -> Optional[int]:
        """Agrega un evento de detección"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO detection_events
                    (session_id, employee_id, track_id, timestamp, emotion,
                     confidence, stress_level, bounding_box, emotion_probabilities,
                     processing_time_ms)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    detection.session_id,
                    detection.employee_id,
                    detection.track_id,
                    detection.timestamp or datetime.now().isoformat(),
                    detection.emotion,
                    detection.confidence,
                    detection.stress_level,
                    detection.bounding_box,
                    detection.emotion_probabilities,
                    detection.processing_time_ms
                ))
                return cursor.lastrowid
        except Exception as e:
            print(f"⚠️ Error agregando detección: {e}")
            return None
    
    def get_detections(
        self,
        employee_id: Optional[str] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        limit: int = 1000
    ) -> List[DetectionEvent]:
        """Obtiene detecciones con filtros"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            query = "SELECT * FROM detection_events WHERE 1=1"
            params = []
            
            if employee_id:
                query += " AND employee_id = ?"
                params.append(employee_id)
            
            if start_time:
                query += " AND timestamp >= ?"
                params.append(start_time)
            
            if end_time:
                query += " AND timestamp <= ?"
                params.append(end_time)
            
            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            
            return [
                DetectionEvent(
                    detection_id=row['detection_id'],
                    session_id=row['session_id'],
                    employee_id=row['employee_id'],
                    track_id=row['track_id'],
                    timestamp=row['timestamp'],
                    emotion=row['emotion'],
                    confidence=row['confidence'],
                    stress_level=row['stress_level'],
                    bounding_box=row['bounding_box'],
                    emotion_probabilities=row['emotion_probabilities'],
                    processing_time_ms=row['processing_time_ms']
                )
                for row in cursor.fetchall()
            ]
    
    # ========================================================================
    # ALERTAS
    # ========================================================================
    
    def add_alert(self, alert: Alert) -> Optional[int]:
        """Agrega una alerta"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO alerts
                    (employee_id, alert_type, severity, stress_level, timestamp,
                     status, message)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    alert.employee_id,
                    alert.alert_type,
                    alert.severity,
                    alert.stress_level,
                    alert.timestamp,
                    alert.status,
                    alert.message
                ))
                return cursor.lastrowid
        except Exception as e:
            print(f"⚠️ Error agregando alerta: {e}")
            return None
    
    def get_alerts(
        self,
        status: Optional[str] = None,
        employee_id: Optional[str] = None,
        limit: int = 100
    ) -> List[Alert]:
        """Obtiene alertas con filtros"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            query = "SELECT * FROM alerts WHERE 1=1"
            params = []
            
            if status:
                query += " AND status = ?"
                params.append(status)
            
            if employee_id:
                query += " AND employee_id = ?"
                params.append(employee_id)
            
            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            
            return [
                Alert(
                    alert_id=row['alert_id'],
                    employee_id=row['employee_id'],
                    alert_type=row['alert_type'],
                    severity=row['severity'],
                    stress_level=row['stress_level'],
                    timestamp=row['timestamp'],
                    status=row['status'],
                    message=row['message'],
                    resolved_at=row['resolved_at'],
                    resolved_by=row['resolved_by']
                )
                for row in cursor.fetchall()
            ]
    
    def update_alert_status(
        self,
        alert_id: int,
        status: str,
        resolved_by: Optional[str] = None
    ) -> bool:
        """Actualiza el estado de una alerta"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                resolved_at = datetime.now().isoformat() if status == AlertStatus.RESOLVED.value else None
                
                cursor.execute("""
                    UPDATE alerts
                    SET status = ?, resolved_at = ?, resolved_by = ?
                    WHERE alert_id = ?
                """, (status, resolved_at, resolved_by, alert_id))
            return True
        except Exception as e:
            print(f"⚠️ Error actualizando alerta: {e}")
            return False
    
    # ========================================================================
    # SESIONES
    # ========================================================================
    
    def create_session(self, device_id: str, location: str = "Aula") -> Optional[str]:
        """Crea una nueva sesión"""
        session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO sessions (session_id, device_id, location, status)
                    VALUES (?, ?, ?, 'active')
                """, (session_id, device_id, location))
            return session_id
        except Exception as e:
            print(f"⚠️ Error creando sesión: {e}")
            return None
    
    def end_session(self, session_id: str) -> bool:
        """Finaliza una sesión"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE sessions
                    SET end_timestamp = CURRENT_TIMESTAMP, status = 'ended'
                    WHERE session_id = ?
                """, (session_id,))
            return True
        except Exception as e:
            print(f"⚠️ Error finalizando sesión: {e}")
            return False

