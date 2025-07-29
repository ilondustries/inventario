#!/usr/bin/env python3
"""
Diagnóstico simple de la base de datos main
"""

import sqlite3
import os

def diagnosticar_db_main():
    """Diagnosticar la base de datos main"""
    
    db_path = "data/almacen_main.db"
    
    print(f"🔍 Verificando archivo: {db_path}")
    print(f"📁 Existe: {os.path.exists(db_path)}")
    print(f"📏 Tamaño: {os.path.getsize(db_path)} bytes")
    
    try:
        print("🔗 Conectando a la base de datos...")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("✅ Conexión exitosa")
        
        # Verificar tablas existentes
        print("📋 Tablas existentes:")
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        for table in tables:
            print(f"  - {table[0]}")
        
        # Verificar estructura de tickets_compra
        if any('tickets_compra' in table for table in tables):
            print("\n📋 Estructura de tickets_compra:")
            cursor.execute("PRAGMA table_info(tickets_compra)")
            columns = cursor.fetchall()
            for col in columns:
                print(f"  {col[1]} ({col[2]}) - Default: {col[4]}")
        
        conn.close()
        print("✅ Diagnóstico completado")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    diagnosticar_db_main() 