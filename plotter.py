"""
plotter.py - Manejo de gráficos estilo osciloscopio real
Se encarga de crear gráficos con cuadrícula sin valores, mostrando V/div y T/div
"""

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import NullFormatter, AutoMinorLocator, MultipleLocator

class Plotter:
    """
    Clase que maneja la creación de gráficos estilo osciloscopio
    """
    
    def __init__(self):
        """
        Inicializa el graficador con colores predefinidos
        """
        self.colores = [
            '#FFD700',  # Amarillo (clásico canal 1)
            '#00FFFF',  # Cian (clásico canal 2)
            '#FF1493',  # Rosa fuerte (canal 3)
            '#00FF00',  # Verde brillante (canal 4)
            '#FF8C00',  # Naranja
            '#FF69B4',  # Rosa claro
            '#7FFF00',  # Verde chartreuse
            '#FF6347',  # Rojo tomate
            '#00CED1',  # Turquesa oscuro
            '#FFB6C1'   # Rosa pálido
        ]
        
        self.prefijos = [
            (1e12, 'T'), (1e9, 'G'), (1e6, 'M'), (1e3, 'k'), (1, ''),
            (1e-3, 'm'), (1e-6, 'μ'), (1e-9, 'n'), (1e-12, 'p'), (1e-15, 'f')
        ]
        
        self.divisiones_x = 10
        self.divisiones_y = 8
    
    def determinar_prefijo(self, valor):
        if valor == 0: return (1, '')
        valor_abs = abs(valor)
        for factor, simbolo in self.prefijos:
            if valor_abs >= factor:
                return (factor, simbolo)
        return (1e-15, 'f')
    
    def calcular_escala_bonita(self, rango, num_divisiones):
        # Si el rango es 0 (línea plana) o inválido, devuelve 1 para evitar división por cero.
        if rango == 0 or not np.isfinite(rango): 
            return 1
            
        division_aproximada = rango / num_divisiones
        magnitud = 10 ** np.floor(np.log10(division_aproximada))
        normalizado = division_aproximada / magnitud
        
        if normalizado <= 1.5: valor_bonito = 1
        elif normalizado <= 3: valor_bonito = 2
        elif normalizado <= 7: valor_bonito = 5
        else: valor_bonito = 10
        
        return valor_bonito * magnitud
    
    def graficar_canales(self, ax, df, canales_con_indices, escalas_voltaje=None, 
                        escalas_tiempo=None, offsets_y=None, offsets_x=None, 
                        colores_manuales=None, cursor_info=None):
        """
        Grafica los canales en estilo osciloscopio con cuadrícula sin valores
        """
        ax.clear()
        
        self.configurar_estilo_osciloscopio(ax)
        
        # Inicializar info_escalas
        info_escalas = {'canales': {}}
        
        # Si no hay canales, solo dibujar cursores (si están activos) y salir
        if not canales_con_indices:
            if cursor_info:
                pos = cursor_info['pos']
                line_x1 = ax.axvline(pos['x1'], color='cyan', linestyle='--', linewidth=1.5, alpha=0.8)
                line_x2 = ax.axvline(pos['x2'], color='cyan', linestyle='--', linewidth=1.5, alpha=0.8)
                line_y1 = ax.axhline(pos['y1'], color='magenta', linestyle='--', linewidth=1.5, alpha=0.8)
                line_y2 = ax.axhline(pos['y2'], color='magenta', linestyle='--', linewidth=1.5, alpha=0.8)
                
                # --- Posiciones X1/X2 Y1/Y2 diferentes ---
                text_x1 = ax.text(pos['x1'], self.divisiones_y/2 - 0.5, f"X1: {pos['x1']:.2f} div", 
                       color='cyan', fontsize=9, fontweight='bold', ha='center',
                       bbox=dict(boxstyle='round,pad=0.3', facecolor='black', edgecolor='cyan', alpha=0.9))
                text_x2 = ax.text(pos['x2'], self.divisiones_y/2 - 0.8, f"X2: {pos['x2']:.2f} div", 
                       color='cyan', fontsize=9, fontweight='bold', ha='center',
                       bbox=dict(boxstyle='round,pad=0.3', facecolor='black', edgecolor='cyan', alpha=0.9))
                text_y1 = ax.text(0.3, pos['y1'], f"Y1: {pos['y1']:.2f} div", 
                       color='magenta', fontsize=9, fontweight='bold', va='center',
                       bbox=dict(boxstyle='round,pad=0.3', facecolor='black', edgecolor='magenta', alpha=0.9))
                text_y2 = ax.text(0.6, pos['y2'], f"Y2: {pos['y2']:.2f} div", 
                       color='magenta', fontsize=9, fontweight='bold', va='center',
                       bbox=dict(boxstyle='round,pad=0.3', facecolor='black', edgecolor='magenta', alpha=0.9))
                
                info_escalas['cursor_artists'] = {
                    'x1': line_x1, 'x2': line_x2, 'y1': line_y1, 'y2': line_y2
                }
                info_escalas['cursor_texts'] = {
                    'text_x1': text_x1, 'text_x2': text_x2, 
                    'text_y1': text_y1, 'text_y2': text_y2
                }
            return info_escalas
        

        # --- MODIFICADO: Cálculo de tiempo a prueba de NaN ---
        tiempo = df[df.columns[0]].values
        t_min = np.nanmin(tiempo) # USAR NANMIN
        t_max = np.nanmax(tiempo) # USAR NANMAX

        if not np.isfinite(t_min) or not np.isfinite(t_max):
             # Si el tiempo es inválido, no se puede graficar
             t_min = 0
             t_max = 1
             t_rango = 1
             t_centro_datos = 0.5
        else:
             t_rango = t_max - t_min
             if t_rango == 0: # Evitar división por cero si solo hay 1 punto de tiempo
                 t_rango = 1 
             t_centro_datos = t_min + t_rango / 2
        # --- FIN MODIFICACIÓN ---

        # Preparar diccionarios
        escalas_voltaje = {} if escalas_voltaje is None else escalas_voltaje
        escalas_tiempo = {} if escalas_tiempo is None else escalas_tiempo
        offsets_y = {} if offsets_y is None else offsets_y
        offsets_x = {} if offsets_x is None else offsets_x
        colores_manuales = {} if colores_manuales is None else colores_manuales

        for i, (canal, indice_canal) in enumerate(canales_con_indices.items()):
            datos = df[canal].values
            
            # --- MODIFICADO: Cálculo de voltaje a prueba de NaN ---
            v_min_datos = np.nanmin(datos)
            v_max_datos = np.nanmax(datos)

            # Comprobar si los datos son válidos
            if not np.isfinite(v_min_datos) or not np.isfinite(v_max_datos):
                # Todos los datos son NaN o Infinitos. Poner valores por defecto.
                v_rango = 0
                v_centro_datos = 0
            else:
                v_rango = v_max_datos - v_min_datos
                v_centro_datos = v_min_datos + v_rango / 2
            # --- FIN MODIFICACIÓN ---
            
            # --- Auto-escala de Voltaje ---
            if canal in escalas_voltaje:
                v_div = escalas_voltaje[canal]
            else:
                v_div = self.calcular_escala_bonita(v_rango, self.divisiones_y - 2)
            
            # --- Auto-escala de Tiempo ---
            if canal in escalas_tiempo:
                t_div = escalas_tiempo[canal]
            else:
                t_div = self.calcular_escala_bonita(t_rango, self.divisiones_x)
            
            # --- Offsets ---
            offset_y_divs = offsets_y.get(canal, 0.0)
            offset_x_divs = offsets_x.get(canal, 0.0)
            
            # Convertir datos a coordenadas de cuadrícula (0-10, -4 a 4)
            # Y = ( (Datos - Centro_Datos) / V_div ) + Offset_Y
            y_transformado = ((datos - v_centro_datos) / v_div) + offset_y_divs
            
            # X = ( (Tiempo - Centro_Datos_T) / T_div ) + (Divs_X / 2) + Offset_X
            x_transformado = ((tiempo - t_centro_datos) / t_div) + (self.divisiones_x / 2) + offset_x_divs
            
            # --- Determinar color ---
            color = colores_manuales.get(canal, self.colores[indice_canal % len(self.colores)])
            
            ax.plot(x_transformado, y_transformado, color=color, 
                    label=f"Canal {indice_canal + 1}", linewidth=1.5)
            
            # --- Guardar información de escala ---
            v_factor, v_simbolo = self.determinar_prefijo(v_div)
            t_factor, t_simbolo = self.determinar_prefijo(t_div)
            
            info_escalas['canales'][canal] = {
                'voltaje_por_div': v_div,
                'tiempo_por_div': t_div,
                'v_centro': v_centro_datos,
                't_centro': t_centro_datos,
                'voltaje_factor': v_factor,
                'voltaje_simbolo': v_simbolo,
                'tiempo_factor': t_factor,
                'tiempo_simbolo': t_simbolo,
                'offset_y_divs': offset_y_divs,
                'offset_x_divs': offset_x_divs,
                'indice_canal': indice_canal,
                'color': color
            }

        # --- Graficar Cursores ---
        if cursor_info:
            pos = cursor_info['pos']
            canal_anclado = cursor_info['canal_anclado']
            
            # Dibujar líneas
            line_x1 = ax.axvline(pos['x1'], color='cyan', linestyle='--', linewidth=1.5, alpha=0.8)
            line_x2 = ax.axvline(pos['x2'], color='cyan', linestyle='--', linewidth=1.5, alpha=0.8)
            line_y1 = ax.axhline(pos['y1'], color='magenta', linestyle='--', linewidth=1.5, alpha=0.8)
            line_y2 = ax.axhline(pos['y2'], color='magenta', linestyle='--', linewidth=1.5, alpha=0.8)
            
            info_escalas['cursor_artists'] = {
                'x1': line_x1, 'x2': line_x2, 'y1': line_y1, 'y2': line_y2
            }
            info_escalas['cursor_texts'] = {}

            if canal_anclado and canal_anclado in info_escalas['canales']:
                info_canal = info_escalas['canales'][canal_anclado]
                
                # Conversión X (tiempo) - SIN offset X
                t_div = info_canal['tiempo_por_div']
                t_centro_canal = info_canal['t_centro']
                t_factor = info_canal['tiempo_factor']
                t_simbolo = info_canal['tiempo_simbolo']
                x1_real = ((pos['x1'] - (self.divisiones_x / 2)) * t_div) + t_centro_canal
                x2_real = ((pos['x2'] - (self.divisiones_x / 2)) * t_div) + t_centro_canal
                delta_x = abs(x2_real - x1_real)
                label_x1 = f"X1: {x1_real/t_factor:.3f}{t_simbolo}s"
                label_x2 = f"X2: {x2_real/t_factor:.3f}{t_simbolo}s"
                label_dx = f"ΔX: {delta_x/t_factor:.3f}{t_simbolo}s"

                # Conversión Y (voltaje) - SIN offset Y
                v_div = info_canal['voltaje_por_div']
                v_centro_canal = info_canal['v_centro']
                v_factor = info_canal['voltaje_factor']
                v_simbolo = info_canal['voltaje_simbolo']
                y1_real = (pos['y1'] * v_div) + v_centro_canal
                y2_real = (pos['y2'] * v_div) + v_centro_canal
                delta_y = abs(y2_real - y1_real)
                label_y1 = f"Y1: {y1_real/v_factor:.3f}{v_simbolo}V"
                label_y2 = f"Y2: {y2_real/v_factor:.3f}{v_simbolo}V"
                label_dy = f"ΔY: {delta_y/v_factor:.3f}{v_simbolo}V"
            
            else:
                # Caso fallback si el canal no es válido (ej: se acaba de apagar)
                label_x1 = f"X1: {pos['x1']:.2f} div"
                label_x2 = f"X2: {pos['x2']:.2f} div"
                label_y1 = f"Y1: {pos['y1']:.2f} div"
                label_y2 = f"Y2: {pos['y2']:.2f} div"
                delta_x = abs(pos['x2'] - pos['x1'])
                delta_y = abs(pos['y2'] - pos['y1'])
                label_dx = f"ΔX: {delta_x:.2f} div"
                label_dy = f"ΔY: {delta_y:.2f} div"

            # --- Posiciones X1/X2 Y1/Y2 diferentes ---
            text_x1 = ax.text(pos['x1'], self.divisiones_y/2 - 0.5, label_x1, 
                   color='cyan', fontsize=9, fontweight='bold', ha='center',
                   bbox=dict(boxstyle='round,pad=0.3', facecolor='black', edgecolor='cyan', alpha=0.9))
            text_x2 = ax.text(pos['x2'], self.divisiones_y/2 - 0.8, label_x2, 
                   color='cyan', fontsize=9, fontweight='bold', ha='center',
                   bbox=dict(boxstyle='round,pad=0.3', facecolor='black', edgecolor='cyan', alpha=0.9))
            text_y1 = ax.text(0.3, pos['y1'], label_y1, 
                   color='magenta', fontsize=9, fontweight='bold', va='center',
                   bbox=dict(boxstyle='round,pad=0.3', facecolor='black', edgecolor='magenta', alpha=0.9))
            text_y2 = ax.text(0.6, pos['y2'], label_y2, 
                   color='magenta', fontsize=9, fontweight='bold', va='center',
                   bbox=dict(boxstyle='round,pad=0.3', facecolor='black', edgecolor='magenta', alpha=0.9))
            # --- FIN MODIFICACIÓN ---

            # Etiquetas Delta (fijas en la esquina)
            text_dx = ax.text(self.divisiones_x - 0.3, self.divisiones_y/2 - 1.9, label_dx, 
                   color='cyan', fontsize=9, fontweight='bold', ha='right',
                   bbox=dict(boxstyle='round,pad=0.3', facecolor='black', edgecolor='cyan', alpha=0.9))
            text_dy = ax.text(self.divisiones_x - 0.3, self.divisiones_y/2 - 2.5, label_dy, 
                   color='magenta', fontsize=9, fontweight='bold', ha='right',
                   bbox=dict(boxstyle='round,pad=0.3', facecolor='black', edgecolor='magenta', alpha=0.9))
            
            info_escalas['cursor_texts'] = {
                'text_x1': text_x1, 'text_x2': text_x2, 
                'text_y1': text_y1, 'text_y2': text_y2,
                'text_dx': text_dx, 'text_dy': text_dy
            }
        
        return info_escalas
    
    def configurar_estilo_osciloscopio(self, ax):
        """
        Configura el aspecto visual estilo osciloscopio (fondo oscuro, cuadrícula sin números)
        """
        ax.set_facecolor('#000000')
        ax.figure.patch.set_facecolor('#1a1a1a')
        
        ax.xaxis.set_major_formatter(NullFormatter())
        ax.yaxis.set_major_formatter(NullFormatter())
        
        ax.grid(True, which='major', color='#00FF00', alpha=0.5, 
               linestyle='-', linewidth=1.2)
        
        ax.minorticks_on()
        ax.grid(True, which='minor', color='#00FF00', alpha=0.2, 
               linestyle='-', linewidth=0.6)
        
        ax.set_xlim(0, self.divisiones_x)
        ax.set_ylim(-(self.divisiones_y / 2), (self.divisiones_y / 2))

        ax.xaxis.set_major_locator(MultipleLocator(1))
        ax.yaxis.set_major_locator(MultipleLocator(1))
        
        ax.xaxis.set_minor_locator(MultipleLocator(0.2))
        ax.yaxis.set_minor_locator(MultipleLocator(0.2))
        
        ax.set_title('Osciloscopio', fontsize=14, color='#00FF00', fontweight='bold')
        ax.figure.tight_layout()