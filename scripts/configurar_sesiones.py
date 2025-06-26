#!/usr/bin/env python3
"""
Script para configurar el comportamiento de sesiones del Sistema de Almacén
"""

import json
from pathlib import Path

def cargar_configuracion():
    """Cargar configuración actual"""
    config_path = Path(__file__).parent.parent / "backend" / "session_config.json"
    
    if config_path.exists():
        with open(config_path, 'r') as f:
            return json.load(f)
    else:
        # Configuración por defecto
        return {
            "browser_close_logout": True,
            "session_timeout_hours": 8,
            "check_session_on_focus": True,
            "log_all_logouts": True
        }

def guardar_configuracion(config):
    """Guardar configuración"""
    config_path = Path(__file__).parent.parent / "backend" / "session_config.json"
    
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    print("✅ Configuración guardada exitosamente")

def mostrar_configuracion(config):
    """Mostrar configuración actual"""
    print("\n📋 Configuración actual de sesiones:")
    print("=" * 50)
    print(f"🔒 Cerrar al cerrar navegador: {'✅ Sí' if config['browser_close_logout'] else '❌ No'}")
    print(f"⏰ Tiempo máximo de sesión: {config['session_timeout_hours']} horas")
    print(f"👁️ Verificar al recuperar foco: {'✅ Sí' if config['check_session_on_focus'] else '❌ No'}")
    print(f"📝 Registrar todos los logouts: {'✅ Sí' if config['log_all_logouts'] else '❌ No'}")

def configurar_seguridad_alta():
    """Configuración para máxima seguridad"""
    return {
        "browser_close_logout": True,
        "session_timeout_hours": 2,
        "check_session_on_focus": True,
        "log_all_logouts": True
    }

def configurar_seguridad_media():
    """Configuración para seguridad media"""
    return {
        "browser_close_logout": True,
        "session_timeout_hours": 4,
        "check_session_on_focus": True,
        "log_all_logouts": True
    }

def configurar_seguridad_baja():
    """Configuración para seguridad baja (conveniencia)"""
    return {
        "browser_close_logout": False,
        "session_timeout_hours": 8,
        "check_session_on_focus": False,
        "log_all_logouts": True
    }

def main():
    print("🏪 Sistema de Almacén - Configuración de Sesiones")
    print("=" * 60)
    
    config = cargar_configuracion()
    mostrar_configuracion(config)
    
    print("\n🎯 Opciones de configuración:")
    print("1. Seguridad Alta (Recomendado para PYMES)")
    print("   - Sesión se cierra al cerrar navegador")
    print("   - Tiempo máximo: 2 horas")
    print("   - Verificación al recuperar foco")
    print("   - Registro completo de logouts")
    
    print("\n2. Seguridad Media (Balanceado)")
    print("   - Sesión se cierra al cerrar navegador")
    print("   - Tiempo máximo: 4 horas")
    print("   - Verificación al recuperar foco")
    print("   - Registro completo de logouts")
    
    print("\n3. Seguridad Baja (Máxima conveniencia)")
    print("   - Sesión persiste hasta 8 horas")
    print("   - No se cierra al cerrar navegador")
    print("   - Sin verificación de foco")
    print("   - Registro básico de logouts")
    
    print("\n4. Configuración personalizada")
    print("5. Salir sin cambios")
    
    opcion = input("\nSelecciona una opción (1-5): ").strip()
    
    if opcion == "1":
        nueva_config = configurar_seguridad_alta()
        print("\n🔒 Aplicando configuración de Seguridad Alta...")
        guardar_configuracion(nueva_config)
        mostrar_configuracion(nueva_config)
        
    elif opcion == "2":
        nueva_config = configurar_seguridad_media()
        print("\n🛡️ Aplicando configuración de Seguridad Media...")
        guardar_configuracion(nueva_config)
        mostrar_configuracion(nueva_config)
        
    elif opcion == "3":
        nueva_config = configurar_seguridad_baja()
        print("\n⚡ Aplicando configuración de Seguridad Baja...")
        guardar_configuracion(nueva_config)
        mostrar_configuracion(nueva_config)
        
    elif opcion == "4":
        print("\n⚙️ Configuración personalizada:")
        
        browser_close = input("¿Cerrar sesión al cerrar navegador? (s/n): ").lower() == 's'
        timeout = int(input("Tiempo máximo de sesión (horas): ") or "8")
        check_focus = input("¿Verificar sesión al recuperar foco? (s/n): ").lower() == 's'
        log_logouts = input("¿Registrar todos los logouts? (s/n): ").lower() == 's'
        
        nueva_config = {
            "browser_close_logout": browser_close,
            "session_timeout_hours": timeout,
            "check_session_on_focus": check_focus,
            "log_all_logouts": log_logouts
        }
        
        guardar_configuracion(nueva_config)
        mostrar_configuracion(nueva_config)
        
    elif opcion == "5":
        print("👋 Configuración no modificada")
        
    else:
        print("❌ Opción inválida")
    
    print("\n💡 Nota: Reinicia el servidor para aplicar los cambios")

if __name__ == "__main__":
    main() 