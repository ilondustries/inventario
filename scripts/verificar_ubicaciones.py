#!/usr/bin/env python3
"""
Script para verificar las ubicaciones actuales de todos los productos
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

import sqlite3
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
        logger.info("Verificando ubicaciones actuales de productos...")
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Obtener todos los productos con sus ubicaciones
        cursor.execute("""
            SELECT id, nombre, ubicacion, codigo_barras
            FROM productos 
            ORDER BY id
        """)
        
        productos = cursor.fetchall()
        
        if not productos:
            logger.info("No hay productos en la base de datos.")
            return
        
        logger.info(f"Total de productos: {len(productos)}")
        logger.info("=" * 60)
        logger.info("ID | Nombre | Ubicación | Código de Barras")
        logger.info("=" * 60)
        
        for producto in productos:
            logger.info(f"{producto['id']:2d} | {producto['nombre']:15s} | {producto['ubicacion']:8s} | {producto['codigo_barras']}")
        
        conn.close()
        
        logger.info("=" * 60)
        logger.info("✅ Verificación completada.")
        
    except Exception as e:
        logger.error(f"Error en la verificación: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 