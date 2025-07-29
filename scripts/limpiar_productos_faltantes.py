#!/usr/bin/env python3
"""
Script para limpiar ticket_items con productos faltantes
"""

import sqlite3
import os
import sys

def limpiar_productos_faltantes():
    """Limpiar ticket_items con productos faltantes"""
    
    db_path = "data/almacen_main.db"
    
    if not os.path.exists(db_path):
        print(f"❌ Error: No se encontró la base de datos {db_path}")
        return False
    
    try:
        print(f"🔧 Conectando a {db_path}...")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Obtener productos existentes
        cursor.execute("SELECT id FROM productos")
        productos_existentes = [p[0] for p in cursor.fetchall()]
        print(f"✅ Productos existentes: {productos_existentes}")
        
        # Encontrar ticket_items con productos faltantes
        print("🔍 Buscando ticket_items con productos faltantes...")
        cursor.execute("""
            SELECT ti.id, ti.ticket_id, ti.producto_id, ti.producto_nombre
            FROM ticket_items ti
            LEFT JOIN productos p ON ti.producto_id = p.id
            WHERE p.id IS NULL
        """)
        
        items_faltantes = cursor.fetchall()
        
        if not items_faltantes:
            print("✅ No se encontraron items con productos faltantes")
            return True
        
        print(f"❌ Encontrados {len(items_faltantes)} items con productos faltantes:")
        for item in items_faltantes:
            print(f"  - Item ID: {item[0]}, Ticket: {item[1]}, Producto ID: {item[2]}, Nombre: '{item[3]}'")
        
        # Confirmar eliminación
        print(f"\n🗑️ ¿Eliminar {len(items_faltantes)} items con productos faltantes?")
        confirmacion = input("Escribe 'SI' para confirmar: ")
        
        if confirmacion != "SI":
            print("❌ Operación cancelada")
            return False
        
        # Eliminar items con productos faltantes
        print("🗑️ Eliminando items con productos faltantes...")
        cursor.execute("""
            DELETE FROM ticket_items 
            WHERE id IN (
                SELECT ti.id
                FROM ticket_items ti
                LEFT JOIN productos p ON ti.producto_id = p.id
                WHERE p.id IS NULL
            )
        """)
        
        items_eliminados = cursor.rowcount
        print(f"✅ Eliminados {items_eliminados} items")
        
        # Verificar tickets vacíos y eliminarlos
        print("🔍 Verificando tickets vacíos...")
        cursor.execute("""
            SELECT t.id, t.numero_ticket
            FROM tickets_compra t
            LEFT JOIN ticket_items ti ON t.id = ti.ticket_id
            WHERE ti.ticket_id IS NULL
        """)
        
        tickets_vacios = cursor.fetchall()
        
        if tickets_vacios:
            print(f"❌ Encontrados {len(tickets_vacios)} tickets vacíos:")
            for ticket in tickets_vacios:
                print(f"  - Ticket {ticket[1]} (ID: {ticket[0]})")
            
            print("🗑️ ¿Eliminar tickets vacíos?")
            confirmacion = input("Escribe 'SI' para confirmar: ")
            
            if confirmacion == "SI":
                cursor.execute("""
                    DELETE FROM tickets_compra 
                    WHERE id IN (
                        SELECT t.id
                        FROM tickets_compra t
                        LEFT JOIN ticket_items ti ON t.id = ti.ticket_id
                        WHERE ti.ticket_id IS NULL
                    )
                """)
                tickets_eliminados = cursor.rowcount
                print(f"✅ Eliminados {tickets_eliminados} tickets vacíos")
        
        # Guardar cambios
        conn.commit()
        conn.close()
        
        print("🎉 ¡Limpieza completada exitosamente!")
        print("✅ Base de datos main limpiada de productos faltantes")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("🧹 Limpiando productos faltantes en base de datos main...")
    success = limpiar_productos_faltantes()
    
    if success:
        print("✅ Script completado exitosamente")
    else:
        print("❌ Script falló")
        sys.exit(1) 