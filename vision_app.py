import tkinter as tk
from PIL import ImageGrab, Image, ImageTk
import cv2
import numpy as np
import requests
import json
import io
import time
import os
from dotenv import load_dotenv
import re

# Cargar variables de entorno
load_dotenv()

class VisionApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Vision Project - Azure AI")
        
        # Configurar la ventana principal para ser transparente
        self.root.attributes('-alpha', 1.0, '-transparentcolor', 'black')
        self.root.configure(bg='black')
        
        # Configuración de Azure desde variables de entorno
        self.endpoint = os.getenv("AZURE_VISION_ENDPOINT")
        self.api_key = os.getenv("AZURE_VISION_KEY")
        
        if not self.endpoint or not self.api_key:
            raise ValueError("Por favor configura las variables de entorno AZURE_VISION_ENDPOINT y AZURE_VISION_KEY")

        self.is_analyzing = False
        self.detected_objects = []
        
        # Archivo de configuración para guardar la posición y tamaño
        self.config_file = 'vision_app_config.json'
        
        # Variables para el cuadro de captura
        self.capture_size = (800, 600)  # Tamaño del cuadro de captura
        
        # Colores para el borde
        self.BORDER_COLOR_NORMAL = '#00ff00'  # Verde
        self.BORDER_COLOR_ANALYZING = '#ff0000'  # Rojo
        
        # Cargar la configuración guardada
        self.load_window_config()
        
        # Inicializar los componentes de la interfaz
        self.setup_ui()
        
        # Iniciar el bucle de actualización
        self.update_capture()
        
        # Hacer que la ventana sea movible desde cualquier parte
        self.root.bind('<Button-1>', self.start_move)
        self.root.bind('<B1-Motion>', self.on_move)
        
        # Guardar configuración al cerrar
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def load_window_config(self):
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    # Configurar geometría de la ventana
                    self.root.geometry(f"{config['width']}x{config['height']}+{config['x']}+{config['y']}")
            else:
                # Configuración por defecto
                self.root.geometry("1050x600")
        except Exception as e:
            print(f"Error al cargar la configuración: {e}")
            # Usar configuración por defecto si hay error
            self.root.geometry("1050x600")

    def save_window_config(self):
        try:
            # Obtener la geometría actual
            geometry = self.root.geometry()
            # Parsear la geometría
            match = re.match(r'(\d+)x(\d+)\+(-?\d+)\+(-?\d+)', geometry)
            if match:
                width, height, x, y = map(int, match.groups())
                config = {
                    'width': width,
                    'height': height,
                    'x': x,
                    'y': y
                }
                with open(self.config_file, 'w') as f:
                    json.dump(config, f)
        except Exception as e:
            print(f"Error al guardar la configuración: {e}")

    def on_closing(self):
        self.save_window_config()
        self.root.destroy()

    def setup_ui(self):
        # Contenedor principal
        self.main_container = tk.Frame(self.root, bg='black')
        self.main_container.pack(expand=True, fill='both')
        
        # Frame izquierdo para el área de captura
        self.capture_frame = tk.Frame(self.main_container, bg='black')
        self.capture_frame.pack(side='left', fill='both', expand=True)
        
        # Canvas para mostrar el área de captura con borde verde
        self.capture_canvas = tk.Canvas(
            self.capture_frame,
            width=self.capture_size[0],
            height=self.capture_size[1],
            bg='black',
            highlightthickness=2,
            highlightbackground=self.BORDER_COLOR_NORMAL
        )
        self.capture_canvas.pack(side='left', fill='both', expand=True)
        
        # Frame derecho para controles (con fondo semi-transparente)
        self.control_frame = tk.Frame(self.main_container, bg='#1a1a1a', width=250)
        self.control_frame.pack(side='right', fill='y')
        self.control_frame.pack_propagate(False)
        
        # Botón de análisis
        self.analyze_btn = tk.Button(
            self.control_frame,
            text="Analizar",
            command=self.toggle_analysis,
            bg='#2a2a2a',
            fg='#00ff00',
            font=('Arial', 10),
            relief=tk.FLAT,
            width=15,
            cursor='hand2'
        )
        self.analyze_btn.pack(pady=10)
        
        # Área de resultados
        self.result_text = tk.Text(
            self.control_frame,
            height=20,
            width=30,
            bg='#1a1a1a',
            fg='#00ff00',
            font=('Arial', 9),
            relief=tk.FLAT
        )
        self.result_text.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Configurar tags para el formato del texto
        self.result_text.tag_configure('title', font=('Arial', 10, 'bold'), foreground='#00ff00')
        self.result_text.tag_configure('subtitle', font=('Arial', 9, 'bold'), foreground='#00ccff')
        self.result_text.tag_configure('tag', font=('Arial', 9), foreground='#ffcc00')
        self.result_text.tag_configure('percentage', font=('Arial', 9), foreground='#ff9900')
        self.result_text.tag_configure('error', font=('Arial', 9, 'bold'), foreground='#ff0000')

        # Hacer que la ventana sea redimensionable
        self.root.resizable(True, True)

        # Crear una "máscara" transparente en el canvas
        self.capture_canvas.create_rectangle(
            2, 2,  # Offset para no tapar el borde
            self.capture_size[0]-2, self.capture_size[1]-2,  # Offset para no tapar el borde
            fill='black',  # Este color será transparente
            outline=''  # Sin borde adicional
        )

    def start_move(self, event):
        self.x = event.x
        self.y = event.y

    def on_move(self, event):
        deltax = event.x - self.x
        deltay = event.y - self.y
        x = self.root.winfo_x() + deltax
        y = self.root.winfo_y() + deltay
        self.root.geometry(f"+{x}+{y}")

    def toggle_analysis(self):
        self.is_analyzing = not self.is_analyzing
        if self.is_analyzing:
            self.analyze_btn.configure(text="Detener", fg='#ff6666')
        else:
            self.analyze_btn.configure(text="Analizar", fg='#00ff00')
            self.detected_objects = []
            self.result_text.delete(1.0, tk.END)

    def update_capture(self):
        if self.is_analyzing:
            try:
                # Obtener las coordenadas del canvas en la pantalla
                x = self.capture_canvas.winfo_rootx()
                y = self.capture_canvas.winfo_rooty()
                w = self.capture_canvas.winfo_width()
                h = self.capture_canvas.winfo_height()
                
                # Capturar el área de la pantalla
                screenshot = ImageGrab.grab(bbox=(x, y, x+w, y+h))
                frame = np.array(screenshot)
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # Analizar el frame
                self.analyze_frame(frame)
            except Exception as e:
                self.show_error(f"Error en la captura: {str(e)}")
        
        # Programar la siguiente actualización
        self.root.after(1000, self.update_capture)

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
            
            self.show_results(analysis)
                
        except Exception as e:
            self.show_error(f"Error en el análisis: {str(e)}")

    def show_results(self, analysis):
        self.result_text.delete(1.0, tk.END)
        
        if 'description' in analysis and analysis['description'].get('captions'):
            self.result_text.insert(tk.END, "Descripción:\n", 'subtitle')
            self.result_text.insert(tk.END, f"{analysis['description']['captions'][0]['text']}\n\n")
        
        if 'objects' in analysis:
            self.result_text.insert(tk.END, "Objetos:\n", 'subtitle')
            for obj in analysis['objects']:
                self.result_text.insert(tk.END, f"• {obj['object']}", 'tag')
                self.result_text.insert(tk.END, f" ({obj['confidence']:.2f})\n")

    def show_error(self, message):
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(tk.END, "ERROR: ", 'error')
        self.result_text.insert(tk.END, message)

def main():
    try:
        root = tk.Tk()
        # Configurar la ventana para que esté siempre encima
        root.attributes('-topmost', True)
        app = VisionApp(root)
        root.mainloop()
    except Exception as e:
        print(f"Error al iniciar la aplicación: {str(e)}")
        input("Presione Enter para salir...")

if __name__ == "__main__":
    main() 