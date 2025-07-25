#!/usr/bin/env python3
"""
Script para probar la funcionalidad de devolución de tickets
"""

import requests
import json
import sqlite3
import urllib3

# Deshabilitar advertencias de SSL para desarrollo
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def test_devolucion():
    """Probar la funcionalidad de devolución"""
    
    print("🧪 Probando funcionalidad de devolución")
    print("=" * 50)
    
    # 1. Verificar datos en BD
    print("\n1. 📊 Verificando datos en BD de desarrollo...")
    try:
        conn = sqlite3.connect('data/almacen_desarrollo.db')
        cursor = conn.cursor()
        
        # Verificar ticket
        cursor.execute("SELECT id, numero_ticket, estado FROM tickets_compra WHERE estado = 'entregado' LIMIT 1")
        ticket = cursor.fetchone()
        if ticket:
            print(f"   ✅ Ticket encontrado: ID {ticket[0]}, {ticket[1]}, Estado: {ticket[2]}")
            ticket_id = ticket[0]
            
            # Verificar items del ticket
            cursor.execute("""
                SELECT ti.id, ti.producto_id, ti.producto_nombre, 
                       ti.cantidad_solicitada, ti.cantidad_entregada
                FROM ticket_items ti
                WHERE ti.ticket_id = ?
            """, (ticket_id,))
            items = cursor.fetchall()
            print(f"   📦 Items en ticket: {len(items)}")
            for item in items:
                print(f"   - Producto ID: {item[1]}, {item[2]}, Entregado: {item[4]}")
            
            # Verificar producto
            if items:
                producto_id = items[0][1]
                cursor.execute("SELECT id, nombre, cantidad FROM productos WHERE id = ?", (producto_id,))
                producto = cursor.fetchone()
                if producto:
                    print(f"   🛠️ Producto: ID {producto[0]}, {producto[1]}, Stock: {producto[2]}")
        
        conn.close()
        
    except Exception as e:
        print(f"   ❌ Error verificando BD: {e}")
        return
    
    # 2. Probar login
    print("\n2. 🔐 Probando login...")
    try:
        login_data = {
            "username": "supervisor",
            "password": "super123"
        }
        
        response = requests.post("https://localhost:8000/api/auth/login", json=login_data, verify=False)
        if response.status_code == 200:
            cookies = response.cookies
            print("   ✅ Login exitoso")
        else:
            print(f"   ❌ Error en login: {response.status_code}")
            print(f"   Response: {response.text}")
            return
            
    except Exception as e:
        print(f"   ❌ Error en login: {e}")
        return
    
    # 3. Probar devolución
    print("\n3. 🔄 Probando devolución...")
    try:
        if not ticket:
            print("   ❌ No hay ticket entregado para probar")
            return
            
        devolucion_data = {
            "codigo": f"ID:{producto_id}|Nombre:{producto[1]}",
            "cantidad": 1
        }
        
        print(f"   📤 Enviando devolución: {devolucion_data}")
        
        response = requests.post(
            f"https://localhost:8000/api/tickets/{ticket_id}/devolver",
            json=devolucion_data,
            cookies=cookies,
            verify=False
        )
        
        print(f"   📥 Status: {response.status_code}")
        print(f"   📋 Response: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Devolución exitosa: {result.get('mensaje', '')}")
        else:
            print(f"   ❌ Error en devolución")
            
    except Exception as e:
        print(f"   ❌ Error probando devolución: {e}")
    
    # 4. Verificar cambios en BD
    print("\n4. 🔍 Verificando cambios en BD...")
    try:
        conn = sqlite3.connect('data/almacen_desarrollo.db')
        cursor = conn.cursor()
        
        # Verificar ticket después de devolución
        cursor.execute("SELECT estado FROM tickets_compra WHERE id = ?", (ticket_id,))
        ticket_estado = cursor.fetchone()
        if ticket_estado:
            print(f"   📋 Estado del ticket: {ticket_estado[0]}")
        
        # Verificar items del ticket
        cursor.execute("""
            SELECT ti.cantidad_entregada
            FROM ticket_items ti
            WHERE ti.ticket_id = ?
        """, (ticket_id,))
        items = cursor.fetchall()
        for i, item in enumerate(items):
            print(f"   📦 Item {i+1} cantidad entregada: {item[0]}")
        
        # Verificar stock del producto
        cursor.execute("SELECT cantidad FROM productos WHERE id = ?", (producto_id,))
        stock = cursor.fetchone()
        if stock:
            print(f"   🛠️ Stock actual del producto: {stock[0]}")
        
        conn.close()
        
    except Exception as e:
        print(f"   ❌ Error verificando cambios: {e}")

if __name__ == "__main__":
    test_devolucion() 