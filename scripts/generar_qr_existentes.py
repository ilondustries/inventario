#!/usr/bin/env python3
"""
Script para generar códigos QR para productos existentes que no los tengan
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

import sqlite3
import qrcode
import base64
from io import BytesIO
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def generar_codigo_qr(producto_id: int, nombre: str, codigo_barras: str = None) -> str:
    """Generar código QR para un producto y devolverlo como base64"""
    try:
        # Crear contenido del QR con información del producto
        contenido = f"ID:{producto_id}|Nombre:{nombre}"
        if codigo_barras:
            contenido += f"|Codigo:{codigo_barras}"
        
        # Generar QR
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(contenido)
        qr.make(fit=True)
        
        # Crear imagen
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convertir a base64
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        img_str = base64.b64encode(buffer.getvalue()).decode()
        
        return img_str
    except Exception as e:
        logger.error(f"Error generando código QR: {e}")
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

def generar_qr_existentes():
    """Generar códigos QR para productos existentes que no los tengan"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Obtener productos sin código QR
        cursor.execute("""
            SELECT id, nombre, codigo_barras
            FROM productos 
            WHERE codigo_qr IS NULL OR codigo_qr = ''
        """)
        productos_sin_qr = cursor.fetchall()
        
        if not productos_sin_qr:
            logger.info("✅ Todos los productos ya tienen códigos QR")
            return
        
        logger.info(f"📱 Generando códigos QR para {len(productos_sin_qr)} productos...")
        
        productos_generados = 0
        for producto in productos_sin_qr:
            try:
                codigo_qr = generar_codigo_qr(
                    producto["id"], 
                    producto["nombre"], 
                    producto["codigo_barras"]
                )
                
                if codigo_qr:
                    cursor.execute("""
                        UPDATE productos SET codigo_qr = ? WHERE id = ?
                    """, (codigo_qr, producto["id"]))
                    productos_generados += 1
                    logger.info(f"✅ QR generado para: {producto['nombre']} (ID: {producto['id']})")
                else:
                    logger.error(f"❌ Error generando QR para: {producto['nombre']} (ID: {producto['id']})")
                    
            except Exception as e:
                logger.error(f"❌ Error procesando producto {producto['id']}: {e}")
        
        conn.commit()
        conn.close()
        
        logger.info(f"🎉 Proceso completado: {productos_generados}/{len(productos_sin_qr)} códigos QR generados")
        
    except Exception as e:
        logger.error(f"❌ Error en el proceso: {e}")
        raise

if __name__ == "__main__":
    print("🚀 Generando códigos QR para productos existentes...")
    print("=" * 50)
    
    try:
        generar_qr_existentes()
        print("\n✅ Proceso completado exitosamente")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1) 