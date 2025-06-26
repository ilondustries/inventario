#!/usr/bin/env python3
"""
Script para diagnosticar problemas con la base de datos
"""

import sqlite3
import os
from pathlib import Path

def check_database():
    """Verificar el estado de la base de datos"""
    db_path = Path(__file__).parent.parent / "data" / "almacen.db"
    
    print("🔍 Diagnóstico de Base de Datos")
    print("=" * 40)
    
    # Verificar si existe el archivo
    if not db_path.exists():
        print(f"❌ No se encontró la base de datos en: {db_path}")
        return False
    
    print(f"✅ Base de datos encontrada: {db_path}")
    print(f"📊 Tamaño: {db_path.stat().st_size} bytes")
    
    try:
        # Conectar a la base de datos
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Verificar tablas
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        print(f"\n📋 Tablas encontradas: {len(tables)}")
        for table in tables:
            print(f"   - {table[0]}")
        
        # Verificar tabla productos
        if ('productos',) in tables:
            cursor.execute("PRAGMA table_info(productos)")
            columns = cursor.fetchall()
            print(f"\n📦 Estructura de tabla 'productos':")
            for col in columns:
                print(f"   - {col[1]} ({col[2]})")
            
            # Contar productos
            cursor.execute("SELECT COUNT(*) FROM productos")
            count = cursor.fetchone()[0]
            print(f"   📊 Total de productos: {count}")
        
        # Verificar tabla historial
        if ('historial',) in tables:
            cursor.execute("SELECT COUNT(*) FROM historial")
            count = cursor.fetchone()[0]
            print(f"   📊 Total de registros en historial: {count}")
        
        # Verificar permisos de escritura
        try:
            cursor.execute("CREATE TABLE IF NOT EXISTS test_write (id INTEGER)")
            cursor.execute("DROP TABLE test_write")
            print("\n✅ Permisos de escritura: OK")
        except Exception as e:
            print(f"\n❌ Error de permisos de escritura: {e}")
        
        conn.close()
        print("\n✅ Diagnóstico completado exitosamente")
        return True
        
    except Exception as e:
        print(f"\n❌ Error al conectar con la base de datos: {e}")
        return False

def reset_database():
    """Reiniciar la base de datos (CUIDADO: borra todos los datos)"""
    db_path = Path(__file__).parent.parent / "data" / "almacen.db"
    
    print("\n⚠️  ADVERTENCIA: Esto borrará todos los datos existentes")
    response = input("¿Estás seguro? (escribe 'SI' para confirmar): ")
    
    if response != "SI":
        print("Operación cancelada")
        return
    
    try:
        # Hacer backup
        backup_path = db_path.with_suffix('.db.backup')
        if db_path.exists():
            import shutil
            shutil.copy2(db_path, backup_path)
            print(f"✅ Backup creado: {backup_path}")
        
        # Eliminar base de datos
        if db_path.exists():
            db_path.unlink()
            print("🗑️  Base de datos eliminada")
        
        print("✅ Base de datos reiniciada. Ejecuta el servidor para recrearla.")
        
    except Exception as e:
        print(f"❌ Error al reiniciar base de datos: {e}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--reset":
        reset_database()
    else:
        check_database() 