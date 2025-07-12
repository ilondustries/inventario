#!/usr/bin/env python3
"""
Script de diagnóstico para verificar el estado de las devoluciones
"""

import sqlite3
import os
import sys

def get_db_connection():
    """Obtener conexión a la base de datos"""
    try:
        db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'almacen.db')
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        print(f"❌ Error conectando a la base de datos: {e}")
        return None

def verificar_tickets_entregados():
    """Verificar tickets entregados que pueden ser devueltos"""
    conn = get_db_connection()
    if not conn:
        return
    
    try:
        cursor = conn.cursor()
        
        print("🔍 Verificando tickets entregados...")
        print("=" * 60)
        
        # Obtener tickets entregados
        cursor.execute("""
            SELECT 
                tc.id,
                tc.numero_ticket,
                tc.estado,
                tc.solicitante_nombre,
                tc.fecha_creacion,
                COUNT(ti.id) as total_items,
                SUM(ti.cantidad_solicitada) as total_solicitado,
                SUM(ti.cantidad_entregada) as total_entregado
            FROM tickets_compra tc
            LEFT JOIN ticket_items ti ON tc.id = ti.ticket_id
            WHERE tc.estado = 'entregado'
            GROUP BY tc.id
            ORDER BY tc.fecha_creacion DESC
        """)
        
        tickets = cursor.fetchall()
        
        if not tickets:
            print("❌ No hay tickets entregados para devolver")
            return
        
        print(f"✅ Encontrados {len(tickets)} tickets entregados:")
        print()
        
        for ticket in tickets:
            print(f"🎫 Ticket: {ticket['numero_ticket']}")
            print(f"   📊 Estado: {ticket['estado']}")
            print(f"   👤 Solicitante: {ticket['solicitante_nombre']}")
            print(f"   📅 Fecha: {ticket['fecha_creacion']}")
            print(f"   📦 Items: {ticket['total_items']}")
            print(f"   🔢 Total solicitado: {ticket['total_solicitado']}")
            print(f"   📤 Total entregado: {ticket['total_entregado']}")
            print()
            
            # Mostrar detalles de los items
            cursor.execute("""
                SELECT 
                    ti.id,
                    ti.producto_id,
                    ti.producto_nombre,
                    ti.cantidad_solicitada,
                    ti.cantidad_entregada,
                    p.cantidad as stock_actual
                FROM ticket_items ti
                JOIN productos p ON ti.producto_id = p.id
                WHERE ti.ticket_id = ?
            """, (ticket['id'],))
            
            items = cursor.fetchall()
            
            for item in items:
                print(f"      🛠️  {item['producto_nombre']}")
                print(f"         📋 Solicitado: {item['cantidad_solicitada']}")
                print(f"         📤 Entregado: {item['cantidad_entregada']}")
                print(f"         📦 Stock actual: {item['stock_actual']}")
                print()
            
            print("-" * 40)
        
    except Exception as e:
        print(f"❌ Error verificando tickets: {e}")
    finally:
        conn.close()

