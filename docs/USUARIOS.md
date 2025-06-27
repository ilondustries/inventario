# 👥 Gestión de Usuarios - Sistema de Almacén

## 📋 **Usuarios Configurados**

### 👑 **Administrador del Sistema**
- **Usuario**: `admin`
- **Contraseña**: `admin123`
- **Nombre**: Administrador del Sistema
- **Email**: admin@empresa.com
- **Rol**: `admin`
- **Permisos**: Acceso total al sistema

### 👨‍💼 **Supervisor Turno Mañana**
- **Usuario**: `supervisor_manana`
- **Contraseña**: `turno123`
- **Nombre**: María González - Supervisor Mañana
- **Email**: maria.gonzalez@empresa.com
- **Rol**: `supervisor`
- **Permisos**: Gestión de inventario y reportes

### 👨‍💼 **Supervisor Turno Tarde**
- **Usuario**: `supervisor_tarde`
- **Contraseña**: `turno456`
- **Nombre**: Carlos Rodríguez - Supervisor Tarde
- **Email**: carlos.rodriguez@empresa.com
- **Rol**: `supervisor`
- **Permisos**: Gestión de inventario y reportes

---

## 🔐 **Sistema de Roles**

### 👑 **Administrador (`admin`)**
- ✅ **Gestión completa** de productos
- ✅ **Gestión de usuarios** (crear, editar, eliminar)
- ✅ **Acceso a reportes** completos
- ✅ **Configuración del sistema**
- ✅ **Auditoría completa**

### 👨‍💼 **Supervisor (`supervisor`)**
- ✅ **Gestión de productos** (crear, editar, eliminar)
- ✅ **Control de inventario**
- ✅ **Acceso a reportes** básicos
- ✅ **Historial de acciones**
- ❌ **No puede gestionar usuarios**

### 👷 **Operador (`operador`)**
- ✅ **Consulta de productos**
- ✅ **Actualización de cantidades**
- ✅ **Búsqueda de productos**
- ❌ **No puede crear/eliminar productos**
- ❌ **No puede acceder a reportes**

---

## 🛠️ **Gestión de Usuarios**

### 📝 **Agregar Nuevo Usuario**
```bash
python scripts/agregar_usuarios.py
# Seleccionar opción 2: "Agregar nuevo usuario"
```

### 📋 **Listar Usuarios**
```bash
python scripts/agregar_usuarios.py listar
```

### 🔧 **Agregar Usuario Específico**
```bash
python scripts/agregar_usuarios.py agregar <username> <password> <nombre> <email> <rol>
```

### 🚀 **Agregar Usuarios de Turno (Automático)**
```bash
python scripts/agregar_usuarios.py
# Seleccionar opción 3: "Agregar usuarios de turno"
```

---

## 🔒 **Seguridad**

### 🔐 **Contraseñas**
- **Hash SHA-256** para almacenamiento seguro
- **Sesiones de 8 horas** con tokens únicos
- **Cookies HttpOnly** para protección
- **Logout automático** al cerrar navegador

### 📊 **Auditoría**
- **Registro de login/logout** por IP
- **Historial de acciones** por usuario
- **Sesiones activas** monitoreadas
- **Logs de seguridad** automáticos

---

## 📱 **Acceso desde Tablet**

### 🌐 **URLs de Acceso:**
- **Local**: `http://localhost:8000`
- **Red**: `http://[IP-DEL-SERVIDOR]:8000`

### 📋 **Proceso de Login:**
1. **Abrir navegador** en tablet
2. **Ir a la URL** del servidor
3. **Ingresar credenciales** del turno correspondiente
4. **Acceder al sistema** con permisos del rol

---

## 🎯 **Recomendaciones para PYMES**

### 📅 **Gestión de Turnos:**
- **Mañana**: Usar `supervisor_manana`
- **Tarde**: Usar `supervisor_tarde`
- **Administración**: Usar `admin`

### 🔄 **Rotación de Contraseñas:**
- **Cambiar cada 3 meses** las contraseñas
- **Usar contraseñas seguras** (8+ caracteres)
- **No compartir credenciales** entre turnos

### 📊 **Monitoreo:**
- **Revisar logs** semanalmente
- **Verificar sesiones activas**
- **Auditar acciones** de usuarios

---

## 🚨 **Solución de Problemas**

### ❌ **No puede iniciar sesión:**
1. Verificar credenciales correctas
2. Verificar que el usuario esté activo
3. Verificar conexión al servidor
4. Contactar al administrador

### ❌ **Acceso denegado:**
1. Verificar rol del usuario
2. Verificar permisos específicos
3. Contactar al administrador

### ❌ **Sesión expirada:**
1. Volver a iniciar sesión
2. Verificar hora del sistema
3. Contactar al administrador

---

## 📞 **Contacto de Soporte**

Para problemas con usuarios o acceso:
- **Administrador**: admin@empresa.com
- **Soporte técnico**: soporte@empresa.com

---

**Última actualización**: Junio 2025 

# Guía de Usuarios - Control de Herramienta Longoria Tooling

## Roles de Usuario

El sistema cuenta con tres roles de usuario con diferentes niveles de permisos:

