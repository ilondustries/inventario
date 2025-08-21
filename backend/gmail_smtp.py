#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sistema de alertas por email usando SMTP + Gmail
Sistema de Inventario - Empresa de Maquinados
"""

import smtplib
import time
import logging
import sqlite3
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Optional
from datetime import datetime, timedelta

# Configurar logging
logger = logging.getLogger(__name__)

class GmailSMTP:
    """Cliente SMTP para Gmail"""
    
    def __init__(self, gmail_email: str, gmail_password: str):
        self.gmail_email = gmail_email
        self.gmail_password = gmail_password
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
        
    def test_connection(self) -> bool:
        """Probar conexión SMTP con Gmail"""
        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.gmail_email, self.gmail_password)
                logger.info("✅ Conexión SMTP exitosa con Gmail")
                return True
        except Exception as e:
            logger.error(f"❌ Error en conexión SMTP: {e}")
            return False
    
    def send_email(self, to_email: str, subject: str, body: str) -> bool:
        """Enviar email usando SMTP"""
        try:
            # Crear mensaje
            mensaje = MIMEMultipart()
            mensaje["From"] = self.gmail_email
            mensaje["To"] = to_email
            mensaje["Subject"] = subject
            
            # Agregar cuerpo del mensaje
            mensaje.attach(MIMEText(body, "plain", "utf-8"))
            
            # Enviar email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.gmail_email, self.gmail_password)
                server.send_message(mensaje)
            
            logger.info(f"✅ Email enviado exitosamente a {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error enviando email: {e}")
            return False
    
    def send_stock_alert(self, to_email: str, product_name: str, 
                         current_stock: int, min_stock: int, 
                         alert_type: str = "stock_bajo") -> bool:
        """Enviar alerta de stock bajo"""
        try:
            if alert_type == "stock_bajo":
                subject = f"🚨 ALERTA: Stock bajo - {product_name}"
                body = f"""
🚨 ALERTA DE STOCK BAJO

Producto: {product_name}
Stock actual: {current_stock}
Stock mínimo: {min_stock}
Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}

⚠️ Este producto ha alcanzado su stock mínimo.
📧 Se enviará una nueva notificación en 48 horas si no se surte.

Sistema de Almacén - Empresa de Maquinados
                """
            else:
                subject = f"⚠️ RE-ALERTA: Stock bajo - {product_name}"
                body = f"""
⚠️ RE-ALERTA DE STOCK BAJO

Producto: {product_name}
Stock actual: {current_stock}
Stock mínimo: {min_stock}
Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}

🚨 Este producto sigue con stock bajo desde la alerta anterior.
📧 Se enviará otra notificación en 48 horas si no se surte.

