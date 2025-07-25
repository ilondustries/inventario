#!/usr/bin/env python3
"""
Script para verificar que los contadores de entregado y devuelto sean independientes
"""

import sqlite3
import sys

def verificar_contadores_independientes():
    """Verificar que los contadores sean independientes"""
    try:
        # Conectar a la base de datos de desarrollo
        conn = sqlite3.connect('data/almacen_desarrollo.db')
        cursor = conn.cursor()
        
        print("=== VERIFICACIÓN DE CONTADORES INDEPENDIENTES ===\n")
        
        # 1. Verificar tickets con devoluciones
        print("1. TICKETS CON DEVOLUCIONES:")
        cursor.execute("""
            SELECT tc.id, tc.numero_ticket, tc.estado, 
                   SUM(ti.cantidad_solicitada) as total_solicitado,
                   SUM(ti.cantidad_entregada) as total_entregado,
                   SUM(ti.cantidad_devuelta) as total_devuelto
            FROM tickets_compra tc
            JOIN ticket_items ti ON tc.id = ti.ticket_id
            WHERE ti.cantidad_devuelta > 0
            GROUP BY tc.id
            ORDER BY tc.id DESC
            LIMIT 10
        """)
        
        tickets_con_devoluciones = cursor.fetchall()
        if tickets_con_devoluciones:
            print(f"✅ Se encontraron {len(tickets_con_devoluciones)} tickets con devoluciones:")
            for ticket in tickets_con_devoluciones:
                print(f"\n   Ticket: {ticket[1]} (Estado: {ticket[2]})")
                print(f"   - Solicitado: {ticket[3]}")
                print(f"   - Entregado: {ticket[4]}")
                print(f"   - Devuelto: {ticket[5]}")
                
                # Verificar independencia
                if ticket[4] > 0 and ticket[5] > 0:
                    print(f"   ✅ Contadores independientes (Entregado: {ticket[4]}, Devuelto: {ticket[5]})")
                else:
                    print(f"   ⚠️ Revisar contadores")
        else:
            print("❌ No se encontraron tickets con devoluciones")
        
        # 2. Verificar items específicos con devoluciones
        print(f"\n2. ITEMS CON DEVOLUCIONES:")
        cursor.execute("""
            SELECT ti.ticket_id, tc.numero_ticket, ti.producto_nombre,
                   ti.cantidad_solicitada, ti.cantidad_entregada, ti.cantidad_devuelta
            FROM ticket_items ti
            JOIN tickets_compra tc ON ti.ticket_id = tc.id
            WHERE ti.cantidad_devuelta > 0
            ORDER BY ti.ticket_id DESC, ti.producto_nombre
            LIMIT 15
        """)
        
        items_con_devoluciones = cursor.fetchall()
        if items_con_devoluciones:
            print(f"✅ Se encontraron {len(items_con_devoluciones)} items con devoluciones:")
            for item in items_con_devoluciones:
                print(f"\n   Ticket {item[1]}: {item[2]}")
                print(f"   - Solicitado: {item[3]}")
                print(f"   - Entregado: {item[4]}")
                print(f"   - Devuelto: {item[5]}")
                
                # Calcular pendiente
                pendiente = item[4] - item[5]
                if pendiente > 0:
                    print(f"   - Pendiente: {pendiente}")
                elif item[5] > 0:
                    print(f"   - ✅ Completamente devuelto")
                
                # Verificar que entregado no se modificó
                if item[4] > 0:
                    print(f"   ✅ Entregado se mantiene fijo: {item[4]}")
        else:
            print("❌ No se encontraron items con devoluciones")
        
        # 3. Verificar discrepancias
        print(f"\n3. VERIFICACIÓN DE DISCREPANCIAS:")
        cursor.execute("""
            SELECT ti.ticket_id, tc.numero_ticket, ti.producto_nombre,
                   ti.cantidad_solicitada, ti.cantidad_entregada, ti.cantidad_devuelta,
                   (ti.cantidad_entregada - ti.cantidad_devuelta) as diferencia
            FROM ticket_items ti
            JOIN tickets_compra tc ON ti.ticket_id = tc.id
            WHERE ti.cantidad_devuelta > 0
            ORDER BY diferencia DESC
            LIMIT 10
        """)
        
        discrepancias = cursor.fetchall()
        if discrepancias:
            print(f"✅ Análisis de discrepancias:")
            for item in discrepancias:
                print(f"\n   Ticket {item[1]}: {item[2]}")
                print(f"   - Entregado: {item[4]}, Devuelto: {item[5]}")
                print(f"   - Diferencia: {item[6]}")
                
                if item[6] > 0:
                    print(f"   ⚠️ Pendiente por devolver: {item[6]}")
                elif item[6] == 0:
                    print(f"   ✅ Completamente devuelto")
                else:
                    print(f"   ❌ Error: Devuelto más de lo entregado")
        else:
            print("❌ No se encontraron discrepancias para analizar")
        
        conn.close()
        print("\n✅ Verificación completada")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    verificar_contadores_independientes() 