def simular_devolucion(ticket_id, producto_id, cantidad=1):
    """Simular una devolución para verificar el proceso"""
    conn = get_db_connection()
    if not conn:
        return
    
    try:
        cursor = conn.cursor()
        
        print(f"🔄 Simulando devolución...")
        print(f"   🎫 Ticket ID: {ticket_id}")
        print(f"   🛠️  Producto ID: {producto_id}")
        print(f"   📦 Cantidad: {cantidad}")
        print()
        
        # Obtener información del ticket
        cursor.execute("""
            SELECT id, numero_ticket, estado, solicitante_nombre
            FROM tickets_compra 
            WHERE id = ?
        """, (ticket_id,))
        
        ticket = cursor.fetchone()
        if not ticket:
            print("❌ Ticket no encontrado")
            return
        
        print(f"✅ Ticket encontrado: {ticket['numero_ticket']}")
        print(f"   📊 Estado: {ticket['estado']}")
        print(f"   👤 Solicitante: {ticket['solicitante_nombre']}")
        print()
        
        # Obtener información del item
        cursor.execute("""
            SELECT ti.id, ti.producto_id, ti.producto_nombre, ti.cantidad_solicitada, 
                   ti.cantidad_entregada, p.cantidad as stock_actual
            FROM ticket_items ti
            JOIN productos p ON ti.producto_id = p.id
            WHERE ti.ticket_id = ? AND ti.producto_id = ?
        """, (ticket_id, producto_id))
        
        item = cursor.fetchone()
        if not item:
            print("❌ Producto no encontrado en el ticket")
            return
        
        print(f"✅ Producto encontrado: {item['producto_nombre']}")
        print(f"   📋 Cantidad solicitada: {item['cantidad_solicitada']}")
        print(f"   📤 Cantidad entregada: {item['cantidad_entregada']}")
        print(f"   📦 Stock actual: {item['stock_actual']}")
        print()
        
        # Verificar que haya productos para devolver
        if item['cantidad_entregada'] <= 0:
            print("❌ No hay productos entregados para devolver")
            return
        
        if cantidad > item['cantidad_entregada']:
            print(f"❌ Solo se pueden devolver hasta {item['cantidad_entregada']} unidades")
            return
        
        # Simular la devolución
        nueva_cantidad_entregada = item['cantidad_entregada'] - cantidad
        nuevo_stock = item['stock_actual'] + cantidad
        
        print(f"🔄 Procesando devolución...")
        print(f"   📤 Nueva cantidad entregada: {nueva_cantidad_entregada}")
        print(f"   📦 Nuevo stock: {nuevo_stock}")
        print()
        
        # Actualizar cantidad entregada
        cursor.execute("""
            UPDATE ticket_items 
            SET cantidad_entregada = ?
            WHERE id = ?
        """, (nueva_cantidad_entregada, item['id']))
        
        # Actualizar stock
        cursor.execute("""
            UPDATE productos 
            SET cantidad = ?, fecha_actualizacion = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (nuevo_stock, producto_id))
        
        # Verificar si todos los items fueron devueltos
        cursor.execute("""
            SELECT 
                SUM(cantidad_solicitada) as total_solicitado,
                SUM(cantidad_entregada) as total_entregado
            FROM ticket_items 
            WHERE ticket_id = ?
        """, (ticket_id,))
        
        totales = dict(cursor.fetchone())
        
        nuevo_estado = "devuelto" if totales["total_entregado"] == 0 else "entregado"
        
        if nuevo_estado == "devuelto":
            cursor.execute("""
                UPDATE tickets_compra 
                SET estado = ?
                WHERE id = ?
            """, (nuevo_estado, ticket_id))
        
        conn.commit()
        
        print(f"✅ Devolución procesada exitosamente")
        print(f"   📊 Nuevo estado del ticket: {nuevo_estado}")
        print(f"   📤 Cantidad restante: {nueva_cantidad_entregada}")
        print(f"   📦 Stock actualizado: {nuevo_stock}")
        
    except Exception as e:
        print(f"❌ Error simulando devolución: {e}")
        conn.rollback()
    finally:
        conn.close()

def main():
    print("🔧 DIAGNÓSTICO DE DEVOLUCIONES")
    print("=" * 60)
    
    # Verificar tickets entregados
    verificar_tickets_entregados()
    
    print()
    print("🔄 Para simular una devolución, ejecuta:")
    print("   python scripts/diagnostico_devolucion.py <ticket_id> <producto_id> [cantidad]")
    print()
    
    # Si se proporcionan argumentos, simular devolución
    if len(sys.argv) >= 3:
        try:
            ticket_id = int(sys.argv[1])
            producto_id = int(sys.argv[2])
            cantidad = int(sys.argv[3]) if len(sys.argv) > 3 else 1
            
            print("🔄 Simulando devolución...")
            simular_devolucion(ticket_id, producto_id, cantidad)
            
        except ValueError:
            print("❌ Error: Los IDs deben ser números enteros")
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    main() 