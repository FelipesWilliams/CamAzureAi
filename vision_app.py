import tkinter as tk
from PIL import ImageGrab, Image
import requests
import json
import io
import time
import os
import math
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

class LoadingButton(tk.Canvas):
    def __init__(self, parent, command, **kwargs):
        super().__init__(parent, **kwargs)
        self.command = command
        self.is_loading = False
        
        # Dimensiones del botón
        self.width = 200
        self.height = 40
        self.configure(width=self.width, height=self.height, bg='black', highlightthickness=0)
        
        # Crear el botón base
        self.create_rectangle(0, 0, self.width, self.height, fill='#1a1a1a', outline='#00ff00', width=2, tags='button')
        self.create_text(self.width/2, self.height/2, text="Capturar y Analizar", fill='#00ff00', 
                        font=('Arial', 12, 'bold'), tags='text')
        
        # Eventos del botón
        self.bind('<Enter>', self.on_enter)
        self.bind('<Leave>', self.on_leave)
        self.bind('<Button-1>', self.on_click)
                       
    def on_enter(self, event):
        if not self.is_loading:
            self.itemconfig('button', fill='#2a2a2a')
            
    def on_leave(self, event):
        if not self.is_loading:
            self.itemconfig('button', fill='#1a1a1a')
            
    def on_click(self, event):
        if not self.is_loading:
            self.start_loading()
            self.command()
            
    def start_loading(self):
        self.is_loading = True
        self.itemconfig('button', fill='#1a1a1a')
        self.itemconfig('button', outline='#ff0000')  # Cambiar borde a rojo
        self.itemconfig('text', fill='#ff0000')  # Cambiar texto a rojo
        self.dots_count = 0
        self.update_loading_text()
        
    def update_loading_text(self):
        if self.is_loading:
            dots = "." * (self.dots_count % 4)
            self.itemconfig('text', text=f"Analizando{dots}")
            self.dots_count += 1
            self.after(500, self.update_loading_text)
            
    def stop_loading(self):
        self.is_loading = False
        self.itemconfig('button', outline='#00ff00')  # Restaurar borde a verde
        self.itemconfig('text', fill='#00ff00')  # Restaurar texto a verde
        self.itemconfig('text', text="Capturar y Analizar")

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

        # Inicializar los componentes de la interfaz
        self.setup_ui()
        
        # Configurar el arrastre de la ventana
        self.setup_window_drag()
        
        # Variable para controlar el estado de análisis
        self.is_analyzing = False
        
        # Hacer visible la ventana después de configurar todo
        self.root.after(100, lambda: self.root.attributes('-alpha', 1.0))

    def setup_ui(self):
        # Crear el panel izquierdo (área de captura)
        self.left_panel = tk.Frame(self.root, bg='white')
        self.left_panel.place(x=0, y=0, relwidth=0.7, relheight=1.0)
        
        # Crear el borde verde que ocupa todo el panel izquierdo
        self.border = tk.Canvas(self.left_panel, bg='white', highlightthickness=5, highlightbackground='#00ff00')
        self.border.place(x=0, y=0, relwidth=1.0, relheight=1.0)
        
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
        
        # Reemplazar el botón normal por el LoadingButton
        self.capture_btn = LoadingButton(self.right_panel, 
                                       command=self.capture_and_analyze,
                                       bg='black')
        self.capture_btn.pack(pady=20)
        
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

    def setup_window_drag(self):
        def start_move(event):
            if self.is_analyzing:  # No permitir movimiento durante el análisis
                return
            widget = event.widget
            if widget == self.right_panel or widget.master == self.right_panel:
                return
            self.x = event.x_root - self.root.winfo_x()
            self.y = event.y_root - self.root.winfo_y()

        def stop_move(event):
            if not self.is_analyzing:  # Solo procesar si no está analizando
                self.x = None
                self.y = None

        def do_move(event):
            if self.is_analyzing:  # No permitir movimiento durante el análisis
                return
            if hasattr(self, 'x') and self.x is not None:
                new_x = event.x_root - self.x
                new_y = event.y_root - self.y
                self.root.geometry(f"+{new_x}+{new_y}")

        # Vincular eventos
        for widget in [self.root, self.left_panel, self.border]:
            widget.bind("<Button-1>", start_move)
            widget.bind("<ButtonRelease-1>", stop_move)
            widget.bind("<B1-Motion>", do_move)

    def capture_and_analyze(self):
        try:
            self.is_analyzing = True  # Activar estado de análisis
            
            # Cambiar el color del borde a rojo
            self.border.configure(highlightbackground='#ff0000')
            
            # Cambiar el título a rojo
            self.title_label.configure(fg='#ff0000')
            
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
            self.restore_colors()
            self.capture_btn.stop_loading()

    def restore_colors(self):
        self.is_analyzing = False  # Desactivar estado de análisis
        self.border.configure(highlightbackground='#00ff00')  # Restaurar borde a verde
        self.title_label.configure(fg='#00ff00')  # Restaurar título a verde

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
        self.restore_colors()  # Restaurar colores después del análisis
        self.capture_btn.stop_loading()
        
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
        self.restore_colors()  # Restaurar colores en caso de error
        self.capture_btn.stop_loading()
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