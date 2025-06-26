#!/usr/bin/env python3
"""
Script para agregar usuarios al Sistema de Almacén
"""

import sqlite3
import hashlib
import sys
from pathlib import Path

def hash_password(password):
    """Generar hash de contraseña"""
    return hashlib.sha256(password.encode()).hexdigest()

def agregar_usuario(username, password, nombre_completo, email, rol):
    """Agregar un nuevo usuario a la base de datos"""
    db_path = Path(__file__).parent.parent / "data" / "almacen.db"
    
    if not db_path.exists():
        print("❌ Error: No se encontró la base de datos")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Verificar si el usuario ya existe
        cursor.execute("SELECT username FROM usuarios WHERE username = ?", (username,))
        if cursor.fetchone():
            print(f"❌ Error: El usuario '{username}' ya existe")
            return False
        
        # Generar hash de la contraseña
        password_hash = hash_password(password)
        
        # Insertar usuario
        cursor.execute("""
            INSERT INTO usuarios (username, password_hash, nombre_completo, email, rol)
            VALUES (?, ?, ?, ?, ?)
        """, (username, password_hash, nombre_completo, email, rol))
        
        conn.commit()
        conn.close()
        
        print(f"✅ Usuario '{username}' agregado exitosamente")
        print(f"   Nombre: {nombre_completo}")
        print(f"   Rol: {rol}")
        print(f"   Contraseña: {password}")
        return True
        
    except Exception as e:
        print(f"❌ Error agregando usuario: {e}")
        return False

def listar_usuarios():
    """Listar todos los usuarios existentes"""
    db_path = Path(__file__).parent.parent / "data" / "almacen.db"
    
    if not db_path.exists():
        print("❌ Error: No se encontró la base de datos")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT username, nombre_completo, email, rol, activo, fecha_creacion
            FROM usuarios 
            ORDER BY username
        """)
        
        usuarios = cursor.fetchall()
        conn.close()
        
        if not usuarios:
            print("📋 No hay usuarios registrados")
            return
        
        print("📋 Usuarios registrados:")
        print("=" * 80)
        print(f"{'Usuario':<15} {'Nombre':<25} {'Email':<25} {'Rol':<12} {'Estado':<8}")
        print("=" * 80)
        
        for usuario in usuarios:
            estado = "✅ Activo" if usuario[4] else "❌ Inactivo"
            print(f"{usuario[0]:<15} {usuario[1]:<25} {usuario[2] or 'N/A':<25} {usuario[3]:<12} {estado:<8}")
        
    except Exception as e:
        print(f"❌ Error listando usuarios: {e}")

def main():
    print("🏪 Sistema de Almacén - Gestión de Usuarios")
    print("=" * 50)
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "listar":
            listar_usuarios()
            return
        elif sys.argv[1] == "agregar":
            if len(sys.argv) < 7:
                print("Uso: python agregar_usuarios.py agregar <username> <password> <nombre> <email> <rol>")
                return
            
            username = sys.argv[2]
            password = sys.argv[3]
            nombre = sys.argv[4]
            email = sys.argv[5]
            rol = sys.argv[6]
            
            if rol not in ['admin', 'supervisor', 'operador']:
                print("❌ Error: Rol debe ser 'admin', 'supervisor' o 'operador'")
                return
            
            agregar_usuario(username, password, nombre, email, rol)
            return
    
    # Modo interactivo
    print("1. Listar usuarios existentes")
    print("2. Agregar nuevo usuario")
    print("3. Agregar usuarios de turno (automático)")
    print("4. Salir")
    
    opcion = input("\nSelecciona una opción (1-4): ").strip()
    
    if opcion == "1":
        listar_usuarios()
    
    elif opcion == "2":
        print("\n📝 Agregar nuevo usuario:")
        username = input("Usuario: ").strip()
        password = input("Contraseña: ").strip()
        nombre = input("Nombre completo: ").strip()
        email = input("Email (opcional): ").strip() or None
        rol = input("Rol (admin/supervisor/operador): ").strip()
        
        if not all([username, password, nombre, rol]):
            print("❌ Error: Todos los campos son obligatorios excepto email")
            return
        
        if rol not in ['admin', 'supervisor', 'operador']:
            print("❌ Error: Rol inválido")
            return
        
        agregar_usuario(username, password, nombre, email, rol)
    
    elif opcion == "3":
        print("\n🔄 Agregando usuarios de turno...")
        
        # Usuario 1: Supervisor de turno mañana
        agregar_usuario(
            "supervisor_manana",
            "turno123",
            "María González - Supervisor Mañana",
            "maria.gonzalez@empresa.com",
            "supervisor"
        )
        
        # Usuario 2: Supervisor de turno tarde
        agregar_usuario(
            "supervisor_tarde", 
            "turno456",
            "Carlos Rodríguez - Supervisor Tarde",
            "carlos.rodriguez@empresa.com",
            "supervisor"
        )
        
        print("\n✅ Usuarios de turno agregados:")
        print("   Usuario: supervisor_manana / Contraseña: turno123")
        print("   Usuario: supervisor_tarde / Contraseña: turno456")
    
    elif opcion == "4":
        print("👋 ¡Hasta luego!")
    
    else:
        print("❌ Opción inválida")

if __name__ == "__main__":
    main() 