#!/usr/bin/env python3
"""
Script para probar el login como lo haría un navegador real
"""
import requests
import json
import time

def test_browser_simulation():
    """Simular el comportamiento de un navegador real"""
    print("🌐 Simulando comportamiento del navegador...")
    
    # Crear sesión que mantenga cookies
    session = requests.Session()
    
    # Configurar headers como un navegador real
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    })
    
    try:
        # Paso 1: Acceder a la página principal (debería redirigir a login)
        print("\n1️⃣ Accediendo a página principal...")
        response = session.get("http://localhost:8000/")
        print(f"   Status: {response.status_code}")
        print(f"   Content-Type: {response.headers.get('content-type', 'N/A')}")
        print(f"   Cookies recibidas: {dict(session.cookies)}")
        
        # Paso 2: Intentar login
        print("\n2️⃣ Intentando login...")
        login_data = {
            "username": "admin",
            "password": "admin123"
        }
        
        response = session.post(
            "http://localhost:8000/api/auth/login",
            json=login_data,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")
        print(f"   Cookies después del login: {dict(session.cookies)}")
        
        if response.status_code == 200:
            print("   ✅ Login exitoso")
            
            # Paso 3: Verificar autenticación inmediatamente
            print("\n3️⃣ Verificando autenticación...")
            auth_response = session.get("http://localhost:8000/api/auth/check")
            print(f"   Status: {auth_response.status_code}")
            print(f"   Auth data: {auth_response.json()}")
            
            # Paso 4: Acceder a la página principal con sesión
            print("\n4️⃣ Accediendo a página principal con sesión...")
            main_response = session.get("http://localhost:8000/")
            print(f"   Status: {main_response.status_code}")
            print(f"   Content-Type: {main_response.headers.get('content-type', 'N/A')}")
            
            if "login.html" in main_response.text:
                print("   ⚠️  Página principal aún redirige a login")
                print("   🔍 Primeros 200 caracteres de la respuesta:")
                print(f"   {main_response.text[:200]}...")
            else:
                print("   ✅ Página principal accesible")
                
            # Paso 5: Verificar productos (endpoint protegido)
            print("\n5️⃣ Probando endpoint protegido...")
            productos_response = session.get("http://localhost:8000/api/productos")
            print(f"   Status: {productos_response.status_code}")
            if productos_response.status_code == 200:
                data = productos_response.json()
                print(f"   Productos obtenidos: {len(data.get('productos', []))}")
            else:
                print(f"   Error: {productos_response.text}")
                
        else:
            print(f"   ❌ Login falló: {response.text}")
            
    except Exception as e:
        print(f"❌ Error en simulación: {e}")

def test_cookie_behavior():
    """Probar comportamiento específico de cookies"""
    print("\n🍪 Probando comportamiento de cookies...")
    
    session = requests.Session()
    
    # Login
    login_data = {"username": "admin", "password": "admin123"}
    response = session.post("http://localhost:8000/api/auth/login", json=login_data)
    
    if response.status_code == 200:
        print("✅ Login exitoso")
        
        # Verificar cookies
        cookies = session.cookies
        for cookie in cookies:
            print(f"Cookie: {cookie.name}")
            print(f"  Valor: {cookie.value[:20]}...")
            print(f"  Dominio: {cookie.domain}")
            print(f"  Path: {cookie.path}")
            print(f"  Expires: {cookie.expires}")
            print(f"  Secure: {cookie.secure}")
            print(f"  HttpOnly: {cookie.has_nonstandard_attr('HttpOnly')}")
            print(f"  SameSite: {cookie.get_nonstandard_attr('SameSite')}")
            print()
        
        # Probar diferentes URLs
        urls_to_test = [
            "http://localhost:8000/api/auth/check",
            "http://127.0.0.1:8000/api/auth/check",
            "http://localhost:8000/",
            "http://127.0.0.1:8000/"
        ]
        
        for url in urls_to_test:
            print(f"Probando {url}...")
            try:
                response = session.get(url)
                print(f"  Status: {response.status_code}")
                if "auth/check" in url:
                    print(f"  Data: {response.json()}")
            except Exception as e:
                print(f"  Error: {e}")

if __name__ == "__main__":
    print("🧪 PRUEBA DE LOGIN CON SIMULACIÓN DE NAVEGADOR")
    print("=" * 60)
    
    test_browser_simulation()
    test_cookie_behavior()
    
    print("\n💡 ANÁLISIS:")
    print("Si el login funciona pero auth/check falla, puede ser:")
    print("1. Problema de dominio de cookies")
    print("2. Problema de path de cookies")
    print("3. Problema de CORS")
    print("4. Problema de configuración de SameSite") 