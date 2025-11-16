"""
data_handler.py - Manejo y procesamiento de archivos CSV
Se encarga de leer, procesar y validar los datos del osciloscopio
"""

import pandas as pd
import numpy as np

class DataHandler:
    """
    Clase que maneja la carga y procesamiento de archivos CSV
    """
    
    def __init__(self):
        """
        Inicializa el manejador de datos
        """
        self.df = None  # DataFrame donde se guardarán los datos
        self.archivo_actual = None
    
    def cargar_csv(self, ruta_archivo):
        """
        Carga un archivo CSV del osciloscopio
        
        Args:
            ruta_archivo (str): Ruta completa del archivo CSV
            
        Returns:
            DataFrame: Datos procesados
            
        Raises:
            Exception: Si hay problemas al cargar el archivo
        """
        self.archivo_actual = ruta_archivo
        
        # Intentar detectar el formato automáticamente
        skiprows = self.detectar_lineas_encabezado(ruta_archivo)
        
        try:
            # Leer el CSV con pandas
            # skiprows: salta las primeras líneas que no son datos
            # header=0: usa la primera línea (después de skip) como nombres de columnas
            self.df = pd.read_csv(
                ruta_archivo,
                skiprows=skiprows,
                header=0,
                delimiter=',',
                engine='python'  # Motor más flexible
            )
            
            # Limpiar nombres de columnas (quitar espacios)
            self.df.columns = self.df.columns.str.strip()
            
            # Convertir todas las columnas a numérico
            self.df = self.convertir_a_numerico(self.df)
            
            # Validar los datos
            self.validar_datos()
            
            return self.df
            
        except Exception as e:
            raise Exception(f"Error al cargar el archivo: {str(e)}")
    
    def detectar_lineas_encabezado(self, ruta_archivo):
        """
        Detecta automáticamente cuántas líneas de encabezado tiene el archivo
        
        Args:
            ruta_archivo (str): Ruta del archivo
            
        Returns:
            int: Número de líneas a saltar
        """
        with open(ruta_archivo, 'r') as f:
            for i, linea in enumerate(f):
                # Limpiar la línea
                linea = linea.strip()
                
                # Saltar líneas vacías
                if not linea:
                    continue
                
                # Intentar detectar si es una línea de datos
                # Los datos empiezan con un número (positivo o negativo) o notación científica
                primera_parte = linea.split(',')[0].strip()
                
                try:
                    # Si podemos convertir a float, probablemente sea datos
                    float(primera_parte)
                    # La línea anterior debe ser el header, así que retornamos i-1
                    return max(0, i - 1)
                except ValueError:
                    # No es un número, continuar buscando
                    continue
        
        # Por defecto, asumir que hay 1 línea de encabezado
        return 1
    
    def convertir_a_numerico(self, df):
        """
        Convierte todas las columnas a valores numéricos
        
        Args:
            df (DataFrame): DataFrame a convertir
            
        Returns:
            DataFrame: DataFrame con valores numéricos
        """
        for col in df.columns:
            # Convertir a numérico, valores inválidos se vuelven NaN
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        return df
    
    def validar_datos(self):
        """
        Valida que los datos cargados sean correctos
        
        Raises:
            Exception: Si los datos no son válidos
        """
        if self.df is None:
            raise Exception("No hay datos cargados")
        
        # Verificar que haya al menos 2 columnas (tiempo + 1 canal)
        if len(self.df.columns) < 2:
            raise Exception("El archivo debe tener al menos 2 columnas (tiempo y 1 canal)")
        
        # Verificar que haya datos
        if len(self.df) == 0:
            raise Exception("El archivo no contiene datos")
        
        # Verificar que no haya demasiados valores NaN
        porcentaje_nan = (self.df.isna().sum().sum() / (len(self.df) * len(self.df.columns))) * 100
        
        if porcentaje_nan > 50:
            raise Exception(f"El archivo tiene demasiados valores inválidos ({porcentaje_nan:.1f}%)")
    
    def obtener_estadisticas(self, columna):
        """
        Calcula estadísticas básicas de una columna
        
        Args:
            columna (str): Nombre de la columna
            
        Returns:
            dict: Diccionario con estadísticas
        """
        if self.df is None or columna not in self.df.columns:
            return None
        
        datos = self.df[columna].dropna()  # Eliminar NaN
        
        estadisticas = {
            'minimo': datos.min(),
            'maximo': datos.max(),
            'promedio': datos.mean(),
            'std': datos.std(),
            'mediana': datos.median(),
            'vpp': datos.max() - datos.min()  # Voltaje pico a pico
        }
        
        return estadisticas
    
    def exportar_datos_filtrados(self, columnas, ruta_salida):
        """
        Exporta datos seleccionados a un nuevo CSV
        
        Args:
            columnas (list): Lista de columnas a exportar
            ruta_salida (str): Ruta donde guardar el archivo
        """
        if self.df is None:
            raise Exception("No hay datos para exportar")
        
        # Siempre incluir la primera columna (tiempo)
        if self.df.columns[0] not in columnas:
            columnas = [self.df.columns[0]] + columnas
        
        # Exportar
        self.df[columnas].to_csv(ruta_salida, index=False)