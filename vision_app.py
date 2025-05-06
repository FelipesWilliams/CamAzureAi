import tkinter as tk
from PIL import ImageGrab, Image
import requests
import json
import io
import time
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

class VisionApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Vision Project - Azure AI")
        
        # Hacer la ventana transparente
        self.root.attributes('-alpha', 0.0)
        self.root.configure(bg='white')
        self.root.wm_attributes('-transparentcolor', 'white')
        
        # Configuración de Azure desde variables de entorno
        self.endpoint = os.getenv("AZURE_VISION_ENDPOINT")
        self.api_key = os.getenv("AZURE_VISION_KEY")
        
        if not self.endpoint or not self.api_key:
            raise ValueError("Por favor configura las variables de entorno AZURE_VISION_ENDPOINT y AZURE_VISION_KEY")

        # Crear el panel izquierdo (área de captura)
        self.left_panel = tk.Frame(root, bg='white')
        self.left_panel.place(x=0, y=0, relwidth=0.7, relheight=1.0)
        
        # Crear el borde verde
        self.border = tk.Canvas(self.left_panel, bg='white', highlightthickness=5, highlightbackground='#00ff00')
        self.border.place(x=20, y=20, relwidth=0.95, relheight=0.95)
        
        # Panel derecho para resultados y controles
        self.right_panel = tk.Frame(root, bg='black')
        self.right_panel.place(relx=0.7, y=0, relwidth=0.3, relheight=1.0)
        
        # Título del panel
        self.title_label = tk.Label(self.right_panel, 
                                  text="Azure Vision AI", 
                                  bg='black', 
                                  fg='#00ff00',
                                  font=('Arial', 14, 'bold'))
        self.title_label.pack(pady=10)
        
        # Botón de captura
        self.capture_btn = tk.Button(self.right_panel, 
                                   text="Capturar y Analizar",
                                   command=self.capture_and_analyze,
                                   bg='#404040',
                                   fg='white',
                                   font=('Arial', 10),
                                   relief='raised',
                                   padx=10)
        self.capture_btn.pack(pady=10)
        
        # Área de resultados
        self.result_text = tk.Text(self.right_panel, 
                                 height=30, 
                                 width=35, 
                                 bg='black', 
                                 fg='white', 
                                 font=('Arial', 10))
        self.result_text.pack(padx=10, pady=10, fill='both', expand=True)
        
        # Configurar el estilo del área de resultados
        self.result_text.configure(insertbackground='white')
        self.result_text.configure(selectbackground='#404040')
        self.result_text.configure(selectforeground='white')
        
        # Configurar tags para el formato del texto
        self.result_text.tag_configure('title', font=('Arial', 12, 'bold'), foreground='#00ff00')
        self.result_text.tag_configure('subtitle', font=('Arial', 10, 'bold'), foreground='#00ccff')
        self.result_text.tag_configure('tag', font=('Arial', 10), foreground='#ffcc00')
        self.result_text.tag_configure('error', font=('Arial', 10, 'bold'), foreground='#ff0000')
        
        # Mostrar capacidades de la API
        self.show_api_capabilities()
        
        # Configurar eventos de movimiento y redimensionamiento
        self.border.bind("<ButtonPress-1>", self.start_move)
        self.border.bind("<B1-Motion>", self.on_move)
        self.border.bind("<ButtonPress-3>", self.start_resize)
        self.border.bind("<B3-Motion>", self.on_resize)
        
        # Hacer visible la ventana después de configurar todo
        self.root.after(100, lambda: self.root.attributes('-alpha', 1.0))
        
    def start_move(self, event):
        self.x = event.x
        self.y = event.y
        
    def on_move(self, event):
        deltax = event.x - self.x
        deltay = event.y - self.y
        x = self.border.winfo_x() + deltax
        y = self.border.winfo_y() + deltay
        self.border.place(x=x, y=y)
        
    def start_resize(self, event):
        self.x = event.x
        self.y = event.y
        
    def on_resize(self, event):
        width = self.border.winfo_width() + (event.x - self.x)
        height = self.border.winfo_height() + (event.y - self.y)
        if width > 100 and height > 100:
            self.border.place(width=width, height=height)
            
    def capture_and_analyze(self):
        try:
            # Ocultar temporalmente la ventana para la captura
            self.root.attributes('-alpha', 0.0)
            self.root.update()
            time.sleep(0.2)
            
            # Obtener coordenadas del área de captura
            x = self.border.winfo_x() + self.left_panel.winfo_x() + self.root.winfo_x()
            y = self.border.winfo_y() + self.left_panel.winfo_y() + self.root.winfo_y()
            width = self.border.winfo_width()
            height = self.border.winfo_height()
            
            # Capturar la imagen
            screenshot = ImageGrab.grab(bbox=(x, y, x+width, y+height))
            
            # Mostrar la ventana nuevamente
            self.root.attributes('-alpha', 1.0)
            
            # Enviar a Azure para análisis
            self.analyze_image(screenshot)
            
        except Exception as e:
            self.show_error(f"Error al capturar la imagen: {str(e)}")
            self.root.attributes('-alpha', 1.0)

    def show_api_capabilities(self):
        capabilities = """CAPACIDADES DE AZURE COMPUTER VISION:

• Descripción de Imágenes
  - Genera descripciones completas en lenguaje natural
  - Identifica escenas y acciones

• Detección de Objetos
  - Identifica objetos comunes
  - Proporciona coordenadas de ubicación
  - Detecta múltiples instancias

• Reconocimiento de Texto (OCR)
  - Lee texto impreso y manuscrito
  - Soporta múltiples idiomas
  - Extrae texto de imágenes

• Análisis Facial
  - Detecta rostros y atributos
  - Estima edad y emociones
  - Identifica accesorios

• Detección de Marcas
  - Reconoce logos y marcas comerciales
  - Identifica productos

• Análisis de Color
  - Detecta colores dominantes
  - Identifica si es B/N o color
  - Determina esquemas de color

• Categorización de Contenido
  - Clasifica escenas y contextos
  - Detecta contenido para adultos
  - Identifica tipos de imágenes

• Etiquetado de Imágenes
  - Genera tags descriptivos
  - Identifica características clave
  - Proporciona niveles de confianza

Presiona 'Capturar y Analizar' para comenzar."""

        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(tk.END, capabilities)
        
    def analyze_image(self, image):
        try:
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format='PNG')
            img_byte_arr = img_byte_arr.getvalue()
            
            analyze_url = f"{self.endpoint}/vision/v3.2/analyze"
            headers = {
                'Ocp-Apim-Subscription-Key': self.api_key,
                'Content-Type': 'application/octet-stream'
            }
            params = {
                'visualFeatures': 'Categories,Description,Objects,Tags',
                'language': 'es'
            }
            
            response = requests.post(analyze_url, headers=headers, params=params, data=img_byte_arr)
            response.raise_for_status()
            analysis = response.json()
            
            self.show_results(analysis)
                
        except requests.exceptions.RequestException as e:
            self.show_error(f"Error de conexión con Azure: {str(e)}")
        except Exception as e:
            self.show_error(f"Error en el análisis: {str(e)}")

    def show_results(self, analysis):
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(tk.END, "RESULTADOS DEL ANÁLISIS:\n\n", 'title')
        
        if 'description' in analysis and analysis['description'].get('captions'):
            self.result_text.insert(tk.END, "Descripción: ", 'subtitle')
            self.result_text.insert(tk.END, f"{analysis['description']['captions'][0]['text']}\n\n")
        
        if 'tags' in analysis:
            self.result_text.insert(tk.END, "Etiquetas detectadas:\n", 'subtitle')
            for tag in analysis['tags']:
                self.result_text.insert(tk.END, f"• {tag['name']} ", 'tag')
                self.result_text.insert(tk.END, f"({tag['confidence']:.2f})\n")
                
        if 'objects' in analysis:
            self.result_text.insert(tk.END, "\nObjetos detectados:\n", 'subtitle')
            for obj in analysis['objects']:
                self.result_text.insert(tk.END, f"• {obj['object']} ", 'tag')
                self.result_text.insert(tk.END, f"({obj['confidence']:.2f})\n")

    def show_error(self, message):
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(tk.END, "ERROR: ", 'error')
        self.result_text.insert(tk.END, message)

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