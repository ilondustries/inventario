# 🔒 Seguridad de Credenciales - Sistema de Inventario

## ⚠️ IMPORTANTE - CREDENCIALES EXPUESTAS

**GitGuardian detectó credenciales expuestas en este repositorio.**
**Este documento explica cómo configurar el sistema de forma segura.**

## 🚨 PROBLEMA DETECTADO

- **Contraseña de email corporativo** expuesta en el código
- **Riesgo de seguridad** para la empresa
- **Acceso no autorizado** al sistema de alertas

## ✅ SOLUCIÓN IMPLEMENTADA

### 1. Variables de Entorno
- Las credenciales ya NO están hardcodeadas en el código
- Se cargan desde archivo `config.env` (NO subir a GitHub)
- Uso de `python-dotenv` para gestión segura

### 2. Archivos de Configuración
- `config.env` - Credenciales reales (NO subir a GitHub)
- `config.env.example` - Ejemplo de configuración (SÍ subir a GitHub)
- `.gitignore` - Protege archivos sensibles

## 🔧 CONFIGURACIÓN SEGURA

### Paso 1: Crear archivo config.env
```bash
# Copiar el archivo de ejemplo
cp config.env.example config.env
```

### Paso 2: Configurar credenciales reales
```bash
# Editar config.env con tus credenciales reales
GMAIL_EMAIL=tu_email@gmail.com
GMAIL_PASSWORD=tu_contraseña_de_aplicacion
ALERT_EMAILS=admin@empresa.com,compras@empresa.com
```

### Paso 3: Verificar .gitignore
```bash
# Asegurarse de que config.env esté en .gitignore
# NO debe aparecer en git status
```

## 🚫 LO QUE NO HACER

- ❌ **NO subir** `config.env` a GitHub
- ❌ **NO escribir** contraseñas en el código
- ❌ **NO compartir** credenciales en chats o emails
- ❌ **NO usar** la misma contraseña en múltiples lugares

## ✅ LO QUE SÍ HACER

- ✅ **Usar contraseñas de aplicación** para Gmail
- ✅ **Cambiar contraseñas** regularmente
- ✅ **Revisar** accesos a la cuenta
- ✅ **Usar autenticación de dos factores**

## 🔄 ACTUALIZACIÓN DE CREDENCIALES

### Si necesitas cambiar la contraseña:
1. **Generar nueva contraseña de aplicación** en Gmail
2. **Actualizar** `config.env`
3. **Reiniciar** el servidor
4. **Verificar** que las alertas funcionen

## 📞 SOPORTE

Si tienes problemas con la configuración:
1. Verificar que `config.env` existe
2. Verificar que las credenciales son correctas
3. Verificar que `python-dotenv` está instalado
4. Revisar logs del servidor

## 🎯 RESULTADO

- ✅ **Credenciales protegidas**
- ✅ **Sistema funcionando**
- ✅ **Seguridad mejorada**
- ✅ **Cumplimiento de estándares**
