#!/usr/bin/env python3
"""
Script para verificar todo el historial relacionado con un ticket
"""

import sqlite3
import sys
import os

def verificar_historial_ticket(ticket_id):
    """Verificar todo el historial relacionado con un ticket"""
    
    # Conectar a la base de datos
    db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'almacen_desarrollo.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    print(f"🔍 Verificando historial para ticket ID: {ticket_id}")
    print("=" * 50)
    
    # Obtener número de ticket
    cursor.execute("SELECT numero_ticket FROM tickets_compra WHERE id = ?", (ticket_id,))
    ticket = cursor.fetchone()
    if not ticket:
        print(f"❌ Ticket {ticket_id} no encontrado")
        return
    
    numero_ticket = ticket['numero_ticket']
    print(f"📋 Ticket: {numero_ticket}")
    print()
    
    # Verificar todo el historial relacionado con este ticket
    cursor.execute("""
        SELECT h.fecha, h.accion, h.detalles, h.usuario_nombre, p.nombre as producto_nombre,
               h.cantidad_anterior, h.cantidad_nueva
        FROM historial h
        LEFT JOIN productos p ON h.producto_id = p.id
        WHERE h.detalles LIKE ?
        ORDER BY h.fecha DESC
    """, (f"%Ticket {numero_ticket}%",))
    
    historial = [dict(item) for item in cursor.fetchall()]
    print(f"📊 Historial encontrado ({len(historial)} registros):")
    
    if historial:
        for item in historial:
            print(f"  📅 {item['fecha']}")
            print(f"     Acción: {item['accion']}")
            print(f"     Usuario: {item['usuario_nombre']}")
            print(f"     Producto: {item['producto_nombre']}")
            print(f"     Cantidad: {item['cantidad_anterior']} → {item['cantidad_nueva']}")
            print(f"     Detalles: {item['detalles']}")
            print()
    else:
        print("  ❌ No se encontró historial para este ticket")
    
    # Verificar también por número de ticket sin el prefijo "Ticket"
    cursor.execute("""
        SELECT h.fecha, h.accion, h.detalles, h.usuario_nombre, p.nombre as producto_nombre,
               h.cantidad_anterior, h.cantidad_nueva
        FROM historial h
        LEFT JOIN productos p ON h.producto_id = p.id
        WHERE h.detalles LIKE ?
        ORDER BY h.fecha DESC
    """, (f"%{numero_ticket}%",))
    
    historial_alt = [dict(item) for item in cursor.fetchall()]
    if historial_alt and not historial:
        print(f"📊 Historial alternativo encontrado ({len(historial_alt)} registros):")
        for item in historial_alt:
            print(f"  📅 {item['fecha']}")
            print(f"     Acción: {item['accion']}")
            print(f"     Usuario: {item['usuario_nombre']}")
            print(f"     Producto: {item['producto_nombre']}")
            print(f"     Cantidad: {item['cantidad_anterior']} → {item['cantidad_nueva']}")
            print(f"     Detalles: {item['detalles']}")
            print()
    
    conn.close()
    print("=" * 50)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uso: python verificar_historial_ticket.py <ticket_id>")
        sys.exit(1)
    
    ticket_id = int(sys.argv[1])
    verificar_historial_ticket(ticket_id) 