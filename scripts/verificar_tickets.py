#!/usr/bin/env python3
"""
Script para verificar tickets y solicitante_id
"""

import sqlite3
import os
import sys

# Agregar el directorio padre al path para importar módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def verificar_tickets():
    """Verificar todos los tickets en la base de datos"""
    try:
        # Conectar a la base de datos
        db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "almacen.db")
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Obtener todos los tickets
        cursor.execute("""
            SELECT t.id, t.numero_ticket, t.estado, t.solicitante_id, t.solicitante_nombre,
                   t.fecha_solicitud, t.fecha_aprobacion, t.fecha_entrega
            FROM tickets_compra t
            ORDER BY t.id
        """)
        
        tickets = cursor.fetchall()
        
        print(f"🎫 Total de tickets en la base de datos: {len(tickets)}")
        print("=" * 80)
        
        if not tickets:
            print("❌ No hay tickets en la base de datos")
            return
        
        for ticket in tickets:
            print(f"ID: {ticket['id']:2d} | Ticket: {ticket['numero_ticket']:<15} | Estado: {ticket['estado']:<10} | Solicitante ID: {ticket['solicitante_id'] or 'NULL':<3} | Nombre: {ticket['solicitante_nombre']}")
        
        print("=" * 80)
        
        # Verificar tickets específicos
        print("\n🔍 Verificando tickets específicos:")
        
        # Tickets entregados
        cursor.execute("SELECT * FROM tickets_compra WHERE estado = 'entregado'")
        tickets_entregados = cursor.fetchall()
        print(f"📦 Tickets entregados: {len(tickets_entregados)}")
        for ticket in tickets_entregados:
            print(f"  - Ticket {ticket['numero_ticket']} (ID: {ticket['id']}) - Solicitante: {ticket['solicitante_id'] or 'NULL'}")
        
        # Verificar usuarios
        cursor.execute("SELECT id, username, nombre_completo, rol FROM usuarios")
        usuarios = cursor.fetchall()
        print(f"\n👥 Usuarios en el sistema: {len(usuarios)}")
        for usuario in usuarios:
            print(f"  - ID: {usuario['id']} | Usuario: {usuario['username']} | Nombre: {usuario['nombre_completo']} | Rol: {usuario['rol']}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error verificando tickets: {e}")

if __name__ == "__main__":
    verificar_tickets() 