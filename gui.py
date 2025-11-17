"""
gui.py - Interfaz gráfica del visor de osciloscopio
Maneja todos los elementos visuales y la interacción con el usuario
Estilo osciloscopio real con información de V/div y T/div
"""

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from tkinter import colorchooser
import numpy as np
import re
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from data_handler import DataHandler
from plotter import Plotter

class OsciloscopioGUI:
    """
    Clase que maneja toda la interfaz gráfica estilo osciloscopio
    """
    
    def __init__(self, root):
        """
        Inicializa la ventana y todos sus componentes
        """
        self.root = root
        self.root.title("Osciloscopio Digital - Visor CSV")
        self.root.geometry("1400x800")
        self.root.configure(bg='#1a1a1a')
        
        self.data_handler = DataHandler()
        self.plotter = Plotter()
        
        self.df = None
        self.info_escalas = None
        
        # Escalas manuales
        self.escalas_tiempo_manual = {}
        self.escalas_voltaje_manual = {}
        self.offset_y_manual = {}
        self.offset_x_manual = {}  # NUEVO: offset horizontal
        self.colores_manuales = {}
        
        # Diccionarios para widgets Entry
        self.entry_widgets_voltaje = {}
        self.entry_widgets_tiempo = {}
        self.entry_widgets_offset = {}
        
        # Estado del modo FINO
        self.fine_mode_voltaje = {}
        self.fine_mode_tiempo = {}
        self.fine_mode_offset = {}
        
        # NUEVO: Estado del eje de offset activo ('x' o 'y')
        self.offset_eje_activo = {}  # {canal: 'y'} o {canal: 'x'}
        
        self.prefijos_parser = {
            'T': 1e12, 'G': 1e9, 'M': 1e6, 'k': 1e3,
            'm': 1e-3, 'u': 1e-6, 'μ': 1e-6, 'n': 1e-9, 'p': 1e-12, 'f': 1e-15
        }
        
        # Variables de estado para cursores
        self.cursores_activos = tk.BooleanVar(value=False)
        self.canal_cursor_seleccionado = tk.StringVar()
        self.mapa_nombres_canales_cursor = {}
        
        # Posiciones de cursores (en coordenadas de gráfico 0-10, -4 a 4)
        self.cursor_pos = {'x1': 3.0, 'x2': 7.0, 'y1': -1.0, 'y2': 1.0}
        
        # Variables para arrastre de cursores
        self.cursor_artists = {}    # { 'x1': Line2D, ... }
        self.linea_arrastrada = None  # (key, line_artist)
        
        
        self.crear_menu()
        self.crear_panel_control()
        self.crear_area_grafico()
        self.crear_panel_escalas()
        self.crear_barra_estado()
    
    
    def crear_barra_estado(self):
        """
        Crea una barra de estado en la parte inferior para mostrar coordenadas
        """
        self.barra_estado = tk.Frame(self.root, bg='#000000', height=30, relief=tk.SUNKEN, bd=2)
        self.barra_estado.pack(side=tk.BOTTOM, fill=tk.X, pady=(5,0))
        
        # Frame para coordenadas del mouse (izquierda)
        frame_coords = tk.Frame(self.barra_estado, bg='#000000')
        frame_coords.pack(side=tk.LEFT, padx=10, pady=2)
        
        self.label_coordenadas = tk.Label(frame_coords, text="Coordenadas: --", 
                                         bg='#000000', fg='#00FF00', 
                                         font=('Courier', 10, 'bold'), anchor=tk.W)
        self.label_coordenadas.pack()
        
        # Frame para la información de los cursores (derecha)
        frame_cursores = tk.Frame(self.barra_estado, bg='#000000')
        frame_cursores.pack(side=tk.RIGHT, padx=10, pady=2)
        
        # Etiqueta para Y1, Y2, DeltaY
        self.label_cursor_y_info = tk.Label(frame_cursores, text="Y1: -- Y2: -- ΔY: --", 
                                         bg='#000000', fg='#FFFFFF', 
                                         font=('Courier', 10, 'bold'), anchor=tk.W)
        self.label_cursor_y_info.pack()

        # Etiqueta para X1, X2, DeltaX
        self.label_cursor_x_info = tk.Label(frame_cursores, text="X1: -- X2: -- ΔX: --", 
                                         bg='#000000', fg='#FFD700', 
                                         font=('Courier', 10, 'bold'), anchor=tk.W)
        self.label_cursor_x_info.pack()
    
    def crear_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        archivo_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Archivo", menu=archivo_menu)
        archivo_menu.add_command(label="Abrir CSV", command=self.abrir_archivo)
        archivo_menu.add_separator()
        archivo_menu.add_command(label="Salir", command=self.root.quit)
        ayuda_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Ayuda", menu=ayuda_menu)
        ayuda_menu.add_command(label="Acerca de", command=self.mostrar_acerca_de)
    
    def crear_panel_control(self):
        """
        Crea el panel lateral izquierdo con controles
        """
        panel = tk.Frame(self.root, width=200, bg='#2a2a2a', relief=tk.RAISED, borderwidth=2)
        panel.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)
        
        tk.Label(panel, text="CONTROLES", font=('Arial', 12, 'bold'), 
                bg='#2a2a2a', fg='#00FF00').pack(pady=10)
        
        btn_cargar = tk.Button(panel, text="📁 CARGAR CSV", command=self.abrir_archivo,
                               width=18, height=2, bg='#003300', fg='#00FF00', 
                               font=('Arial', 10, 'bold'), relief=tk.RAISED, bd=3)
        btn_cargar.pack(pady=10)
        
        ttk.Separator(panel, orient='horizontal').pack(fill='x', pady=10)
        
        tk.Label(panel, text="CANALES:", font=('Arial', 10, 'bold'), 
                bg='#2a2a2a', fg='#00FF00').pack(pady=5)
        
        self.frame_canales = tk.Frame(panel, bg='#2a2a2a')
        self.frame_canales.pack(pady=5, fill=tk.X)
        
        self.canal_vars = []
        
        ttk.Separator(panel, orient='horizontal').pack(fill='x', pady=10)

        # --- SECCIÓN DE CURSORES ---
        tk.Label(panel, text="CURSORES:", font=('Arial', 10, 'bold'), 
                bg='#2a2a2a', fg='#00FF00').pack(pady=5)
        
        frame_cursores = tk.Frame(panel, bg='#2a2a2a')
        frame_cursores.pack(pady=5, padx=5, fill=tk.X)

        tk.Checkbutton(frame_cursores, text="Activar Cursores", 
                       variable=self.cursores_activos, 
                       command=self.toggle_cursores,
                       bg='#2a2a2a', fg='#CCCCCC',
                       selectcolor='#000000', activebackground='#2a2a2a',
                       activeforeground='#00FF00', font=('Arial', 9, 'bold')
                       ).pack(anchor=tk.W)

        tk.Label(frame_cursores, text="Anclar a:", 
                 bg='#2a2a2a', fg='#CCCCCC', font=('Arial', 9)
                 ).pack(anchor=tk.W, pady=(5,0))

        self.combo_canal_cursor = ttk.Combobox(frame_cursores, 
                                               textvariable=self.canal_cursor_seleccionado, 
                                               state='readonly', width=17)
        self.combo_canal_cursor.pack(anchor=tk.W, pady=5)
        self.combo_canal_cursor.bind("<<ComboboxSelected>>", self.actualizar_cursores)
        
        ttk.Separator(panel, orient='horizontal').pack(fill='x', pady=10)
        # --- FIN SECCIÓN CURSORES ---
        
        self.btn_graficar = tk.Button(panel, text="🔄 ACTUALIZAR", 
                                      command=self.actualizar_grafico,
                                      width=18, height=2, bg='#000033', fg='#00FFFF',
                                      font=('Arial', 10, 'bold'), relief=tk.RAISED, bd=3,
                                      state=tk.DISABLED)
        self.btn_graficar.pack(pady=15)
        
        tk.Label(panel, text="INFO ARCHIVO:", font=('Arial', 9, 'bold'), 
                bg='#2a2a2a', fg='#FFD700').pack(pady=(15,5))
        
        self.info_label = tk.Label(panel, text="Sin archivo cargado", 
                                   bg='#2a2a2a', fg='#CCCCCC', wraplength=180, 
                                   justify=tk.LEFT, font=('Courier', 8))
        self.info_label.pack(pady=5, padx=10)
    
    def crear_area_grafico(self):
        """
        Crea el área central donde se mostrará el gráfico estilo osciloscopio
        """
        frame_grafico = tk.Frame(self.root, bg='#1a1a1a')
        frame_grafico.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.fig = Figure(figsize=(10, 7), dpi=100, facecolor='#1a1a1a')
        self.ax = self.fig.add_subplot(111)
        
        self.plotter.configurar_estilo_osciloscopio(self.ax)
        
        self.canvas = FigureCanvasTkAgg(self.fig, master=frame_grafico)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
       
        # Conectar eventos de mouse para arrastrar cursores
        self.canvas.mpl_connect('button_press_event', self.on_press)
        self.canvas.mpl_connect('motion_notify_event', self.on_motion)
        self.canvas.mpl_connect('button_release_event', self.on_release)
    
    def crear_panel_escalas(self):
        panel = tk.Frame(self.root, width=220, bg='#2a2a2a', relief=tk.RAISED, borderwidth=2)
        panel.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 5), pady=5) 
        tk.Label(panel, text="CONTROLES CANAL", font=('Arial', 10, 'bold'), 
                bg='#2a2a2a', fg='#00FF00').pack(pady=3)
        canvas_scroll = tk.Canvas(panel, bg='#2a2a2a', highlightthickness=0)
        scrollbar = tk.Scrollbar(panel, orient="vertical", command=canvas_scroll.yview)
        self.frame_escalas = tk.Frame(canvas_scroll, bg='#2a2a2a')
        self.frame_escalas.bind(
            "<Configure>",
            lambda e: canvas_scroll.configure(scrollregion=canvas_scroll.bbox("all"))
        )
        canvas_scroll.create_window((0, 0), window=self.frame_escalas, anchor="nw")
        canvas_scroll.configure(yscrollcommand=scrollbar.set)
        canvas_scroll.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        scrollbar.pack(side="right", fill="y")
        self.label_sin_datos = tk.Label(self.frame_escalas, 
                                        text="Cargue un archivo\npara ver las escalas", 
                                        bg='#2a2a2a', fg='#888888',
                                        font=('Arial', 9, 'italic'))
        self.label_sin_datos.pack(pady=30)
    
    def abrir_archivo(self):
        archivo = filedialog.askopenfilename(
            title="Seleccionar archivo CSV del osciloscopio",
            filetypes=[("Archivos CSV", "*.csv"), ("Todos los archivos", "*.*")]
        )
        if archivo:
            try:
                self.df = self.data_handler.cargar_csv(archivo)
                self.crear_checkboxes_canales()
                self.actualizar_info_archivo(archivo)
                self.btn_graficar.config(state=tk.NORMAL)
                self.escalas_voltaje_manual.clear()
                self.escalas_tiempo_manual.clear()
                self.offset_y_manual.clear()
                self.offset_x_manual.clear()
                self.colores_manuales.clear()
                self.offset_eje_activo.clear()
                self.actualizar_grafico()
                messagebox.showinfo("Éxito", "Archivo cargado correctamente")
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo cargar el archivo:\n{str(e)}")
    
    def crear_checkboxes_canales(self):
        for widget in self.frame_canales.winfo_children():
            widget.destroy()
        self.canal_vars = []
        
        columnas = self.df.columns[1:]
        for i, col in enumerate(columnas):
            var = tk.BooleanVar(value=True)
            frame_canal = tk.Frame(self.frame_canales, bg='#2a2a2a')
            frame_canal.pack(anchor=tk.W, padx=5, pady=2)
            
            chk = tk.Checkbutton(frame_canal, text=f"Canal {i+1}", 
                                variable=var, bg='#2a2a2a', fg='#CCCCCC',
                                selectcolor='#000000', activebackground='#2a2a2a',
                                activeforeground='#00FF00', font=('Arial', 9, 'bold'))
            chk.pack(side=tk.LEFT)
            self.canal_vars.append((col, var, i)) 
    
    def actualizar_info_archivo(self, archivo):
        nombre = archivo.split('/')[-1].split('\\')[-1]
        num_puntos = len(self.df)
        num_canales = len(self.df.columns) - 1
        info = f"📄 {nombre}\n\n"
        info += f"Canales: {num_canales}\n"
        info += f"Muestras: {num_puntos:,}\n"
        tiempo = self.df[self.df.columns[0]]
        duracion = tiempo.max() - tiempo.min()
        factor, simbolo = self.plotter.determinar_prefijo(duracion)
        duracion_str = f"{duracion/factor:.2f} {simbolo}s"
        info += f"Duración: {duracion_str}"
        self.info_label.config(text=info)
    
    def actualizar_grafico(self):
        # Esta función ahora solo llama a redibujar_con_escalas
        self.redibujar_con_escalas()
    

    def actualizar_panel_escalas(self):
        """
        Actualiza el panel derecho con la información de escalas y controles
        """
        for widget in self.frame_escalas.winfo_children():
            widget.destroy()
        
        if self.info_escalas is None or not self.info_escalas.get('canales'):
            self.label_sin_datos = tk.Label(self.frame_escalas, 
                                        text="Cargue un archivo\ny seleccione un canal", 
                                        bg='#2a2a2a', fg='#888888',
                                        font=('Arial', 9, 'italic'))
            self.label_sin_datos.pack(pady=30)
            return
            
        self.entry_widgets_voltaje.clear()
        self.entry_widgets_tiempo.clear()
        self.entry_widgets_offset.clear()
        
        canales_ordenados = sorted(self.info_escalas['canales'].items(), 
                                  key=lambda item: item[1]['indice_canal'])

        for canal, info in canales_ordenados:
            
            color_actual = info['color']
            
            frame_canal = tk.Frame(self.frame_escalas, bg='#1a1a1a', relief=tk.RAISED, bd=2)
            frame_canal.pack(fill=tk.X, padx=5, pady=2)
            
            header_frame = tk.Frame(frame_canal, bg=color_actual)
            header_frame.pack(fill=tk.X)
            
            indice_canal = info['indice_canal']
            tk.Label(header_frame, text=f"CANAL {indice_canal + 1}", bg=color_actual, 
                    fg='#000000', font=('Arial', 9, 'bold')).pack(side=tk.LEFT, padx=5, pady=3)
            
            tk.Button(header_frame, text="🎨", 
                      bg=color_actual, 
                      font=('Arial', 8), 
                      width=2,
                      relief=tk.FLAT,
                      activebackground=color_actual,
                      command=lambda c=canal: self.elegir_color(c)
                      ).pack(side=tk.RIGHT, padx=3, pady=2)
            
            
            main_controls_frame = tk.Frame(frame_canal, bg='#1a1a1a')
            main_controls_frame.pack(fill=tk.X, padx=2, pady=3)
            
            left_frame = tk.Frame(main_controls_frame, bg='#1a1a1a')
            left_frame.pack(side=tk.LEFT, anchor=tk.N)
            
            right_frame = tk.Frame(main_controls_frame, bg='#1a1a1a')
            right_frame.pack(side=tk.RIGHT, anchor=tk.N, padx=(10, 2))


            # --- SECCIÓN VOLTAJE (en left_frame) ---
            if canal in self.escalas_voltaje_manual:
                v_div_actual = self.escalas_voltaje_manual[canal]
                v_factor_actual, v_simbolo_actual = self.plotter.determinar_prefijo(v_div_actual)
            else:
                v_div_actual = info['voltaje_por_div']
                v_factor_actual = info['voltaje_factor']
                v_simbolo_actual = info['voltaje_simbolo']
            valor_voltaje_str = f"{v_div_actual/v_factor_actual:.3f}{v_simbolo_actual}V"
            
            controles_voltaje_entry = tk.Frame(left_frame, bg='#1a1a1a')
            controles_voltaje_entry.pack(pady=(5,2))
            tk.Label(controles_voltaje_entry, text="V/div:", bg='#1a1a1a', 
                    fg='#FFFFFF', font=('Arial', 9, 'bold')).pack(side=tk.LEFT, padx=(5,2))
            v_var = tk.StringVar(value=valor_voltaje_str)
            v_entry = tk.Entry(controles_voltaje_entry, textvariable=v_var, width=10,
                               bg='#333333', fg='#FFFFFF', insertbackground='white',
                               font=('Courier', 10, 'bold'))
            v_entry.pack(side=tk.LEFT, padx=3)
            v_entry.bind('<Return>', lambda event, c=canal: self.set_escala_voltaje(c, event))
            self.entry_widgets_voltaje[canal] = v_entry
            tk.Button(controles_voltaje_entry, text="AUTO", 
                     command=lambda c=canal: self.auto_escala_voltaje(c),
                     bg='#330033', fg='#FF00FF', font=('Arial', 8, 'bold'), 
                     width=5).pack(side=tk.LEFT, padx=2)
            
            controles_voltaje_ajuste = tk.Frame(left_frame, bg='#1a1a1a')
            controles_voltaje_ajuste.pack(pady=(0, 5))
            tk.Button(controles_voltaje_ajuste, text="▲", 
                     command=lambda c=canal: self.ajustar_voltaje(c, -1),
                     bg='#000033', fg='#00FFFF', font=('Arial', 10, 'bold'), 
                     width=3).pack(side=tk.LEFT, padx=5)
            tk.Button(controles_voltaje_ajuste, text="▼", 
                     command=lambda c=canal: self.ajustar_voltaje(c, 1),
                     bg='#000033', fg='#00FFFF', font=('Arial', 10, 'bold'), 
                     width=3).pack(side=tk.LEFT, padx=5)
            is_fine_v = self.fine_mode_voltaje.get(canal, False)
            fine_v_relief = tk.SUNKEN if is_fine_v else tk.RAISED
            fine_v_fg = '#FFFF00' if is_fine_v else '#FF00FF'
            tk.Button(controles_voltaje_ajuste, text="FINE", 
                     command=lambda c=canal: self.toggle_fine_voltaje(c),
                     bg='#330033', fg=fine_v_fg, relief=fine_v_relief,
                     font=('Arial', 8, 'bold'), 
                     width=5).pack(side=tk.LEFT, padx=5)
            
            ttk.Separator(left_frame, orient='horizontal').pack(fill='x', pady=5, padx=10)
            
            # --- SECCIÓN TIEMPO (en left_frame) ---
            if canal in self.escalas_tiempo_manual:
                t_div_actual = self.escalas_tiempo_manual[canal]
                t_factor_actual, t_simbolo_actual = self.plotter.determinar_prefijo(t_div_actual)
            else:
                t_div_actual = info['tiempo_por_div']
                t_factor_actual = info['tiempo_factor']
                t_simbolo_actual = info['tiempo_simbolo']
            valor_tiempo_str = f"{t_div_actual/t_factor_actual:.3f}{t_simbolo_actual}s"

            controles_tiempo_entry = tk.Frame(left_frame, bg='#1a1a1a')
            controles_tiempo_entry.pack(pady=(5,2))
            tk.Label(controles_tiempo_entry, text="T/div:", bg='#1a1a1a', 
                    fg='#FFD700', font=('Arial', 9, 'bold')).pack(side=tk.LEFT, padx=(5,2))
            t_var = tk.StringVar(value=valor_tiempo_str)
            t_entry = tk.Entry(controles_tiempo_entry, textvariable=t_var, width=10,
                               bg='#333333', fg='#FFFFFF', insertbackground='white',
                               font=('Courier', 10, 'bold'))
            t_entry.pack(side=tk.LEFT, padx=3)
            t_entry.bind('<Return>', lambda event, c=canal: self.set_escala_tiempo(c, event))
            self.entry_widgets_tiempo[canal] = t_entry
            tk.Button(controles_tiempo_entry, text="AUTO", 
                     command=lambda c=canal: self.auto_escala_tiempo(c),
                     bg='#330033', fg='#FF00FF', font=('Arial', 8, 'bold'), 
                     width=5).pack(side=tk.LEFT, padx=2)
            
            controles_tiempo_ajuste = tk.Frame(left_frame, bg='#1a1a1a')
            controles_tiempo_ajuste.pack(pady=(0, 5))
            tk.Button(controles_tiempo_ajuste, text="◀", 
                     command=lambda c=canal: self.ajustar_tiempo(c, -1),
                     bg='#003300', fg='#00FF00', font=('Arial', 10, 'bold'), 
                     width=3).pack(side=tk.LEFT, padx=5)
            tk.Button(controles_tiempo_ajuste, text="▶", 
                     command=lambda c=canal: self.ajustar_tiempo(c, 1),
                     bg='#003300', fg='#00FF00', font=('Arial', 10, 'bold'), 
                     width=3).pack(side=tk.LEFT, padx=5)
            is_fine_t = self.fine_mode_tiempo.get(canal, False)
            fine_t_relief = tk.SUNKEN if is_fine_t else tk.RAISED
            fine_t_fg = '#FFFF00' if is_fine_t else '#FF00FF'
            tk.Button(controles_tiempo_ajuste, text="FINE", 
                     command=lambda c=canal: self.toggle_fine_tiempo(c),
                     bg='#330033', fg=fine_t_fg, relief=fine_t_relief,
                     font=('Arial', 8, 'bold'), 
                     width=5).pack(side=tk.LEFT, padx=5)

            # --- SECCIÓN OFFSET (en right_frame) ---
            # Determinar qué eje está activo
            eje_activo = self.offset_eje_activo.get(canal, 'y')
            
            # Label clickeable para cambiar entre X e Y
            if eje_activo == 'y':
                label_text = "Offset Y"
                label_fg = '#AAAAFF'
            else:
                label_text = "Offset X"
                label_fg = '#FFAA55'
            
            label_offset = tk.Label(right_frame, text=label_text, bg='#1a1a1a', 
                    fg=label_fg, font=('Arial', 8, 'bold'), cursor='hand2')
            label_offset.pack(pady=(3,1))
            label_offset.bind('<Button-1>', lambda e, c=canal: self.toggle_offset_eje(c))

            # Obtener offset actual según el eje activo
            if eje_activo == 'y':
                offset_actual = self.offset_y_manual.get(canal, 0.0)
            else:
                offset_actual = self.offset_x_manual.get(canal, 0.0)

            controles_offset_entry = tk.Frame(right_frame, bg='#1a1a1a')
            controles_offset_entry.pack(pady=(1,1))

            o_var = tk.StringVar(value=f"{offset_actual:.2f}")
            o_entry = tk.Entry(controles_offset_entry, textvariable=o_var, width=5,
                            bg='#333333', fg='#FFFFFF', insertbackground='white',
                            font=('Courier', 9, 'bold'))
            o_entry.pack(side=tk.LEFT, padx=1)
            o_entry.bind('<Return>', lambda event, c=canal: self.set_escala_offset(c, event))
            self.entry_widgets_offset[canal] = o_entry

            controles_offset_ajuste = tk.Frame(right_frame, bg='#1a1a1a')
            controles_offset_ajuste.pack(pady=(0, 2))
            tk.Button(controles_offset_ajuste, text="▲", 
                    command=lambda c=canal: self.ajustar_offset(c, 1),
                    bg='#222222', fg='#AAAAFF' if eje_activo == 'y' else '#FFAA55', 
                    font=('Arial', 8, 'bold'), 
                    width=2, height=1).pack(side=tk.LEFT, padx=1)
            tk.Button(controles_offset_ajuste, text="▼", 
                    command=lambda c=canal: self.ajustar_offset(c, -1),
                    bg='#222222', fg='#AAAAFF' if eje_activo == 'y' else '#FFAA55', 
                    font=('Arial', 8, 'bold'), 
                    width=2, height=1).pack(side=tk.LEFT, padx=1)

            controles_offset_modo = tk.Frame(right_frame, bg='#1a1a1a')
            controles_offset_modo.pack(pady=(0, 2))
            is_fine_o = self.fine_mode_offset.get(canal, False)
            fine_o_relief = tk.SUNKEN if is_fine_o else tk.RAISED
            fine_o_fg = '#FFFF00' if is_fine_o else '#FF00FF'
            tk.Button(controles_offset_modo, text="F", 
                    command=lambda c=canal: self.toggle_fine_offset(c),
                    bg='#330033', fg=fine_o_fg, relief=fine_o_relief,
                    font=('Arial', 7, 'bold'), 
                    width=3, height=1).pack(side=tk.LEFT, padx=1)
            tk.Button(controles_offset_modo, text="R", 
                    command=lambda c=canal: self.reset_offset(c),
                    bg='#330033', fg='#FF00FF', font=('Arial', 7, 'bold'), 
                    width=3, height=1).pack(side=tk.LEFT, padx=1)
    
    def toggle_offset_eje(self, canal):
        """Cambia entre offset X y offset Y"""
        actual = self.offset_eje_activo.get(canal, 'y')
        if actual == 'y':
            self.offset_eje_activo[canal] = 'x'
        else:
            self.offset_eje_activo[canal] = 'y'
        self.actualizar_panel_escalas()
    
    def parse_escala_valor(self, input_str):
        if not input_str: return None
        input_str = input_str.strip().replace(' ', '')
        input_str = re.sub(r"(V|s|/div)", "", input_str, flags=re.IGNORECASE)
        prefijo_char = input_str[-1]
        multiplier = 1.0
        num_part = input_str
        if prefijo_char in self.prefijos_parser:
            multiplier = self.prefijos_parser[prefijo_char]
            num_part = input_str[:-1]
        try:
            valor_base = float(num_part)
            valor_final = valor_base * multiplier
            if valor_final <= 0: return None
            return valor_final
        except ValueError:
            return None

    def set_escala_voltaje(self, canal, event=None):
        entry_widget = self.entry_widgets_voltaje.get(canal)
        if not entry_widget: return
        valor_str = entry_widget.get()
        valor_float = self.parse_escala_valor(valor_str)
        if valor_float:
            self.escalas_voltaje_manual[canal] = valor_float
            self.redibujar_con_escalas()
        else:
            messagebox.showerror("Valor Inválido", 
                                 f"El valor '{valor_str}' no es válido.\n\n"
                                 "Use números y prefijos (ej: 500m, 1.5, 2k)")
            self.actualizar_panel_escalas()

    def set_escala_tiempo(self, canal, event=None):
        entry_widget = self.entry_widgets_tiempo.get(canal)
        if not entry_widget: return
        valor_str = entry_widget.get()
        valor_float = self.parse_escala_valor(valor_str)
        if valor_float:
            self.escalas_tiempo_manual[canal] = valor_float
            self.redibujar_con_escalas()
        else:
            messagebox.showerror("Valor Inválido", 
                                 f"El valor '{valor_str}' no es válido.\n\n"
                                 "Use números y prefijos (ej: 10m, 500u, 1.5)")
            self.actualizar_panel_escalas()
    
    
    def auto_escala_tiempo(self, canal):
        if canal in self.escalas_tiempo_manual:
            del self.escalas_tiempo_manual[canal]
        if canal in self.fine_mode_tiempo:
            del self.fine_mode_tiempo[canal]
        self.redibujar_con_escalas()
    
    def auto_escala_voltaje(self, canal):
        if canal in self.escalas_voltaje_manual:
            del self.escalas_voltaje_manual[canal]
        if canal in self.fine_mode_voltaje:
            del self.fine_mode_voltaje[canal]
        self.redibujar_con_escalas()
    
    
    def toggle_fine_voltaje(self, canal):
        actual = self.fine_mode_voltaje.get(canal, False)
        self.fine_mode_voltaje[canal] = not actual
        self.actualizar_panel_escalas()
    
    def toggle_fine_tiempo(self, canal):
        actual = self.fine_mode_tiempo.get(canal, False)
        self.fine_mode_tiempo[canal] = not actual
        self.actualizar_panel_escalas()
    
    
    def ajustar_voltaje(self, canal, direccion):
        if self.info_escalas is None or not self.info_escalas.get('canales') or canal not in self.info_escalas['canales']:
            return
        if canal in self.escalas_voltaje_manual:
            actual = self.escalas_voltaje_manual[canal]
        else:
            actual = self.info_escalas['canales'][canal]['voltaje_por_div']
        
        is_fine = self.fine_mode_voltaje.get(canal, False)
        
        if is_fine:
            step = actual * 0.02
            if direccion < 0: nuevo_valor = actual - step
            else: nuevo_valor = actual + step
        else:
            escalas_std = [1, 2, 5]
            magnitud = 10 ** np.floor(np.log10(actual))
            normalizado = actual / magnitud
            idx = min(range(len(escalas_std)), key=lambda i: abs(escalas_std[i] - normalizado))
            
            if direccion > 0:
                if idx < len(escalas_std) - 1:
                    nuevo_normalizado = escalas_std[idx + 1]
                else:
                    magnitud *= 10
                    nuevo_normalizado = escalas_std[0]
            else:
                if idx > 0:
                    nuevo_normalizado = escalas_std[idx - 1]
                else:
                    magnitud /= 10
                    nuevo_normalizado = escalas_std[-1]
            nuevo_valor = nuevo_normalizado * magnitud
        
        if nuevo_valor <= 0: nuevo_valor = actual
        self.escalas_voltaje_manual[canal] = nuevo_valor
        self.redibujar_con_escalas()

    def ajustar_tiempo(self, canal, direccion):
        if self.info_escalas is None or not self.info_escalas.get('canales') or canal not in self.info_escalas['canales']:
            return
        if canal in self.escalas_tiempo_manual:
            actual = self.escalas_tiempo_manual[canal]
        else:
            actual = self.info_escalas['canales'][canal]['tiempo_por_div']
        
        is_fine = self.fine_mode_tiempo.get(canal, False)
        
        if is_fine:
            step = actual * 0.02
            if direccion < 0: nuevo_valor = actual - step
            else: nuevo_valor = actual + step
        else:
            escalas_std = [1, 2, 5]
            magnitud = 10 ** np.floor(np.log10(actual))
            normalizado = actual / magnitud
            idx = min(range(len(escalas_std)), key=lambda i: abs(escalas_std[i] - normalizado))
            
            if direccion > 0:
                if idx < len(escalas_std) - 1:
                    nuevo_normalizado = escalas_std[idx + 1]
                else:
                    magnitud *= 10
                    nuevo_normalizado = escalas_std[0]
            else:
                if idx > 0:
                    nuevo_normalizado = escalas_std[idx - 1]
                else:
                    magnitud /= 10
                    nuevo_normalizado = escalas_std[-1]
            nuevo_valor = nuevo_normalizado * magnitud
        
        if nuevo_valor <= 0: nuevo_valor = actual
        self.escalas_tiempo_manual[canal] = nuevo_valor
        self.redibujar_con_escalas()
    
    
    def set_escala_offset(self, canal, event=None):
        entry_widget = self.entry_widgets_offset.get(canal)
        if not entry_widget: return
        valor_str = entry_widget.get()
        try:
            valor_float = float(valor_str)
            # Guardar en el diccionario correcto según el eje activo
            eje_activo = self.offset_eje_activo.get(canal, 'y')
            if eje_activo == 'y':
                self.offset_y_manual[canal] = valor_float
            else:
                self.offset_x_manual[canal] = valor_float
            self.redibujar_con_escalas()
        except ValueError:
            messagebox.showerror("Valor Inválido", 
                                 f"El valor '{valor_str}' debe ser un número.\n\n"
                                 "Ej: 0.5, -1.2")
            self.actualizar_panel_escalas()

    def reset_offset(self, canal):
        # Resetear ambos offsets
        if canal in self.offset_y_manual:
            del self.offset_y_manual[canal]
        if canal in self.offset_x_manual:
            del self.offset_x_manual[canal]
        if canal in self.fine_mode_offset:
            del self.fine_mode_offset[canal]
        self.redibujar_con_escalas()

    def toggle_fine_offset(self, canal):
        actual = self.fine_mode_offset.get(canal, False)
        self.fine_mode_offset[canal] = not actual
        self.actualizar_panel_escalas()
        
    def ajustar_offset(self, canal, direccion):
        if self.info_escalas is None or not self.info_escalas.get('canales') or canal not in self.info_escalas['canales']:
            return
        
        # Determinar qué eje está activo
        eje_activo = self.offset_eje_activo.get(canal, 'y')
        
        if eje_activo == 'y':
            actual = self.offset_y_manual.get(canal, 0.0)
        else:
            actual = self.offset_x_manual.get(canal, 0.0)
        
        is_fine = self.fine_mode_offset.get(canal, False)
        
        if is_fine:
            step = 0.02
        else:
            step = 0.1
        
        nuevo_valor = actual + (step * direccion)
        
        # Límites según el eje
        if eje_activo == 'y':
            limite = self.plotter.divisiones_y * 2
        else:
            limite = self.plotter.divisiones_x * 2
            
        if nuevo_valor > limite: nuevo_valor = limite
        if nuevo_valor < -limite: nuevo_valor = -limite
        
        # Guardar en el diccionario correcto
        if eje_activo == 'y':
            self.offset_y_manual[canal] = nuevo_valor
        else:
            self.offset_x_manual[canal] = nuevo_valor
            
        self.redibujar_con_escalas()
        
    
    def elegir_color(self, canal):
        """Abre el color-picker para cambiar el color de un canal."""
        if self.info_escalas is None or not self.info_escalas.get('canales') or canal not in self.info_escalas['canales']:
            return
        color_actual = self.info_escalas['canales'][canal]['color']
        color_info = colorchooser.askcolor(color=color_actual)
        
        if color_info and color_info[1]:
            nuevo_color = color_info[1]
            self.colores_manuales[canal] = nuevo_color
            self.redibujar_con_escalas()

    
    def redibujar_con_escalas(self):
        """
        Redibuja el gráfico aplicando las escalas manuales
        """
        if self.df is None:
            return
        
        canales_a_graficar = {col: i for col, var, i in self.canal_vars if var.get()}
        
        # Obtener nombre real del canal anclado
        nombre_ui = self.canal_cursor_seleccionado.get()
        nombre_real = self.mapa_nombres_canales_cursor.get(nombre_ui)
        
        cursor_info_dict = {
            'pos': self.cursor_pos,
            'canal_anclado': nombre_real
        } if self.cursores_activos.get() else None

        if not canales_a_graficar:
            self.ax.clear()
            self.plotter.configurar_estilo_osciloscopio(self.ax)
            if cursor_info_dict:
                 info_cursores = self.plotter.graficar_canales(self.ax, self.df, {}, cursor_info=cursor_info_dict)
                 self.cursor_artists = info_cursores.get('cursor_artists', {})
                 # Guardar también las etiquetas de texto
                 if 'cursor_texts' in info_cursores:
                     # Asegurarse que self.info_escalas exista
                     if self.info_escalas is None:
                         self.info_escalas = {}
                     self.info_escalas['cursor_texts'] = info_cursores.get('cursor_texts', {})
            else:
                 self.cursor_artists = {}
            self.canvas.draw()
            self.info_escalas = None # Limpiar info si no hay canales
            self.actualizar_panel_escalas()
            self.actualizar_display_cursores()
            self.actualizar_lista_canales_cursor_y_redibujar_si_es_necesario() # Llamada a la nueva lógica
            return
        
        self.ax.clear()
        
        self.info_escalas = self.plotter.graficar_canales(
            self.ax, self.df, canales_a_graficar, 
            self.escalas_voltaje_manual,
            self.escalas_tiempo_manual,
            self.offset_y_manual,
            self.offset_x_manual,
            self.colores_manuales,
            cursor_info=cursor_info_dict
        )
        
        self.cursor_artists = self.info_escalas.get('cursor_artists', {})
        
        self.actualizar_panel_escalas()
        self.actualizar_display_cursores()
        self.canvas.draw()
        
        # Llamar a la lógica de actualización del ComboBox de cursores
        # Esta función ahora también maneja el redibujado si es necesario
        self.actualizar_lista_canales_cursor_y_redibujar_si_es_necesario()
    
    
    def actualizar_lista_canales_cursor_y_redibujar_si_es_necesario(self):
        """
        Actualiza el ComboBox de cursores y redibuja si el canal anclado
        se fuerza a cambiar (ej: al activar cursores por primera vez).
        """
        
        # Guardar el nombre UI actual ANTES de recalcular la lista
        nombre_ui_actual = self.canal_cursor_seleccionado.get()
        
        # Actualizar lista de canales para el desplegable de cursores
        self.mapa_nombres_canales_cursor.clear()
        nombres_canales_ui = []
        if self.info_escalas and self.info_escalas.get('canales'):
            canales_ordenados = sorted(self.info_escalas['canales'].items(), 
                                      key=lambda item: item[1]['indice_canal'])
            for col_name, info in canales_ordenados:
                nombre_ui = f"Canal {info['indice_canal'] + 1}"
                nombres_canales_ui.append(nombre_ui)
                self.mapa_nombres_canales_cursor[nombre_ui] = col_name
            
        self.combo_canal_cursor['values'] = nombres_canales_ui
        self.combo_canal_cursor.config(state='readonly')
        
        # Comprobar si el canal anclado actual sigue siendo válido
        nombre_real_actual = self.mapa_nombres_canales_cursor.get(nombre_ui_actual)
        needs_redraw_for_cursors = False

        if (not nombre_real_actual) and nombres_canales_ui:
            # El canal seleccionado (o "") no es válido, pero SÍ hay canales visibles.
            # Forzar la selección al primer canal disponible.
            self.canal_cursor_seleccionado.set(nombres_canales_ui[0])
            # Marcar que necesitamos redibujar para que las etiquetas (ej: "div") se actualicen
            needs_redraw_for_cursors = True
        elif not nombres_canales_ui:
            # No hay canales visibles, limpiar la selección
            self.canal_cursor_seleccionado.set("")
        
        # Si forzamos una nueva selección de canal Y los cursores están activos,
        # llamamos a redibujar OTRA VEZ.
        # Esto reemplazará las etiquetas "div" con las etiquetas correctas.
        if needs_redraw_for_cursors and self.cursores_activos.get():
            # Esta llamada recursiva es segura (limitada a 1 nivel)
            self.redibujar_con_escalas()

    
    def toggle_cursores(self):
        """Activa o desactiva la visualización de los cursores"""
        if not self.cursores_activos.get():
            self.cursor_artists = {}
            self.linea_arrastrada = None
        self.redibujar_con_escalas()

    def actualizar_cursores(self, event=None):
        """Se llama al cambiar el canal anclado"""
        # Al cambiar de canal, redibujar para que las etiquetas de texto se actualicen
        self.redibujar_con_escalas() 
        
    def _formatear_valor(self, valor, unidad):
        """Función helper para formatear números con prefijos (m, u, k, etc.)"""
        if not np.isfinite(valor):
            return "--"
        if valor == 0:
            return f"0.00{unidad}"
        factor, simbolo = self.plotter.determinar_prefijo(abs(valor))
        return f"{valor/factor:.2f}{simbolo}{unidad}"

    
    def actualizar_display_cursores(self):
        """Actualiza las etiquetas de la barra de estado con los valores"""
        
        # Si la info de escalas no está lista, no hacer nada
        if self.info_escalas is None:
            self.label_cursor_x_info.config(text="X1: -- X2: -- ΔX: --")
            self.label_cursor_y_info.config(text="Y1: -- Y2: -- ΔY: --")
            return
            
        if not self.cursores_activos.get() or not self.info_escalas.get('canales'):
            self.label_cursor_x_info.config(text="X1: -- X2: -- ΔX: --")
            self.label_cursor_y_info.config(text="Y1: -- Y2: -- ΔY: --")
            return

        nombre_ui = self.canal_cursor_seleccionado.get()
        nombre_real = self.mapa_nombres_canales_cursor.get(nombre_ui)
        
        if not nombre_real or nombre_real not in self.info_escalas['canales']:
            self.label_cursor_x_info.config(text="X (Canal no válido)")
            self.label_cursor_y_info.config(text="Y (Canal no válido)")
            return
            
        info = self.info_escalas['canales'][nombre_real]
        
        t_div = info['tiempo_por_div']
        t_centro = info['t_centro']
        v_div = info['voltaje_por_div']
        v_centro = info['v_centro']
        divs_x = self.plotter.divisiones_x
        
        x1p = self.cursor_pos['x1']
        x2p = self.cursor_pos['x2']
        y1p = self.cursor_pos['y1']
        y2p = self.cursor_pos['y2']

        # Conversión de Tiempo (SIN considerar offset X)
        t1_real = ((x1p - (divs_x / 2)) * t_div) + t_centro
        t2_real = ((x2p - (divs_x / 2)) * t_div) + t_centro
        dt = t2_real - t1_real
        
        str_t1 = self._formatear_valor(t1_real, 's')
        str_t2 = self._formatear_valor(t2_real, 's')
        str_dt = self._formatear_valor(dt, 's')
        
        self.label_cursor_x_info.config(text=f"X1: {str_t1}  X2: {str_t2}  ΔX: {str_dt}")

        # Conversión de Tensión (SIN considerar offset Y)
        v1_abs = (y1p * v_div) + v_centro
        v2_abs = (y2p * v_div) + v_centro
        dv = v2_abs - v1_abs
        
        str_v1 = self._formatear_valor(v1_abs, 'V')
        str_v2 = self._formatear_valor(v2_abs, 'V')
        str_dv = self._formatear_valor(dv, 'V')

        self.label_cursor_y_info.config(text=f"Y1: {str_v1}  Y2: {str_v2}  ΔY: {str_dv}")
    
    
    def on_motion(self, event):
        
        if self.linea_arrastrada is None:
            return
        if event.inaxes != self.ax:
            return
        
        key, line = self.linea_arrastrada
        x, y = event.xdata, event.ydata

        if x is None or y is None:
            return
        
        # Si la info de escalas no está lista, no hacer nada
        if self.info_escalas is None:
            return
            
        # Obtener nombre real del canal anclado
        nombre_ui = self.canal_cursor_seleccionado.get()
        nombre_real = self.mapa_nombres_canales_cursor.get(nombre_ui)
        
        if key.startswith('x'):
            x = max(0, min(self.plotter.divisiones_x, x)) 
            line.set_xdata([x, x])
            self.cursor_pos[key] = x
            
            # Actualizar etiqueta X1 o X2
            if 'cursor_texts' in self.info_escalas:
                text_key = f'text_{key}'
                if text_key in self.info_escalas['cursor_texts']:
                    text_artist = self.info_escalas['cursor_texts'][text_key]
                    
                    # Calcular nuevo label
                    if nombre_real and self.info_escalas.get('canales') and nombre_real in self.info_escalas['canales']:
                        info_canal = self.info_escalas['canales'][nombre_real]
                        t_div = info_canal['tiempo_por_div']
                        t_centro = info_canal['t_centro']
                        t_factor = info_canal['tiempo_factor']
                        t_simbolo = info_canal['tiempo_simbolo']
                        # CÁLCULO SIN OFFSET:
                        x_real = ((x - (self.plotter.divisiones_x / 2)) * t_div) + t_centro
                        nuevo_label = f"{key.upper()}: {x_real/t_factor:.3f}{t_simbolo}s"
                    else:
                        nuevo_label = f"{key.upper()}: {x:.3f}div"
                    
                    text_artist.set_text(nuevo_label)
                    
                    # --- MODIFICADO: Posiciones X1/X2 diferentes ---
                    if key == 'x1':
                        # Posición Y para la etiqueta X1 (ej: -0.5)
                        text_artist.set_position((x, self.plotter.divisiones_y/2 - 0.5))
                    elif key == 'x2':
                        # Posición Y diferente para la etiqueta X2 (ej: -0.8, más abajo)
                        text_artist.set_position((x, self.plotter.divisiones_y/2 - 0.8))
                    # --- FIN MODIFICACIÓN ---
            
        elif key.startswith('y'):
            y = max(-self.plotter.divisiones_y/2, min(self.plotter.divisiones_y/2, y))
            line.set_ydata([y, y])
            self.cursor_pos[key] = y
            
            # Actualizar etiqueta Y1 o Y2
            if 'cursor_texts' in self.info_escalas:
                text_key = f'text_{key}'
                if text_key in self.info_escalas['cursor_texts']:
                    text_artist = self.info_escalas['cursor_texts'][text_key]
                    
                    # Calcular nuevo label
                    if nombre_real and self.info_escalas.get('canales') and nombre_real in self.info_escalas['canales']:
                        info_canal = self.info_escalas['canales'][nombre_real]
                        v_div = info_canal['voltaje_por_div']
                        v_centro = info_canal['v_centro']
                        v_factor = info_canal['voltaje_factor']
                        v_simbolo = info_canal['voltaje_simbolo']
                        # CÁLCULO SIN OFFSET:
                        y_real = (y * v_div) + v_centro
                        nuevo_label = f"{key.upper()}: {y_real/v_factor:.3f}{v_simbolo}V"
                    else:
                        nuevo_label = f"{key.upper()}: {y:.3f}div"
                    
                    text_artist.set_text(nuevo_label)

                    # --- MODIFICADO: Posiciones Y1/Y2 diferentes ---
                    if key == 'y1':
                        # Posición X para la etiqueta Y1 (ej: 0.3)
                        text_artist.set_position((0.3, y))
                    elif key == 'y2':
                        # Posición X diferente para la etiqueta Y2 (ej: 0.6, más a la derecha)
                        text_artist.set_position((0.6, y))
                    # --- FIN MODIFICACIÓN ---
            
        # Actualizar ΔX y ΔY SIEMPRE, sin importar qué línea se movió.
        if 'cursor_texts' in self.info_escalas:
            
            # Actualizar ΔX
            if 'text_dx' in self.info_escalas['cursor_texts']:
                text_dx = self.info_escalas['cursor_texts']['text_dx']
                x1_pos = self.cursor_pos['x1']
                x2_pos = self.cursor_pos['x2']
                
                if nombre_real and self.info_escalas.get('canales') and nombre_real in self.info_escalas['canales']:
                    info_canal = self.info_escalas['canales'][nombre_real]
                    t_div = info_canal['tiempo_por_div']
                    t_centro = info_canal['t_centro']
                    t_factor = info_canal['tiempo_factor']
                    t_simbolo = info_canal['tiempo_simbolo']
                    
                    # CÁLCULO SIN OFFSET:
                    x1_real = ((x1_pos - (self.plotter.divisiones_x / 2)) * t_div) + t_centro
                    x2_real = ((x2_pos - (self.plotter.divisiones_x / 2)) * t_div) + t_centro
                    delta_x = abs(x2_real - x1_real)
                    label_dx = f"ΔX: {delta_x/t_factor:.3f}{t_simbolo}s"
                else:
                    delta_x = abs(x2_pos - x1_pos)
                    label_dx = f"ΔX: {delta_x:.3f}div"
                
                text_dx.set_text(label_dx)

            # Actualizar ΔY
            if 'text_dy' in self.info_escalas['cursor_texts']:
                text_dy = self.info_escalas['cursor_texts']['text_dy']
                y1_pos = self.cursor_pos['y1']
                y2_pos = self.cursor_pos['y2']
                
                if nombre_real and self.info_escalas.get('canales') and nombre_real in self.info_escalas['canales']:
                    info_canal = self.info_escalas['canales'][nombre_real]
                    v_div = info_canal['voltaje_por_div']
                    v_centro = info_canal['v_centro']
                    v_factor = info_canal['voltaje_factor']
                    v_simbolo = info_canal['voltaje_simbolo']
                    
                    # CÁLCULO SIN OFFSET:
                    y1_real = (y1_pos * v_div) + v_centro
                    y2_real = (y2_pos * v_div) + v_centro
                    delta_y = abs(y2_real - y1_real)
                    label_dy = f"ΔY: {delta_y/v_factor:.3f}{v_simbolo}V"
                else:
                    delta_y = abs(y2_pos - y1_pos)
                    label_dy = f"ΔY: {delta_y:.3f}div"
                
                text_dy.set_text(label_dy)

        self.canvas.draw_idle()
        self.actualizar_display_cursores()

    def on_press(self, event):
        """Manejador para cuando se presiona el botón del mouse"""
        if not self.cursores_activos.get() or not self.cursor_artists:
            return
        if event.inaxes != self.ax:
            return
        
        pick_tolerance = 0.1 
        
        x, y = event.xdata, event.ydata
        
        if x is None or y is None:
            return
            
        for key, line in self.cursor_artists.items():
            if key.startswith('x'):
                line_pos = line.get_xdata()[0]
                if abs(x - line_pos) < pick_tolerance:
                    self.linea_arrastrada = (key, line)
                    return
            elif key.startswith('y'):
                line_pos = line.get_ydata()[0]
                if abs(y - line_pos) < pick_tolerance:
                    self.linea_arrastrada = (key, line)
                    return

    def on_release(self, event):
        """Manejador para cuando se suelta el botón del mouse"""
        if self.linea_arrastrada:
            self.actualizar_display_cursores()
        self.linea_arrastrada = None

    
    def mostrar_acerca_de(self):
        """
        Muestra información sobre la aplicación
        """
        messagebox.showinfo("Acerca de", 
                          "Osciloscopio Digital - Visor CSV v2.8\n\n"
                          "Visualizador de datos de osciloscopio\n"
                          "con interfaz estilo instrumento real\n\n"
                          "Características:\n"
                          "• Cuadrícula fija (10x8)\n"
                          "• V/div, T/div y Posición Vertical/Horizontal\n"
                          "• Cursores X/Y arrastrables con etiquetas en vivo\n"
                          "• Cálculo de ΔX y ΔY en barra de estado")

# Bloque principal para ejecutar la aplicación (si se desea)
if __name__ == "__main__":
    try:
        # Importar los módulos necesarios que podrían faltar si se ejecuta solo
        from data_handler import DataHandler
        from plotter import Plotter
    except ImportError:
        print("Asegúrate de que data_handler.py y plotter.py están en el mismo directorio.")
        # Definir clases dummy para permitir que el script al menos se inicie
        # y muestre la GUI, aunque no funcionará sin los archivos reales.
        if 'DataHandler' not in globals():
            class DataHandler:
                def cargar_csv(self, archivo):
                    print(f"Dummy: Cargar {archivo}")
                    return None # No se puede continuar sin datos reales
        if 'Plotter' not in globals():
            class Plotter:
                def __init__(self):
                    self.divisiones_x = 10
                    self.divisiones_y = 8
                def configurar_estilo_osciloscopio(self, ax):
                    print("Dummy: Configurar estilo")
                def graficar_canales(self, ax, df, canales, *args, **kwargs):
                    print("Dummy: Graficar canales")
                    return {}
                def determinar_prefijo(self, valor):
                    return (1, "")

    root = tk.Tk()
    app = OsciloscopioGUI(root)
    root.mainloop()