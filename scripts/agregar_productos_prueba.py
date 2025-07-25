#!/usr/bin/env python3
"""
Agregar productos de prueba a la base de datos de desarrollo
"""

import sqlite3
from datetime import datetime

def agregar_productos_prueba():
    """Agregar productos de prueba para testing"""
    
    productos_prueba = [
        {
            "nombre": "DESTORNILLADOR PHILLIPS",
            "descripcion": "Destornillador Phillips de prueba",
            "categoria": "HERRAMIENTAS",
            "cantidad": 10,
            "cantidad_minima": 2,
            "ubicacion": "A1-B1-C1",
            "precio_unitario": 25.50
        },
        {
            "nombre": "MARTILLO 500G",
            "descripcion": "Martillo de 500g de prueba",
            "categoria": "HERRAMIENTAS", 
            "cantidad": 5,
            "cantidad_minima": 1,
            "ubicacion": "A2-B2-C2",
            "precio_unitario": 45.00
        },
        {
            "nombre": "LLAVE AJUSTABLE 10\"",
            "descripcion": "Llave ajustable de 10 pulgadas",
            "categoria": "HERRAMIENTAS",
            "cantidad": 8,
            "cantidad_minima": 2,
            "ubicacion": "A3-B3-C3",
            "precio_unitario": 35.75
        }
    ]
    
    try:
        conn = sqlite3.connect('data/almacen_desarrollo.db')
        cursor = conn.cursor()
        
        print("📦 Agregando productos de prueba...")
        
        for i, producto in enumerate(productos_prueba, 1):
            # Generar código de barras automático
            codigo_barras = f"{i:012d}"
            
            cursor.execute("""
                INSERT INTO productos (
                    codigo_barras, nombre, descripcion, cantidad, 
                    cantidad_minima, ubicacion, categoria, precio_unitario,
                    fecha_creacion, fecha_actualizacion
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                codigo_barras,
                producto["nombre"],
                producto["descripcion"],
                producto["cantidad"],
                producto["cantidad_minima"],
                producto["ubicacion"],
                producto["categoria"],
                producto["precio_unitario"],
                datetime.now().isoformat(),
                datetime.now().isoformat()
            ))
            
            producto_id = cursor.lastrowid
            
            # Generar código QR
            codigo_qr = f"ID:{producto_id}|Nombre:{producto['nombre']}"
            cursor.execute("""
                UPDATE productos SET codigo_qr = ? WHERE id = ?
            """, (codigo_qr, producto_id))
            
            print(f"✅ {producto['nombre']} - ID: {producto_id}")
        
        conn.commit()
        conn.close()
        
        print(f"\n🎉 {len(productos_prueba)} productos de prueba agregados exitosamente!")
        print("📋 Productos disponibles para testing:")
        for i, producto in enumerate(productos_prueba, 1):
            print(f"   {i}. {producto['nombre']} (ID: {i})")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    agregar_productos_prueba() 