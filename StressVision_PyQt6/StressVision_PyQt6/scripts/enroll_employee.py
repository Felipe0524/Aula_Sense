"""
📝 Script de Enrollment de Empleados
Permite registrar nuevos empleados en el sistema
"""
import cv2
import sys
from pathlib import Path

# Agregar directorio raíz al path
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

from core.detectors.face_detector import FaceDetector
from core.detectors.face_recognizer import FaceRecognizer

def enroll_employee_from_camera(employee_id: str, name: str, num_samples: int = 10):
    """
    Registra un empleado desde la cámara
    
    Args:
        employee_id: ID único del empleado
        name: Nombre del empleado
        num_samples: Número de muestras a capturar
    """
    print(f"📝 Iniciando enrollment para: {name} ({employee_id})")
    print(f"📸 Se capturarán {num_samples} muestras")
    print("Presiona ESPACIO para capturar, ESC para salir\n")
    
    # Inicializar detectores
    face_detector = FaceDetector(backend="mediapipe")
    face_recognizer = FaceRecognizer()
    
    # Abrir cámara
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    if not cap.isOpened():
        print("❌ Error: No se pudo abrir la cámara")
        return False
    
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    
    samples = []
    sample_count = 0
    
    print("✅ Cámara lista. Posiciona el rostro frente a la cámara...")
    
    while sample_count < num_samples:
        ret, frame = cap.read()
        if not ret:
            break
        
        # Detectar rostros
        faces = face_detector.detect_faces(frame)
        
        # Dibujar en frame
        display_frame = frame.copy()
        
        if faces:
            face = faces[0]  # Tomar el primer rostro
            x, y, w, h = face.bbox
            
            # Dibujar bounding box
            cv2.rectangle(display_frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.putText(
                display_frame,
                f"Muestra {sample_count + 1}/{num_samples}",
                (x, y - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2
            )
        else:
            cv2.putText(
                display_frame,
                "No se detecta rostro",
                (50, 50),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 0, 255),
                2
            )
        
        cv2.putText(
            display_frame,
            f"Presiona ESPACIO para capturar ({sample_count}/{num_samples})",
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2
        )
        
        cv2.imshow("Enrollment - Presiona ESPACIO para capturar", display_frame)
        
        key = cv2.waitKey(1) & 0xFF
        
        if key == 27:  # ESC
            print("❌ Enrollment cancelado")
            break
        elif key == 32 and faces:  # ESPACIO
            # Capturar muestra
            face = faces[0]
            x, y, w, h = face.bbox
            
            # Extraer ROI con padding
            padding = 20
            x1 = max(0, x - padding)
            y1 = max(0, y - padding)
            x2 = min(frame.shape[1], x + w + padding)
            y2 = min(frame.shape[0], y + h + padding)
            
            face_roi = frame[y1:y2, x1:x2]
            
            if face_roi.size > 0:
                samples.append(face_roi)
                sample_count += 1
                print(f"✅ Muestra {sample_count}/{num_samples} capturada")
    
    cap.release()
    cv2.destroyAllWindows()
    
    if len(samples) < 3:
        print(f"❌ Se requieren al menos 3 muestras. Solo se capturaron {len(samples)}")
        return False
    
    # Realizar enrollment
    print(f"\n🔄 Procesando {len(samples)} muestras...")
    success = face_recognizer.enroll_employee(employee_id, samples)
    
    if success:
        print(f"✅ Empleado {name} ({employee_id}) registrado exitosamente")
        
        # Guardar información adicional en base de datos
        from core.database.database import Database
        from core.utils.types import Employee
        
        db = Database()
        employee = Employee(
            employee_id=employee_id,
            name=name,
            department="",
            consent_given=True,
            active=True
        )
        db.add_employee(employee)
        
        return True
    else:
        print(f"❌ Error en el enrollment. Verifica la calidad de las muestras.")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Uso: python enroll_employee.py <employee_id> <nombre> [num_samples]")
        print("Ejemplo: python enroll_employee.py EMP001 'Juan Pérez' 10")
        sys.exit(1)
    
    employee_id = sys.argv[1]
    name = sys.argv[2]
    num_samples = int(sys.argv[3]) if len(sys.argv) > 3 else 10
    
    enroll_employee_from_camera(employee_id, name, num_samples)

