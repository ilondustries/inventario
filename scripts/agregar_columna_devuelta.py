#!/usr/bin/env python3
"""
Script para agregar la columna cantidad_devuelta a la tabla ticket_items
"""

import sqlite3
import os

def agregar_columna_devuelta():
    """Agregar la columna cantidad_devuelta a ticket_items"""
    
    # Conectar a la base de datos
    db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'almacen_desarrollo.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("🔧 Verificando estructura de tabla ticket_items...")
    
    # Verificar columnas existentes
    cursor.execute("PRAGMA table_info(ticket_items)")
    columnas = [col[1] for col in cursor.fetchall()]
    print(f"Columnas existentes: {columnas}")
    
    # Verificar si la columna ya existe
    if 'cantidad_devuelta' not in columnas:
        print("➕ Agregando columna cantidad_devuelta...")
        cursor.execute("ALTER TABLE ticket_items ADD COLUMN cantidad_devuelta INTEGER DEFAULT 0")
        print("✅ Columna cantidad_devuelta agregada exitosamente")
    else:
        print("✅ La columna cantidad_devuelta ya existe")
    
    # Verificar la nueva estructura
    cursor.execute("PRAGMA table_info(ticket_items)")
    columnas_nuevas = [col[1] for col in cursor.fetchall()]
    print(f"Columnas después del cambio: {columnas_nuevas}")
    
    conn.commit()
    conn.close()
    print("✅ Proceso completado")

if __name__ == "__main__":
    agregar_columna_devuelta() 