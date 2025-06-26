#!/usr/bin/env python3
"""
Script para verificar directamente la sesión en la base de datos
"""
import sqlite3
import os
import sys

def verificar_sesion_db():
    """Verificar la sesión directamente en la base de datos"""
    print("🔍 Verificando sesión en la base de datos...")
    
    # Ruta de la base de datos
    db_path = os.path.join(os.path.dirname(__file__), "..", "data", "almacen.db")
    print(f"📁 Ruta de la base de datos: {db_path}")
    
    if not os.path.exists(db_path):
        print(f"❌ La base de datos no existe en: {db_path}")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Verificar que las tablas existen
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        print(f"📋 Tablas encontradas: {tables}")
        
        # Verificar sesiones activas
        cursor.execute("""
            SELECT s.id, s.token, s.fecha_inicio, s.fecha_expiracion, s.activa,
                   u.username, u.nombre_completo
            FROM sesiones s
            JOIN usuarios u ON s.usuario_id = u.id
            WHERE s.activa = 1
            ORDER BY s.fecha_inicio DESC
        """)
        
        sessions = cursor.fetchall()
        print(f"📊 Sesiones activas encontradas: {len(sessions)}")
        
        for session in sessions:
            print(f"  - ID: {session[0]}")
            print(f"    Token: {session[1][:20]}...")
            print(f"    Usuario: {session[5]} ({session[6]})")
            print(f"    Activa: {session[4]}")
            print(f"    Inicio: {session[2]}")
            print(f"    Expira: {session[3]}")
            print()
        
        # Verificar usuarios
        cursor.execute("SELECT id, username, nombre_completo, rol FROM usuarios")
        users = cursor.fetchall()
        print(f"👥 Usuarios en la base de datos: {len(users)}")
        for user in users:
            print(f"  - {user[1]} ({user[3]}) - {user[2]}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error accediendo a la base de datos: {e}")
        import traceback
        traceback.print_exc()

def verificar_token_especifico(token):
    """Verificar un token específico"""
    print(f"\n🔍 Verificando token específico: {token[:20]}...")
    
    db_path = os.path.join(os.path.dirname(__file__), "..", "data", "almacen.db")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT s.*, u.username, u.nombre_completo, u.rol
            FROM sesiones s
            JOIN usuarios u ON s.usuario_id = u.id
            WHERE s.token = ?
        """, (token,))
        
        session = cursor.fetchone()
        
        if session:
            print("✅ Token encontrado en la base de datos:")
            print(f"  - ID: {session[0]}")
            print(f"  - Usuario: {session[6]} ({session[7]})")
            print(f"  - Activa: {session[4]}")
            print(f"  - Inicio: {session[2]}")
            print(f"  - Expira: {session[3]}")
            
            # Verificar si la sesión está activa y no expirada
            from datetime import datetime
            now = datetime.now()
            expira = datetime.fromisoformat(session[3].replace('Z', '+00:00'))
            
            if session[4] and now < expira:
                print("✅ Sesión válida y activa")
            else:
                print("❌ Sesión inactiva o expirada")
        else:
            print("❌ Token no encontrado en la base de datos")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error verificando token: {e}")

if __name__ == "__main__":
    print("🔧 VERIFICACIÓN DE SESIÓN EN BASE DE DATOS")
    print("=" * 50)
    
    verificar_sesion_db()
    
    # Si se proporciona un token como argumento, verificarlo
    if len(sys.argv) > 1:
        token = sys.argv[1]
        verificar_token_especifico(token)
    else:
        print("\n💡 Para verificar un token específico:")
        print("python scripts/verificar_sesion_db.py <token>") 