"""
👤 Reconocimiento Facial
Sistema de enrollment y reconocimiento de colaboradores
"""
import cv2
import numpy as np
import json
from pathlib import Path
from typing import Optional, Tuple, List, Dict
from deepface import DeepFace
from core.utils.types import Employee
import os

class FaceRecognizer:
    """
    Sistema de reconocimiento facial basado en embeddings
    """
    
    def __init__(self, enrollments_dir: str = "data/enrollments", threshold: float = 0.70):
        """
        Inicializa el reconocedor
        
        Args:
            enrollments_dir: Directorio con embeddings de enrollment
            threshold: Umbral de similitud para reconocimiento (0-1)
        """
        self.enrollments_dir = Path(enrollments_dir)
        self.enrollments_dir.mkdir(parents=True, exist_ok=True)
        self.threshold = threshold
        self.embeddings_cache: Dict[str, np.ndarray] = {}
        self._load_embeddings()
    
    def _load_embeddings(self):
        """Carga todos los embeddings desde archivos JSON"""
        self.embeddings_cache = {}
        
        for json_file in self.enrollments_dir.glob("*_embedding.json"):
            try:
                with open(json_file, 'r') as f:
                    data = json.load(f)
                    employee_id = data.get('employee_id')
                    embedding = np.array(data.get('embedding', []))
                    
                    if employee_id and len(embedding) > 0:
                        self.embeddings_cache[employee_id] = embedding
            except Exception as e:
                print(f"⚠️ Error cargando embedding {json_file}: {e}")
        
        print(f"✅ Cargados {len(self.embeddings_cache)} embeddings")
    
    def generate_embedding(self, face_roi: np.ndarray) -> Optional[np.ndarray]:
        """
        Genera embedding facial de 512 dimensiones
        
        Args:
            face_roi: ROI del rostro (BGR)
            
        Returns:
            Embedding vector o None si falla
        """
        try:
            # Usar DeepFace para generar embedding
            embedding = DeepFace.represent(
                face_roi,
                model_name='Facenet',
                enforce_detection=False,
                silent=True
            )
            
            if isinstance(embedding, list):
                embedding = embedding[0]
            
            embedding_vector = np.array(embedding.get('embedding', []))
            return embedding_vector
            
        except Exception as e:
            print(f"⚠️ Error generando embedding: {e}")
            return None
    
    def recognize_face(self, face_roi: np.ndarray) -> Tuple[Optional[str], float]:
        """
        Reconoce un rostro comparando con embeddings registrados
        
        Args:
            face_roi: ROI del rostro (BGR)
            
        Returns:
            Tupla (employee_id, confidence) o (None, 0.0) si no hay match
        """
        # Generar embedding del rostro
        query_embedding = self.generate_embedding(face_roi)
        
        if query_embedding is None or len(self.embeddings_cache) == 0:
            return (None, 0.0)
        
        # Comparar con todos los embeddings registrados
        best_match = None
        best_similarity = 0.0
        
        for employee_id, stored_embedding in self.embeddings_cache.items():
            similarity = self._cosine_similarity(query_embedding, stored_embedding)
            
            if similarity > best_similarity:
                best_similarity = similarity
                best_match = employee_id
        
        # Verificar umbral
        if best_similarity >= self.threshold:
            return (best_match, best_similarity)
        else:
            return (None, best_similarity)
    
    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """
        Calcula similitud coseno entre dos vectores
        
        Args:
            vec1: Vector 1
            vec2: Vector 2
            
        Returns:
            Similitud coseno (0-1)
        """
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    def enroll_employee(self, employee_id: str, face_samples: List[np.ndarray]) -> bool:
        """
        Registra un nuevo empleado con múltiples muestras
        
        Args:
            employee_id: ID del empleado
            face_samples: Lista de muestras faciales
            
        Returns:
            True si el enrollment fue exitoso
        """
        if len(face_samples) < 3:
            print("⚠️ Se requieren al menos 3 muestras para enrollment")
            return False
        
        embeddings = []
        
        # Generar embeddings de todas las muestras
        for sample in face_samples:
            embedding = self.generate_embedding(sample)
            if embedding is not None:
                embeddings.append(embedding)
        
        if len(embeddings) < 3:
            print("⚠️ No se pudieron generar suficientes embeddings")
            return False
        
        # Calcular embedding promedio
        avg_embedding = np.mean(embeddings, axis=0)
        
        # Calcular calidad (similitud entre muestras)
        similarities = []
        for i in range(len(embeddings)):
            for j in range(i + 1, len(embeddings)):
                sim = self._cosine_similarity(embeddings[i], embeddings[j])
                similarities.append(sim)
        
        quality_score = np.mean(similarities) if similarities else 0.0
        
        if quality_score < 0.70:
            print(f"⚠️ Calidad de enrollment baja: {quality_score:.2f}")
            return False
        
        # Guardar embedding
        embedding_data = {
            'employee_id': employee_id,
            'embedding': avg_embedding.tolist(),
            'quality_score': float(quality_score),
            'num_samples': len(embeddings)
        }
        
        json_path = self.enrollments_dir / f"{employee_id}_embedding.json"
        
        try:
            with open(json_path, 'w') as f:
                json.dump(embedding_data, f, indent=2)
            
            # Actualizar cache
            self.embeddings_cache[employee_id] = avg_embedding
            
            # Guardar muestras
            samples_dir = self.enrollments_dir / f"{employee_id}_samples"
            samples_dir.mkdir(exist_ok=True)
            
            for i, sample in enumerate(face_samples[:10]):  # Máximo 10 muestras
                sample_path = samples_dir / f"sample_{i+1}.jpg"
                cv2.imwrite(str(sample_path), sample)
            
            print(f"✅ Empleado {employee_id} registrado exitosamente (calidad: {quality_score:.2f})")
            return True
            
        except Exception as e:
            print(f"⚠️ Error guardando enrollment: {e}")
            return False
    
    def reload_embeddings(self):
        """Recarga embeddings desde disco"""
        self._load_embeddings()

