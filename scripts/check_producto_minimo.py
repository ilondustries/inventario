#!/usr/bin/env python3
import sqlite3
import os

def check_producto_minimo():
    """Verificar el estado de 'Producto Mínimo' en la base de datos"""
    try:
        # Conectar a la base de datos
        db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'almacen.db')
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        print("🔍 Verificando 'Producto Mínimo' en la base de datos...")
        
        # Buscar el producto
        cursor.execute("""
            SELECT id, nombre, cantidad, cantidad_minima, ubicacion, categoria
            FROM productos 
            WHERE nombre LIKE '%Mínimo%' OR nombre LIKE '%Minimo%'
        """)
        
        productos = cursor.fetchall()
        
        if not productos:
            print("❌ No se encontró 'Producto Mínimo' en la base de datos")
            
            # Mostrar todos los productos para referencia
            cursor.execute("SELECT id, nombre, cantidad FROM productos ORDER BY nombre")
            todos = cursor.fetchall()
            print(f"\n📋 Productos disponibles ({len(todos)}):")
            for p in todos:
                print(f"  - ID {p['id']}: {p['nombre']} (Stock: {p['cantidad']})")
        else:
            print(f"✅ Encontrados {len(productos)} productos:")
            for p in productos:
                print(f"  - ID {p['id']}: {p['nombre']}")
                print(f"    Stock actual: {p['cantidad']}")
                print(f"    Stock mínimo: {p['cantidad_minima']}")
                print(f"    Ubicación: {p['ubicacion']}")
                print(f"    Categoría: {p['categoria']}")
                
                # Verificar tickets que usan este producto
                cursor.execute("""
                    SELECT ti.ticket_id, ti.cantidad_solicitada, ti.cantidad_entregada,
                           t.numero_ticket, t.estado, t.solicitante_nombre
                    FROM ticket_items ti
                    JOIN tickets_compra t ON ti.ticket_id = t.id
                    WHERE ti.producto_id = ?
                    ORDER BY t.fecha_solicitud DESC
                """, (p['id'],))
                
                tickets = cursor.fetchall()
                if tickets:
                    print(f"    📋 Tickets que usan este producto ({len(tickets)}):")
                    for t in tickets:
                        print(f"      - Ticket {t['numero_ticket']} ({t['estado']}): {t['cantidad_solicitada']} solicitados, {t['cantidad_entregada']} entregados")
                else:
                    print("    📋 No hay tickets que usen este producto")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_producto_minimo() 