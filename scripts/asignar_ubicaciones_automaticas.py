#!/usr/bin/env python3
"""
Script para asignar ubicaciones automáticas a productos existentes que no las tengan
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

import sqlite3
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def generar_ubicacion_automatica(producto_id: int) -> str:
    """Generar ubicación automática para un producto basada en su ID"""
    try:
        # Sistema de ubicaciones: A01, A02, A03... B01, B02, B03... etc.
        # Cada 10 productos cambia de letra (A01-A10, B01-B10, C01-C10...)
        letra = chr(65 + ((producto_id - 1) // 10))  # A=65, B=66, C=67...
        numero = ((producto_id - 1) % 10) + 1
        
        ubicacion = f"{letra}{numero:02d}"
        return ubicacion
    except Exception as e:
        logger.error(f"Error generando ubicación para producto {producto_id}: {e}")
        return "A01"  # Ubicación por defecto

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
        logger.info("Iniciando asignación de ubicaciones automáticas...")
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Obtener productos que no tienen ubicación
        cursor.execute("""
            SELECT id, nombre, ubicacion
            FROM productos 
            WHERE ubicacion IS NULL OR ubicacion = '' OR ubicacion = 'N/A'
        """)
        
        productos_sin_ubicacion = cursor.fetchall()
        
        if not productos_sin_ubicacion:
            logger.info("Todos los productos ya tienen ubicaciones asignadas.")
            return
        
        logger.info(f"Encontrados {len(productos_sin_ubicacion)} productos sin ubicación.")
        
        # Asignar ubicaciones automáticas para cada producto
        for producto in productos_sin_ubicacion:
            producto_id = producto['id']
            nombre = producto['nombre']
            
            # Generar ubicación automática
            nueva_ubicacion = generar_ubicacion_automatica(producto_id)
            
            # Actualizar en la base de datos
            cursor.execute("""
                UPDATE productos SET ubicacion = ? WHERE id = ?
            """, (nueva_ubicacion, producto_id))
            
            logger.info(f"Producto '{nombre}' (ID: {producto_id}) - Ubicación asignada: {nueva_ubicacion}")
        
        # Confirmar cambios
        conn.commit()
        conn.close()
        
        logger.info("✅ Asignación de ubicaciones completada exitosamente.")
        
    except Exception as e:
        logger.error(f"Error en la asignación de ubicaciones: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 