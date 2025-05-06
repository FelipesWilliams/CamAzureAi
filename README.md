# Vision Project - Azure AI

Esta aplicación permite capturar y analizar imágenes del escritorio usando Azure Computer Vision.

## Características

- Marco rojo ajustable en tamaño y posición
- Captura de imagen dentro del marco
- Análisis de imagen usando Azure Computer Vision
- Detección de objetos, etiquetas y descripción de la imagen
- Interfaz gráfica intuitiva

## Requisitos

- Python 3.7 o superior
- Cuenta de Azure con servicio Computer Vision activo

## Instalación

1. Clonar o descargar este repositorio
2. Instalar las dependencias:
```bash
pip install -r requirements.txt
```

3. Crear un archivo `.env` en la raíz del proyecto con las siguientes variables:
```
AZURE_VISION_ENDPOINT=your_endpoint_here
AZURE_VISION_KEY=your_key_here
```

## Uso

1. Ejecutar la aplicación:
```bash
python vision_app.py
```

2. Usar el marco rojo:
   - Click izquierdo y arrastrar para mover
   - Click derecho y arrastrar para redimensionar
   - Botón "Capturar y Analizar" para procesar la imagen

3. Los resultados se mostrarán en el área de texto inferior

## Notas

- La aplicación necesita permisos para capturar la pantalla
- Asegúrate de tener una conexión a internet activa
- Las credenciales de Azure deben ser válidas # CamAzureAi
