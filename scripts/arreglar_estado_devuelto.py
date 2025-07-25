#!/usr/bin/env python3
"""
Arreglar la restricción CHECK para incluir el estado 'devuelto'
"""

import sqlite3

def arreglar_estado_devuelto():
    """Agregar estado 'devuelto' a la restricción CHECK"""
    
    try:
        conn = sqlite3.connect('data/almacen_desarrollo.db')
        cursor = conn.cursor()
        
        print("🔧 Arreglando restricción CHECK para estado 'devuelto'...")
        
        # 1. Crear tabla temporal con la nueva restricción
        cursor.execute("""
            CREATE TABLE tickets_compra_temp (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                numero_ticket TEXT UNIQUE NOT NULL,
                orden_produccion TEXT,
                justificacion TEXT,
                solicitante_id INTEGER,
                solicitante_nombre TEXT,
                solicitante_rol TEXT,
                estado TEXT CHECK(estado IN ('pendiente', 'aprobado', 'rechazado', 'entregado', 'devuelto')),
                fecha_solicitud TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                fecha_aprobacion TIMESTAMP,
                aprobador_id INTEGER,
                aprobador_nombre TEXT,
                comentarios_aprobador TEXT,
                fecha_entrega TIMESTAMP,
                entregado_por_id INTEGER,
                entregado_por_nombre TEXT
            )
        """)
        
        # 2. Copiar datos de la tabla original
        cursor.execute("""
            INSERT INTO tickets_compra_temp 
            SELECT * FROM tickets_compra
        """)
        
        # 3. Eliminar tabla original
        cursor.execute("DROP TABLE tickets_compra")
        
        # 4. Renombrar tabla temporal
        cursor.execute("ALTER TABLE tickets_compra_temp RENAME TO tickets_compra")
        
        conn.commit()
        conn.close()
        
        print("✅ Restricción CHECK actualizada exitosamente")
        print("✅ Estado 'devuelto' ahora está permitido")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    arreglar_estado_devuelto() 