#!/usr/bin/env python3
"""
Script para probar el endpoint de PDF
"""

import requests
import json

# Configuración
BASE_URL = "https://localhost:8000"

def test_pdf_endpoint():
    """Probar el endpoint de PDF"""
    try:
        # Primero, obtener un ticket existente
        print("🔍 Obteniendo tickets existentes...")
        response = requests.get(f"{BASE_URL}/api/tickets", verify=False)
        
        if response.status_code == 200:
            data = response.json()
            tickets = data.get('tickets', [])
            
            if tickets:
                # Usar el primer ticket
                ticket = tickets[0]
                ticket_id = ticket['id']
                numero_ticket = ticket['numero_ticket']
                
                print(f"✅ Ticket encontrado: {numero_ticket} (ID: {ticket_id})")
                
                # Probar endpoint de PDF
                print(f"🔍 Probando endpoint de PDF para ticket {ticket_id}...")
                pdf_response = requests.get(f"{BASE_URL}/api/tickets/{ticket_id}/pdf", verify=False)
                
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
            print(f"❌ Error obteniendo tickets: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error en la prueba: {e}")

if __name__ == "__main__":
    test_pdf_endpoint() 