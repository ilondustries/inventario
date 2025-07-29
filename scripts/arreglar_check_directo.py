#!/usr/bin/env python3
"""
Script para arreglar la restricción CHECK directamente usando SQL
"""

import sqlite3
import os
import sys

def arreglar_check_directo():
    """Arreglar la restricción CHECK directamente"""
    
    db_path = "data/almacen_main.db"
    
    if not os.path.exists(db_path):
        print(f"❌ Error: No se encontró la base de datos {db_path}")
        return False
    
    try:
        print(f"🔧 Conectando a {db_path}...")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Verificar la restricción actual
        print("🔍 Verificando restricción actual...")
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='tickets_compra'")
        create_statement = cursor.fetchone()
        
        if not create_statement:
            print("❌ No se encontró la tabla tickets_compra")
            return False
        
        current_sql = create_statement[0]
        print(f"📝 SQL actual: {current_sql}")
        
        # Verificar si ya tiene 'devuelto'
        if 'devuelto' in current_sql:
            print("✅ La restricción ya incluye 'devuelto'")
            return True
        
        # Reemplazar la restricción CHECK
        print("🔄 Actualizando restricción CHECK...")
        new_sql = current_sql.replace(
            "CHECK(estado IN ('pendiente', 'aprobado', 'rechazado', 'entregado'))",
            "CHECK(estado IN ('pendiente', 'aprobado', 'rechazado', 'entregado', 'devuelto'))"
        )
        
        if new_sql == current_sql:
            print("❌ No se pudo encontrar la restricción CHECK para reemplazar")
            return False
        
        print("📝 Nuevo SQL:")
        print(new_sql)
        
        # Eliminar la tabla y recrearla
        print("🗑️ Eliminando tabla original...")
        cursor.execute("DROP TABLE tickets_compra")
        
        print("📝 Recreando tabla con nueva restricción...")
        cursor.execute(new_sql)
        
        # Verificar que se aplicó correctamente
        print("✅ Verificando nueva restricción...")
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='tickets_compra'")
        new_create_statement = cursor.fetchone()
        
        if new_create_statement and 'devuelto' in new_create_statement[0]:
            print("✅ Restricción CHECK actualizada correctamente")
        else:
            print("❌ Error: La restricción no se actualizó correctamente")
            return False
        
        # Guardar cambios
        conn.commit()
        conn.close()
        
        print("🎉 ¡Base de datos main actualizada exitosamente!")
        print("✅ Ahora se puede usar el estado 'devuelto' en tickets")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Arreglando restricción CHECK directamente...")
    success = arreglar_check_directo()
    
    if success:
        print("✅ Script completado exitosamente")
    else:
        print("❌ Script falló")
        sys.exit(1) 