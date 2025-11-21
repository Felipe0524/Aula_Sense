"""
👁️ Detector Facial Multi-Rostro
Soporta MediaPipe y OpenCV para detección en tiempo real
"""
import cv2
import numpy as np
from typing import List, Optional
import mediapipe as mp
from core.utils.types import FaceRegion

class FaceDetector:
    """
    Detector facial que soporta múltiples backends
    """
    
    def __init__(self, backend: str = "mediapipe", min_face_size: int = 30):
        """
        Inicializa el detector facial
        
        Args:
            backend: "mediapipe" o "opencv"
            min_face_size: Tamaño mínimo de rostro en píxeles
        """
        self.backend = backend
        self.min_face_size = min_face_size
        
        if backend == "mediapipe":
            self._init_mediapipe()
        elif backend == "opencv":
            self._init_opencv()
        else:
            raise ValueError(f"Backend no soportado: {backend}")
    
    def _init_mediapipe(self):
        """Inicializa MediaPipe Face Detection"""
        self.mp_face_detection = mp.solutions.face_detection
        self.face_detection = self.mp_face_detection.FaceDetection(
            model_selection=1,  # 0: corto alcance, 1: largo alcance
            min_detection_confidence=0.5
        )
    
    def _init_opencv(self):
        """Inicializa OpenCV Haar Cascades"""
        cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        self.face_cascade = cv2.CascadeClassifier(cascade_path)
        if self.face_cascade.empty():
            raise RuntimeError("No se pudo cargar el clasificador Haar Cascade")
    
    def detect_faces(self, frame: np.ndarray) -> List[FaceRegion]:
        """
        Detecta rostros en un frame
        
        Args:
            frame: Frame BGR de OpenCV
            
        Returns:
            Lista de FaceRegion detectadas
        """
        if self.backend == "mediapipe":
            return self._detect_mediapipe(frame)
        else:
            return self._detect_opencv(frame)
    
    def _detect_mediapipe(self, frame: np.ndarray) -> List[FaceRegion]:
        """Detección con MediaPipe"""
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.face_detection.process(rgb_frame)
        
        faces = []
        h, w = frame.shape[:2]
        
        if results.detections:
            for detection in results.detections:
                bbox = detection.location_data.relative_bounding_box
                
                # Convertir coordenadas relativas a absolutas
                x = int(bbox.xmin * w)
                y = int(bbox.ymin * h)
                width = int(bbox.width * w)
                height = int(bbox.height * h)
                
                # Validar tamaño mínimo
                if width >= self.min_face_size and height >= self.min_face_size:
                    confidence = detection.score[0]
                    faces.append(FaceRegion(
                        x=x,
                        y=y,
                        width=width,
                        height=height,
                        confidence=float(confidence)
                    ))
        
        return faces
    
    def _detect_opencv(self, frame: np.ndarray) -> List[FaceRegion]:
        """Detección con OpenCV Haar Cascades"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        detections = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(self.min_face_size, self.min_face_size),
            flags=cv2.CASCADE_SCALE_IMAGE
        )
        
        faces = []
        for (x, y, w, h) in detections:
            faces.append(FaceRegion(
                x=int(x),
                y=int(y),
                width=int(w),
                height=int(h),
                confidence=0.8  # OpenCV no proporciona confidence
            ))
        
        return faces
    
    def release(self):
        """Libera recursos"""
        if self.backend == "mediapipe" and hasattr(self, 'face_detection'):
            self.face_detection.close()

