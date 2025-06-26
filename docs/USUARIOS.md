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