### 👑 Administrador
- **Acceso completo** a todas las funcionalidades del sistema
- **Gestión de productos**: Crear, editar, eliminar herramientas
- **Gestión de usuarios**: Agregar, modificar y eliminar usuarios
- **Aprobación de tickets**: Revisar y aprobar/rechazar solicitudes de compra
- **Entrega de herramientas**: Procesar entregas de tickets aprobados
- **Reportes y estadísticas**: Acceso completo a todos los reportes

### 👨‍💼 Supervisor
- **Consulta de inventario**: Ver todos los productos y su estado
- **Búsqueda y filtros**: Usar todas las herramientas de búsqueda
- **Sistema de tickets**: Crear solicitudes de compra de herramientas
- **Seguimiento de tickets**: Ver el estado de sus solicitudes
- **Sin acceso** a gestión de productos o usuarios

### 👷 Operador
- **Consulta de inventario**: Ver todos los productos y su estado
- **Búsqueda básica**: Usar herramientas de búsqueda
- **Sistema de tickets**: Crear solicitudes de compra de herramientas
- **Seguimiento de tickets**: Ver el estado de sus solicitudes
- **Sin acceso** a gestión de productos o usuarios

## Funcionalidades por Rol

### Gestión de Productos
| Función | Administrador | Supervisor | Operador |
|---------|---------------|------------|----------|
| Ver productos | ✅ | ✅ | ✅ |
| Crear productos | ✅ | ❌ | ❌ |
| Editar productos | ✅ | ❌ | ❌ |
| Eliminar productos | ✅ | ❌ | ❌ |
| Generar códigos QR | ✅ | ✅ | ✅ |

### Sistema de Tickets de Compra
| Función | Administrador | Supervisor | Operador |
|---------|---------------|------------|----------|
| Crear tickets | ✅ | ✅ | ✅ |
| Ver tickets propios | ✅ | ✅ | ✅ |
| Ver todos los tickets | ✅ | ❌ | ❌ |
| Aprobar/rechazar tickets | ✅ | ❌ | ❌ |
| Entregar herramientas | ✅ | ❌ | ❌ |

## Sistema de Tickets de Compra

### Crear un Ticket de Compra

1. **Acceso**: Solo supervisores y operadores pueden crear tickets
2. **Proceso**:
   - Hacer clic en "➕ Nuevo Ticket" en la sección de tickets
   - Completar la información requerida:
     - **Orden de Producción**: Número de orden o proyecto
     - **Justificación**: Explicar por qué se necesitan las herramientas
   - Agregar herramientas al ticket:
     - Seleccionar herramienta del inventario
     - Especificar cantidad solicitada
     - Opcional: Precio unitario
   - Enviar ticket para revisión

### Estados del Ticket

- **🟡 Pendiente**: Ticket creado, esperando aprobación
- **🟢 Aprobado**: Ticket aprobado por administrador, listo para entrega
- **🔴 Rechazado**: Ticket rechazado por administrador
- **🔵 Entregado**: Herramientas entregadas completamente

### Flujo de Trabajo

1. **Solicitud**: Supervisor/Operador crea ticket
2. **Revisión**: Administrador revisa y aprueba/rechaza
3. **Entrega**: Administrador entrega las herramientas
4. **Completado**: Ticket marcado como entregado

### Seguimiento de Tickets

- **Supervisores/Operadores**: Ven solo sus propios tickets
- **Administradores**: Ven todos los tickets del sistema
- **Filtros**: Por estado (pendiente, aprobado, rechazado, entregado)
- **Detalles**: Información completa de cada ticket

## Funcionalidades Comunes

### Búsqueda de Productos
- **Búsqueda en tiempo real** por nombre, código, ubicación o categoría
- **Filtro de stock bajo**: Hacer clic en el indicador "Stock Bajo" en la barra de estadísticas
- **Tecla Escape**: Limpiar búsqueda y filtros
- **Mensaje de resultados**: Muestra cantidad de productos encontrados

### Navegación
- **Responsive**: Optimizado para tablets y dispositivos móviles
- **Accesibilidad**: Botones grandes para uso táctil
- **Notificaciones**: Feedback visual para todas las acciones

### Sesión de Usuario
- **Persistencia**: La sesión se mantiene activa
- **Cierre automático**: Al cerrar el navegador
- **Información visible**: Nombre, rol y botón de cerrar sesión en la parte superior

## Mejores Prácticas

### Para Supervisores y Operadores
- **Crear tickets específicos**: Incluir orden de producción y justificación clara
- **Revisar inventario**: Verificar disponibilidad antes de solicitar
- **Seguimiento**: Revisar regularmente el estado de sus tickets

### Para Administradores
- **Revisión oportuna**: Revisar tickets pendientes regularmente
- **Comentarios claros**: Proporcionar feedback al aprobar/rechazar
- **Control de inventario**: Verificar stock antes de aprobar entregas

## Solución de Problemas

### Problemas Comunes
- **Sesión expirada**: El sistema redirige automáticamente al login
- **Error de permisos**: Verificar que el rol tenga acceso a la función
- **Productos no encontrados**: Usar búsqueda o verificar filtros activos

### Contacto
Para problemas técnicos o solicitudes de acceso, contactar al administrador del sistema. 