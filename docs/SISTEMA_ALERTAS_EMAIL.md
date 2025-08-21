# 🚨 Sistema de Alertas Automáticas por Email

## 📋 **Descripción General**

Sistema de alertas automáticas que notifica por email cuando las herramientas del almacén alcanzan su stock mínimo. Diseñado específicamente para la empresa de maquinados, este sistema ayuda a automatizar el proceso de compra de herramientas.

## 🎯 **Características Principales**

- ✅ **Alertas instantáneas** cuando el stock llega al mínimo
- ✅ **Re-alertas automáticas** cada 2 días si no se surte
- ✅ **Solo envío** (no se reciben correos en el sistema)
- ✅ **Completamente automático** (solo backend)
- ✅ **Productos reales** desde la base de datos
- ✅ **Múltiples destinatarios** configurados

## 🏗️ **Arquitectura del Sistema**

### 📁 **Archivos del Sistema**

```
backend/
├── gmail_smtp.py              # Sistema principal de alertas
└── main.py                    # API principal (integración futura)

scripts/
├── configurar_sistema_automatico.py  # Configuración automática
└── verificar_estructura_db.py        # Verificación de BD

docs/
└── SISTEMA_ALERTAS_EMAIL.md   # Esta documentación
```

### 🔧 **Componentes Principales**

1. **`GmailSMTP`** - Cliente SMTP para Gmail
2. **`AlertSystem`** - Lógica de alertas automáticas
3. **`init_alert_system`** - Inicialización del sistema
4. **`send_stock_alerts`** - Envío de alertas

## 📧 **Configuración de Email**

### 🔐 **Credenciales Gmail**

- **Servidor SMTP**: `smtp.gmail.com:587`
- **Autenticación**: TLS + Contraseña de Aplicación
- **Email origen**: `ivan.longoria@gmail.com`
- **Destinatarios**: `compras@longoriatm.com.mx`

### ⚠️ **Requisitos Gmail**

1. **Autenticación de 2 factores** habilitada
2. **Contraseña de aplicación** generada
3. **Acceso a aplicaciones menos seguras** (si es necesario)

## 🗄️ **Integración con Base de Datos**

### 📊 **Tabla Productos**

```sql
SELECT id, nombre, cantidad, cantidad_minima 
FROM productos 
WHERE cantidad <= cantidad_minima
```

### 🔍 **Lógica de Detección**

- **Stock bajo**: `cantidad <= cantidad_minima`
- **Verificación**: Diaria automática
- **Alerta inicial**: Inmediata al detectar stock bajo
- **Re-alerta**: Cada 2 días si no se surte

## 🚀 **Funcionamiento del Sistema**

### 📅 **Ciclo de Verificación**

1. **Día 0**: Producto alcanza stock mínimo → **Alerta inmediata**
2. **Día 2**: Si no se surte → **Re-alerta**
3. **Día 4**: Si no se surte → **Re-alerta**
4. **Continúa** hasta que se surta el stock

### 📧 **Formato de Emails**

#### 🚨 **Alerta Inicial**
```
🚨 ALERTA: Stock bajo - [Nombre Producto]

Producto: [Nombre]
Stock actual: [Cantidad]
Stock mínimo: [Cantidad Mínima]
Fecha: [DD/MM/AAAA HH:MM:SS]

⚠️ Este producto ha alcanzado su stock mínimo.
📧 Se enviará una nueva notificación en 2 días si no se surte.
```

#### ⚠️ **Re-alerta**
```
⚠️ RE-ALERTA: Stock bajo - [Nombre Producto]

Producto: [Nombre]
Stock actual: [Cantidad]
Stock mínimo: [Cantidad Mínima]
Fecha: [DD/MM/AAAA HH:MM:SS]

🚨 Este producto sigue con stock bajo desde la alerta anterior.
📧 Se enviará otra notificación en 2 días si no se surte.
```

## 🛠️ **Instalación y Configuración**

### 📦 **Dependencias**

