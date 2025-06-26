#!/usr/bin/env python3
"""
Script para generar códigos de barras para productos existentes que no los tengan
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

import sqlite3
import barcode
from barcode.writer import ImageWriter
import base64
from io import BytesIO
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def generar_codigo_barras(producto_id: int, nombre: str, codigo_barras: str = None) -> str:
    """Generar código de barras imprimible para un producto y devolverlo como base64"""
    try:
        # Usar el código de barras existente o generar uno basado en el ID
        if codigo_barras and codigo_barras.strip():
            codigo = codigo_barras
        else:
            # Generar código de barras basado en ID (formato: 123456789012)
            codigo = f"{producto_id:012d}"
        
        # Crear código de barras Code128 (más común y legible)
        codigo_barras_obj = barcode.get('code128', codigo, writer=ImageWriter())
        
        # Configurar opciones de imagen
        options = {
            'text_distance': 1.0,
            'font_size': 12,
            'module_height': 15.0,
            'module_width': 0.2,
            'quiet_zone': 6.0,
            'background': 'white',
            'foreground': 'black'
        }
        
        # Generar imagen
        buffer = BytesIO()
        codigo_barras_obj.write(buffer, options)
        buffer.seek(0)
        
        # Convertir a base64
        img_str = base64.b64encode(buffer.getvalue()).decode()
        
        return f"data:image/png;base64,{img_str}"
    except Exception as e:
        logger.error(f"Error generando código de barras para producto {producto_id}: {e}")
        return None

def get_db_connection():
    """Obtener conexión a la base de datos"""
    try:
        conn = sqlite3.connect("data/almacen.db", timeout=60.0)
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        logger.error(f"Error conectando a la base de datos: {e}")
        raise

def main():
    """Función principal"""
    try:
        logger.info("Iniciando generación de códigos de barras para productos existentes...")
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Obtener productos que no tienen código de barras
        cursor.execute("""
            SELECT id, nombre, codigo_barras
            FROM productos 
            WHERE codigo_barras IS NULL OR codigo_barras = ''
        """)
        
        productos_sin_barcode = cursor.fetchall()
        
        if not productos_sin_barcode:
            logger.info("Todos los productos ya tienen códigos de barras asignados.")
            return
        
        logger.info(f"Encontrados {len(productos_sin_barcode)} productos sin código de barras.")
        
        # Generar códigos de barras para cada producto
        for producto in productos_sin_barcode:
            producto_id = producto['id']
            nombre = producto['nombre']
            codigo_barras_existente = producto['codigo_barras']
            
            # Generar código de barras automáticamente
            nuevo_codigo_barras = f"{producto_id:012d}"
            
            # Actualizar en la base de datos
            cursor.execute("""
                UPDATE productos SET codigo_barras = ? WHERE id = ?
            """, (nuevo_codigo_barras, producto_id))
            
            logger.info(f"Producto '{nombre}' (ID: {producto_id}) - Código de barras asignado: {nuevo_codigo_barras}")
        
        # Confirmar cambios
        conn.commit()
        conn.close()
        
        logger.info("✅ Generación de códigos de barras completada exitosamente.")
        
    except Exception as e:
        logger.error(f"Error en la generación de códigos de barras: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 