#!/usr/bin/env python3
"""
Script para verificar los detalles de un ticket y sus devoluciones
"""

import sqlite3
import sys
import os

# Agregar el directorio backend al path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

def verificar_ticket(ticket_id):
    """Verificar los datos de un ticket específico"""
    
    # Conectar a la base de datos
    db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'almacen_desarrollo.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    print(f"🔍 Verificando ticket ID: {ticket_id}")
    print("=" * 50)
    
    # 1. Obtener información del ticket
    cursor.execute("""
        SELECT id, numero_ticket, estado, fecha_solicitud, fecha_entrega
        FROM tickets_compra 
        WHERE id = ?
    """, (ticket_id,))
    
    ticket = cursor.fetchone()
    if not ticket:
        print(f"❌ Ticket {ticket_id} no encontrado")
        return
    
    ticket = dict(ticket)
    print(f"📋 Ticket: {ticket['numero_ticket']}")
    print(f"📊 Estado: {ticket['estado']}")
    print(f"📅 Fecha solicitud: {ticket['fecha_solicitud']}")
    print(f"📦 Fecha entrega: {ticket['fecha_entrega']}")
    print()
    
    # 2. Obtener items del ticket
    cursor.execute("""
        SELECT id, producto_id, producto_nombre, cantidad_solicitada, 
               cantidad_entregada, cantidad_devuelta
        FROM ticket_items 
        WHERE ticket_id = ?
    """, (ticket_id,))
    
    items = [dict(item) for item in cursor.fetchall()]
    print(f"🛠️ Items del ticket ({len(items)}):")
    for item in items:
        print(f"  - {item['producto_nombre']}")
        print(f"    Solicitado: {item['cantidad_solicitada']}")
        print(f"    Entregado: {item['cantidad_entregada']}")
        print(f"    Devuelto: {item['cantidad_devuelta']}")
        print()
    
    # 3. Verificar devoluciones en el historial
    print("📊 Devoluciones en historial:")
    cursor.execute("""
        SELECT h.fecha, h.accion, h.detalles, h.usuario_nombre, p.nombre as producto_nombre
        FROM historial h
        LEFT JOIN productos p ON h.producto_id = p.id
        WHERE h.accion IN ('devolucion_buen_estado', 'devolucion_mal_estado', 'devolucion')
        AND h.detalles LIKE ?
        ORDER BY h.fecha DESC
    """, (f"%{ticket['numero_ticket']}%",))
    
    devoluciones = [dict(item) for item in cursor.fetchall()]
    if devoluciones:
        for dev in devoluciones:
            print(f"  - {dev['fecha']}: {dev['accion']}")
            print(f"    Producto: {dev['producto_nombre']}")
            print(f"    Usuario: {dev['usuario_nombre']}")
            print(f"    Detalles: {dev['detalles']}")
            print()
    else:
        print("  ❌ No se encontraron devoluciones en el historial")
    
    # 4. Verificar estructura de la tabla ticket_items
    print("🔧 Estructura de tabla ticket_items:")
    cursor.execute("PRAGMA table_info(ticket_items)")
    columnas = cursor.fetchall()
    for col in columnas:
        print(f"  - {col['name']}: {col['type']}")
    
    conn.close()
    print("=" * 50)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uso: python verificar_ticket_detalles.py <ticket_id>")
        sys.exit(1)
    
    ticket_id = int(sys.argv[1])
    verificar_ticket(ticket_id) 