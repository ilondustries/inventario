#!/usr/bin/env python3
"""
Script simple para verificar productos y tickets
"""

import sqlite3
import os

def verificar_productos_simple():
    """Verificar productos y tickets de forma simple"""
    
    db_path = "data/almacen_main.db"
    
    try:
        print(f"🔧 Conectando a {db_path}...")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Verificar productos existentes
        print("📋 Productos existentes:")
        cursor.execute("SELECT id, nombre FROM productos")
        productos = cursor.fetchall()
        print(f"Total: {len(productos)} productos")
        for p in productos:
            print(f"  ID: {p[0]}, Nombre: {p[1]}")
        
        # Verificar tickets
        print("\n📋 Tickets existentes:")
        cursor.execute("SELECT id, numero_ticket, estado FROM tickets_compra")
        tickets = cursor.fetchall()
        print(f"Total: {len(tickets)} tickets")
        for t in tickets:
            print(f"  ID: {t[0]}, Ticket: {t[1]}, Estado: {t[2]}")
        
        # Verificar ticket_items
        print("\n📋 Items en tickets:")
        cursor.execute("SELECT ticket_id, producto_id, producto_nombre FROM ticket_items")
        items = cursor.fetchall()
        print(f"Total: {len(items)} items")
        for item in items:
            print(f"  Ticket: {item[0]}, Producto ID: {item[1]}, Nombre: {item[2]}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    verificar_productos_simple() 