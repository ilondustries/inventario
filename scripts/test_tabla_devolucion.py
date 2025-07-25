#!/usr/bin/env python3
"""
Script para probar la visualización de devoluciones en la tabla de herramientas
"""

import requests
import json
import sys
import os

# Configuración
BASE_URL = "https://localhost:8000"
LOGIN_URL = f"{BASE_URL}/api/auth/login"
TICKET_URL = f"{BASE_URL}/api/tickets"

def login(username, password):
    """Iniciar sesión y obtener token"""
    try:
        response = requests.post(LOGIN_URL, json={
            "username": username,
            "password": password
        }, verify=False)
        
        if response.status_code == 200:
            return response.json().get("access_token")
        else:
            print(f"Error de login: {response.status_code}")
            return None
    except Exception as e:
        print(f"Error de conexión: {e}")
        return None

def get_ticket_details(token, ticket_id):
    """Obtener detalles de un ticket específico"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{TICKET_URL}/{ticket_id}", headers=headers, verify=False)
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error obteniendo ticket: {response.status_code}")
            return None
    except Exception as e:
        print(f"Error de conexión: {e}")
        return None

def main():
    print("=== Prueba de Visualización de Devoluciones en Tabla ===\n")
    
    # Credenciales de supervisor
    username = "supervisor"
    password = "super123"
    
    print(f"1. Iniciando sesión como {username}...")
    token = login(username, password)
    
    if not token:
        print("❌ Error: No se pudo obtener token de autenticación")
        return
    
    print("✅ Login exitoso")
    
    # Solicitar ID del ticket a probar
    ticket_id = input("\n2. Ingresa el ID del ticket a probar (o presiona Enter para usar 27): ").strip()
    if not ticket_id:
        ticket_id = "27"
    
    print(f"\n3. Obteniendo detalles del ticket {ticket_id}...")
    ticket = get_ticket_details(token, ticket_id)
    
    if not ticket:
        print("❌ Error: No se pudo obtener detalles del ticket")
        return
    
    print("✅ Detalles del ticket obtenidos")
    
    # Mostrar información del ticket
    print(f"\n=== DATOS DEL TICKET {ticket.get('numero_ticket', 'N/A')} ===")
    print(f"Estado: {ticket.get('estado', 'N/A')}")
    print(f"Fecha de Solicitud: {ticket.get('fecha_solicitud', 'N/A')}")
    print(f"Fecha de Entrega: {ticket.get('fecha_entrega', 'N/A')}")
    print(f"Entregado por: {ticket.get('entregado_por_nombre', 'N/A')}")
    print(f"Fecha de Devolución: {ticket.get('fecha_devolucion', 'N/A')}")
    print(f"Devuelto por: {ticket.get('devuelto_por_nombre', 'N/A')}")
    
    # Mostrar items con información de devolución
    print(f"\n=== TABLA DE HERRAMIENTAS ===")
    items = ticket.get('items', [])
    if items:
        print(f"✅ Se encontraron {len(items)} herramientas:")
        for i, item in enumerate(items, 1):
            cantidadDevuelta = item.get('cantidad_devuelta', 0) or 0
            print(f"\n{i}. {item.get('producto_nombre', 'N/A')}")
            print(f"   📋 Solicitado: {item.get('cantidad_solicitada', 0)}")
            print(f"   📦 Entregado: {item.get('cantidad_entregada', 0)}")
            print(f"   🔄 Devuelto: {cantidadDevuelta}")
            
            # Calcular pendiente
            pendiente = (item.get('cantidad_entregada', 0) or 0) - cantidadDevuelta
            if pendiente > 0:
                print(f"   ⏳ Pendiente: {pendiente}")
            elif cantidadDevuelta > 0:
                print(f"   ✅ Completamente devuelto")
    else:
        print("❌ No hay herramientas en este ticket")
    
    print(f"\n=== INSTRUCCIONES PARA PROBAR ===")
    print("1. Abre el navegador y ve a https://localhost:8000")
    print("2. Inicia sesión como supervisor (supervisor/super123)")
    print("3. Ve a la sección de Tickets")
    print("4. Haz clic en 'Detalles' del ticket que probaste")
    print("5. Verifica que en la tabla de herramientas aparezca:")
    print("   - Solicitado: [cantidad]")
    print("   - Entregado: [cantidad]")
    print("   - Devuelto: [cantidad] (con fondo verde si > 0)")
    print("6. Los valores deben estar alineados horizontalmente")
    print("7. Las devoluciones deben destacarse visualmente")

if __name__ == "__main__":
    main() 