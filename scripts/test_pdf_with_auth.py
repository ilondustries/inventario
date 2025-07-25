#!/usr/bin/env python3
"""
Script para probar el endpoint de PDF con autenticación
"""

import requests
import json

# Configuración
BASE_URL = "https://localhost:8000"

def test_pdf_with_auth():
    """Probar el endpoint de PDF con autenticación"""
    try:
        # Crear sesión para mantener cookies
        session = requests.Session()
        session.verify = False
        
        # Login
        print("🔐 Iniciando sesión...")
        login_data = {
            "username": "supervisor",
            "password": "super123"
        }
        
        login_response = session.post(f"{BASE_URL}/api/auth/login", json=login_data)
        
        if login_response.status_code == 200:
            print("✅ Login exitoso")
            
            # Obtener tickets
            print("🔍 Obteniendo tickets...")
            tickets_response = session.get(f"{BASE_URL}/api/tickets")
            
            if tickets_response.status_code == 200:
                data = tickets_response.json()
                tickets = data.get('tickets', [])
                
                if tickets:
                    # Usar el primer ticket
                    ticket = tickets[0]
                    ticket_id = ticket['id']
                    numero_ticket = ticket['numero_ticket']
                    
                    print(f"✅ Ticket encontrado: {numero_ticket} (ID: {ticket_id})")
                    
                    # Probar endpoint de PDF
                    print(f"🔍 Probando endpoint de PDF para ticket {ticket_id}...")
                    pdf_response = session.get(f"{BASE_URL}/api/tickets/{ticket_id}/pdf")
                    
                    if pdf_response.status_code == 200:
                        print("✅ PDF generado exitosamente")
                        print(f"📄 Tamaño del PDF: {len(pdf_response.content)} bytes")
                        
                        # Guardar PDF para verificar
                        with open(f"test_ticket_{numero_ticket}.pdf", "wb") as f:
                            f.write(pdf_response.content)
                        print(f"💾 PDF guardado como: test_ticket_{numero_ticket}.pdf")
                        
                    else:
                        print(f"❌ Error generando PDF: {pdf_response.status_code}")
                        print(f"📄 Respuesta: {pdf_response.text}")
                else:
                    print("❌ No hay tickets disponibles para probar")
            else:
                print(f"❌ Error obteniendo tickets: {tickets_response.status_code}")
        else:
            print(f"❌ Error en login: {login_response.status_code}")
            print(f"📄 Respuesta: {login_response.text}")
            
    except Exception as e:
        print(f"❌ Error en la prueba: {e}")

if __name__ == "__main__":
    test_pdf_with_auth() 