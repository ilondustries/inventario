#!/usr/bin/env python3
"""
Script para eliminar un ticket específico del sistema
"""

import sqlite3
import os
import sys

def eliminar_ticket(numero_ticket):
    """Eliminar un ticket específico por número"""
    
    # Conectar a la base de datos principal
    db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'almacen_main.db')
    
    if not os.path.exists(db_path):
        print(f"❌ Base de datos no encontrada: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print(f"🔍 Buscando ticket: {numero_ticket}")
        
        # Buscar el ticket
        cursor.execute("""
            SELECT id, numero_ticket, estado, solicitante_nombre, fecha_solicitud
            FROM tickets_compra 
            WHERE numero_ticket = ?
        """, (numero_ticket,))
        
        ticket = cursor.fetchone()
        if not ticket:
            print(f"❌ Ticket {numero_ticket} no encontrado")
            return False
        
        ticket_id, numero, estado, solicitante, fecha = ticket
        print(f"✅ Ticket encontrado:")
        print(f"   ID: {ticket_id}")
        print(f"   Número: {numero}")
        print(f"   Estado: {estado}")
        print(f"   Solicitante: {solicitante}")
        print(f"   Fecha: {fecha}")
        
        # Contar items del ticket
        cursor.execute("SELECT COUNT(*) FROM ticket_items WHERE ticket_id = ?", (ticket_id,))
        total_items = cursor.fetchone()[0]
        print(f"   Items: {total_items}")
        
        # Confirmar eliminación
        print(f"\n⚠️ ¿Estás seguro de que quieres eliminar el ticket {numero_ticket}?")
        confirmacion = input("Escribe 'ELIMINAR' para confirmar: ")
        
        if confirmacion != "ELIMINAR":
            print("❌ Operación cancelada")
            return False
        
        print(f"🗑️ Eliminando ticket {numero_ticket}...")
        
        # Eliminar items del ticket primero (por integridad referencial)
        cursor.execute("DELETE FROM ticket_items WHERE ticket_id = ?", (ticket_id,))
        items_eliminados = cursor.rowcount
        print(f"✅ Eliminados {items_eliminados} items del ticket")
        
        # Eliminar registros del historial relacionados con este ticket
        cursor.execute("""
            DELETE FROM historial 
            WHERE detalles LIKE ?
        """, (f"%{numero_ticket}%",))
        historial_eliminado = cursor.rowcount
        print(f"✅ Eliminados {historial_eliminado} registros del historial")
        
        # Eliminar el ticket principal
        cursor.execute("DELETE FROM tickets_compra WHERE id = ?", (ticket_id,))
        if cursor.rowcount > 0:
            print(f"✅ Ticket {numero_ticket} eliminado exitosamente")
        else:
            print(f"❌ Error al eliminar el ticket")
            return False
        
        # Guardar cambios
        conn.commit()
        conn.close()
        
        print(f"🎉 Ticket {numero_ticket} eliminado completamente del sistema")
        return True
        
    except Exception as e:
        print(f"❌ Error eliminando ticket: {e}")
        return False

def main():
    """Función principal"""
    print("🗑️ ELIMINADOR DE TICKETS")
    print("=" * 40)
    
    # Ticket a eliminar
    numero_ticket = "TICK-000020"
    
    print(f"🎯 Objetivo: Eliminar {numero_ticket}")
    print("⚠️  ADVERTENCIA: Esta acción es irreversible")
    print("⚠️  Se eliminarán todos los datos relacionados")
    print()
    
    if eliminar_ticket(numero_ticket):
        print(f"\n✅ Ticket {numero_ticket} eliminado exitosamente")
    else:
        print(f"\n❌ No se pudo eliminar el ticket {numero_ticket}")

if __name__ == "__main__":
    main()
