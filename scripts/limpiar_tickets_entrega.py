#!/usr/bin/env python3
"""
Script para limpiar tickets del sistema antes de la entrega al cliente.
Solo elimina tickets, preserva productos, usuarios y funcionalidades.
"""

import sqlite3
import os
import sys
from datetime import datetime

def conectar_db():
    """Conectar a la base de datos principal"""
    try:
        # Intentar conectar a la base de datos principal
        db_path = os.path.join('data', 'almacen_main.db')
        if not os.path.exists(db_path):
            print(f"❌ Base de datos no encontrada en: {db_path}")
            print("💡 Asegúrate de ejecutar este script desde la raíz del proyecto")
            return None
        
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        print(f"✅ Conectado a: {db_path}")
        return conn
    except Exception as e:
        print(f"❌ Error conectando a la base de datos: {e}")
        return None

def verificar_estado_actual(conn):
    """Verificar el estado actual de tickets en el sistema"""
    try:
        cursor = conn.cursor()
        
        # Contar tickets existentes
        cursor.execute("SELECT COUNT(*) as total FROM tickets_compra")
        total_tickets = cursor.fetchone()['total']
        
        # Contar productos
        cursor.execute("SELECT COUNT(*) as total FROM productos")
        total_productos = cursor.fetchone()['total']
        
        # Contar usuarios
        cursor.execute("SELECT COUNT(*) as total FROM usuarios")
        total_usuarios = cursor.fetchone()['total']
        
        print("\n📊 ESTADO ACTUAL DEL SISTEMA:")
        print(f"   🎫 Tickets: {total_tickets}")
        print(f"   🛠️  Productos: {total_productos}")
        print(f"   👥 Usuarios: {total_usuarios}")
        
        return total_tickets, total_productos, total_usuarios
        
    except Exception as e:
        print(f"❌ Error verificando estado: {e}")
        return None, None, None

def confirmar_limpieza(total_tickets):
    """Confirmar la operación de limpieza"""
    if total_tickets == 0:
        print("\n✅ El sistema ya está limpio (0 tickets)")
        return False
    
    print(f"\n⚠️  ATENCIÓN: Se eliminarán {total_tickets} tickets del sistema")
    print("🔒 Se PRESERVARÁN:")
    print("   ✅ Productos del inventario")
    print("   ✅ Usuarios y roles")
    print("   ✅ Funcionalidades del sistema")
    print("   ✅ Configuraciones")
    
    print("\n🗑️  Se ELIMINARÁN:")
    print("   ❌ Todos los tickets de compra")
    print("   ❌ Items de tickets")
    print("   ❌ Historial relacionado con tickets")
    
    respuesta = input("\n❓ ¿Estás seguro de continuar? (sí/no): ").lower().strip()
    
    if respuesta in ['si', 'sí', 'yes', 'y', 's']:
        return True
    else:
        print("❌ Operación cancelada")
        return False

def limpiar_tickets(conn):
    """Limpiar todos los tickets del sistema"""
    try:
        cursor = conn.cursor()
        
        print("\n🧹 INICIANDO LIMPIEZA DE TICKETS...")
        
        # 1. Eliminar items de tickets
        cursor.execute("DELETE FROM ticket_items")
        items_eliminados = cursor.rowcount
        print(f"   ✅ Items de tickets eliminados: {items_eliminados}")
        
        # 2. Eliminar historial relacionado con tickets
        cursor.execute("DELETE FROM historial WHERE accion IN ('entrega', 'devolucion', 'devolucion_buen_estado', 'devolucion_mal_estado')")
        historial_eliminado = cursor.rowcount
        print(f"   ✅ Historial de tickets eliminado: {historial_eliminado}")
        
        # 3. Eliminar tickets principales
        cursor.execute("DELETE FROM tickets_compra")
        tickets_eliminados = cursor.rowcount
        print(f"   ✅ Tickets eliminados: {tickets_eliminados}")
        
        # 4. Resetear contadores de tickets (si existen)
        try:
            cursor.execute("DELETE FROM sqlite_sequence WHERE name='tickets_compra'")
            print("   ✅ Contador de tickets reseteado")
        except:
            print("   ℹ️  No se pudo resetear contador de tickets")
        
        # Confirmar cambios
        conn.commit()
        
        print(f"\n✅ LIMPIEZA COMPLETADA:")
        print(f"   🎫 Tickets eliminados: {tickets_eliminados}")
        print(f"   📋 Items eliminados: {items_eliminados}")
        print(f"   📚 Historial eliminado: {historial_eliminado}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error durante la limpieza: {e}")
        conn.rollback()
        return False

def verificar_limpieza(conn):
    """Verificar que la limpieza fue exitosa"""
    try:
        cursor = conn.cursor()
        
        # Verificar tickets
        cursor.execute("SELECT COUNT(*) as total FROM tickets_compra")
        tickets_restantes = cursor.fetchone()['total']
        
        # Verificar items
        cursor.execute("SELECT COUNT(*) as total FROM ticket_items")
        items_restantes = cursor.fetchone()['total']
        
        print(f"\n🔍 VERIFICACIÓN POST-LIMPIEZA:")
        print(f"   🎫 Tickets restantes: {tickets_restantes}")
        print(f"   📋 Items restantes: {items_restantes}")
        
        if tickets_restantes == 0 and items_restantes == 0:
            print("✅ LIMPIEZA EXITOSA - Sistema listo para entrega")
            return True
        else:
            print("⚠️  ADVERTENCIA: Algunos tickets no se eliminaron completamente")
            return False
            
    except Exception as e:
        print(f"❌ Error verificando limpieza: {e}")
        return False

def main():
    """Función principal del script"""
    print("🧹 LIMPIADOR DE TICKETS PARA ENTREGA")
    print("=" * 50)
    
    # Conectar a la base de datos
    conn = conectar_db()
    if not conn:
        return
    
    try:
        # Verificar estado actual
        total_tickets, total_productos, total_usuarios = verificar_estado_actual(conn)
        if total_tickets is None:
            return
        
        # Si no hay tickets, no hay nada que limpiar
        if total_tickets == 0:
            print("\n✅ El sistema ya está limpio y listo para entrega")
            return
        
        # Confirmar operación
        if not confirmar_limpieza(total_tickets):
            return
        
        # Ejecutar limpieza
        if limpiar_tickets(conn):
            # Verificar resultado
            verificar_limpieza(conn)
            
            print("\n🎉 SISTEMA LISTO PARA ENTREGA:")
            print("   🎁 El cliente verá un sistema como 'producto nuevo'")
            print("   📚 Puedes crear tickets de prueba durante la capacitación")
            print("   🚀 Funcionalidades intactas y operativas")
        else:
            print("\n❌ La limpieza falló. Revisa los errores anteriores.")
    
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
    
    finally:
        if conn:
            conn.close()
            print("\n🔌 Conexión a base de datos cerrada")

if __name__ == "__main__":
    main()

