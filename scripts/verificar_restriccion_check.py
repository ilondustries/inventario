#!/usr/bin/env python3
"""
Script para verificar específicamente la restricción CHECK de la columna estado
"""

import sqlite3
import os

def verificar_restriccion_check():
    """Verificar la restricción CHECK de la columna estado"""
    
    db_path = "data/almacen_main.db"
    
    try:
        print(f"🔧 Conectando a {db_path}...")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Obtener el CREATE TABLE statement completo
        print("📝 CREATE TABLE statement de tickets_compra:")
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='tickets_compra'")
        create_statement = cursor.fetchone()
        if create_statement:
            print(create_statement[0])
        else:
            print("❌ No se encontró la tabla tickets_compra")
            return
        
        # Verificar específicamente la columna estado
        print("\n🔍 Información específica de la columna 'estado':")
        cursor.execute("PRAGMA table_info(tickets_compra)")
        columns = cursor.fetchall()
        
        for col in columns:
            if col[1] == 'estado':
                print(f"  Nombre: {col[1]}")
                print(f"  Tipo: {col[2]}")
                print(f"  NOT NULL: {col[3]}")
                print(f"  Default: {col[4]}")
                print(f"  PK: {col[5]}")
                
                # Verificar si incluye 'devuelto'
                if col[4] and 'devuelto' in col[4]:
                    print("✅ La restricción CHECK incluye 'devuelto'")
                else:
                    print("❌ La restricción CHECK NO incluye 'devuelto'")
                break
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    verificar_restriccion_check() 