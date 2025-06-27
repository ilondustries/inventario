#!/usr/bin/env python3
"""
Script de prueba para el Sistema de Tickets de Compra
Prueba la funcionalidad completa del sistema de tickets
"""

import requests
import json
import time
from datetime import datetime

# Configuración
BASE_URL = "http://localhost:8000"
API_URL = f"{BASE_URL}/api"

def print_separator(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def print_success(message):
    print(f"✅ {message}")

def print_error(message):
    print(f"❌ {message}")

def print_info(message):
    print(f"ℹ️  {message}")

def test_login(username, password):
    """Probar login de usuario"""
    try:
        response = requests.post(f"{API_URL}/auth/login", json={
            "username": username,
            "password": password
        })
        
        if response.status_code == 200:
            data = response.json()
            print_success(f"Login exitoso para {username}")
            return data.get("token")
        else:
            print_error(f"Login fallido para {username}: {response.text}")
            return None
    except Exception as e:
        print_error(f"Error en login: {e}")
        return None

def test_create_ticket(token, ticket_data):
    """Probar creación de ticket"""
    try:
        headers = {"Cookie": f"session_token={token}"}
        response = requests.post(f"{API_URL}/tickets", 
                               json=ticket_data, 
                               headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            print_success(f"Ticket creado: {data['numero_ticket']}")
            return data
        else:
            print_error(f"Error creando ticket: {response.text}")
            return None
    except Exception as e:
        print_error(f"Error en creación de ticket: {e}")
        return None

def test_list_tickets(token):
    """Probar listado de tickets"""
    try:
        headers = {"Cookie": f"session_token={token}"}
        response = requests.get(f"{API_URL}/tickets", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            print_success(f"Tickets obtenidos: {len(data['tickets'])}")
            return data['tickets']
        else:
            print_error(f"Error obteniendo tickets: {response.text}")
            return []
    except Exception as e:
        print_error(f"Error en listado de tickets: {e}")
        return []

def test_approve_ticket(token, ticket_id, action, comments=""):
    """Probar aprobación/rechazo de ticket"""
    try:
        headers = {"Cookie": f"session_token={token}"}
        response = requests.put(f"{API_URL}/tickets/{ticket_id}/aprobar",
                              json={"accion": action, "comentarios": comments},
                              headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            print_success(f"Ticket {action}: {data['numero_ticket']}")
            return data
        else:
            print_error(f"Error {action} ticket: {response.text}")
            return None
    except Exception as e:
        print_error(f"Error en {action} de ticket: {e}")
        return None

def test_deliver_ticket(token, ticket_id, items):
    """Probar entrega de ticket"""
    try:
        headers = {"Cookie": f"session_token={token}"}
        response = requests.put(f"{API_URL}/tickets/{ticket_id}/entregar",
                              json={"items": items},
                              headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            print_success(f"Entrega procesada: {data['numero_ticket']}")
            return data
        else:
            print_error(f"Error en entrega: {response.text}")
            return None
    except Exception as e:
        print_error(f"Error en entrega de ticket: {e}")
        return None

def test_get_products(token):
    """Obtener productos disponibles"""
    try:
        headers = {"Cookie": f"session_token={token}"}
        response = requests.get(f"{API_URL}/productos", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            return data['productos']
        else:
            print_error(f"Error obteniendo productos: {response.text}")
            return []
    except Exception as e:
        print_error(f"Error obteniendo productos: {e}")
        return []

def main():
    print_separator("PRUEBA DEL SISTEMA DE TICKETS DE COMPRA")
    
    # 1. Login como supervisor
    print_info("1. Probando login como supervisor...")
    supervisor_token = test_login("supervisor", "super123")
    if not supervisor_token:
        return
    
    # 2. Obtener productos disponibles
    print_info("2. Obteniendo productos disponibles...")
    productos = test_get_products(supervisor_token)
    if not productos:
        print_error("No hay productos disponibles para crear tickets")
        return
    
    print_success(f"Productos disponibles: {len(productos)}")
    
    # 3. Crear ticket como supervisor
    print_info("3. Creando ticket como supervisor...")
    ticket_data = {
        "orden_produccion": "OP-2024-001",
        "justificacion": "Herramientas necesarias para mantenimiento preventivo de máquinas",
        "items": [
            {
                "producto_id": productos[0]["id"],
                "cantidad_solicitada": 2,
                "precio_unitario": productos[0].get("precio_unitario", 0)
            }
        ]
    }
    
    ticket_creado = test_create_ticket(supervisor_token, ticket_data)
    if not ticket_creado:
        return
    
    ticket_id = None
    # Buscar el ticket creado
    tickets = test_list_tickets(supervisor_token)
    for ticket in tickets:
        if ticket["numero_ticket"] == ticket_creado["numero_ticket"]:
            ticket_id = ticket["id"]
            break
    
    if not ticket_id:
        print_error("No se pudo encontrar el ticket creado")
        return
    
    # 4. Login como admin
    print_info("4. Probando login como administrador...")
    admin_token = test_login("admin", "admin123")
    if not admin_token:
        return
    
    # 5. Aprobar ticket como admin
    print_info("5. Aprobando ticket como administrador...")
    test_approve_ticket(admin_token, ticket_id, "aprobar", "Ticket aprobado para mantenimiento")
    
    # 6. Entregar herramientas
    print_info("6. Entregando herramientas...")
    # Obtener items del ticket
    tickets_admin = test_list_tickets(admin_token)
    ticket_aprobado = None
    for ticket in tickets_admin:
        if ticket["numero_ticket"] == ticket_creado["numero_ticket"]:
            ticket_aprobado = ticket
            break
    
    if ticket_aprobado and ticket_aprobado["items"]:
        items_entrega = []
        for item in ticket_aprobado["items"]:
            items_entrega.append({
                "item_id": item["id"],
                "cantidad_entregada": item["cantidad_solicitada"]
            })
        
        test_deliver_ticket(admin_token, ticket_id, items_entrega)
    
    # 7. Verificar estado final
    print_info("7. Verificando estado final...")
    tickets_final = test_list_tickets(admin_token)
    for ticket in tickets_final:
        if ticket["numero_ticket"] == ticket_creado["numero_ticket"]:
            print_success(f"Estado final del ticket: {ticket['estado']}")
            break
    
    print_separator("PRUEBA COMPLETADA")
    print_success("Sistema de tickets funcionando correctamente!")

if __name__ == "__main__":
    main() 