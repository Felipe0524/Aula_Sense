"""
🖥️ Ventana Principal de StressVision
Interfaz gráfica PyQt6 para detección en tiempo real
"""
import sys
import cv2
import numpy as np
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QLabel, QPushButton, QComboBox, QTextEdit, QTableWidget,
    QTableWidgetItem, QGroupBox, QGridLayout, QSpinBox, QCheckBox
)
from PyQt6.QtCore import QThread, pyqtSignal, QTimer, Qt, QSize
from PyQt6.QtGui import QImage, QPixmap, QFont
from typing import Optional, Dict, List
import time
from datetime import datetime

from core.detectors.face_detector import FaceDetector
from core.detectors.emotion_analyzer import EmotionAnalyzer
from core.detectors.face_recognizer import FaceRecognizer
from core.services.stress_calculator import StressCalculator
from core.services.alert_manager import AlertManager
from core.services.report_generator import ReportGenerator
from core.database.database import Database
from core.utils.types import DetectionResult, Alert, Employee

class VideoThread(QThread):
    """Thread para captura y procesamiento de video"""
    
    frame_ready = pyqtSignal(np.ndarray, list)  # frame, detections
    fps_updated = pyqtSignal(float)
    
    def __init__(self, camera_index: int = 0):
        super().__init__()
        self.camera_index = camera_index
        self.running = False
        self.cap = None
        
        # Inicializar detectores
        self.face_detector = FaceDetector(backend="mediapipe")
        self.emotion_analyzer = EmotionAnalyzer(use_ensemble=False)
        self.face_recognizer = FaceRecognizer()
        
        # Configuración
        self.frame_skip = 3  # Analizar 1 de cada N frames
        self.frame_count = 0
        
        # Métricas
        self.fps_counter = 0
        self.fps_last_time = time.time()
    
    def start_capture(self):
        """Inicia la captura de video"""
        self.cap = cv2.VideoCapture(self.camera_index, cv2.CAP_DSHOW)
        if not self.cap.isOpened():
            print(f"⚠️ No se pudo abrir cámara {self.camera_index}")
            return False
        
        # Configurar resolución
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        self.cap.set(cv2.CAP_PROP_FPS, 30)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        
        self.running = True
        self.start()
        return True
    
    def stop_capture(self):
        """Detiene la captura"""
        self.running = False
        if self.cap:
            self.cap.release()
        self.wait()
    
    def run(self):
        """Loop principal de procesamiento"""
        last_detections = []
        
        while self.running:
            ret, frame = self.cap.read()
            if not ret:
                break
            
            self.frame_count += 1
            
            # Calcular FPS
            self.fps_counter += 1
            current_time = time.time()
            if current_time - self.fps_last_time >= 1.0:
                fps = self.fps_counter
                self.fps_updated.emit(fps)
                self.fps_counter = 0
                self.fps_last_time = current_time
            
            # Procesar frame (con frame skipping)
            if self.frame_count % self.frame_skip == 0:
                # Detectar rostros
                faces = self.face_detector.detect_faces(frame)
                
                # Analizar emociones
                detections = []
                for face_region in faces:
                    x, y, w, h = face_region.bbox
                    face_roi = frame[y:y+h, x:x+w]
                    
                    if face_roi.size > 0:
                        # Análisis emocional
                        emotion_result = self.emotion_analyzer.analyze_face(face_roi)
                        
                        # Reconocimiento facial
                        employee_id, recog_confidence = self.face_recognizer.recognize_face(face_roi)
                        
                        detection = DetectionResult(
                            face_region=face_region,
                            emotion=emotion_result,
                            employee_id=employee_id,
                            recognition_confidence=recog_confidence
                        )
                        detections.append(detection)
                
                last_detections = detections
            
            # Dibujar overlays
            annotated_frame = self._draw_overlays(frame.copy(), last_detections)
            
            # Emitir frame
            self.frame_ready.emit(annotated_frame, last_detections)
            
            # Pequeña pausa para no saturar CPU
            self.msleep(10)
    
    def _draw_overlays(self, frame: np.ndarray, detections: List[DetectionResult]) -> np.ndarray:
        """Dibuja overlays en el frame"""
        from core.utils.types import EMOTION_COLORS, EMOTION_LABELS_ES
        
        for detection in detections:
            x, y, w, h = detection.face_region.bbox
            
            # Color según emoción
            emotion = detection.emotion.emotion
            color = EMOTION_COLORS.get(emotion, (200, 200, 200))
            
            # Dibujar bounding box
            cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
            
            # Etiqueta de emoción
            emotion_label = EMOTION_LABELS_ES.get(emotion, emotion)
            confidence = detection.emotion.confidence
            
            label_text = f"{emotion_label} ({confidence:.0%})"
            if detection.employee_id:
                label_text = f"{detection.employee_id}: {label_text}"
            
            # Fondo para texto
            (text_width, text_height), _ = cv2.getTextSize(
                label_text, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2
            )
            cv2.rectangle(
                frame,
                (x, y - text_height - 10),
                (x + text_width, y),
                color,
                -1
            )
            
            # Texto
            cv2.putText(
                frame,
                label_text,
                (x, y - 5),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (255, 255, 255),
                2
            )
        
        return frame

