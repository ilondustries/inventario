#!/usr/bin/env python3
"""
Script de prueba para verificar la funcionalidad de códigos de barras
"""

import requests
import json

def test_barcode_functionality():
    """Probar la funcionalidad de códigos de barras"""
    base_url = "http://localhost:8000"
    
    try:
        # 1. Obtener productos
        print("1. Obteniendo productos...")
        response = requests.get(f"{base_url}/api/productos")
        if response.status_code != 200:
            print(f"❌ Error obteniendo productos: {response.status_code}")
            return
        
        productos = response.json()["productos"]
        print(f"✅ Productos obtenidos: {len(productos)} productos")
        
        if not productos:
            print("❌ No hay productos para probar")
            return
        
        # 2. Probar código de barras del primer producto
        primer_producto = productos[0]
        producto_id = primer_producto["id"]
        nombre = primer_producto["nombre"]
        
        print(f"\n2. Probando código de barras para producto: {nombre} (ID: {producto_id})")
        
        response = requests.get(f"{base_url}/api/productos/{producto_id}/barcode")
        if response.status_code != 200:
            print(f"❌ Error obteniendo código de barras: {response.status_code}")
            print(f"Respuesta: {response.text}")
            return
        
        barcode_data = response.json()
        if "barcode" in barcode_data and barcode_data["barcode"].startswith("data:image/png;base64,"):
            print("✅ Código de barras generado correctamente")
            print(f"   Tamaño del código: {len(barcode_data['barcode'])} caracteres")
        else:
            print("❌ Formato de código de barras incorrecto")
            print(f"Respuesta: {barcode_data}")
        
        # 3. Probar código QR del mismo producto
        print(f"\n3. Probando código QR para producto: {nombre} (ID: {producto_id})")
        
        response = requests.get(f"{base_url}/api/productos/{producto_id}/qr")
        if response.status_code != 200:
            print(f"❌ Error obteniendo código QR: {response.status_code}")
            print(f"Respuesta: {response.text}")
            return
        
        qr_data = response.json()
        if "qr" in qr_data and qr_data["qr"].startswith("data:image/png;base64,"):
            print("✅ Código QR generado correctamente")
            print(f"   Tamaño del QR: {len(qr_data['qr'])} caracteres")
        else:
            print("❌ Formato de código QR incorrecto")
            print(f"Respuesta: {qr_data}")
        
        # 4. Mostrar información del producto
        print(f"\n4. Información del producto probado:")
        print(f"   ID: {primer_producto['id']}")
        print(f"   Nombre: {primer_producto['nombre']}")
        print(f"   Código de barras: {primer_producto.get('codigo_barras', 'N/A')}")
        print(f"   Ubicación: {primer_producto.get('ubicacion', 'N/A')}")
        print(f"   Cantidad: {primer_producto['cantidad']}")
        
        print("\n✅ Todas las pruebas completadas exitosamente!")
        
    except requests.exceptions.ConnectionError:
        print("❌ Error: No se puede conectar al servidor. Asegúrate de que esté ejecutándose en http://localhost:8000")
    except Exception as e:
        print(f"❌ Error inesperado: {e}")

if __name__ == "__main__":
    test_barcode_functionality() 