Sistema de Almacén - Empresa de Maquinados
                """
            
            return self.send_email(to_email, subject, body)
            
        except Exception as e:
            logger.error(f"❌ Error enviando alerta de stock: {e}")
            return False

class AlertSystem:
    """Sistema de alertas automáticas"""
    
    def __init__(self, gmail_email: str, gmail_password: str, 
                 alert_emails: List[str], db_path: str = "../data/almacen_main.db"):
        self.gmail_client = GmailSMTP(gmail_email, gmail_password)
        self.alert_emails = alert_emails
        self.db_path = db_path
        self.last_alert_dates: Dict[str, float] = {}
        
    def get_products_with_low_stock(self) -> List[Dict]:
        """Obtener productos con stock bajo desde la base de datos"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Obtener productos con stock bajo
            cursor.execute("""
                SELECT id, nombre, cantidad, cantidad_minima 
                FROM productos 
                WHERE cantidad <= cantidad_minima
                ORDER BY nombre
            """)
            
            products = []
            for row in cursor.fetchall():
                products.append({
                    'id': row['id'],
                    'nombre': row['nombre'],
                    'stock_actual': row['cantidad'],
                    'stock_minimo': row['cantidad_minima']
                })
            
            conn.close()
            logger.info(f"📊 Productos con stock bajo encontrados: {len(products)}")
            return products
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo productos: {e}")
            return []
    
    def check_and_send_alerts(self) -> Dict:
        """Verificar stock y enviar alertas"""
        try:
            current_time = time.time()
            alertas_enviadas = 0
            
            # Obtener productos reales con stock bajo
            products_data = self.get_products_with_low_stock()
            productos_verificados = len(products_data)
            
            if productos_verificados == 0:
                logger.info("✅ No hay productos con stock bajo")
                return {
                    "productos_verificados": 0,
                    "alertas_enviadas": 0,
                    "mensaje": "No hay productos con stock bajo."
                }
            
            logger.info(f"🔍 Verificando {productos_verificados} productos con stock bajo...")
            
            for product in products_data:
                product_id = str(product['id'])
                product_name = product['nombre']
                current_stock = product['stock_actual']
                min_stock = product['stock_minimo']
                
                # Verificar si ya se envió alerta recientemente
                last_alert = self.last_alert_dates.get(product_id, 0)
                hours_since_last = (current_time - last_alert) / 3600
                
                # Enviar alerta inicial o re-alerta cada 48 horas (2 días)
                if last_alert == 0 or hours_since_last >= 48:
                    alert_type = "stock_bajo" if last_alert == 0 else "re_alerta"
                    
                    # Enviar a todos los emails configurados
                    for email in self.alert_emails:
                        if self.gmail_client.send_stock_alert(
                            email, product_name, current_stock, min_stock, alert_type
                        ):
                            alertas_enviadas += 1
                    
                    # Actualizar fecha de última alerta
                    self.last_alert_dates[product_id] = current_time
                    
                    logger.info(f"🚨 Alerta enviada para {product_name} (Stock: {current_stock}/{min_stock})")
                else:
                    hours_remaining = 48 - hours_since_last
                    logger.info(f"⏳ {product_name}: Re-alerta en {hours_remaining:.1f} horas")
            
            return {
                "productos_verificados": productos_verificados,
                "alertas_enviadas": alertas_enviadas,
                "mensaje": f"Verificación completada. {alertas_enviadas} alertas enviadas."
            }
            
        except Exception as e:
            logger.error(f"❌ Error en verificación de alertas: {e}")
            return {
                "productos_verificados": 0,
                "alertas_enviadas": 0,
                "mensaje": f"Error en verificación: {str(e)}"
            }
    
    def test_system(self) -> bool:
        """Probar el sistema de alertas"""
        try:
            # Probar conexión SMTP
            if not self.gmail_client.test_connection():
                return False
            
            # Probar envío de email de prueba
            test_body = """
🧪 PRUEBA DEL SISTEMA DE ALERTAS

Este es un email de prueba para verificar que el sistema de alertas
está funcionando correctamente.

✅ El sistema está listo para enviar alertas automáticas.

Sistema de Almacén - Empresa de Maquinados
            """
            
            for email in self.alert_emails:
                if not self.gmail_client.send_email(email, "🧪 Prueba Sistema de Alertas", test_body):
                    return False
            
            logger.info("✅ Sistema de alertas probado exitosamente")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error probando sistema: {e}")
            return False

# Instancia global del sistema de alertas
alert_system = None

def init_alert_system(gmail_email: str, gmail_password: str, alert_emails: List[str], db_path: str = "../data/almacen_main.db") -> bool:
    """Inicializar el sistema de alertas"""
    global alert_system
    try:
        alert_system = AlertSystem(gmail_email, gmail_password, alert_emails, db_path)
        if alert_system.test_system():
            logger.info("✅ Sistema de alertas inicializado correctamente")
            return True
        else:
            logger.error("❌ Error probando sistema de alertas")
            return False
    except Exception as e:
        logger.error(f"❌ Error inicializando sistema: {e}")
        return False

def send_stock_alerts() -> Dict:
    """Enviar alertas de stock usando el sistema global"""
    global alert_system
    if not alert_system:
        return {
            "productos_verificados": 0,
            "alertas_enviadas": 0,
            "mensaje": "Sistema de alertas no inicializado"
        }
    
    return alert_system.check_and_send_alerts()

def test_alert_system() -> bool:
    """Probar el sistema de alertas"""
    global alert_system
    if not alert_system:
        return False
    
    return alert_system.test_system()
