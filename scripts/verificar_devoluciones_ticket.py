#!/usr/bin/env python3
"""
Script para verificar devoluciones de un ticket específico
"""

import sqlite3
import sys
import os

def verificar_devoluciones_ticket(numero_ticket):
    """Verificar devoluciones de un ticket específico"""
    
    # Conectar a la base de datos
    db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'almacen_desarrollo.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    print(f"🔍 Verificando devoluciones para ticket: {numero_ticket}")
    print("=" * 50)
    
    # Buscar devoluciones por número de ticket
    cursor.execute("""
        SELECT h.fecha, h.accion, h.detalles, h.usuario_nombre, p.nombre as producto_nombre,
               h.producto_id
        FROM historial h
        LEFT JOIN productos p ON h.producto_id = p.id
        WHERE h.accion IN ('devolucion_buen_estado', 'devolucion_mal_estado', 'devolucion')
        AND h.detalles LIKE ?
        ORDER BY h.fecha DESC
    """, (f"%{numero_ticket}%",))
    
    devoluciones = [dict(item) for item in cursor.fetchall()]
    print(f"📦 Devoluciones encontradas ({len(devoluciones)}):")
    
    if devoluciones:
        for dev in devoluciones:
            print(f"  📅 {dev['fecha']}")
            print(f"     Producto: {dev['producto_nombre']} (ID: {dev['producto_id']})")
            print(f"     Usuario: {dev['usuario_nombre']}")
            print(f"     Acción: {dev['accion']}")
            print(f"     Detalles: '{dev['detalles']}'")
            print()
    else:
        print("  ❌ No se encontraron devoluciones para este ticket")
    
    conn.close()
    print("=" * 50)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uso: python verificar_devoluciones_ticket.py <numero_ticket>")
        sys.exit(1)
    
    numero_ticket = sys.argv[1]
    verificar_devoluciones_ticket(numero_ticket) 