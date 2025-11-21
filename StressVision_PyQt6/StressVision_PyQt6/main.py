"""
🎯 StressVision - Sistema de Detección de Estrés Laboral
Aplicación PyQt6 para detección en tiempo real
"""
import sys
import os
from pathlib import Path

# Agregar directorio raíz al path
ROOT_DIR = Path(__file__).parent
sys.path.insert(0, str(ROOT_DIR))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from app.main_window import MainWindow

def main():
    """Punto de entrada principal de la aplicación"""
    # Configurar variables de entorno para TensorFlow
    os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
    os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
    
    # Crear aplicación Qt
    app = QApplication(sys.argv)
    app.setApplicationName("StressVision")
    app.setOrganizationName("Gloria S.A.")
    
    # Configurar estilo
    app.setStyle("Fusion")
    
    # Crear ventana principal
    window = MainWindow()
    window.show()
    
    # Ejecutar loop de eventos
    sys.exit(app.exec())

if __name__ == "__main__":
    main()

