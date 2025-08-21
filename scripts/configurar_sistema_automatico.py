#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para configurar automáticamente el sistema de alertas
Sistema de Inventario - Empresa de Maquinados
"""

import sys
import os

# Agregar el directorio backend al path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from gmail_smtp import init_alert_system, test_alert_system, send_stock_alerts

def main():
    """Función principal con configuración automática"""
    print("🚀 CONFIGURACIÓN AUTOMÁTICA DEL SISTEMA DE ALERTAS")
    print("=" * 60)
    
    # Configuración automática (las credenciales que funcionan)
    gmail_email = "ivan.longoria@gmail.com"
    gmail_password = "gjvrafutjeonkytd"  # Contraseña de aplicación sin espacios
    alert_emails = ["compras@longoriatm.com.mx"]
    
    print(f"📧 Configuración automática:")
    print(f"   - Email Gmail: {gmail_email}")
    print(f"   - Contraseña de app: {gmail_password[:4]}...{gmail_password[-4:]}")
    print(f"   - Alertas a: {', '.join(alert_emails)}")
    
    try:
        # 1. Inicializar sistema
        print("\n🔧 Inicializando sistema de alertas...")
        if not init_alert_system(gmail_email, gmail_password, alert_emails):
            print("❌ Error inicializando sistema de alertas")
            return
        
        print("✅ Sistema de alertas inicializado correctamente")
        
        # 2. Probar sistema
        print("\n🧪 Probando sistema...")
        if not test_alert_system():
            print("❌ Error probando sistema")
            return
        
        print("✅ Sistema probado exitosamente")
        
        # 3. Verificar productos reales con stock bajo
        print("\n🔍 Verificando productos reales con stock bajo...")
        result = send_stock_alerts()
        print(f"✅ Resultado: {result['mensaje']}")
        print(f"   - Productos verificados: {result['productos_verificados']}")
        print(f"   - Alertas enviadas: {result['alertas_enviadas']}")
        
        if result['productos_verificados'] > 0:
            print(f"\n📊 PRODUCTOS CON STOCK BAJO:")
            print("   - El sistema detectó productos reales de la base de datos")
            print("   - Las alertas se enviaron automáticamente")
            print("   - Se enviarán re-alertas cada 2 días si no se surten")
        else:
            print("\n✅ No hay productos con stock bajo en este momento")
        
        print("\n🎉 ¡SISTEMA CONFIGURADO EXITOSAMENTE!")
        print("\n📱 El sistema SMTP está funcionando correctamente")
        print("🚀 Las alertas se enviarán automáticamente cuando el stock esté bajo")
        print("\n💡 CONFIGURACIÓN:")
        print(f"   - Email origen: {gmail_email}")
        print(f"   - Destinatarios: {', '.join(alert_emails)}")
        print("   - Verificación: Productos reales de la base de datos")
        print("   - Alerta instantánea: Cuando stock <= mínimo")
        print("   - Re-alertas: Cada 2 días si no se surte")
        
        print("\n🔧 FUNCIONAMIENTO:")
        print("   1. ✅ Solo envío de correos (no se reciben)")
        print("   2. ✅ Solo backend (sin interfaz de usuario)")
        print("   3. ✅ Productos reales de la base de datos")
        print("   4. ✅ Alertas instantáneas + re-alertas cada 2 días")
        print("   5. ✅ Sistema completamente automático")
        
    except Exception as e:
        print(f"❌ Error durante la configuración: {e}")
        print("\n💡 VERIFICAR:")
        print("   1. Que las credenciales sean correctas")
        print("   2. Que Gmail tenga autenticación de 2 factores")
        print("   3. Que la contraseña de aplicación sea válida")
        print("   4. Que la base de datos esté accesible")

if __name__ == "__main__":
    main()
