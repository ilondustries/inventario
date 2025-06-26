#!/usr/bin/env python3
"""
Script para estandarizar todas las ubicaciones al formato automático
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
        logger.info("Iniciando estandarización de ubicaciones...")
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Obtener todos los productos
        cursor.execute("""
            SELECT id, nombre, ubicacion
            FROM productos 
            ORDER BY id
        """)
        
        productos = cursor.fetchall()
        
        if not productos:
            logger.info("No hay productos en la base de datos.")
            return
        
        logger.info(f"Total de productos a procesar: {len(productos)}")
        logger.info("=" * 70)
        logger.info("ID | Nombre | Ubicación Anterior | Nueva Ubicación")
        logger.info("=" * 70)
        
        cambios_realizados = 0
        
        # Asignar ubicaciones automáticas para cada producto
        for producto in productos:
            producto_id = producto['id']
            nombre = producto['nombre']
            ubicacion_anterior = producto['ubicacion'] or 'None'
            
            # Generar ubicación automática
            nueva_ubicacion = generar_ubicacion_automatica(producto_id)
            
            # Actualizar en la base de datos
            cursor.execute("""
                UPDATE productos SET ubicacion = ? WHERE id = ?
            """, (nueva_ubicacion, producto_id))
            
            logger.info(f"{producto_id:2d} | {nombre:15s} | {ubicacion_anterior:16s} | {nueva_ubicacion}")
            
            if ubicacion_anterior != nueva_ubicacion:
                cambios_realizados += 1
        
        # Confirmar cambios
        conn.commit()
        conn.close()
        
        logger.info("=" * 70)
        logger.info(f"✅ Estandarización completada. {cambios_realizados} ubicaciones actualizadas.")
        
    except Exception as e:
        logger.error(f"Error en la estandarización: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 