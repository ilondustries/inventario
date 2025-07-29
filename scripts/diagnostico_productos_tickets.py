#!/usr/bin/env python3
"""
Script para diagnosticar productos faltantes en tickets
"""

import sqlite3
import os

def diagnosticar_productos_tickets():
    """Diagnosticar productos faltantes en tickets"""
    
    db_path = "data/almacen_main.db"
    
    if not os.path.exists(db_path):
        print(f"❌ Error: No se encontró la base de datos {db_path}")
        return
    
    try:
        print(f"🔧 Conectando a {db_path}...")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Verificar productos existentes
        print("📋 Productos existentes en inventario:")
        cursor.execute("SELECT id, nombre FROM productos ORDER BY id")
        productos = cursor.fetchall()
        productos_ids = [p[0] for p in productos]
        print(f"  Total productos: {len(productos)}")
        for p in productos:
            print(f"  ID: {p[0]}, Nombre: {p[1]}")
        
        # Verificar ticket_items con productos faltantes
        print("\n🔍 Verificando ticket_items con productos faltantes...")
        cursor.execute("""
            SELECT DISTINCT ti.producto_id, ti.producto_nombre, COUNT(*) as cantidad_tickets
            FROM ticket_items ti
            LEFT JOIN productos p ON ti.producto_id = p.id
            WHERE p.id IS NULL
            GROUP BY ti.producto_id, ti.producto_nombre
        """)
        
        productos_faltantes = cursor.fetchall()
        
        if productos_faltantes:
            print("❌ Productos faltantes encontrados:")
            for pf in productos_faltantes:
                print(f"  ID: {pf[0]}, Nombre: '{pf[1]}', Referenciado en {pf[2]} tickets")
        else:
            print("✅ No se encontraron productos faltantes")
        
        # Verificar tickets afectados
        if productos_faltantes:
            print("\n📋 Tickets afectados:")
            for pf in productos_faltantes:
                cursor.execute("""
                    SELECT DISTINCT t.id, t.numero_ticket, t.estado, t.solicitante_nombre
                    FROM tickets_compra t
                    JOIN ticket_items ti ON t.id = ti.ticket_id
                    WHERE ti.producto_id = ?
                """, (pf[0],))
                
                tickets_afectados = cursor.fetchall()
                print(f"\n  Producto '{pf[1]}' (ID: {pf[0]}) aparece en:")
                for ticket in tickets_afectados:
                    print(f"    - Ticket {ticket[1]} (ID: {ticket[0]}) - Estado: {ticket[2]} - Solicitante: {ticket[3]}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    diagnosticar_productos_tickets() 