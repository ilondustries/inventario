#!/usr/bin/env python3
"""
Script para verificar los detalles exactos de las devoluciones
"""

import sqlite3
import os

def verificar_devoluciones_detalle():
    """Verificar los detalles exactos de las devoluciones"""
    
    # Conectar a la base de datos
    db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'almacen_desarrollo.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    print("🔍 Verificando detalles de devoluciones...")
    print("=" * 50)
    
    # Obtener todas las devoluciones con sus detalles
    cursor.execute("""
        SELECT h.fecha, h.accion, h.detalles, h.usuario_nombre, p.nombre as producto_nombre,
               h.producto_id
        FROM historial h
        LEFT JOIN productos p ON h.producto_id = p.id
        WHERE h.accion = 'devolucion'
        ORDER BY h.fecha DESC
        LIMIT 10
    """)
    
    devoluciones = [dict(item) for item in cursor.fetchall()]
    print(f"📦 Devoluciones encontradas ({len(devoluciones)}):")
    
    for dev in devoluciones:
        print(f"  📅 {dev['fecha']}")
        print(f"     Producto: {dev['producto_nombre']} (ID: {dev['producto_id']})")
        print(f"     Usuario: {dev['usuario_nombre']}")
        print(f"     Detalles: '{dev['detalles']}'")
        print()
    
    conn.close()
    print("=" * 50)

if __name__ == "__main__":
    verificar_devoluciones_detalle() 