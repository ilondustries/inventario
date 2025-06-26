#!/usr/bin/env python3
"""
Script para limpiar y optimizar la base de datos del Sistema de Almacén
"""

import sqlite3
import os
from pathlib import Path

def limpiar_base_datos():
    """Limpiar y optimizar la base de datos"""
    db_path = Path(__file__).parent.parent / "data" / "almacen.db"
    
    if not db_path.exists():
        print("❌ Error: No se encontró la base de datos")
        return False
    
    try:
        print("🔧 Limpiando y optimizando base de datos...")
        
        # Conectar con timeout extendido
        conn = sqlite3.connect(db_path, timeout=30.0)
        cursor = conn.cursor()
        
        # Configurar para mejor rendimiento
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA cache_size=10000")
        cursor.execute("PRAGMA temp_store=MEMORY")
        cursor.execute("PRAGMA optimize")
        
        # Limpiar sesiones expiradas
        cursor.execute("DELETE FROM sesiones WHERE fecha_expiracion < CURRENT_TIMESTAMP")
        sesiones_limpiadas = cursor.rowcount
        
        # Limpiar sesiones inactivas antiguas (más de 24 horas)
        cursor.execute("DELETE FROM sesiones WHERE activa = 0 AND fecha_inicio < datetime('now', '-1 day')")
        sesiones_antiguas = cursor.rowcount
        
        conn.commit()  # Commit antes de VACUUM
        conn.close()
        
        # VACUUM y ANALYZE en nueva conexión
        conn2 = sqlite3.connect(db_path, timeout=30.0)
        cursor2 = conn2.cursor()
        cursor2.execute("VACUUM")
        cursor2.execute("ANALYZE")
        conn2.commit()
        conn2.close()
        
        print(f"✅ Base de datos optimizada exitosamente")
        print(f"   Sesiones expiradas eliminadas: {sesiones_limpiadas}")
        print(f"   Sesiones antiguas eliminadas: {sesiones_antiguas}")
        print(f"   Base de datos optimizada y compactada")
        
        return True
        
    except Exception as e:
        print(f"❌ Error optimizando base de datos: {e}")
        return False

def verificar_estado_bd():
    """Verificar el estado de la base de datos"""
    db_path = Path(__file__).parent.parent / "data" / "almacen.db"
    
    if not db_path.exists():
        print("❌ Error: No se encontró la base de datos")
        return
    
    try:
        conn = sqlite3.connect(db_path, timeout=10.0)
        cursor = conn.cursor()
        
        # Información general
        cursor.execute("PRAGMA database_list")
        db_info = cursor.fetchone()
        
        # Tamaño de la base de datos
        db_size = db_path.stat().st_size / (1024 * 1024)  # MB
        
        # Contar registros
        cursor.execute("SELECT COUNT(*) FROM usuarios")
        usuarios = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM sesiones WHERE activa = 1")
        sesiones_activas = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM productos")
        productos = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM historial")
        historial = cursor.fetchone()[0]
        
        conn.close()
        
        print("📊 Estado de la Base de Datos:")
        print("=" * 40)
        print(f"📁 Ubicación: {db_path}")
        print(f"📏 Tamaño: {db_size:.2f} MB")
        print(f"👥 Usuarios: {usuarios}")
        print(f"🔐 Sesiones activas: {sesiones_activas}")
        print(f"📦 Productos: {productos}")
        print(f"📝 Registros en historial: {historial}")
        
    except Exception as e:
        print(f"❌ Error verificando base de datos: {e}")

def forzar_limpieza():
    """Forzar limpieza incluso si hay bloqueos"""
    db_path = Path(__file__).parent.parent / "data" / "almacen.db"
    
    if not db_path.exists():
        print("❌ Error: No se encontró la base de datos")
        return False
    
    try:
        print("⚠️  Forzando limpieza de base de datos...")
        
        # Crear backup antes de la limpieza
        backup_path = db_path.with_suffix('.db.backup')
        import shutil
        shutil.copy2(db_path, backup_path)
        print(f"✅ Backup creado: {backup_path}")
        
        # Intentar conectar con timeout muy largo
        conn = sqlite3.connect(db_path, timeout=60.0)
        cursor = conn.cursor()
        
        # Forzar WAL mode
        cursor.execute("PRAGMA journal_mode=DELETE")
        cursor.execute("PRAGMA journal_mode=WAL")
        
        # Limpiar todo
        cursor.execute("DELETE FROM sesiones WHERE activa = 0")
        cursor.execute("DELETE FROM sesiones WHERE fecha_expiracion < CURRENT_TIMESTAMP")
        
        # Optimizar
        cursor.execute("VACUUM")
        cursor.execute("ANALYZE")
        
        conn.commit()
        conn.close()
        
        print("✅ Limpieza forzada completada")
        return True
        
    except Exception as e:
        print(f"❌ Error en limpieza forzada: {e}")
        return False

def main():
    print("🏪 Sistema de Almacén - Limpieza de Base de Datos")
    print("=" * 50)
    
    print("1. Verificar estado de la base de datos")
    print("2. Limpiar y optimizar base de datos")
    print("3. Forzar limpieza (si hay bloqueos)")
    print("4. Salir")
    
    opcion = input("\nSelecciona una opción (1-4): ").strip()
    
    if opcion == "1":
        verificar_estado_bd()
    
    elif opcion == "2":
        if limpiar_base_datos():
            print("\n✅ Limpieza completada. El servidor debería funcionar mejor ahora.")
        else:
            print("\n❌ Error en la limpieza. Intenta la opción 3.")
    
    elif opcion == "3":
        print("\n⚠️  ADVERTENCIA: Esta opción puede tomar más tiempo")
        confirmacion = input("¿Continuar? (s/n): ").lower()
        
        if confirmacion == 's':
            if forzar_limpieza():
                print("\n✅ Limpieza forzada completada.")
            else:
                print("\n❌ Error en limpieza forzada.")
        else:
            print("Operación cancelada")
    
    elif opcion == "4":
        print("👋 ¡Hasta luego!")
    
    else:
        print("❌ Opción inválida")

if __name__ == "__main__":
    main() 