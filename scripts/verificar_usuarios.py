#!/usr/bin/env python3
"""
Verificar usuarios en la base de datos de desarrollo
"""

import sqlite3

def verificar_usuarios():
    """Verificar usuarios disponibles"""
    
    try:
        conn = sqlite3.connect('data/almacen_desarrollo.db')
        cursor = conn.cursor()
        
        print("👥 Usuarios en base de datos de desarrollo:")
        print("=" * 40)
        
        cursor.execute("SELECT id, username, nombre_completo, rol FROM usuarios")
        usuarios = cursor.fetchall()
        
        if usuarios:
            for usuario in usuarios:
                print(f"   - ID: {usuario[0]}, Usuario: {usuario[1]}, Nombre: {usuario[2]}, Rol: {usuario[3]}")
        else:
            print("   ❌ No hay usuarios en la base de datos")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    verificar_usuarios() 