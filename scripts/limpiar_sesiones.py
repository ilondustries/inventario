#!/usr/bin/env python3
"""
Script para limpiar sesiones expiradas
"""
import sqlite3
import os
from datetime import datetime, timezone

def limpiar_sesiones_expiradas():
    """Limpiar sesiones expiradas de la base de datos"""
    print("🧹 Limpiando sesiones expiradas...")
    
    db_path = os.path.join(os.path.dirname(__file__), "..", "data", "almacen.db")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Contar sesiones antes de limpiar
        cursor.execute("SELECT COUNT(*) FROM sesiones WHERE activa = 1")
        sesiones_antes = cursor.fetchone()[0]
        print(f"📊 Sesiones activas antes de limpiar: {sesiones_antes}")
        
        # Marcar como inactivas las sesiones expiradas
        now_utc = datetime.now(timezone.utc)
        
        cursor.execute("SELECT id, fecha_expiracion FROM sesiones WHERE activa = 1")
        sesiones = cursor.fetchall()
        
        sesiones_expiradas = 0
        for sesion in sesiones:
            try:
                expiration = datetime.fromisoformat(sesion[1].replace('Z', '+00:00'))
                if now_utc >= expiration:
                    cursor.execute("UPDATE sesiones SET activa = 0 WHERE id = ?", (sesion[0],))
                    sesiones_expiradas += 1
            except Exception as e:
                print(f"Error procesando sesión {sesion[0]}: {e}")
                # Marcar como inactiva si hay error
                cursor.execute("UPDATE sesiones SET activa = 0 WHERE id = ?", (sesion[0],))
                sesiones_expiradas += 1
        
        conn.commit()
        
        # Contar sesiones después de limpiar
        cursor.execute("SELECT COUNT(*) FROM sesiones WHERE activa = 1")
        sesiones_despues = cursor.fetchone()[0]
        
        print(f"🗑️  Sesiones expiradas marcadas como inactivas: {sesiones_expiradas}")
        print(f"📊 Sesiones activas después de limpiar: {sesiones_despues}")
        
        conn.close()
        
        if sesiones_expiradas > 0:
            print("✅ Limpieza completada")
        else:
            print("ℹ️  No había sesiones expiradas")
            
    except Exception as e:
        print(f"❌ Error limpiando sesiones: {e}")

if __name__ == "__main__":
    print("🧹 LIMPIEZA DE SESIONES EXPIRADAS")
    print("=" * 40)
    limpiar_sesiones_expiradas() 