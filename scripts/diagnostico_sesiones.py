#!/usr/bin/env python3
"""
Script de diagnóstico para problemas de sesiones
"""
import sqlite3
import requests
import json
from datetime import datetime

def check_database_sessions():
    """Verificar sesiones en la base de datos"""
    print("🔍 Verificando sesiones en la base de datos...")
    
    try:
        conn = sqlite3.connect("../data/almacen.db")
        cursor = conn.cursor()
        
        # Verificar sesiones activas
        cursor.execute("""
            SELECT s.id, s.token, s.fecha_inicio, s.fecha_expiracion, s.activa,
                   u.username, u.nombre_completo
            FROM sesiones s
            JOIN usuarios u ON s.usuario_id = u.id
            ORDER BY s.fecha_inicio DESC
            LIMIT 10
        """)
        
        sessions = cursor.fetchall()
        print(f"📊 Total de sesiones encontradas: {len(sessions)}")
        
        for session in sessions:
            print(f"  - ID: {session[0]}, Usuario: {session[5]}, Activa: {session[4]}")
            print(f"    Token: {session[1][:20]}...")
            print(f"    Inicio: {session[2]}, Expira: {session[3]}")
            print()
        
        # Verificar usuarios
        cursor.execute("SELECT id, username, nombre_completo, rol FROM usuarios")
        users = cursor.fetchall()
        print(f"👥 Usuarios disponibles: {len(users)}")
        for user in users:
            print(f"  - {user[1]} ({user[3]}) - {user[2]}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error verificando base de datos: {e}")

def test_login_flow():
    """Probar el flujo de login"""
    print("\n🧪 Probando flujo de login...")
    
    try:
        # Crear sesión
        session = requests.Session()
        
        # Intentar login
        login_data = {
            "username": "admin",
            "password": "admin123"
        }
        
        print("📤 Enviando login...")
        response = session.post("http://localhost:8000/api/auth/login", 
                              json=login_data)
        
        print(f"📥 Respuesta del servidor: {response.status_code}")
        print(f"📋 Headers de respuesta:")
        for header, value in response.headers.items():
            if 'set-cookie' in header.lower():
                print(f"  {header}: {value}")
        
        print(f"🍪 Cookies en sesión:")
        for cookie in session.cookies:
            print(f"  {cookie.name}: {cookie.value}")
        
        if response.status_code == 200:
            print("✅ Login exitoso")
            
            # Verificar autenticación
            print("\n🔐 Verificando autenticación...")
            auth_response = session.get("http://localhost:8000/api/auth/check")
            print(f"Auth check: {auth_response.status_code}")
            print(f"Auth data: {auth_response.json()}")
            
            # Intentar acceder a la página principal
            print("\n🏠 Accediendo a página principal...")
            main_response = session.get("http://localhost:8000/")
            print(f"Main page: {main_response.status_code}")
            print(f"Content-Type: {main_response.headers.get('content-type', 'N/A')}")
            
            if "login.html" in main_response.text:
                print("⚠️  Página principal redirige a login")
            else:
                print("✅ Página principal accesible")
                
        else:
            print(f"❌ Login falló: {response.text}")
            
    except Exception as e:
        print(f"❌ Error en test de login: {e}")

def check_cookie_settings():
    """Verificar configuración de cookies"""
    print("\n🍪 Verificando configuración de cookies...")
    
    try:
        session = requests.Session()
        
        # Login
        login_data = {"username": "admin", "password": "admin123"}
        response = session.post("http://localhost:8000/api/auth/login", 
                              json=login_data)
        
        if response.status_code == 200:
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
                print()
        else:
            print("❌ No se pudo obtener cookies - login falló")
            
    except Exception as e:
        print(f"❌ Error verificando cookies: {e}")

if __name__ == "__main__":
    print("🔧 DIAGNÓSTICO DE SESIONES")
    print("=" * 50)
    
    check_database_sessions()
    test_login_flow()
    check_cookie_settings()
    
    print("\n💡 RECOMENDACIONES:")
    print("1. Verifica que el servidor esté corriendo en puerto 8000")
    print("2. Asegúrate de que no haya problemas de CORS")
    print("3. Revisa la configuración de cookies en el navegador")
    print("4. Verifica que el dominio y path de las cookies sean correctos") 