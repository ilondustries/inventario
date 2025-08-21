#!/usr/bin/env python3
"""
Script de migración para agregar la columna comentarios_entrega
a la tabla tickets_compra después de eliminar el estado 'aprobado'
"""

import sqlite3
import os
import shutil
from datetime import datetime

def backup_database():
    """Crear backup de la base de datos actual"""
    db_path = "../data/almacen_main.db"
    if os.path.exists(db_path):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"../data/almacen_main_backup_{timestamp}.db"
        shutil.copy2(db_path, backup_path)
        print(f"✅ Backup creado: {backup_path}")
        return True
    else:
        print("❌ No se encontró la base de datos")
        return False

def add_comentarios_entrega_column():
    """Agregar la columna comentarios_entrega a tickets_compra"""
    try:
        conn = sqlite3.connect("../data/almacen_main.db")
        cursor = conn.cursor()
        
        # Verificar si la columna ya existe
        cursor.execute("PRAGMA table_info(tickets_compra)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'comentarios_entrega' not in columns:
            # Agregar la columna comentarios_entrega
            cursor.execute("""
                ALTER TABLE tickets_compra 
                ADD COLUMN comentarios_entrega TEXT
            """)
            print("✅ Columna comentarios_entrega agregada")
        else:
            print("ℹ️ La columna comentarios_entrega ya existe")
        
        # Verificar la estructura final
        cursor.execute("PRAGMA table_info(tickets_compra)")
        print("\n📋 Estructura actual de tickets_compra:")
        for column in cursor.fetchall():
            print(f"  - {column[1]} ({column[2]})")
        
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error durante la migración: {e}")
        return False

def main():
    """Función principal de migración"""
    print("🚀 Iniciando migración de base de datos...")
    print("=" * 50)
    
    # Crear backup
    if not backup_database():
        return
    
    # Agregar columna comentarios_entrega
    if add_comentarios_entrega_column():
        print("\n✅ Migración completada exitosamente")
        print("🔄 Reinicia el servidor para aplicar los cambios")
    else:
        print("\n❌ La migración falló")

if __name__ == "__main__":
    main()












