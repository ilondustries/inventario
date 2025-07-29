#!/usr/bin/env python3
"""
Script para verificar la estructura exacta de la tabla tickets_compra
"""

import sqlite3
import os

def verificar_estructura_tickets():
    """Verificar la estructura exacta de tickets_compra"""
    
    db_path = "data/almacen_main.db"
    
    if not os.path.exists(db_path):
        print(f"❌ Error: No se encontró la base de datos {db_path}")
        return
    
    try:
        print(f"🔧 Conectando a {db_path}...")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Obtener información de la tabla
        print("📋 Estructura de tickets_compra:")
        cursor.execute("PRAGMA table_info(tickets_compra)")
        columns = cursor.fetchall()
        
        for i, col in enumerate(columns):
            print(f"  {i+1}. {col[1]} ({col[2]}) - Default: {col[4]} - PK: {col[5]}")
        
        # Obtener el CREATE TABLE statement
        print("\n📝 CREATE TABLE statement:")
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='tickets_compra'")
        create_statement = cursor.fetchone()
        if create_statement:
            print(create_statement[0])
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    verificar_estructura_tickets() 