class MainWindow(QMainWindow):
    """Ventana principal de la aplicación"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("StressVision - Sistema de Detección de Estrés")
        self.setGeometry(100, 100, 1400, 900)
        
        # Inicializar componentes
        self.database = Database()
        self.stress_calculator = StressCalculator()
        self.alert_manager = AlertManager(self.database, self.stress_calculator)
        self.report_generator = ReportGenerator(
            self.database,
            self.stress_calculator
        )
        
        # Thread de video
        self.video_thread: Optional[VideoThread] = None
        
        # Estado
        self.current_session_id: Optional[str] = None
        self.selected_employee_id: Optional[str] = None
        
        # Timers
        self.alert_timer = QTimer()
        self.alert_timer.timeout.connect(self.check_alerts)
        self.alert_timer.start(30000)  # Cada 30 segundos
        
        self.report_timer = QTimer()
        self.report_timer.timeout.connect(self.generate_periodic_report)
        self.report_timer.start(900000)  # Cada 15 minutos
        
        # UI
        self._init_ui()
        
        # Cargar empleados
        self._load_employees()
    
    def _init_ui(self):
        """Inicializa la interfaz de usuario"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)
        
        # Barra de herramientas superior
        toolbar = self._create_toolbar()
        main_layout.addWidget(toolbar)
        
        # Tabs principales
        self.tabs = QTabWidget()
        
        # Tab 1: Monitoreo en Tiempo Real
        self.realtime_tab = self._create_realtime_tab()
        self.tabs.addTab(self.realtime_tab, "📹 Tiempo Real")
        
        # Tab 2: Dashboard
        self.dashboard_tab = self._create_dashboard_tab()
        self.tabs.addTab(self.dashboard_tab, "📊 Dashboard")
        
        # Tab 3: Alertas
        self.alerts_tab = self._create_alerts_tab()
        self.tabs.addTab(self.alerts_tab, "🚨 Alertas")
        
        # Tab 4: Empleados
        self.employees_tab = self._create_employees_tab()
        self.tabs.addTab(self.employees_tab, "👥 Empleados")
        
        main_layout.addWidget(self.tabs)
        
        # Barra de estado
        self.statusBar().showMessage("Listo")
    
    def _create_toolbar(self) -> QWidget:
        """Crea barra de herramientas"""
        toolbar = QWidget()
        layout = QHBoxLayout()
        toolbar.setLayout(layout)
        
        # Botón iniciar/detener
        self.start_btn = QPushButton("▶ Iniciar Monitoreo")
        self.start_btn.clicked.connect(self.toggle_monitoring)
        layout.addWidget(self.start_btn)
        
        # Selector de cámara
        layout.addWidget(QLabel("Cámara:"))
        self.camera_combo = QSpinBox()
        self.camera_combo.setMinimum(0)
        self.camera_combo.setMaximum(10)
        self.camera_combo.setValue(0)
        layout.addWidget(self.camera_combo)
        
        layout.addStretch()
        
        # Métricas rápidas
        self.fps_label = QLabel("FPS: 0")
        layout.addWidget(self.fps_label)
        
        self.detections_label = QLabel("Detecciones: 0")
        layout.addWidget(self.detections_label)
        
        self.stress_label = QLabel("Estrés: 0%")
        layout.addWidget(self.stress_label)
        
        return toolbar
    
    def _create_realtime_tab(self) -> QWidget:
        """Crea tab de monitoreo en tiempo real"""
        widget = QWidget()
        layout = QHBoxLayout()
        widget.setLayout(layout)
        
        # Panel izquierdo: Video
        video_group = QGroupBox("Video en Tiempo Real")
        video_layout = QVBoxLayout()
        video_group.setLayout(video_layout)
        
        self.video_label = QLabel()
        self.video_label.setMinimumSize(960, 540)
        self.video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_label.setText("Presiona 'Iniciar Monitoreo' para comenzar")
        self.video_label.setStyleSheet("background-color: black; color: white;")
        video_layout.addWidget(self.video_label)
        
        layout.addWidget(video_group, 2)
        
        # Panel derecho: Métricas y controles
        metrics_group = QGroupBox("Métricas y Controles")
        metrics_layout = QVBoxLayout()
        metrics_group.setLayout(metrics_layout)
        
        # Selector de empleado
        metrics_layout.addWidget(QLabel("Ver métricas de:"))
        self.employee_combo = QComboBox()
        self.employee_combo.addItem("Todos (Global)", None)
        self.employee_combo.currentIndexChanged.connect(self.on_employee_selected)
        metrics_layout.addWidget(self.employee_combo)
        
        # Métricas del empleado seleccionado
        self.metrics_text = QTextEdit()
        self.metrics_text.setReadOnly(True)
        self.metrics_text.setMaximumHeight(300)
        metrics_layout.addWidget(self.metrics_text)
        
        # Actualizar métricas cada segundo
        self.metrics_timer = QTimer()
        self.metrics_timer.timeout.connect(self.update_metrics)
        self.metrics_timer.start(1000)
        
        layout.addWidget(metrics_group, 1)
        
        return widget
    
    def _create_dashboard_tab(self) -> QWidget:
        """Crea tab de dashboard"""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)
        
        # Grid de métricas
        metrics_grid = QGridLayout()
        
        # Métricas principales
        self.total_detections_label = QLabel("0")
        self.total_detections_label.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        metrics_grid.addWidget(QLabel("Total Detecciones:"), 0, 0)
        metrics_grid.addWidget(self.total_detections_label, 0, 1)
        
        self.avg_stress_label = QLabel("0%")
        self.avg_stress_label.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        metrics_grid.addWidget(QLabel("Estrés Promedio:"), 1, 0)
        metrics_grid.addWidget(self.avg_stress_label, 1, 1)
        
        self.active_employees_label = QLabel("0")
        self.active_employees_label.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        metrics_grid.addWidget(QLabel("Empleados Activos:"), 2, 0)
        metrics_grid.addWidget(self.active_employees_label, 2, 1)
        
        self.pending_alerts_label = QLabel("0")
        self.pending_alerts_label.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        metrics_grid.addWidget(QLabel("Alertas Pendientes:"), 3, 0)
        metrics_grid.addWidget(self.pending_alerts_label, 3, 1)
        
        layout.addLayout(metrics_grid)
        
        # Actualizar dashboard cada 5 segundos
        self.dashboard_timer = QTimer()
        self.dashboard_timer.timeout.connect(self.update_dashboard)
        self.dashboard_timer.start(5000)
        
        return widget
    
    def _create_alerts_tab(self) -> QWidget:
        """Crea tab de alertas"""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)
        
        # Tabla de alertas
        self.alerts_table = QTableWidget()
        self.alerts_table.setColumnCount(6)
        self.alerts_table.setHorizontalHeaderLabels([
            "ID", "Empleado", "Tipo", "Severidad", "Estrés", "Estado"
        ])
        layout.addWidget(self.alerts_table)
        
        # Botones de acción
        buttons_layout = QHBoxLayout()
        
        self.refresh_alerts_btn = QPushButton("🔄 Actualizar")
        self.refresh_alerts_btn.clicked.connect(self.refresh_alerts)
        buttons_layout.addWidget(self.refresh_alerts_btn)
        
        self.acknowledge_btn = QPushButton("✓ Reconocer")
        self.acknowledge_btn.clicked.connect(self.acknowledge_selected_alert)
        buttons_layout.addWidget(self.acknowledge_btn)
        
        self.resolve_btn = QPushButton("✓ Resolver")
        self.resolve_btn.clicked.connect(self.resolve_selected_alert)
        buttons_layout.addWidget(self.resolve_btn)
        
        buttons_layout.addStretch()
        layout.addLayout(buttons_layout)
        
        return widget
    
    def _create_employees_tab(self) -> QWidget:
        """Crea tab de empleados"""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)
        
        # Tabla de empleados
        self.employees_table = QTableWidget()
        self.employees_table.setColumnCount(5)
        self.employees_table.setHorizontalHeaderLabels([
            "ID", "Nombre", "Departamento", "Turno", "Estado"
        ])
        layout.addWidget(self.employees_table)
        
        return widget
    
    def toggle_monitoring(self):
        """Inicia o detiene el monitoreo"""
        if self.video_thread is None or not self.video_thread.isRunning():
            # Iniciar
            camera_index = self.camera_combo.value()
            self.video_thread = VideoThread(camera_index)
            self.video_thread.frame_ready.connect(self.on_frame_ready)
            self.video_thread.fps_updated.connect(self.on_fps_updated)
            
            if self.video_thread.start_capture():
                self.start_btn.setText("⏸ Detener Monitoreo")
                self.statusBar().showMessage("Monitoreo activo")
                
                # Crear sesión
                self.current_session_id = self.database.create_session(
                    device_id=f"camera_{camera_index}",
                    location="Aula"
                )
            else:
                self.statusBar().showMessage("Error: No se pudo abrir la cámara")
        else:
            # Detener
            self.video_thread.stop_capture()
            self.video_thread = None
            self.start_btn.setText("▶ Iniciar Monitoreo")
            self.statusBar().showMessage("Monitoreo detenido")
            
            # Finalizar sesión
            if self.current_session_id:
                self.database.end_session(self.current_session_id)
                self.current_session_id = None
    
    def on_frame_ready(self, frame: np.ndarray, detections: List[DetectionResult]):
        """Callback cuando hay un nuevo frame"""
        # Convertir frame a QImage
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_frame.shape
        bytes_per_line = ch * w
        qt_image = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
        
        # Escalar si es necesario
        pixmap = QPixmap.fromImage(qt_image)
        scaled_pixmap = pixmap.scaled(
            self.video_label.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        
        self.video_label.setPixmap(scaled_pixmap)
        
        # Procesar detecciones
        self.process_detections(detections)
    
    def process_detections(self, detections: List[DetectionResult]):
        """Procesa las detecciones y actualiza base de datos"""
        from core.utils.types import DetectionEvent
        
        for detection in detections:
            # Agregar a calculadora de estrés
            self.stress_calculator.add_emotion(
                emotion=detection.emotion.emotion,
                employee_id=detection.employee_id,
                confidence=detection.emotion.confidence
            )
            
            # Guardar en base de datos
            stress_level = self.stress_calculator.calculate_stress_index(
                employee_id=detection.employee_id
            ) / 100.0
            
            detection_event = DetectionEvent(
                session_id=self.current_session_id,
                employee_id=detection.employee_id,
                track_id=detection.track_id,
                timestamp=datetime.now().isoformat(),
                emotion=detection.emotion.emotion,
                confidence=detection.emotion.confidence,
                stress_level=stress_level,
                bounding_box=str(detection.face_region.bbox),
                emotion_probabilities=str(detection.emotion.probabilities)
            )
            
            self.database.add_detection(detection_event)
        
        # Actualizar contador
        self.detections_label.setText(f"Detecciones: {len(detections)}")
    
    def on_fps_updated(self, fps: float):
        """Callback cuando se actualiza el FPS"""
        self.fps_label.setText(f"FPS: {fps:.1f}")
    
    def on_employee_selected(self, index: int):
        """Callback cuando se selecciona un empleado"""
        self.selected_employee_id = self.employee_combo.itemData(index)
        self.update_metrics()
    
    def update_metrics(self):
        """Actualiza las métricas mostradas"""
        metrics = self.stress_calculator.get_metrics(
            employee_id=self.selected_employee_id
        )
        
        text = f"""
        <h3>Métricas {'del Empleado' if self.selected_employee_id else 'Globales'}</h3>
        <b>Índice de Estrés:</b> {metrics['stress_index']:.1f}%<br>
        <b>Total Detecciones:</b> {metrics['total_detections']}<br>
        <b>Emociones Negativas:</b> {metrics['negative_count']} ({metrics['negative_percentage']:.1f}%)<br>
        <b>Emoción Predominante:</b> {metrics['predominant_emotion']}<br>
        <b>Eventos de Estrés:</b> {metrics['stress_events_count']}<br>
        """
        
        self.metrics_text.setHtml(text)
        
        # Actualizar label de estrés
        self.stress_label.setText(f"Estrés: {metrics['stress_index']:.1f}%")
    
    def update_dashboard(self):
        """Actualiza el dashboard"""
        # Obtener métricas globales
        metrics = self.stress_calculator.get_metrics()
        
        self.total_detections_label.setText(str(metrics['total_detections']))
        self.avg_stress_label.setText(f"{metrics['stress_index']:.1f}%")
        
        # Empleados activos
        employees = self.database.get_all_employees(active_only=True)
        self.active_employees_label.setText(str(len(employees)))
        
        # Alertas pendientes
        pending_alerts = self.alert_manager.get_pending_alerts()
        self.pending_alerts_label.setText(str(len(pending_alerts)))
    
    def check_alerts(self):
        """Verifica y genera alertas"""
        alerts = self.alert_manager.check_and_generate_alerts(
            employee_id=self.selected_employee_id
        )
        
        if alerts:
            self.statusBar().showMessage(f"⚠️ {len(alerts)} nueva(s) alerta(s) generada(s)")
            self.refresh_alerts()
    
    def refresh_alerts(self):
        """Actualiza la tabla de alertas"""
        alerts = self.alert_manager.get_pending_alerts(limit=100)
        
        self.alerts_table.setRowCount(len(alerts))
        
        for row, alert in enumerate(alerts):
            self.alerts_table.setItem(row, 0, QTableWidgetItem(str(alert.alert_id)))
            self.alerts_table.setItem(row, 1, QTableWidgetItem(alert.employee_id or "Global"))
            self.alerts_table.setItem(row, 2, QTableWidgetItem(alert.alert_type))
            self.alerts_table.setItem(row, 3, QTableWidgetItem(alert.severity))
            self.alerts_table.setItem(row, 4, QTableWidgetItem(f"{alert.stress_level:.1%}"))
            self.alerts_table.setItem(row, 5, QTableWidgetItem(alert.status))
    
    def acknowledge_selected_alert(self):
        """Reconoce la alerta seleccionada"""
        current_row = self.alerts_table.currentRow()
        if current_row >= 0:
            alert_id = int(self.alerts_table.item(current_row, 0).text())
            self.alert_manager.acknowledge_alert(alert_id, "user")
            self.refresh_alerts()
    
    def resolve_selected_alert(self):
        """Resuelve la alerta seleccionada"""
        current_row = self.alerts_table.currentRow()
        if current_row >= 0:
            alert_id = int(self.alerts_table.item(current_row, 0).text())
            self.alert_manager.resolve_alert(alert_id, "user")
            self.refresh_alerts()
    
    def generate_periodic_report(self):
        """Genera reporte periódico"""
        report = self.report_generator.generate_report()
        if report:
            self.statusBar().showMessage(f"📊 Reporte generado: {report['total_detections']} detecciones")
    
    def _load_employees(self):
        """Carga empleados en el combo"""
        employees = self.database.get_all_employees(active_only=True)
        
        self.employee_combo.clear()
        self.employee_combo.addItem("Todos (Global)", None)
        
        for employee in employees:
            self.employee_combo.addItem(
                f"{employee.name} ({employee.employee_id})",
                employee.employee_id
            )
    
    def closeEvent(self, event):
        """Evento al cerrar la ventana"""
        if self.video_thread and self.video_thread.isRunning():
            self.video_thread.stop_capture()
        
        if self.current_session_id:
            self.database.end_session(self.current_session_id)
        
        event.accept()

