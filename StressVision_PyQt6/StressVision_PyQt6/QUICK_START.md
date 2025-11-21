# 🚀 Guía de Inicio Rápido - StressVision

## Instalación en 5 Pasos

### 1. Instalar Python
Asegúrate de tener Python 3.8 o superior:
```bash
python --version
```

### 2. Crear Entorno Virtual
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 3. Instalar Dependencias
```bash
pip install -r requirements.txt
```

**Nota**: La primera vez, DeepFace descargará modelos automáticamente (requiere internet).

### 4. Ejecutar la Aplicación
```bash
python main.py
```

### 5. Iniciar Monitoreo
1. Haz clic en "▶ Iniciar Monitoreo"
2. Ajusta el índice de cámara si es necesario
3. ¡Listo! El sistema comenzará a detectar rostros y emociones

## Primeros Pasos

### Registrar un Empleado

1. **Abrir terminal** en el directorio del proyecto
2. **Ejecutar script de enrollment**:
   ```bash
   python scripts/enroll_employee.py EMP001 "Juan Pérez" 10
   ```
3. **Seguir instrucciones**:
   - Posiciona el rostro frente a la cámara
   - Presiona ESPACIO para capturar cada muestra
   - Se requieren mínimo 3 muestras (recomendado: 10)
4. **Verificar**: El empleado aparecerá en el tab "Empleados"

### Ver Métricas de un Empleado

1. Ve al tab **"Tiempo Real"**
2. En el panel derecho, selecciona el empleado del dropdown
3. Las métricas se actualizarán automáticamente cada segundo

### Gestionar Alertas

1. Ve al tab **"Alertas"**
2. Verás todas las alertas pendientes
3. Selecciona una alerta y haz clic en:
   - **"✓ Reconocer"**: Marca la alerta como reconocida
   - **"✓ Resolver"**: Marca la alerta como resuelta

## Configuración Básica

### Cambiar Backend de Detección

En `config.py`:
```python
FACE_DETECTION_BACKEND = "opencv"  # Más rápido
# o
FACE_DETECTION_BACKEND = "mediapipe"  # Más preciso
```

### Ajustar Rendimiento

En `app/main_window.py`, clase `VideoThread`:
```python
self.frame_skip = 5  # Analizar 1 de cada 5 frames (más rápido)
# o
self.frame_skip = 1  # Analizar todos los frames (más preciso)
```

### Cambiar Umbral de Alertas

En `config.py`:
```python
ALERT_THRESHOLD = 10  # Número de eventos de estrés
ALERT_WINDOW_MINUTES = 15  # Ventana de tiempo
```

## Solución de Problemas Comunes

### ❌ "No se pudo abrir la cámara"

**Solución**:
- Verifica que la cámara no esté siendo usada por otra app
- Prueba diferentes índices: 0, 1, 2...
- En Windows: Verifica permisos de cámara en Configuración

### ❌ FPS muy bajos (< 5 FPS)

**Solución**:
- Aumenta `frame_skip` a 5 o más
- Usa backend `opencv` en lugar de `mediapipe`
- Cierra otras aplicaciones que usen CPU

### ❌ "Error generando embedding"

**Solución**:
- Asegúrate de tener conexión a internet la primera vez
- Verifica que el rostro esté bien iluminado
- Captura más muestras (10-15)

### ❌ Base de datos bloqueada

**Solución**:
- Cierra otras instancias de la aplicación
- Verifica permisos de escritura en `data/`
- Elimina `data/stressvision.db` si está corrupto (se recreará)

## Próximos Pasos

1. ✅ **Registrar empleados**: Usa el script de enrollment
2. ✅ **Configurar alertas**: Ajusta umbrales según necesidades
3. ✅ **Revisar reportes**: Los reportes se generan cada 15 minutos
4. ✅ **Exportar datos**: (Funcionalidad futura)

## Recursos Adicionales

- **Documentación completa**: `README.md`
- **Configuración avanzada**: `config.py`
- **Estructura del proyecto**: Ver `README.md` sección "Estructura"

---

¿Problemas? Revisa los logs en `logs/` o consulta la documentación completa.

