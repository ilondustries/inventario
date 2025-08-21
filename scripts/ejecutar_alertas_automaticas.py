#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para ejecutar alertas automáticas en segundo plano
Sistema de Inventario - Empresa de Maquinados
"""

import sys
import os
import time
import logging
import threading
from datetime import datetime, timedelta

# Agregar el directorio backend al path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('alertas_automaticas.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AlertasAutomaticas:
    """Sistema de alertas automáticas en segundo plano"""
    
    def __init__(self, check_interval_hours=24):
        self.check_interval_hours = check_interval_hours
        self.running = False
        self.thread = None
        self.last_check = None
        
    def start(self):
        """Iniciar el sistema de alertas automáticas"""
        if self.running:
            logger.warning("⚠️ Sistema de alertas ya está ejecutándose")
            return False
        
        try:
            # Importar sistema de alertas
            from gmail_smtp import init_alert_system, send_stock_alerts
            
            # Configuración
            gmail_email = "ivan.longoria@gmail.com"
            gmail_password = "gjvrafutjeonkytd"
            alert_emails = ["compras@longoriatm.com.mx"]
            
            # Inicializar sistema
            logger.info("🔧 Inicializando sistema de alertas automáticas...")
            if not init_alert_system(gmail_email, gmail_password, alert_emails):
                logger.error("❌ Error inicializando sistema de alertas")
                return False
            
            logger.info("✅ Sistema de alertas inicializado correctamente")
            
            # Iniciar thread en segundo plano
            self.running = True
            self.thread = threading.Thread(target=self._run_loop, daemon=True)
            self.thread.start()
            
            logger.info(f"🚀 Sistema de alertas automáticas iniciado (verificación cada {self.check_interval_hours} horas)")
            return True
            
        except ImportError as e:
            logger.error(f"❌ Error importando sistema de alertas: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Error iniciando sistema: {e}")
            return False
    
    def stop(self):
        """Detener el sistema de alertas automáticas"""
        if not self.running:
            logger.warning("⚠️ Sistema de alertas no está ejecutándose")
            return
        
        logger.info("🛑 Deteniendo sistema de alertas automáticas...")
        self.running = False
        
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=5)
        
        logger.info("✅ Sistema de alertas automáticas detenido")
    
    def _run_loop(self):
        """Bucle principal de verificación de alertas"""
        logger.info("🔄 Iniciando bucle de verificación de alertas...")
        
        while self.running:
            try:
                current_time = datetime.now()
                
                # Verificar si es momento de hacer la verificación
                if (self.last_check is None or 
                    (current_time - self.last_check).total_seconds() >= self.check_interval_hours * 3600):
                    
                    logger.info(f"🔍 Verificando alertas de stock... ({current_time.strftime('%d/%m/%Y %H:%M:%S')})")
                    
                    # Importar y ejecutar verificación
                    from gmail_smtp import send_stock_alerts
                    result = send_stock_alerts()
                    
                    if result["productos_verificados"] > 0:
                        logger.info(f"📧 Verificación completada: {result['productos_verificados']} productos verificados, {result['alertas_enviadas']} alertas enviadas")
                    else:
                        logger.info("✅ Verificación completada: No hay productos con stock bajo")
                    
                    self.last_check = current_time
                    
                    # Esperar hasta la próxima verificación
                    logger.info(f"⏳ Próxima verificación en {self.check_interval_hours} horas")
                
                # Esperar 1 hora antes de verificar nuevamente
                time.sleep(3600)  # 1 hora
                
            except Exception as e:
                logger.error(f"❌ Error en bucle de alertas: {e}")
                time.sleep(3600)  # Esperar 1 hora antes de reintentar
    
    def check_now(self):
        """Ejecutar verificación de alertas inmediatamente"""
        try:
            from gmail_smtp import send_stock_alerts
            
            logger.info("🔍 Ejecutando verificación inmediata de alertas...")
            result = send_stock_alerts()
            
            logger.info(f"✅ Verificación inmediata completada: {result['mensaje']}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Error en verificación inmediata: {e}")
            return None
    
    def get_status(self):
        """Obtener estado del sistema"""
        return {
            "running": self.running,
            "check_interval_hours": self.check_interval_hours,
            "last_check": self.last_check.isoformat() if self.last_check else None,
            "thread_alive": self.thread.is_alive() if self.thread else False
        }

def main():
    """Función principal"""
    print("🚀 SISTEMA DE ALERTAS AUTOMÁTICAS")
    print("=" * 50)
    
    # Crear instancia del sistema
    alertas = AlertasAutomaticas(check_interval_hours=24)
    
    try:
        # Iniciar sistema
        if not alertas.start():
            print("❌ Error iniciando sistema de alertas")
            return
        
        print("✅ Sistema iniciado correctamente")
        print("📧 Verificando alertas cada 24 horas")
        print("🔄 Ejecutando verificación inicial...")
        
        # Verificación inicial
        result = alertas.check_now()
        if result:
            print(f"✅ Verificación inicial: {result['mensaje']}")
        
        print("\n💡 El sistema está ejecutándose en segundo plano")
        print("📝 Los logs se guardan en 'alertas_automaticas.log'")
        print("🛑 Presiona Ctrl+C para detener")
        
        # Mantener el script ejecutándose
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n🛑 Deteniendo sistema...")
        alertas.stop()
        print("✅ Sistema detenido correctamente")
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        alertas.stop()

if __name__ == "__main__":
    main()

