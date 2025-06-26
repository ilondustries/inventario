#!/usr/bin/env python3
"""
Script para probar la API del sistema de almacén
"""

import requests
import json

def test_crear_producto():
    """Probar la creación de un producto"""
    url = "http://localhost:8000/api/productos"
    
    # Datos de prueba (simulando lo que envía la tablet)
    producto = {
        "codigo_barras": "123456789",
        "nombre": "Producto de Prueba",
        "descripcion": "Descripción de prueba",
        "cantidad": "10",
        "cantidad_minima": "5",
        "ubicacion": "Estante A",
        "categoria": "Electrónicos",
        "precio_unitario": "99.99"
    }
    
    print("🧪 Probando creación de producto...")
    print(f"📤 Enviando datos: {json.dumps(producto, indent=2)}")
    
    try:
        response = requests.post(url, json=producto)
        
        print(f"📥 Respuesta: {response.status_code}")
        print(f"📋 Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Éxito: {data}")
        else:
            print(f"❌ Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Error de conexión: {e}")

def test_crear_producto_minimo():
    """Probar creación con datos mínimos"""
    url = "http://localhost:8000/api/productos"
    
    # Solo nombre (datos mínimos)
    producto = {
        "nombre": "Producto Mínimo"
    }
    
    print("\n🧪 Probando creación con datos mínimos...")
    print(f"📤 Enviando datos: {json.dumps(producto, indent=2)}")
    
    try:
        response = requests.post(url, json=producto)
        
        print(f"📥 Respuesta: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Éxito: {data}")
        else:
            print(f"❌ Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Error de conexión: {e}")

def test_obtener_productos():
    """Probar obtener productos"""
    url = "http://localhost:8000/api/productos"
    
    print("\n🧪 Probando obtener productos...")
    
    try:
        response = requests.get(url)
        
        print(f"📥 Respuesta: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Productos encontrados: {len(data.get('productos', []))}")
        else:
            print(f"❌ Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Error de conexión: {e}")

if __name__ == "__main__":
    print("🚀 Iniciando pruebas de API")
    print("=" * 40)
    
    # Verificar que el servidor esté corriendo
    try:
        response = requests.get("http://localhost:8000/")
        if response.status_code == 200:
            print("✅ Servidor está corriendo")
        else:
            print("❌ Servidor no responde correctamente")
            exit(1)
    except:
        print("❌ No se puede conectar al servidor. Asegúrate de que esté corriendo en http://localhost:8000")
        exit(1)
    
    # Ejecutar pruebas
    test_obtener_productos()
    test_crear_producto_minimo()
    test_crear_producto()
    
    print("\n✅ Pruebas completadas") 