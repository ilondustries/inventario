#!/usr/bin/env python3
"""
Script para verificar todas las acciones diferentes en el historial
"""

import sqlite3
import os

def verificar_acciones_historial():
    """Verificar todas las acciones diferentes en el historial"""
    
    # Conectar a la base de datos
    db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'almacen_desarrollo.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    print("🔍 Verificando acciones en el historial...")
    print("=" * 50)
    
    # Obtener todas las acciones diferentes
    cursor.execute("""
        SELECT DISTINCT accion, COUNT(*) as cantidad
        FROM historial 
        GROUP BY accion 
        ORDER BY cantidad DESC
    """)
    
    acciones = cursor.fetchall()
    print(f"📊 Acciones encontradas ({len(acciones)} tipos):")
    
    for accion in acciones:
        print(f"  - {accion['accion']}: {accion['cantidad']} registros")
    
    print()
    
    # Verificar devoluciones específicamente
    cursor.execute("""
        SELECT accion, COUNT(*) as cantidad
        FROM historial 
        WHERE accion LIKE '%devolucion%'
        GROUP BY accion
    """)
    
    devoluciones = cursor.fetchall()
    print(f"📦 Devoluciones encontradas ({len(devoluciones)} tipos):")
    
    for dev in devoluciones:
        print(f"  - {dev['accion']}: {dev['cantidad']} registros")
    
    conn.close()
    print("=" * 50)

if __name__ == "__main__":
    verificar_acciones_historial() 