#!/usr/bin/env python3
"""
Script para migrar la base de datos y eliminar el estado 'aprobado'
- Elimina campos relacionados con aprobación
- Convierte tickets 'aprobado' a 'pendiente' para que puedan ser entregados
- Actualiza la estructura de la tabla tickets_compra
"""

import sqlite3
import os
import sys
from datetime import datetime

def get_db_path():
    """Obtiene la ruta de la base de datos según la variable de entorno BRANCH"""
    branch = os.environ.get('BRANCH', 'main')
    if branch == 'desarrollo':
        return 'almacen_desarrollo.db'
    else:
        return 'almacen_main.db'

def backup_database(db_path):
    """Crea una copia de seguridad de la base de datos"""
    backup_path = f"{db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    if os.path.exists(db_path):
        import shutil
        shutil.copy2(db_path, backup_path)
        print(f"✅ Backup creado: {backup_path}")
        return backup_path
    return None

def migrate_database(db_path):
    """Ejecuta la migración de la base de datos"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        print(f"🔄 Iniciando migración en: {db_path}")
        
        # 1. Verificar estructura actual
        cursor.execute("PRAGMA table_info(tickets_compra)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        print(f"📋 Columnas actuales: {column_names}")
        
        # 2. Convertir tickets 'aprobado' a 'pendiente'
        cursor.execute("""
            UPDATE tickets_compra 
            SET estado = 'pendiente' 
            WHERE estado = 'aprobado'
        """)
        aprobados_convertidos = cursor.rowcount
        print(f"🔄 Tickets 'aprobado' convertidos a 'pendiente': {aprobados_convertidos}")
        
        # 3. Eliminar campos de aprobación si existen
        campos_a_eliminar = ['fecha_aprobacion', 'aprobador_id', 'aprobador_nombre', 'comentarios_aprobador']
        
        for campo in campos_a_eliminar:
            if campo in column_names:
                try:
                    cursor.execute(f"ALTER TABLE tickets_compra DROP COLUMN {campo}")
                    print(f"🗑️ Columna eliminada: {campo}")
                except sqlite3.OperationalError as e:
                    print(f"⚠️ No se pudo eliminar {campo}: {e}")
        
        # 4. Actualizar la restricción CHECK del estado
        try:
            # Crear tabla temporal con nueva estructura
            cursor.execute("""
                CREATE TABLE tickets_compra_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    numero_ticket TEXT UNIQUE NOT NULL,
                    orden_produccion TEXT NOT NULL,
                    justificacion TEXT NOT NULL,
                    solicitante_id INTEGER NOT NULL,
                    solicitante_nombre TEXT NOT NULL,
                    solicitante_rol TEXT NOT NULL,
                    estado TEXT DEFAULT 'pendiente' CHECK (estado IN ('pendiente', 'entregado', 'devuelto')),
                    fecha_solicitud TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    fecha_entrega TIMESTAMP,
                    entregado_por_id INTEGER,
                    entregado_por_nombre TEXT,
                    comentarios_entrega TEXT
                )
            """)
            
            # Copiar datos existentes
            cursor.execute("""
                INSERT INTO tickets_compra_new 
                SELECT 
                    id, numero_ticket, orden_produccion, justificacion,
                    solicitante_id, solicitante_nombre, solicitante_rol, estado,
                    fecha_solicitud, fecha_entrega, entregado_por_id,
                    entregado_por_nombre, comentarios_entrega
                FROM tickets_compra
            """)
            
            # Eliminar tabla antigua y renombrar la nueva
            cursor.execute("DROP TABLE tickets_compra")
            cursor.execute("ALTER TABLE tickets_compra_new RENAME TO tickets_compra")
            
            print("✅ Estructura de tabla actualizada")
            
        except sqlite3.OperationalError as e:
            print(f"⚠️ No se pudo actualizar la estructura: {e}")
            print("La migración continuará con la estructura actual")
        
        # 5. Verificar resultado
        cursor.execute("SELECT estado, COUNT(*) FROM tickets_compra GROUP BY estado")
        estados_finales = cursor.fetchall()
        
        print("\n📊 Estado final de tickets:")
        for estado, cantidad in estados_finales:
            print(f"  - {estado}: {cantidad}")
        
        # 6. Verificar que no queden referencias a 'aprobado'
        cursor.execute("SELECT COUNT(*) FROM tickets_compra WHERE estado = 'aprobado'")
        aprobados_restantes = cursor.fetchone()[0]
        
        if aprobados_restantes == 0:
            print("✅ Migración completada exitosamente")
        else:
            print(f"⚠️ Aún quedan {aprobados_restantes} tickets con estado 'aprobado'")
        
        conn.commit()
        
    except Exception as e:
        print(f"❌ Error durante la migración: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

def main():
    """Función principal"""
    print("🚀 Script de migración para eliminar estado 'aprobado'")
    print("=" * 60)
    
    # Obtener ruta de la base de datos
    db_path = get_db_path()
    
    if not os.path.exists(db_path):
        print(f"❌ Base de datos no encontrada: {db_path}")
        print("Asegúrate de ejecutar este script desde el directorio backend/")
        sys.exit(1)
    
    print(f"📁 Base de datos: {db_path}")
    
    # Crear backup
    backup_path = backup_database(db_path)
    
    # Confirmar antes de continuar
    if backup_path:
        print(f"\n⚠️ Se creará un backup en: {backup_path}")
    
    respuesta = input("\n¿Continuar con la migración? (s/N): ").strip().lower()
    if respuesta not in ['s', 'si', 'sí', 'y', 'yes']:
        print("❌ Migración cancelada")
        sys.exit(0)
    
    try:
        migrate_database(db_path)
        print("\n🎉 Migración completada exitosamente!")
        print(f"💾 Backup disponible en: {backup_path}")
        
    except Exception as e:
        print(f"\n❌ Error durante la migración: {e}")
        if backup_path and os.path.exists(backup_path):
            print(f"🔄 Puedes restaurar desde el backup: {backup_path}")
        sys.exit(1)

if __name__ == "__main__":
    main()
