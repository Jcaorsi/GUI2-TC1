"""
main.py - Punto de entrada de la aplicación
Este archivo inicia la interfaz gráfica del visor de osciloscopio
"""

# Importamos las librerías necesarias
import tkinter as tk
from gui import OsciloscopioGUI

def main():
    """
    Función principal que inicia la aplicación
    """
    # Crear la ventana principal de tkinter
    root = tk.Tk()
    
    # Crear la interfaz gráfica
    app = OsciloscopioGUI(root)
    
    # Iniciar el loop de la aplicación (mantiene la ventana abierta)
    root.mainloop()

# Esto asegura que main() solo se ejecute si corremos este archivo directamente
if __name__ == "__main__":
    main()