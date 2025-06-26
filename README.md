# Control de Herramienta Longoria Tooling

Sistema de gestión de inventario de herramientas optimizado para uso en tablet con red local.

## Características

- ✅ Interfaz responsive optimizada para tablet
- ✅ Base de datos SQLite local
- ✅ API REST completa
- ✅ Búsqueda en tiempo real
- ✅ Historial de acciones
- ✅ Estadísticas del almacén
- ✅ Códigos QR automáticos con impresión
- ✅ Ubicaciones automáticas
- ✅ Códigos de barras automáticos
- ✅ Diseño moderno y intuitivo

## 📋 Requisitos

- Python 3.7 o superior
- Conexión de red local
- Navegador web moderno

## 🚀 Instalación y Uso

### 1. Clonar o descargar el proyecto
```bash
git clone <url-del-repositorio>
cd inventario
```

### 2. Ejecutar el servidor
```bash
python scripts/start_server.py
```

### 3. Acceder al sistema
- **Desde la misma computadora**: http://localhost:8000
- **Desde tablet en la red**: http://[IP-DEL-SERVIDOR]:8000

## 📱 Uso en Tablet

1. Asegúrate de que la tablet esté conectada a la misma red WiFi
2. Abre el navegador y ve a la URL mostrada en el servidor
3. ¡Listo! El sistema está optimizado para uso táctil

## 🔧 Funcionalidades

### Gestión de Herramientas
- ✅ Agregar nuevas herramientas
- ✅ Editar herramientas existentes
- ✅ Eliminar herramientas
- ✅ Búsqueda por nombre, código, ubicación

### Inventario
- ✅ Control de stock
- ✅ Alertas de stock bajo
- ✅ Ubicaciones automáticas (A01, A02, B01, etc.)
- ✅ Categorías de herramientas

### Códigos QR y Barras
- ✅ Generación automática de códigos QR
- ✅ Códigos de barras automáticos
- ✅ Impresión de etiquetas QR
- ✅ Información completa en etiquetas

### Reportes
- ✅ Historial de acciones
- ✅ Estadísticas del almacén
- ✅ Valor total del inventario

## 🗄️ Estructura del Proyecto 

## 🔒 Seguridad

- Los datos se almacenan localmente
- No requiere conexión a internet
- Acceso solo desde la red local
- Sistema de autenticación con sesiones

## 🆘 Soporte

Si encuentras algún problema:

1. Verifica que Python 3.7+ esté instalado
2. Asegúrate de que el puerto 8000 esté libre
3. Confirma que la tablet esté en la misma red

## 🔮 Próximas Mejoras

- [ ] Exportación a Excel/PDF
- [ ] Escáner de códigos de barras
- [ ] Múltiples usuarios con roles
- [ ] Backup automático
- [ ] Notificaciones push

---

**Desarrollado para Longoria Tooling** 🔧 