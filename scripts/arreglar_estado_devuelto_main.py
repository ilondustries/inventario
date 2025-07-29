#!/usr/bin/env python3
"""
Script para arreglar la restricción CHECK en la base de datos main
para permitir el estado 'devuelto' en tickets_compra
"""

import sqlite3
import os
import sys

def arreglar_estado_devuelto_main():
    """Arreglar la restricción CHECK en la base de datos main"""
    
    # Ruta de la base de datos main
    db_path = "data/almacen_main.db"
    
    if not os.path.exists(db_path):
        print(f"❌ Error: No se encontró la base de datos {db_path}")
        return False
    
    try:
        print(f"🔧 Conectando a {db_path}...")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Verificar la estructura actual de la tabla
        print("📋 Verificando estructura actual de tickets_compra...")
        cursor.execute("PRAGMA table_info(tickets_compra)")
        columns = cursor.fetchall()
        
        estado_column = None
        for col in columns:
            if col[1] == 'estado':
                estado_column = col
                break
        
        if not estado_column:
            print("❌ Error: No se encontró la columna 'estado' en tickets_compra")
            return False
        
        print(f"✅ Columna 'estado' encontrada: {estado_column}")
        
        # Verificar si ya tiene la restricción correcta
        if 'devuelto' in estado_column[4]:
            print("✅ La restricción CHECK ya incluye 'devuelto'")
            return True
        
        print("🔄 La restricción CHECK no incluye 'devuelto', actualizando...")
        
        # Crear tabla temporal con la nueva restricción
        print("📝 Creando tabla temporal con nueva restricción...")
        cursor.execute("""
            CREATE TABLE tickets_compra_temp (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                numero_ticket TEXT UNIQUE NOT NULL,
                solicitante_id INTEGER NOT NULL,
                solicitante_nombre TEXT NOT NULL,
                fecha_solicitud TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                fecha_aprobacion TIMESTAMP,
                fecha_entrega TIMESTAMP,
                fecha_devolucion TIMESTAMP,
                devuelto_por_nombre TEXT,
                aprobador_id INTEGER,
                aprobador_nombre TEXT,
                estado TEXT CHECK(estado IN ('pendiente', 'aprobado', 'rechazado', 'entregado', 'devuelto')) DEFAULT 'pendiente',
                observaciones TEXT,
                FOREIGN KEY (solicitante_id) REFERENCES usuarios (id),
                FOREIGN KEY (aprobador_id) REFERENCES usuarios (id)
            )
        """)
        
        # Copiar datos existentes
        print("📋 Copiando datos existentes...")
        cursor.execute("""
            INSERT INTO tickets_compra_temp 
            SELECT * FROM tickets_compra
        """)
        
        # Eliminar tabla original
        print("🗑️ Eliminando tabla original...")
        cursor.execute("DROP TABLE tickets_compra")
        
        # Renombrar tabla temporal
        print("🔄 Renombrando tabla temporal...")
        cursor.execute("ALTER TABLE tickets_compra_temp RENAME TO tickets_compra")
        
        # Verificar que se aplicó correctamente
        print("✅ Verificando nueva restricción...")
        cursor.execute("PRAGMA table_info(tickets_compra)")
        columns = cursor.fetchall()
        
        for col in columns:
            if col[1] == 'estado':
                if 'devuelto' in col[4]:
                    print("✅ Restricción CHECK actualizada correctamente")
                    break
                else:
                    print("❌ Error: La restricción no se actualizó correctamente")
                    return False
        
        # Guardar cambios
        conn.commit()
        conn.close()
        
        print("🎉 ¡Base de datos main actualizada exitosamente!")
        print("✅ Ahora se puede usar el estado 'devuelto' en tickets")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Arreglando restricción CHECK en base de datos main...")
    success = arreglar_estado_devuelto_main()
    
    if success:
        print("✅ Script completado exitosamente")
    else:
        print("❌ Script falló")
        sys.exit(1) 