```bash
# El sistema usa solo librerías estándar de Python:
# - smtplib (SMTP)
# - email.mime (formato de emails)
# - sqlite3 (base de datos)
# - datetime (fechas)
# - logging (registro de eventos)
```

### ⚙️ **Configuración Automática**

```bash
python scripts/configurar_sistema_automatico.py
```

### 🔍 **Verificación de Base de Datos**

```bash
python scripts/verificar_estructura_db.py
```

## 📱 **Uso del Sistema**

### 🚀 **Inicialización Manual**

```python
from gmail_smtp import init_alert_system

# Inicializar sistema
init_alert_system(
    gmail_email="tu_email@gmail.com",
    gmail_password="tu_app_password",
    alert_emails=["destinatario@empresa.com"]
)
```

### 🔍 **Verificación Manual**

```python
from gmail_smtp import send_stock_alerts

# Verificar y enviar alertas
result = send_stock_alerts()
print(f"Alertas enviadas: {result['alertas_enviadas']}")
```

### 🧪 **Prueba del Sistema**

```python
from gmail_smtp import test_alert_system

# Probar sistema completo
if test_alert_system():
    print("✅ Sistema funcionando correctamente")
else:
    print("❌ Error en el sistema")
```

## 🔒 **Seguridad y Privacidad**

### 🛡️ **Medidas de Seguridad**

1. **Contraseñas de aplicación** (no contraseñas principales)
2. **Autenticación TLS** para conexiones SMTP
3. **Logs de auditoría** de todas las operaciones
4. **Manejo seguro de errores** sin exponer información sensible

### 📊 **Logs y Auditoría**

- **Conexiones SMTP** exitosas/fallidas
- **Emails enviados** con timestamp
- **Productos verificados** y alertas generadas
- **Errores del sistema** para diagnóstico

## 🚨 **Solución de Problemas**

### ❌ **Error: "Username and Password not accepted"**

**Causa**: Gmail requiere autenticación de 2 factores
**Solución**: 
1. Habilitar 2FA en Gmail
2. Generar contraseña de aplicación
3. Usar la contraseña de aplicación

### ❌ **Error: "Connection timeout"**

**Causa**: Problemas de red o firewall
**Solución**:
1. Verificar conectividad a internet
2. Verificar firewall corporativo
3. Probar desde otra red

### ❌ **Error: "No such column: stock_actual"**

**Causa**: Nombres de columnas incorrectos
**Solución**: 
1. Verificar estructura de BD con `verificar_estructura_db.py`
2. Usar nombres correctos: `cantidad` y `cantidad_minima`

## 🔮 **Futuras Mejoras**

### 📈 **Funcionalidades Planificadas**

1. **Dashboard de alertas** en frontend (opcional)
2. **Historial de alertas** en base de datos
3. **Configuración de umbrales** personalizados
4. **Sistema de notificaciones avanzado** (opcional)
5. **Reportes de consumo** de herramientas

### 🔧 **Optimizaciones Técnicas**

1. **Pool de conexiones SMTP** para mejor rendimiento
2. **Cache de productos** para reducir consultas BD
3. **Sistema de reintentos** para emails fallidos
4. **Métricas de rendimiento** del sistema

## 📞 **Soporte y Contacto**

### 👨‍💻 **Desarrollador**
- **Sistema**: Sistema de Inventario - Empresa de Maquinados
- **Versión**: 1.0.0
- **Fecha**: Diciembre 2024

### 📧 **Contacto Técnico**
- **Email**: `ivan.longoria@gmail.com`
- **Empresa**: Longoria TM

---

## 📝 **Notas de Implementación**

Este sistema fue desarrollado como parte del proyecto de inventario para la empresa de maquinados, enfocado en resolver el problema de pérdida de herramientas y tiempo por falta de stock. El sistema automatiza completamente el proceso de notificación, permitiendo a los administradores enfocarse en la gestión del almacén en lugar de monitorear manualmente los niveles de stock.

**Última actualización**: Diciembre 2024
**Estado**: ✅ Implementado y Funcionando



