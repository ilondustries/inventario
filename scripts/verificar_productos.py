#!/usr/bin/env python3
"""
Script para verificar productos en la base de datos
"""

import sqlite3
import os
import sys

# Agregar el directorio padre al path para importar módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def verificar_productos():
    """Verificar todos los productos en la base de datos"""
    try:
        # Conectar a la base de datos
        db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "almacen.db")
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Obtener todos los productos
        cursor.execute("""
            SELECT id, codigo_barras, nombre, descripcion, cantidad, 
                   cantidad_minima, ubicacion, categoria, precio_unitario
            FROM productos 
            ORDER BY id
        """)
        
        productos = cursor.fetchall()
        
        print(f"📦 Total de productos en la base de datos: {len(productos)}")
        print("=" * 80)
        
        if not productos:
            print("❌ No hay productos en la base de datos")
            return
        
        for producto in productos:
            print(f"ID: {producto['id']:2d} | Nombre: {producto['nombre']:<20} | Código: {producto['codigo_barras'] or 'N/A':<15} | Cantidad: {producto['cantidad']}")
        
        print("=" * 80)
        
        # Verificar productos específicos
        print("\n🔍 Verificando productos específicos:")
        
        # Buscar producto con ID 8
        cursor.execute("SELECT * FROM productos WHERE id = ?", (8,))
        producto_8 = cursor.fetchone()
        if producto_8:
            print(f"✅ Producto ID 8 encontrado: {producto_8['nombre']}")
        else:
            print("❌ Producto ID 8 NO encontrado")
        
        # Buscar producto con ID 7
        cursor.execute("SELECT * FROM productos WHERE id = ?", (7,))
        producto_7 = cursor.fetchone()
        if producto_7:
            print(f"✅ Producto ID 7 encontrado: {producto_7['nombre']}")
        else:
            print("❌ Producto ID 7 NO encontrado")
        
        # Buscar por nombre "Popote"
        cursor.execute("SELECT * FROM productos WHERE nombre LIKE ?", ("%Popote%",))
        popote = cursor.fetchone()
        if popote:
            print(f"✅ Producto 'Popote' encontrado: ID {popote['id']}")
        else:
            print("❌ Producto 'Popote' NO encontrado")
        
        # Buscar por nombre "Huelo"
        cursor.execute("SELECT * FROM productos WHERE nombre LIKE ?", ("%Huelo%",))
        huelo = cursor.fetchone()
        if huelo:
            print(f"✅ Producto 'Huelo' encontrado: ID {huelo['id']}")
        else:
            print("❌ Producto 'Huelo' NO encontrado")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error verificando productos: {e}")

if __name__ == "__main__":
    verificar_productos() 