#!/usr/bin/env python3
"""
Script para agregar usuarios de operador y supervisor al sistema
"""

import sqlite3
import hashlib
import os

def hash_password(password):
    """Generar hash de contraseña"""
    return hashlib.sha256(password.encode()).hexdigest()

def agregar_usuarios():
    """Agregar usuarios de operador y supervisor"""
    
    # Ruta de la base de datos
    db_path = "data/almacen.db"
    
    if not os.path.exists(db_path):
        print("❌ Base de datos no encontrada")
        return False
    
    try:
        # Conectar a la base de datos
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔄 Agregando usuarios al sistema...")
        
        # Verificar si la tabla usuarios existe
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='usuarios'")
        if not cursor.fetchone():
            print("❌ Tabla usuarios no existe")
            return False
        
        # Lista de usuarios a agregar
        usuarios = [
            {
                "username": "operador",
                "password": "oper123",
                "nombre_completo": "Operador del Sistema",
                "rol": "operador",
                "email": "operador@longoria.com"
            },
            {
                "username": "supervisor",
                "password": "super123",
                "nombre_completo": "Supervisor de Producción",
                "rol": "supervisor",
                "email": "supervisor@longoria.com"
            }
        ]
        
        usuarios_agregados = 0
        
        for usuario in usuarios:
            # Verificar si el usuario ya existe
            cursor.execute("SELECT id FROM usuarios WHERE username = ?", (usuario["username"],))
            if cursor.fetchone():
                print(f"⚠️  Usuario {usuario['username']} ya existe, saltando...")
                continue
            
            # Generar hash de la contraseña
            password_hash = hash_password(usuario["password"])
            
            # Insertar usuario
            cursor.execute("""
                INSERT INTO usuarios (username, password_hash, nombre_completo, rol, email, fecha_creacion)
                VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (
                usuario["username"],
                password_hash,
                usuario["nombre_completo"],
                usuario["rol"],
                usuario["email"]
            ))
            
            usuarios_agregados += 1
            print(f"✅ Usuario {usuario['username']} agregado exitosamente")
            print(f"   Rol: {usuario['rol']}")
            print(f"   Contraseña: {usuario['password']}")
            print(f"   Nombre: {usuario['nombre_completo']}")
            print()
        
        # Confirmar cambios
        conn.commit()
        conn.close()
        
        if usuarios_agregados > 0:
            print(f"✅ {usuarios_agregados} usuarios agregados exitosamente")
            print("\n📋 Resumen de credenciales:")
            print("=" * 40)
            for usuario in usuarios:
                print(f"Usuario: {usuario['username']}")
                print(f"Contraseña: {usuario['password']}")
                print(f"Rol: {usuario['rol']}")
                print("-" * 20)
        else:
            print("ℹ️  Todos los usuarios ya existían en el sistema")
        
        return True
        
    except Exception as e:
        print(f"❌ Error agregando usuarios: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return False

if __name__ == "__main__":
    print("👥 Script para Agregar Usuarios")
    print("=" * 40)
    
    if agregar_usuarios():
        print("\n✅ Proceso completado exitosamente")
    else:
        print("\n❌ Error en el proceso") 