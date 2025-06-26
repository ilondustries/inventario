#!/usr/bin/env python3
"""
Script para cerrar todas las sesiones activas del Sistema de Almacén
"""

import sqlite3
from pathlib import Path

def cerrar_todas_sesiones():
    """Cerrar todas las sesiones activas"""
    db_path = Path(__file__).parent.parent / "data" / "almacen.db"
    
    if not db_path.exists():
        print("❌ Error: No se encontró la base de datos")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Contar sesiones activas antes
        cursor.execute("SELECT COUNT(*) FROM sesiones WHERE activa = 1")
        sesiones_antes = cursor.fetchone()[0]
        
        # Cerrar todas las sesiones activas
        cursor.execute("UPDATE sesiones SET activa = 0 WHERE activa = 1")
        
        # Contar sesiones activas después
        cursor.execute("SELECT COUNT(*) FROM sesiones WHERE activa = 1")
        sesiones_despues = cursor.fetchone()[0]
        
        conn.commit()
        conn.close()
        
        print(f"✅ Sesiones cerradas exitosamente")
        print(f"   Sesiones activas antes: {sesiones_antes}")
        print(f"   Sesiones activas después: {sesiones_despues}")
        print(f"   Sesiones cerradas: {sesiones_antes - sesiones_despues}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error cerrando sesiones: {e}")
        return False

def listar_sesiones_activas():
    """Listar todas las sesiones activas"""
    db_path = Path(__file__).parent.parent / "data" / "almacen.db"
    
    if not db_path.exists():
        print("❌ Error: No se encontró la base de datos")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT s.id, s.token, s.fecha_inicio, s.fecha_expiracion, s.ip_address,
                   u.username, u.nombre_completo
            FROM sesiones s
            JOIN usuarios u ON s.usuario_id = u.id
            WHERE s.activa = 1
            ORDER BY s.fecha_inicio DESC
        """)
        
        sesiones = cursor.fetchall()
        conn.close()
        
        if not sesiones:
            print("📋 No hay sesiones activas")
            return
        
        print("📋 Sesiones activas:")
        print("=" * 80)
        print(f"{'ID':<5} {'Usuario':<15} {'IP':<15} {'Inicio':<20} {'Expira':<20}")
        print("=" * 80)
        
        for sesion in sesiones:
            print(f"{sesion[0]:<5} {sesion[5]:<15} {sesion[4] or 'N/A':<15} {sesion[2]:<20} {sesion[3]:<20}")
        
    except Exception as e:
        print(f"❌ Error listando sesiones: {e}")

def main():
    print("🏪 Sistema de Almacén - Gestión de Sesiones")
    print("=" * 50)
    
    print("1. Listar sesiones activas")
    print("2. Cerrar todas las sesiones")
    print("3. Salir")
    
    opcion = input("\nSelecciona una opción (1-3): ").strip()
    
    if opcion == "1":
        listar_sesiones_activas()
    
    elif opcion == "2":
        print("\n⚠️  ADVERTENCIA: Esto cerrará TODAS las sesiones activas")
        confirmacion = input("¿Estás seguro? (escribe 'SI' para confirmar): ")
        
        if confirmacion == "SI":
            cerrar_todas_sesiones()
        else:
            print("Operación cancelada")
    
    elif opcion == "3":
        print("👋 ¡Hasta luego!")
    
    else:
        print("❌ Opción inválida")

if __name__ == "__main__":
    main() 