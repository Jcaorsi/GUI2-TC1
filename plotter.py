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
        if rango == 0: return 1
        division_aproximada = rango / num_divisiones
        magnitud = 10 ** np.floor(np.log10(division_aproximada))
        normalizado = division_aproximada / magnitud
        
        if normalizado <= 1.5: valor_bonito = 1
        elif normalizado <= 3: valor_bonito = 2
        elif normalizado <= 7: valor_bonito = 5
        else: valor_bonito = 10
        
        return valor_bonito * magnitud
    
    def graficar_canales(self, ax, df, canales_con_indices, escalas_voltaje=None, 
                        escalas_tiempo=None, offsets=None, colores_manuales=None, 
                        cursor_info=None):
        """
        Grafica los canales en estilo osciloscopio con cuadrícula sin valores
        
        Args:
            ax: Eje de matplotlib
            df: DataFrame con los datos
            canales_con_indices: Dict {nombre_canal: índice}
            escalas_voltaje: Dict {canal: V/div}
            escalas_tiempo: Dict {canal: T/div}
            offsets: Dict {canal: offset_en_divs}
            colores_manuales: Dict {canal: color_hex}
            cursor_info: Dict con info de cursores {'pos': {...}, 'canal_anclado': 'nombre_canal'}
        
        Returns:
            dict: Información de escalas y artistas de cursores
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
                
                # Sin canal anclado, mostrar divisiones
                text_x1 = ax.text(pos['x1'], self.divisiones_y/2 - 0.3, f"X1: {pos['x1']:.2f} div", 
                       color='cyan', fontsize=9, fontweight='bold', ha='center',
                       bbox=dict(boxstyle='round,pad=0.3', facecolor='black', edgecolor='cyan', alpha=0.9))
                text_x2 = ax.text(pos['x2'], self.divisiones_y/2 - 0.3, f"X2: {pos['x2']:.2f} div", 
                       color='cyan', fontsize=9, fontweight='bold', ha='center',
                       bbox=dict(boxstyle='round,pad=0.3', facecolor='black', edgecolor='cyan', alpha=0.9))
                text_y1 = ax.text(0.3, pos['y1'], f"Y1: {pos['y1']:.2f} div", 
                       color='magenta', fontsize=9, fontweight='bold', va='center',
                       bbox=dict(boxstyle='round,pad=0.3', facecolor='black', edgecolor='magenta', alpha=0.9))
                text_y2 = ax.text(0.3, pos['y2'], f"Y2: {pos['y2']:.2f} div", 
                       color='magenta', fontsize=9, fontweight='bold', va='center',
                       bbox=dict(boxstyle='round,pad=0.3', facecolor='black', edgecolor='magenta', alpha=0.9))
                
                info_escalas['cursor_artists'] = {
                    'x1': line_x1, 'x2': line_x2, 'y1': line_y1, 'y2': line_y2
                }
                info_escalas['cursor_texts'] = {
                    'text_x1': text_x1, 'text_x2': text_x2, 'text_y1': text_y1, 'text_y2': text_y2
                }
            return info_escalas
            
        tiempo_original = df[df.columns[0]]
        t_min, t_max = tiempo_original.min(), tiempo_original.max()
        rango_tiempo = t_max - t_min
        t_centro = (t_min + t_max) / 2
        tiempo_por_div_base = self.calcular_escala_bonita(rango_tiempo, self.divisiones_x)
        
        for canal, i in canales_con_indices.items():
            
            if colores_manuales and canal in colores_manuales:
                color = colores_manuales[canal]
            else:
                color = self.colores[i % len(self.colores)]
            
            voltaje_original = df[canal]
            
            # --- ESCALA DE TIEMPO ---
            if escalas_tiempo and canal in escalas_tiempo:
                tiempo_por_div_canal = escalas_tiempo[canal]
            else:
                tiempo_por_div_canal = tiempo_por_div_base
            tiempo_canal = (tiempo_original - t_centro) / tiempo_por_div_canal + (self.divisiones_x / 2)
            factor_tiempo, simbolo_tiempo = self.determinar_prefijo(tiempo_por_div_canal)
            
            # --- ESCALA DE VOLTAJE ---
            v_min, v_max = voltaje_original.min(), voltaje_original.max()
            rango_voltaje = v_max - v_min
            v_centro = (v_min + v_max) / 2
            voltaje_por_div_base = self.calcular_escala_bonita(rango_voltaje, self.divisiones_y)
            
            if escalas_voltaje and canal in escalas_voltaje:
                voltaje_por_div_canal = escalas_voltaje[canal]
            else:
                voltaje_por_div_canal = voltaje_por_div_base
            
            voltaje_canal = (voltaje_original - v_centro) / voltaje_por_div_canal
            factor_voltaje, simbolo_voltaje = self.determinar_prefijo(voltaje_por_div_canal)
            
            # --- OFFSET ---
            offset_divs = offsets.get(canal, 0.0) if offsets else 0.0
            voltaje_canal_con_offset = voltaje_canal + offset_divs
            
            info_escalas['canales'][canal] = {
                'indice_canal': i,
                'tiempo_por_div': tiempo_por_div_canal,
                'tiempo_factor': factor_tiempo,
                'tiempo_simbolo': simbolo_tiempo,
                't_centro': t_centro,
                'voltaje_por_div': voltaje_por_div_canal,
                'voltaje_factor': factor_voltaje,
                'voltaje_simbolo': simbolo_voltaje,
                'v_centro': v_centro,
                'color': color,
                'offset_divs': offset_divs
            }
            
            ax.plot(tiempo_canal, voltaje_canal_con_offset, 
                   label=f"Canal {i+1}",
                   color=color, linewidth=2, alpha=0.9)
        
        # Dibujar cursores con etiquetas según canal anclado
        if cursor_info:
            pos = cursor_info['pos']
            canal_anclado = cursor_info.get('canal_anclado')
            
            # Líneas de cursores
            line_x1 = ax.axvline(pos['x1'], color='cyan', linestyle='--', linewidth=1.5, alpha=0.8)
            line_x2 = ax.axvline(pos['x2'], color='cyan', linestyle='--', linewidth=1.5, alpha=0.8)
            line_y1 = ax.axhline(pos['y1'], color='magenta', linestyle='--', linewidth=1.5, alpha=0.8)
            line_y2 = ax.axhline(pos['y2'], color='magenta', linestyle='--', linewidth=1.5, alpha=0.8)
            
            # Calcular valores según canal anclado
            if canal_anclado and canal_anclado in info_escalas['canales']:
                info_canal = info_escalas['canales'][canal_anclado]
                
                # Conversión X (tiempo) - SIN OFFSET, solo posición en cuadrícula × escala
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
                
                # Conversión Y (voltaje) - SIN OFFSET, solo posición en cuadrícula × escala
                v_div = info_canal['voltaje_por_div']
                v_centro_canal = info_canal['v_centro']
                v_factor = info_canal['voltaje_factor']
                v_simbolo = info_canal['voltaje_simbolo']
                # NO usar offset aquí - medir desde centro de cuadrícula (0)
                
                y1_real = (pos['y1'] * v_div) + v_centro_canal
                y2_real = (pos['y2'] * v_div) + v_centro_canal
                delta_y = abs(y2_real - y1_real)
                
                label_y1 = f"Y1: {y1_real/v_factor:.3f}{v_simbolo}V"
                label_y2 = f"Y2: {y2_real/v_factor:.3f}{v_simbolo}V"
                label_dy = f"ΔY: {delta_y/v_factor:.3f}{v_simbolo}V"
            else:
                # Sin canal válido, mostrar divisiones
                label_x1 = f"X1: {pos['x1']:.2f}div"
                label_x2 = f"X2: {pos['x2']:.2f}div"
                label_dx = f"ΔX: {abs(pos['x2']-pos['x1']):.2f}div"
                label_y1 = f"Y1: {pos['y1']:.2f}div"
                label_y2 = f"Y2: {pos['y2']:.2f}div"
                label_dy = f"ΔY: {abs(pos['y2']-pos['y1']):.2f}div"
            
            # Crear etiquetas de texto para X1, X2
            text_x1 = ax.text(pos['x1'], self.divisiones_y/2 - 0.3, label_x1, 
                   color='cyan', fontsize=9, fontweight='bold', ha='center',
                   bbox=dict(boxstyle='round,pad=0.3', facecolor='black', edgecolor='cyan', alpha=0.9))
            text_x2 = ax.text(pos['x2'], self.divisiones_y/2 - 0.3, label_x2, 
                   color='cyan', fontsize=9, fontweight='bold', ha='center',
                   bbox=dict(boxstyle='round,pad=0.3', facecolor='black', edgecolor='cyan', alpha=0.9))
            
            # Crear etiquetas de texto para Y1, Y2
            text_y1 = ax.text(0.3, pos['y1'], label_y1, 
                   color='magenta', fontsize=9, fontweight='bold', va='center',
                   bbox=dict(boxstyle='round,pad=0.3', facecolor='black', edgecolor='magenta', alpha=0.9))
            text_y2 = ax.text(0.3, pos['y2'], label_y2, 
                   color='magenta', fontsize=9, fontweight='bold', va='center',
                   bbox=dict(boxstyle='round,pad=0.3', facecolor='black', edgecolor='magenta', alpha=0.9))
            
            # Crear etiquetas de DELTA en esquina superior derecha
            text_dx = ax.text(self.divisiones_x - 0.3, self.divisiones_y/2 - 1.9, label_dx,
                   color='cyan', fontsize=10, fontweight='bold', ha='right',
                   bbox=dict(boxstyle='round,pad=0.4', facecolor='black', edgecolor='cyan', alpha=0.95, linewidth=2))
            text_dy = ax.text(self.divisiones_x - 0.3, self.divisiones_y/2 - 2.5, label_dy,
                   color='magenta', fontsize=10, fontweight='bold', ha='right',
                   bbox=dict(boxstyle='round,pad=0.4', facecolor='black', edgecolor='magenta', alpha=0.95, linewidth=2))
            
            # Guardar artistas
            info_escalas['cursor_artists'] = {
                'x1': line_x1, 'x2': line_x2, 'y1': line_y1, 'y2': line_y2
            }
            info_escalas['cursor_texts'] = {
                'text_x1': text_x1, 'text_x2': text_x2, 
                'text_y1': text_y1, 'text_y2': text_y2,
                'text_dx': text_dx, 'text_dy': text_dy
            }
        
        if len(canales_con_indices) > 1:
            ax.legend(loc='upper right', framealpha=0.7, 
                     facecolor='black', edgecolor='gray', 
                     labelcolor='white', fontsize=10)
        
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
        
        ax.set_title('Osciloscopio', fontsize=14, color='white')
        
        ax.set_xlabel('Tiempo', color='#FFD700', fontsize=10, ha='center')
        ax.set_ylabel('Tensión', color='#FFFFFF', fontsize=10, va='center')
        
        for spine in ax.spines.values():
            spine.set_edgecolor('#00FF00')
            spine.set_linewidth(1.5)
        
        ax.tick_params(colors='#00FF00', which='both')