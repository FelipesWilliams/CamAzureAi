import tkinter as tk
from PIL import ImageGrab, Image, ImageTk
import cv2
import numpy as np
import requests
import json
import io
import time
import os
import math
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

class VisionApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Vision Project - Azure AI")
        
        # Configuración de Azure desde variables de entorno
        self.endpoint = os.getenv("AZURE_VISION_ENDPOINT")
        self.api_key = os.getenv("AZURE_VISION_KEY")
        
        if not self.endpoint or not self.api_key:
            raise ValueError("Por favor configura las variables de entorno AZURE_VISION_ENDPOINT y AZURE_VISION_KEY")

        # Inicializar la captura de video
        self.cap = cv2.VideoCapture(0)
        self.is_analyzing = False
        self.detected_objects = []
        
        # Inicializar los componentes de la interfaz
        self.setup_ui()
        
        # Iniciar el bucle de video
        self.update_video()

    def setup_ui(self):
        # Panel izquierdo (área de video)
        self.left_panel = tk.Frame(self.root, bg='black')
        self.left_panel.place(x=0, y=0, relwidth=0.7, relheight=1.0)
        
        # Canvas para mostrar el video
        self.video_canvas = tk.Canvas(self.left_panel, bg='black', highlightthickness=0)
        self.video_canvas.place(x=0, y=0, relwidth=1.0, relheight=1.0)
        
        # Panel derecho para resultados y controles
        self.right_panel = tk.Frame(self.root, bg='black')
        self.right_panel.place(relx=0.7, y=0, relwidth=0.3, relheight=1.0)
        
        # Título del panel
        self.title_label = tk.Label(self.right_panel, 
                                  text="Azure Vision AI", 
                                  bg='black', 
                                  fg='#00ff00',
                                  font=('Arial', 14, 'bold'))
        self.title_label.pack(pady=10)
        
        # Botón de análisis
        self.analyze_btn = tk.Button(self.right_panel,
                                   text="Analizar",
                                   command=self.toggle_analysis,
                                   bg='#1a1a1a',
                                   fg='#00ff00',
                                   font=('Arial', 12, 'bold'),
                                   relief=tk.FLAT,
                                   width=15,
                                   height=2)
        self.analyze_btn.pack(pady=20)
        
        # Área de resultados
        self.result_text = tk.Text(self.right_panel, 
                                 height=30, 
                                 width=35, 
                                 bg='black', 
                                 fg='white', 
                                 font=('Arial', 10))
        self.result_text.pack(padx=10, pady=10, fill='both', expand=True)
        
        # Configurar tags para el formato del texto
        self.result_text.tag_configure('title', font=('Arial', 12, 'bold'), foreground='#00ff00')
        self.result_text.tag_configure('subtitle', font=('Arial', 10, 'bold'), foreground='#00ccff')
        self.result_text.tag_configure('tag', font=('Arial', 10), foreground='#ffcc00')
        self.result_text.tag_configure('error', font=('Arial', 10, 'bold'), foreground='#ff0000')

    def toggle_analysis(self):
        self.is_analyzing = not self.is_analyzing
        if self.is_analyzing:
            self.analyze_btn.configure(text="Detener", fg='#ff0000')
        else:
            self.analyze_btn.configure(text="Analizar", fg='#00ff00')
            self.detected_objects = []
            self.result_text.delete(1.0, tk.END)

    def update_video(self):
        ret, frame = self.cap.read()
        if ret:
            # Convertir frame de BGR a RGB
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            if self.is_analyzing and time.time() - getattr(self, 'last_analysis', 0) > 1:
                self.last_analysis = time.time()
                self.analyze_frame(frame_rgb.copy())
            
            # Dibujar los objetos detectados
            for obj in self.detected_objects:
                x, y, w, h = obj['rectangle']
                cv2.rectangle(frame_rgb, (x, y), (x + w, y + h), (0, 255, 0), 2)
                cv2.putText(frame_rgb, f"{obj['object']} ({obj['confidence']:.2f})",
                          (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            
            # Convertir el frame a formato PIL y luego a PhotoImage
            image = Image.fromarray(frame_rgb)
            # Ajustar el tamaño al canvas
            image = image.resize((self.video_canvas.winfo_width(), 
                                self.video_canvas.winfo_height()))
            photo = ImageTk.PhotoImage(image=image)
            
            # Actualizar el canvas
            self.video_canvas.create_image(0, 0, image=photo, anchor=tk.NW)
            self.video_canvas.photo = photo
        
        # Programar la siguiente actualización
        self.root.after(10, self.update_video)

    def analyze_frame(self, frame):
        try:
            # Convertir frame a bytes
            img = Image.fromarray(frame)
            img_byte_arr = io.BytesIO()
            img.save(img_byte_arr, format='PNG')
            img_byte_arr = img_byte_arr.getvalue()
            
            # Enviar a Azure para análisis
            analyze_url = f"{self.endpoint}/vision/v3.2/analyze"
            headers = {
                'Ocp-Apim-Subscription-Key': self.api_key,
                'Content-Type': 'application/octet-stream'
            }
            params = {
                'visualFeatures': 'Objects,Description',
                'language': 'es'
            }
            
            response = requests.post(analyze_url, headers=headers, params=params, data=img_byte_arr)
            response.raise_for_status()
            analysis = response.json()
            
            # Actualizar objetos detectados y mostrar resultados
            self.detected_objects = []
            if 'objects' in analysis:
                for obj in analysis['objects']:
                    rect = obj['rectangle']
                    self.detected_objects.append({
                        'object': obj['object'],
                        'confidence': obj['confidence'],
                        'rectangle': (rect['x'], rect['y'], rect['w'], rect['h'])
                    })
            
            self.show_results(analysis)
                
        except Exception as e:
            self.show_error(f"Error en el análisis: {str(e)}")

    def show_results(self, analysis):
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(tk.END, "ANÁLISIS EN TIEMPO REAL:\n\n", 'title')
        
        if 'description' in analysis and analysis['description'].get('captions'):
            self.result_text.insert(tk.END, "Descripción: ", 'subtitle')
            self.result_text.insert(tk.END, f"{analysis['description']['captions'][0]['text']}\n\n")
        
        if 'objects' in analysis:
            self.result_text.insert(tk.END, "Objetos detectados:\n", 'subtitle')
            for obj in analysis['objects']:
                self.result_text.insert(tk.END, f"• {obj['object']} ", 'tag')
                self.result_text.insert(tk.END, f"({obj['confidence']:.2f})\n")

    def show_error(self, message):
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(tk.END, "ERROR: ", 'error')
        self.result_text.insert(tk.END, message)

    def __del__(self):
        if hasattr(self, 'cap'):
            self.cap.release()

def main():
    try:
        root = tk.Tk()
        root.geometry("1024x768")  # Ventana más grande por defecto
        app = VisionApp(root)
        root.mainloop()
    except Exception as e:
        print(f"Error al iniciar la aplicación: {str(e)}")
        input("Presione Enter para salir...")

if __name__ == "__main__":
    main() 