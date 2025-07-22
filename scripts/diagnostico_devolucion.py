#!/usr/bin/env python3
"""
Diagnóstico del problema de devolución de tickets
"""

import sqlite3
import requests
import json

def diagnosticar_devolucion():
    """Diagnosticar el problema de devolución"""
    
    print("🔍 Diagnóstico del problema de devolución")
    print("=" * 50)
    
    # 1. Verificar base de datos de desarrollo
    print("\n1. 📊 Verificando base de datos de desarrollo...")
    try:
        conn = sqlite3.connect('data/almacen_desarrollo.db')
        cursor = conn.cursor()
        
        # Verificar tickets
        cursor.execute("SELECT id, numero_ticket, estado FROM tickets_compra ORDER BY id DESC LIMIT 5")
        tickets = cursor.fetchall()
        print(f"   Tickets encontrados: {len(tickets)}")
        for ticket in tickets:
            print(f"   - ID: {ticket[0]}, Ticket: {ticket[1]}, Estado: {ticket[2]}")
        
        # Verificar items de tickets
        if tickets:
            ticket_id = tickets[0][0]  # Último ticket
            cursor.execute("""
                SELECT ti.id, ti.producto_id, ti.producto_nombre, 
                       ti.cantidad_solicitada, ti.cantidad_entregada
                FROM ticket_items ti
                WHERE ti.ticket_id = ?
            """, (ticket_id,))
            items = cursor.fetchall()
            print(f"   Items del ticket {ticket_id}: {len(items)}")
            for item in items:
                if len(item) >= 5:  # Verificar que tenga suficientes elementos
                    print(f"   - Producto: {item[2]}, Solicitado: {item[3]}, Entregado: {item[4]}")
                else:
                    print(f"   - Item con estructura inesperada: {item}")
        
        # Verificar productos
        cursor.execute("SELECT id, nombre, cantidad FROM productos LIMIT 5")
        productos = cursor.fetchall()
        print(f"   Productos disponibles: {len(productos)}")
        for producto in productos:
            print(f"   - ID: {producto[0]}, {producto[1]}, Stock: {producto[2]}")
        
        conn.close()
        
    except Exception as e:
        print(f"   ❌ Error verificando BD: {e}")
    
    # 2. Verificar servidor de desarrollo (puerto 8000)
    print("\n2. 🌐 Verificando servidor de desarrollo (puerto 8000)...")
    try:
        response = requests.get("http://localhost:8000/api/productos", timeout=5)
        if response.status_code == 200:
            print("   ✅ Servidor de desarrollo respondiendo")
        else:
            print(f"   ⚠️ Servidor responde con status: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("   ❌ Servidor de desarrollo NO está corriendo en puerto 8000")
        print("   💡 Ejecuta: python backend/main.py")
    except Exception as e:
        print(f"   ❌ Error conectando al servidor: {e}")
    
    print("\n3. 📋 Resumen del diagnóstico:")
    print("   - Verificar que el servidor de desarrollo esté corriendo en puerto 8000")
    print("   - Verificar que haya tickets entregados")
    print("   - Verificar que los productos tengan códigos QR válidos")
    print("   - Revisar logs del servidor para errores específicos")

if __name__ == "__main__":
    diagnosticar_devolucion() 