#!/usr/bin/env python3
"""
Script para probar la visualización de fecha de devolución en detalles del ticket
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
    print("=== Prueba de Información de Devolución en Detalles del Ticket ===\n")
    
    # Credenciales de supervisor (puede ver todos los tickets)
    username = "supervisor"
    password = "super123"
    
    print(f"1. Iniciando sesión como {username}...")
    token = login(username, password)
    
    if not token:
        print("❌ Error: No se pudo obtener token de autenticación")
        return
    
    print("✅ Login exitoso")
    
    # Solicitar ID del ticket a probar
    ticket_id = input("\n2. Ingresa el ID del ticket a probar (o presiona Enter para usar 1): ").strip()
    if not ticket_id:
        ticket_id = "1"
    
    print(f"\n3. Obteniendo detalles del ticket {ticket_id}...")
    ticket = get_ticket_details(token, ticket_id)
    
    if not ticket:
        print("❌ Error: No se pudo obtener detalles del ticket")
        return
    
    print("✅ Detalles del ticket obtenidos")
    
    # Mostrar información del ticket
    print(f"\n=== DETALLES DEL TICKET {ticket.get('numero_ticket', 'N/A')} ===")
    print(f"Estado: {ticket.get('estado', 'N/A')}")
    print(f"Fecha de Solicitud: {ticket.get('fecha_solicitud', 'N/A')}")
    print(f"Fecha de Entrega: {ticket.get('fecha_entrega', 'N/A')}")
    print(f"Entregado por: {ticket.get('entregado_por_nombre', 'N/A')}")
    print(f"Fecha de Devolución: {ticket.get('fecha_devolucion', 'N/A')}")
    print(f"Devuelto por: {ticket.get('devuelto_por_nombre', 'N/A')}")
    
    # Verificar si tiene información de devolución
    if ticket.get('fecha_devolucion') and ticket.get('devuelto_por_nombre'):
        print("\n✅ El ticket SÍ tiene información de devolución")
        print(f"   Devuelto por: {ticket['devuelto_por_nombre']}")
        print(f"   Fecha: {ticket['fecha_devolucion']}")
    elif ticket.get('fecha_devolucion'):
        print("\n⚠️ El ticket tiene fecha de devolución pero no usuario")
        print(f"   Fecha: {ticket['fecha_devolucion']}")
    else:
        print("\n❌ El ticket NO tiene información de devolución")
        print("   Esto puede ser porque:")
        print("   - El ticket no ha sido devuelto")
        print("   - No hay registros de devolución en el historial")
    
    # Mostrar items del ticket
    print(f"\n=== ITEMS DEL TICKET ===")
    items = ticket.get('items', [])
    if items:
        for i, item in enumerate(items, 1):
            print(f"{i}. {item.get('producto_nombre', 'N/A')}")
            print(f"   Solicitado: {item.get('cantidad_solicitada', 0)}")
            print(f"   Entregado: {item.get('cantidad_entregada', 0)}")
    else:
        print("No hay items en este ticket")
    
    print(f"\n=== INSTRUCCIONES PARA PROBAR ===")
    print("1. Abre el navegador y ve a https://localhost:8000")
    print("2. Inicia sesión como supervisor (supervisor/super123)")
    print("3. Ve a la sección de Tickets")
    print("4. Haz clic en 'Detalles' del ticket que probaste")
    print("5. Verifica que aparezca 'Devuelto por: [usuario] (fecha)' en el modal")
    print("6. La información debe aparecer justo debajo de 'Entregado por:'")
    
    if ticket.get('fecha_devolucion') and ticket.get('devuelto_por_nombre'):
        print("\n✅ El ticket debería mostrar 'Devuelto por: [usuario] (fecha)' en el modal")
        print("   Formato esperado: 'Devuelto por: [nombre_usuario] (dd/mm/aaaa hh:mm:ss)'")
    else:
        print("\n❌ El ticket no debería mostrar información de devolución (no ha sido devuelto)")

if __name__ == "__main__":
    main() 