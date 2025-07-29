from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import sqlite3
import uvicorn
from datetime import datetime, timedelta, timezone
from typing import List, Optional
import os
import logging
import hashlib
import secrets
import time
import qrcode
import base64
from io import BytesIO
import barcode
from barcode.writer import ImageWriter
import ipaddress
import tempfile
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Crear directorio de datos si no existe
os.makedirs("../data", exist_ok=True)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    init_database()
    
    # Obtener información de la rama y base de datos
    branch = os.getenv("BRANCH")
    if not branch:
        branch = get_current_git_branch()
    
    if branch.lower() == "desarrollo":
        db_name = "almacen_desarrollo.db"
    else:
        db_name = "almacen_main.db"
    
    print("✅ Base de datos inicializada")
    print(f"🌿 Rama configurada: {branch}")
    print(f"🗄️  Base de datos: {db_name}")
    print("🚀 Servidor listo en http://localhost:8000")
    
    yield
    # Shutdown
    print("🛑 Servidor detenido")

app = FastAPI(
    title="Sistema de Almacén Local",
    description="API para gestión de inventario en red local",
    version="1.0.0",
    lifespan=lifespan
)

# Configurar CORS para acceso desde tablet
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especificar IPs específicas
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Montar archivos estáticos
app.mount("/static", StaticFiles(directory="../frontend/static"), name="static")

# Configuración de sesiones
SESSION_CONFIG = {
    "browser_close_logout": True,  # Cerrar sesión al cerrar navegador
    "session_timeout_hours": 8,    # Tiempo máximo de sesión (solo si no se cierra navegador)
    "check_session_on_focus": True, # Verificar sesión al recuperar foco
    "log_all_logouts": True        # Registrar todos los logouts en historial
}

# Función para detectar la rama Git actual
def get_current_git_branch():
    """Detecta la rama Git actual"""
    try:
        import subprocess
        import os
        
        # Intentar desde el directorio actual
        result = subprocess.run(['git', 'branch', '--show-current'], 
                              capture_output=True, text=True, cwd='.')
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
        
        # Intentar desde el directorio padre
        result = subprocess.run(['git', 'branch', '--show-current'], 
                              capture_output=True, text=True, cwd='..')
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
        
        # Fallback: intentar con git rev-parse desde directorio actual
        result = subprocess.run(['git', 'rev-parse', '--abbrev-ref', 'HEAD'], 
                              capture_output=True, text=True, cwd='.')
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
        
        # Fallback: intentar con git rev-parse desde directorio padre
        result = subprocess.run(['git', 'rev-parse', '--abbrev-ref', 'HEAD'], 
                              capture_output=True, text=True, cwd='..')
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
            
    except Exception as e:
        logger.warning(f"No se pudo detectar la rama Git: {e}")
    
    return "main"  # Rama por defecto

# Función para obtener conexión a la base de datos
def get_db_connection():
    try:
        # Priorizar variable de entorno BRANCH sobre detección automática
        branch = os.getenv("BRANCH")
        if not branch:
            # Si no hay variable de entorno, detectar rama Git actual
            branch = get_current_git_branch()
        
        # Definir nombre de base de datos según la rama
        if branch.lower() == "desarrollo":
            db_name = "almacen_desarrollo.db"
        else:
            db_name = "almacen_main.db"
        
        db_path = f"../data/{db_name}"
        logger.info(f"Conectando a base de datos: {db_path} (rama: {branch})")
        conn = sqlite3.connect(db_path, timeout=60.0)  # Aumentar timeout a 60 segundos
        conn.row_factory = sqlite3.Row  # Permite acceso por nombre de columna
        # Configurar para mejor rendimiento y evitar bloqueos
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute("PRAGMA cache_size=20000")  # Aumentar cache
        conn.execute("PRAGMA temp_store=MEMORY")
        conn.execute("PRAGMA busy_timeout=60000")  # 60 segundos de timeout
        conn.execute("PRAGMA wal_autocheckpoint=1000")  # Checkpoint cada 1000 páginas
        return conn
    except Exception as e:
        logger.error(f"Error conectando a la base de datos: {e}")
        raise

def generar_codigo_qr(producto_id: int, nombre: str, codigo_barras: str = None) -> str:
    """Generar código QR para un producto y devolverlo como base64"""
    try:
        # Crear contenido del QR con información del producto
        contenido = f"ID:{producto_id}|Nombre:{nombre}"
        if codigo_barras:
            contenido += f"|Codigo:{codigo_barras}"
        
        # Generar QR
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(contenido)
        qr.make(fit=True)
        
        # Crear imagen
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convertir a base64
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        img_str = base64.b64encode(buffer.getvalue()).decode()
        
        return f"data:image/png;base64,{img_str}"
    except Exception as e:
        logger.error(f"Error generando QR para producto {producto_id}: {e}")
        return None

def generar_codigo_barras(producto_id: int, nombre: str, codigo_barras: str = None) -> str:
    """Generar código de barras imprimible para un producto y devolverlo como base64"""
    try:
        # Usar el código de barras existente o generar uno basado en el ID
        if codigo_barras and codigo_barras.strip():
            codigo = codigo_barras
        else:
            # Generar código de barras basado en ID (formato: 123456789012)
            codigo = f"{producto_id:012d}"
        
        # Crear código de barras Code128 (más común y legible)
        codigo_barras_obj = barcode.get('code128', codigo, writer=ImageWriter())
        
        # Configurar opciones de imagen
        options = {
            'text_distance': 1.0,
            'font_size': 12,
            'module_height': 15.0,
            'module_width': 0.2,
            'quiet_zone': 6.0,
            'background': 'white',
            'foreground': 'black'
        }
        
        # Generar imagen
        buffer = BytesIO()
        codigo_barras_obj.write(buffer, options)
        buffer.seek(0)
        
        # Convertir a base64
        img_str = base64.b64encode(buffer.getvalue()).decode()
        
        return f"data:image/png;base64,{img_str}"
    except Exception as e:
        logger.error(f"Error generando código de barras para producto {producto_id}: {e}")
        return None

def generar_ubicacion_automatica(producto_id: int) -> str:
    """Generar ubicación automática para un producto basada en su ID"""
    try:
        # Sistema de ubicaciones: A1, A2, A3... B1, B2, B3... etc.
        # Cada 10 productos cambia de letra (A1-A10, B1-B10, C1-C10...)
        letra = chr(65 + ((producto_id - 1) // 10))  # A=65, B=66, C=67...
        numero = ((producto_id - 1) % 10) + 1
        
        ubicacion = f"{letra}{numero:02d}"
        logger.info(f"Ubicación automática generada para producto {producto_id}: {ubicacion}")
        return ubicacion
    except Exception as e:
        logger.error(f"Error generando ubicación para producto {producto_id}: {e}")
        return "A01"  # Ubicación por defecto

# Inicializar base de datos
def init_database():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Crear tabla de usuarios
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                nombre_completo TEXT NOT NULL,
                email TEXT,
                rol TEXT NOT NULL CHECK (rol IN ('admin', 'supervisor', 'operador')),
                activo BOOLEAN DEFAULT 1,
                fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ultimo_acceso TIMESTAMP
            )
        ''')
        
        # Crear tabla de sesiones
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sesiones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario_id INTEGER NOT NULL,
                token TEXT UNIQUE NOT NULL,
                fecha_inicio TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                fecha_expiracion TIMESTAMP NOT NULL,
                ip_address TEXT,
                user_agent TEXT,
                activa BOOLEAN DEFAULT 1,
                FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
            )
        ''')
        
        # Crear tabla de productos
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS productos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                codigo_barras TEXT UNIQUE,
                nombre TEXT NOT NULL,
                descripcion TEXT,
                cantidad INTEGER DEFAULT 0 CHECK (cantidad >= 0),
                cantidad_minima INTEGER DEFAULT 0,
                ubicacion TEXT,
                categoria TEXT,
                precio_unitario REAL,
                codigo_qr TEXT,
                fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Crear tabla de historial
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS historial (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                accion TEXT NOT NULL,
                producto_id INTEGER,
                cantidad_anterior INTEGER,
                cantidad_nueva INTEGER,
                usuario_id INTEGER,
                usuario_nombre TEXT,
                fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                detalles TEXT,
                FOREIGN KEY (producto_id) REFERENCES productos (id),
                FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
            )
        ''')
        
        # Verificar si las columnas existen, si no, agregarlas
        cursor.execute("PRAGMA table_info(historial)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'usuario_id' not in columns:
            cursor.execute("ALTER TABLE historial ADD COLUMN usuario_id INTEGER")
            logger.info("Columna usuario_id agregada a tabla historial")
        
        if 'usuario_nombre' not in columns:
            cursor.execute("ALTER TABLE historial ADD COLUMN usuario_nombre TEXT")
            logger.info("Columna usuario_nombre agregada a tabla historial")
        
        if 'detalles' not in columns:
            cursor.execute("ALTER TABLE historial ADD COLUMN detalles TEXT")
            logger.info("Columna detalles agregada a tabla historial")
        
        # Verificar si la columna codigo_qr existe en productos, si no, agregarla
        cursor.execute("PRAGMA table_info(productos)")
        columnas_productos = [column[1] for column in cursor.fetchall()]
        
        if 'codigo_qr' not in columnas_productos:
            cursor.execute("ALTER TABLE productos ADD COLUMN codigo_qr TEXT")
            logger.info("Columna codigo_qr agregada a tabla productos")
        
        # Crear índices para rendimiento (solo para tablas que ya existen)
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_productos_nombre ON productos(nombre)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_productos_ubicacion ON productos(ubicacion)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_historial_producto ON historial(producto_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_usuarios_username ON usuarios(username)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_sesiones_token ON sesiones(token)')
        
        # Crear tabla de tickets de compra
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tickets_compra (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                numero_ticket TEXT UNIQUE NOT NULL,
                orden_produccion TEXT NOT NULL,
                justificacion TEXT NOT NULL,
                solicitante_id INTEGER NOT NULL,
                solicitante_nombre TEXT NOT NULL,
                solicitante_rol TEXT NOT NULL,
                estado TEXT DEFAULT 'pendiente' CHECK (estado IN ('pendiente', 'aprobado', 'rechazado', 'entregado', 'devuelto')),
                fecha_solicitud TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                fecha_aprobacion TIMESTAMP,
                aprobador_id INTEGER,
                aprobador_nombre TEXT,
                comentarios_aprobador TEXT,
                fecha_entrega TIMESTAMP,
                entregado_por_id INTEGER,
                entregado_por_nombre TEXT,
                FOREIGN KEY (solicitante_id) REFERENCES usuarios (id),
                FOREIGN KEY (aprobador_id) REFERENCES usuarios (id),
                FOREIGN KEY (entregado_por_id) REFERENCES usuarios (id)
            )
        ''')
        
        # Crear tabla de items del ticket
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ticket_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticket_id INTEGER NOT NULL,
                producto_id INTEGER NOT NULL,
                producto_nombre TEXT NOT NULL,
                cantidad_solicitada INTEGER NOT NULL,
                cantidad_entregada INTEGER DEFAULT 0,
                cantidad_devuelta INTEGER DEFAULT 0,
                precio_unitario REAL,
                FOREIGN KEY (ticket_id) REFERENCES tickets_compra (id) ON DELETE CASCADE,
                FOREIGN KEY (producto_id) REFERENCES productos (id)
            )
        ''')
        
        # Verificar si la columna cantidad_devuelta existe, si no, agregarla
        cursor.execute("PRAGMA table_info(ticket_items)")
        columnas_ticket_items = [column[1] for column in cursor.fetchall()]
        
        if 'cantidad_devuelta' not in columnas_ticket_items:
            cursor.execute("ALTER TABLE ticket_items ADD COLUMN cantidad_devuelta INTEGER DEFAULT 0")
            logger.info("Columna cantidad_devuelta agregada a tabla ticket_items")
            
        # Crear índices para tablas de tickets (después de crear las tablas)
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_tickets_solicitante ON tickets_compra(solicitante_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_tickets_estado ON tickets_compra(estado)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_tickets_fecha ON tickets_compra(fecha_solicitud)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_ticket_items_ticket ON ticket_items(ticket_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_ticket_items_producto ON ticket_items(producto_id)')
        
        # Crear índices para tickets (después de crear las tablas)
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_tickets_solicitante ON tickets_compra(solicitante_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_tickets_estado ON tickets_compra(estado)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_tickets_fecha ON tickets_compra(fecha_solicitud)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_ticket_items_ticket ON ticket_items(ticket_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_ticket_items_producto ON ticket_items(producto_id)')
        
        # Crear usuario administrador por defecto si no existe
        cursor.execute("SELECT COUNT(*) FROM usuarios WHERE username = 'admin'")
        if cursor.fetchone()[0] == 0:
            import hashlib
            password_hash = hashlib.sha256('admin123'.encode()).hexdigest()
            cursor.execute("""
                INSERT INTO usuarios (username, password_hash, nombre_completo, email, rol)
                VALUES (?, ?, ?, ?, ?)
            """, ('admin', password_hash, 'Administrador del Sistema', 'admin@empresa.com', 'admin'))
            logger.info("Usuario administrador creado: admin / admin123")
        
        conn.commit()
        conn.close()
        logger.info("Base de datos inicializada correctamente")
    except Exception as e:
        logger.error(f"Error inicializando base de datos: {e}")
        raise

# Rutas de la API
@app.get("/")
async def read_index(request: Request):
    """Servir la página principal o redirigir al login"""
    # Verificar si el usuario está autenticado
    user = get_current_user(request)
    if not user:
        return FileResponse("../frontend/static/login.html")
    
    return FileResponse("../frontend/static/index.html")

@app.get("/login")
async def read_login():
    """Servir la página de login"""
    return FileResponse("../frontend/static/login.html")

@app.get("/api/productos")
async def get_productos():
    """Obtener todos los productos"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, codigo_barras, nombre, descripcion, cantidad, 
                   cantidad_minima, ubicacion, categoria, precio_unitario,
                   codigo_qr, fecha_creacion, fecha_actualizacion
            FROM productos 
            ORDER BY nombre
        """)
        productos = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return {"productos": productos}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener productos: {str(e)}")

@app.get("/api/productos/{producto_id}/qr")
async def get_qr_producto(producto_id: int):
    """Obtener código QR de un producto específico"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, nombre, codigo_barras, codigo_qr
            FROM productos 
            WHERE id = ?
        """, (producto_id,))
        producto = cursor.fetchone()
        conn.close()
        
        if not producto:
            raise HTTPException(status_code=404, detail="Producto no encontrado")
        
        # Si no tiene código QR, generarlo
        if not producto["codigo_qr"]:
            codigo_qr = generar_codigo_qr(producto["id"], producto["nombre"], producto["codigo_barras"])
            if codigo_qr:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE productos SET codigo_qr = ? WHERE id = ?
                """, (codigo_qr, producto_id))
                conn.commit()
                conn.close()
                return {"qr": codigo_qr}
        
        # Verificar si el QR ya tiene el formato data:image/png;base64,
        qr_data = producto["codigo_qr"]
        if qr_data and not qr_data.startswith("data:image/png;base64,"):
            qr_data = f"data:image/png;base64,{qr_data}"
        
        return {"qr": qr_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener QR: {str(e)}")

@app.get("/api/productos/{producto_id}/barcode")
async def get_barcode_producto(producto_id: int):
    """Obtener código de barras de un producto específico"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, nombre, codigo_barras
            FROM productos 
            WHERE id = ?
        """, (producto_id,))
        producto = cursor.fetchone()
        conn.close()
        
        if not producto:
            raise HTTPException(status_code=404, detail="Producto no encontrado")
        
        # Generar código de barras
        codigo_barras = generar_codigo_barras(
            producto['id'], 
            producto['nombre'], 
            producto['codigo_barras']
        )
        
        if not codigo_barras:
            raise HTTPException(status_code=500, detail="Error generando código de barras")
        
        return {"barcode": codigo_barras}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener código de barras: {str(e)}")

@app.post("/api/productos/buscar")
async def buscar_producto_por_codigo(datos: dict):
    """Buscar un producto por su código de barras o QR"""
    try:
        codigo = datos.get("codigo")
        if not codigo:
            raise HTTPException(status_code=400, detail="El código es obligatorio")
        
        logger.info(f"Buscando producto con código: {codigo}")
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Buscar por código de barras exacto
        cursor.execute("""
            SELECT id, codigo_barras, nombre, descripcion, cantidad, 
                   cantidad_minima, ubicacion, categoria, precio_unitario
            FROM productos 
            WHERE codigo_barras = ?
        """, (codigo,))
        producto = cursor.fetchone()
        
        # Si no se encuentra, buscar por ID si el código contiene "ID:"
        if not producto and "ID:" in codigo:
            try:
                # Extraer el ID del formato "ID:8|Nombre:Popote"
                id_part = codigo.split("|")[0]
                producto_id = int(id_part.replace("ID:", ""))
                
                cursor.execute("""
                    SELECT id, codigo_barras, nombre, descripcion, cantidad, 
                           cantidad_minima, ubicacion, categoria, precio_unitario
                    FROM productos 
                    WHERE id = ?
                """, (producto_id,))
                producto = cursor.fetchone()
                logger.info(f"Buscando por ID extraído: {producto_id}")
            except (ValueError, IndexError) as e:
                logger.warning(f"Error extrayendo ID del código QR: {e}")
        
        # Si aún no se encuentra, buscar por nombre en el contenido del QR
        if not producto and "|" in codigo:
            try:
                # Extraer el nombre del formato "ID:8|Nombre:Popote"
                nombre_part = codigo.split("|")[1]
                nombre = nombre_part.replace("Nombre:", "").strip()
                
                cursor.execute("""
                    SELECT id, codigo_barras, nombre, descripcion, cantidad, 
                           cantidad_minima, ubicacion, categoria, precio_unitario
                    FROM productos 
                    WHERE nombre LIKE ?
                """, (f"%{nombre}%",))
                producto = cursor.fetchone()
                logger.info(f"Buscando por nombre extraído: {nombre}")
            except (IndexError, Exception) as e:
                logger.warning(f"Error extrayendo nombre del código QR: {e}")
        
        # Si aún no se encuentra, buscar por cualquier parte del código en el nombre
        if not producto:
            cursor.execute("""
                SELECT id, codigo_barras, nombre, descripcion, cantidad, 
                       cantidad_minima, ubicacion, categoria, precio_unitario
                FROM productos 
                WHERE nombre LIKE ? OR codigo_barras LIKE ?
            """, (f"%{codigo}%", f"%{codigo}%"))
            producto = cursor.fetchone()
        
        conn.close()
        
        if not producto:
            raise HTTPException(status_code=404, detail="Producto no encontrado")
        
        logger.info(f"Producto encontrado: {producto['nombre']}")
        return {"producto": dict(producto)}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error buscando producto: {e}")
        raise HTTPException(status_code=500, detail=f"Error buscando producto: {str(e)}")

def require_supervisor_or_operator(user):
    """Verificar que el usuario sea supervisor u operador"""
    if not user:
        raise HTTPException(status_code=401, detail="Autenticación requerida")
    
    if user["rol"] not in ["supervisor", "operador"]:
        logger.warning(f"Usuario {user['username']} intentó acceder a función de ticket sin permisos")
        raise HTTPException(
            status_code=403, 
            detail="Acceso denegado. Solo supervisores y operadores pueden solicitar herramientas."
        )
    
    return user

def require_admin(user):
    """Verificar que el usuario sea administrador"""
    if not user:
        raise HTTPException(status_code=401, detail="Autenticación requerida")
    
    if user["rol"] != "admin":
        logger.warning(f"Usuario {user['username']} intentó acceder a función de administrador sin permisos")
        raise HTTPException(
            status_code=403, 
            detail="Acceso denegado. Solo administradores pueden realizar esta acción."
        )
    
    return user

def require_auth(user):
    """Verificar que el usuario esté autenticado"""
    if not user:
        raise HTTPException(status_code=401, detail="Autenticación requerida")
    return user

@app.post("/api/productos")
async def crear_producto(producto: dict, request: Request):
    """Crear un nuevo producto - Solo administradores"""
    try:
        # Verificar que el usuario sea administrador
        current_user = get_current_user(request)
        require_admin(current_user)
        
        logger.info(f"Administrador {current_user['username']} creando producto: {producto}")
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Validar datos
        if not producto.get("nombre"):
            raise HTTPException(status_code=400, detail="El nombre es obligatorio")
        
        # Limpiar y convertir valores
        codigo_barras = producto.get("codigo_barras", "").strip() or None
        nombre = producto["nombre"].strip()
        descripcion = producto.get("descripcion", "").strip() or None
        ubicacion = producto.get("ubicacion", "").strip() or None
        categoria = producto.get("categoria", "").strip() or None
        
        # Convertir valores numéricos con manejo de errores
        try:
            cantidad = int(producto.get("cantidad", 0)) if producto.get("cantidad") else 0
        except (ValueError, TypeError):
            cantidad = 0
            
        try:
            cantidad_minima = int(producto.get("cantidad_minima", 0)) if producto.get("cantidad_minima") else 0
        except (ValueError, TypeError):
            cantidad_minima = 0
            
        try:
            precio_unitario = float(producto.get("precio_unitario", 0)) if producto.get("precio_unitario") else None
        except (ValueError, TypeError):
            precio_unitario = None
        
        if cantidad < 0:
            raise HTTPException(status_code=400, detail="La cantidad no puede ser negativa")
        
        logger.info(f"Datos procesados: nombre='{nombre}', cantidad={cantidad}, precio={precio_unitario}")
        
        # Insertar producto primero para obtener el ID
        cursor.execute("""
            INSERT INTO productos (codigo_barras, nombre, descripcion, cantidad, 
                                  cantidad_minima, ubicacion, categoria, precio_unitario)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            codigo_barras,
            nombre,
            descripcion,
            cantidad,
            cantidad_minima,
            ubicacion,
            categoria,
            precio_unitario
        ))
        
        producto_id = cursor.lastrowid
        
        # Si no se proporcionó código de barras, generar uno automáticamente
        if not codigo_barras:
            codigo_barras = f"{producto_id:012d}"
            cursor.execute("""
                UPDATE productos SET codigo_barras = ? WHERE id = ?
            """, (codigo_barras, producto_id))
            logger.info(f"Código de barras generado automáticamente: {codigo_barras}")
        
        # Si no se proporcionó ubicación, generar una automáticamente
        if not ubicacion:
            ubicacion = generar_ubicacion_automatica(producto_id)
            cursor.execute("""
                UPDATE productos SET ubicacion = ? WHERE id = ?
            """, (ubicacion, producto_id))
            logger.info(f"Ubicación generada automáticamente: {ubicacion}")
        
        # Generar código QR automáticamente
        codigo_qr = generar_codigo_qr(producto_id, nombre, codigo_barras)
        
        # Actualizar el producto con el código QR generado
        if codigo_qr:
            cursor.execute("""
                UPDATE productos SET codigo_qr = ? WHERE id = ?
            """, (codigo_qr, producto_id))
            logger.info(f"Código QR generado para producto {producto_id}")
        
        # Registrar en historial con usuario actual
        try:
            cursor.execute("""
                INSERT INTO historial (accion, producto_id, cantidad_anterior, cantidad_nueva, usuario_id, usuario_nombre)
                VALUES (?, ?, ?, ?, ?, ?)
            """, ("crear", producto_id, 0, cantidad, current_user["id"], current_user["nombre_completo"]))
        except sqlite3.OperationalError as e:
            # Si hay error con las columnas, registrar sin ellas
            logger.warning(f"Error registrando en historial: {e}")
            cursor.execute("""
                INSERT INTO historial (accion, producto_id, cantidad_anterior, cantidad_nueva)
                VALUES (?, ?, ?, ?)
            """, ("crear", producto_id, 0, cantidad))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Producto creado exitosamente con ID: {producto_id}")
        return {"mensaje": "Herramienta creada exitosamente", "id": producto_id}
    except sqlite3.IntegrityError as e:
        logger.error(f"Error de integridad: {e}")
        raise HTTPException(status_code=400, detail="El código de barras ya existe")
    except Exception as e:
        logger.error(f"Error al crear producto: {e}")
        raise HTTPException(status_code=500, detail=f"Error al crear herramienta: {str(e)}")

@app.put("/api/productos/{producto_id}")
async def actualizar_producto(producto_id: int, producto: dict, request: Request):
    """Actualizar un producto existente - Solo administradores"""
    try:
        # Verificar que el usuario sea administrador
        current_user = get_current_user(request)
        require_admin(current_user)
        
        logger.info(f"Administrador {current_user['username']} actualizando producto {producto_id}")
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Obtener cantidad anterior
        cursor.execute("SELECT cantidad FROM productos WHERE id = ?", (producto_id,))
        result = cursor.fetchone()
        if not result:
            raise HTTPException(status_code=404, detail="Producto no encontrado")
        
        cantidad_anterior = result["cantidad"]
        
        # Actualizar producto
        cursor.execute("""
            UPDATE productos 
            SET nombre = ?, descripcion = ?, cantidad = ?, cantidad_minima = ?,
                ubicacion = ?, categoria = ?, precio_unitario = ?, fecha_actualizacion = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (
            producto.get("nombre"),
            producto.get("descripcion"),
            producto.get("cantidad", 0),
            producto.get("cantidad_minima", 0),
            producto.get("ubicacion"),
            producto.get("categoria"),
            producto.get("precio_unitario"),
            producto_id
        ))
        
        # Registrar en historial
        cursor.execute("""
            INSERT INTO historial (accion, producto_id, cantidad_anterior, cantidad_nueva, usuario_id, usuario_nombre)
            VALUES (?, ?, ?, ?, ?, ?)
        """, ("actualizar", producto_id, cantidad_anterior, producto.get("cantidad", 0), current_user["id"], current_user["nombre_completo"]))
        
        conn.commit()
        conn.close()
        
        return {"mensaje": "Herramienta actualizada exitosamente"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al actualizar herramienta: {str(e)}")

@app.delete("/api/productos/{producto_id}")
async def eliminar_producto(producto_id: int, request: Request):
    """Eliminar un producto - Solo administradores"""
    try:
        # Verificar que el usuario sea administrador
        current_user = get_current_user(request)
        require_admin(current_user)
        
        logger.info(f"Administrador {current_user['username']} eliminando producto {producto_id}")
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Verificar si existe
        cursor.execute("SELECT id FROM productos WHERE id = ?", (producto_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Herramienta no encontrada")
        
        # Eliminar producto
        cursor.execute("DELETE FROM productos WHERE id = ?", (producto_id,))
        
        # Registrar en historial
        cursor.execute("""
            INSERT INTO historial (accion, producto_id, cantidad_anterior, cantidad_nueva, usuario_id, usuario_nombre)
            VALUES (?, ?, ?, ?, ?, ?)
        """, ("eliminar", producto_id, 0, 0, current_user["id"], current_user["nombre_completo"]))
        
        conn.commit()
        conn.close()
        
        return {"mensaje": "Herramienta eliminada exitosamente"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al eliminar herramienta: {str(e)}")

@app.get("/api/historial")
async def get_historial():
    """Obtener historial de acciones"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT h.*, p.nombre as producto_nombre
            FROM historial h
            LEFT JOIN productos p ON h.producto_id = p.id
            ORDER BY h.fecha DESC
            LIMIT 100
        """)
        historial = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return {"historial": historial}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener historial: {str(e)}")

@app.get("/api/estadisticas")
async def get_estadisticas():
    """Obtener estadísticas del almacén"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Total de productos
        cursor.execute("SELECT COUNT(*) as total FROM productos")
        total_productos = cursor.fetchone()["total"]
        
        # Productos con stock bajo
        cursor.execute("""
            SELECT COUNT(*) as stock_bajo 
            FROM productos 
            WHERE cantidad <= cantidad_minima AND cantidad_minima > 0
        """)
        stock_bajo = cursor.fetchone()["stock_bajo"]
        
        # Valor total del inventario
        cursor.execute("""
            SELECT SUM(cantidad * COALESCE(precio_unitario, 0)) as valor_total 
            FROM productos
        """)
        valor_total = cursor.fetchone()["valor_total"] or 0
        
        conn.close()
        
        return {
            "total_productos": total_productos,
            "stock_bajo": stock_bajo,
            "valor_total": round(valor_total, 2)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener estadísticas: {str(e)}")

# Funciones de autenticación
def hash_password(password):
    """Generar hash de contraseña"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password, password_hash):
    """Verificar contraseña"""
    return hash_password(password) == password_hash

def generate_token():
    """Generar token de sesión"""
    return secrets.token_urlsafe(32)

def create_session(user_id, ip_address, user_agent):
    """Crear nueva sesión"""
    conn = None
    max_retries = 5  # Aumentar de 3 a 5 reintentos
    retry_count = 0
    
    logger.info(f"Iniciando creación de sesión para usuario {user_id}")
    
    while retry_count < max_retries:
        try:
            logger.debug(f"Intento {retry_count + 1} de crear sesión")
            conn = get_db_connection()
            cursor = conn.cursor()
            
            token = generate_token()
            logger.debug(f"Token generado: {token[:20]}...")
            
            # Usar UTC para evitar problemas de zona horaria
            now_utc = datetime.now(timezone.utc)
            
            # Si está configurado para cerrar al cerrar navegador, usar tiempo más corto
            if SESSION_CONFIG["browser_close_logout"]:
                expiration = now_utc + timedelta(hours=1)  # 1 hora como respaldo
            else:
                expiration = now_utc + timedelta(hours=SESSION_CONFIG["session_timeout_hours"])
            
            logger.debug(f"Fecha de expiración: {expiration.isoformat()}")
            
            cursor.execute("""
                INSERT INTO sesiones (usuario_id, token, fecha_expiracion, ip_address, user_agent)
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, token, expiration.isoformat(), ip_address, user_agent))
            
            logger.debug("Sesión insertada en la base de datos")
            
            # Actualizar último acceso
            cursor.execute("""
                UPDATE usuarios SET ultimo_acceso = CURRENT_TIMESTAMP WHERE id = ?
            """, (user_id,))
            
            logger.debug("Último acceso actualizado")
            
            conn.commit()
            logger.info(f"Nueva sesión creada para usuario {user_id} desde {ip_address}")
            
            # Cerrar conexión antes de retornar
            if conn:
                try:
                    conn.close()
                except:
                    pass
            
            return token
            
        except sqlite3.OperationalError as e:
            if "database is locked" in str(e) and retry_count < max_retries - 1:
                retry_count += 1
                logger.warning(f"Base de datos bloqueada, reintentando ({retry_count}/{max_retries})")
                if conn:
                    try:
                        conn.close()
                    except:
                        pass
                import time
                time.sleep(1 * retry_count)  # Espera lineal más larga
                continue
            else:
                logger.error(f"Error creando sesión después de {retry_count + 1} intentos: {e}")
                if conn:
                    conn.rollback()
                raise
        except Exception as e:
            logger.error(f"Error creando sesión: {e}")
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                try:
                    conn.close()
                except:
                    pass
    
    # Si llegamos aquí, significa que se agotaron los reintentos
    logger.error("No se pudo crear la sesión después de todos los reintentos")
    raise Exception("No se pudo crear la sesión después de múltiples intentos")

def validate_session(token):
    """Validar sesión activa"""
    if not token:
        logger.debug("No se proporcionó token")
        return None
    
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Usar UTC para la comparación
        now_utc = datetime.now(timezone.utc)
        
        cursor.execute("""
            SELECT s.*, u.username, u.nombre_completo, u.rol, u.activo
            FROM sesiones s
            JOIN usuarios u ON s.usuario_id = u.id
            WHERE s.token = ? AND s.activa = 1
        """, (token,))
        
        session = cursor.fetchone()
        
        if session:
            # Verificar si la sesión no ha expirado
            try:
                expiration = datetime.fromisoformat(session["fecha_expiracion"].replace('Z', '+00:00'))
                if now_utc < expiration:
                    logger.debug(f"Sesión válida encontrada para usuario: {session['username']}")
                    return session
                else:
                    logger.debug(f"Sesión expirada para usuario: {session['username']}")
                    return None
            except Exception as e:
                logger.error(f"Error parseando fecha de expiración: {e}")
                return None
        else:
            logger.debug(f"Token no encontrado: {token[:20]}...")
            return None
        
    except Exception as e:
        logger.error(f"Error validando sesión: {e}")
        return None
    finally:
        if conn:
            try:
                conn.close()
            except:
                pass

def get_current_user(request):
    """Obtener usuario actual desde el token"""
    token = request.cookies.get("session_token")
    if not token:
        logger.debug("No se encontró cookie session_token")
        return None
    
    logger.debug(f"Validando token: {token[:20]}...")
    session = validate_session(token)
    if not session:
        logger.debug("Sesión inválida o expirada")
        return None
    
    user_info = {
        "id": session["usuario_id"],
        "username": session["username"],
        "nombre_completo": session["nombre_completo"],
        "rol": session["rol"]
    }
    logger.debug(f"Usuario autenticado: {user_info['username']}")
    return user_info

# Rutas de autenticación
@app.post("/api/auth/login")
async def login(request: Request, credentials: dict):
    """Iniciar sesión"""
    conn = None
    try:
        username = credentials.get("username")
        password = credentials.get("password")
        
        if not username or not password:
            raise HTTPException(status_code=400, detail="Usuario y contraseña son requeridos")
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Verificar usuario
        cursor.execute("""
            SELECT id, username, password_hash, nombre_completo, rol, activo
            FROM usuarios 
            WHERE username = ?
        """, (username,))
        
        user = cursor.fetchone()
        
        if not user:
            raise HTTPException(status_code=401, detail="Usuario o contraseña incorrectos")
        
        if not user["activo"]:
            raise HTTPException(status_code=401, detail="Usuario desactivado")
        
        if not verify_password(password, user["password_hash"]):
            raise HTTPException(status_code=401, detail="Usuario o contraseña incorrectos")
        
        # Crear sesión
        user_agent = request.headers.get("user-agent", "")
        ip_address = request.client.host
        token = create_session(user["id"], ip_address, user_agent)
        
        if not token:
            logger.error("No se pudo crear la sesión: token es None")
            raise HTTPException(status_code=500, detail="No se pudo crear la sesión")
        
        logger.info(f"Usuario {username} inició sesión desde {ip_address}")
        
        response = {
            "mensaje": "Inicio de sesión exitoso",
            "usuario": {
                "id": user["id"],
                "username": user["username"],
                "nombre_completo": user["nombre_completo"],
                "rol": user["rol"]
            }
        }
        
        # Crear respuesta con cookie
        json_response = JSONResponse(content=response)
        json_response.set_cookie(
            key="session_token",
            value=token,
            httponly=True,
            secure=False,  # Cambiar a True en producción con HTTPS
            samesite="lax",
            domain=None,  # Usar None para evitar problemas con .localhost
            path="/"
            # max_age eliminado para que la sesión se cierre al cerrar el navegador
        )
        
        logger.info(f"Cookie configurada: session_token={token[:20]}... domain=None")
        
        return json_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en login: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")
    finally:
        if conn:
            try:
                conn.close()
            except:
                pass

@app.post("/api/auth/logout")
async def logout(request: Request):
    """Cerrar sesión"""
    try:
        token = request.cookies.get("session_token")
        if token:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Marcar la sesión como inactiva
            cursor.execute("UPDATE sesiones SET activa = 0 WHERE token = ?", (token,))
            
            # Registrar el logout en el historial (verificar si las columnas existen)
            try:
                cursor.execute("""
                    SELECT usuario_id, u.nombre_completo 
                    FROM sesiones s 
                    JOIN usuarios u ON s.usuario_id = u.id 
                    WHERE s.token = ?
                """, (token,))
                
                session_info = cursor.fetchone()
                if session_info:
                    cursor.execute("""
                        INSERT INTO historial (accion, usuario_id, usuario_nombre, detalles)
                        VALUES (?, ?, ?, ?)
                    """, ("logout", session_info[0], session_info[1], f"Logout desde {request.client.host}"))
            except sqlite3.OperationalError as e:
                # Si las columnas no existen, registrar sin ellas
                logger.warning(f"No se pudo registrar logout en historial: {e}")
                cursor.execute("""
                    INSERT INTO historial (accion, detalles)
                    VALUES (?, ?)
                """, ("logout", f"Logout desde {request.client.host}"))
            
            conn.commit()
            conn.close()
        
        from fastapi.responses import JSONResponse
        response = JSONResponse(content={"mensaje": "Sesión cerrada exitosamente"})
        response.delete_cookie(
            key="session_token",
            domain=None,  # Usar None para que coincida con la configuración de login
            path="/"
        )
        return response
        
    except Exception as e:
        logger.error(f"Error en logout: {e}")
        # Aún así, intentar eliminar la cookie
        from fastapi.responses import JSONResponse
        response = JSONResponse(content={"mensaje": "Sesión cerrada"})
        response.delete_cookie(
            key="session_token",
            domain=None,
            path="/"
        )
        return response

@app.get("/api/auth/me")
async def get_current_user_info(request: Request):
    """Obtener información del usuario actual"""
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="No autenticado")
    
    return {"usuario": user}

@app.get("/api/auth/check")
async def check_auth(request: Request):
    """Verificar si el usuario está autenticado"""
    logger.info(f"Check auth - Cookies: {dict(request.cookies)}")
    user = get_current_user(request)
    result = {"autenticado": user is not None, "usuario": user}
    logger.info(f"Check auth result: {result}")
    return result

def generar_numero_ticket() -> str:
    """Generar número único de ticket"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Obtener el último ticket para generar número secuencial
        cursor.execute("SELECT MAX(CAST(SUBSTR(numero_ticket, 6) AS INTEGER)) FROM tickets_compra")
        ultimo_numero = cursor.fetchone()[0]
        
        if ultimo_numero is None:
            ultimo_numero = 0
        
        nuevo_numero = ultimo_numero + 1
        numero_ticket = f"TICK-{nuevo_numero:06d}"
        
        conn.close()
        return numero_ticket
    except Exception as e:
        logger.error(f"Error generando número de ticket: {e}")
        # Fallback con timestamp
        import time
        return f"TICK-{int(time.time())}"

@app.post("/api/tickets")
async def crear_ticket_compra(ticket: dict, request: Request):
    """Crear un nuevo ticket de compra - Solo supervisores y operadores"""
    try:
        # Verificar que el usuario sea supervisor u operador
        current_user = get_current_user(request)
        require_supervisor_or_operator(current_user)
        
        logger.info(f"Usuario {current_user['username']} creando ticket de compra")
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Validar datos del ticket
        if not ticket.get("orden_produccion"):
            raise HTTPException(status_code=400, detail="Orden de producción es obligatoria")
        
        if not ticket.get("justificacion"):
            raise HTTPException(status_code=400, detail="Justificación es obligatoria")
        
        # Validar items del ticket
        items = ticket.get("items", [])
        if not items or len(items) == 0:
            raise HTTPException(status_code=400, detail="El ticket debe contener al menos una herramienta")
        
        # Verificar que todos los productos existen
        productos_ids = [item["producto_id"] for item in items]
        placeholders = ','.join(['?' for _ in productos_ids])
        cursor.execute(f"SELECT id, nombre FROM productos WHERE id IN ({placeholders})", productos_ids)
        productos_existentes = {row["id"]: row["nombre"] for row in cursor.fetchall()}
        
        if len(productos_existentes) != len(productos_ids):
            raise HTTPException(status_code=400, detail="Uno o más productos no existen")
        
        # Generar número de ticket
        numero_ticket = generar_numero_ticket()
        
        # Crear ticket principal
        cursor.execute("""
            INSERT INTO tickets_compra (
                numero_ticket, orden_produccion, justificacion, solicitante_id, solicitante_nombre, solicitante_rol
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (
            numero_ticket,
            ticket["orden_produccion"],
            ticket["justificacion"],
            current_user["id"],
            current_user["nombre_completo"],
            current_user["rol"]
        ))
        
        ticket_id = cursor.lastrowid
        
        # Crear items del ticket
        for item in items:
            cursor.execute("""
                INSERT INTO ticket_items (
                    ticket_id, producto_id, producto_nombre, cantidad_solicitada, precio_unitario
                ) VALUES (?, ?, ?, ?, ?)
            """, (
                ticket_id,
                item["producto_id"],
                productos_existentes[item["producto_id"]],
                item["cantidad_solicitada"],
                item.get("precio_unitario")
            ))
            
            # Registrar en historial
            try:
                cursor.execute("""
                    INSERT INTO historial (accion, producto_id, usuario_id, usuario_nombre, detalles)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    "solicitud_compra",
                    item["producto_id"],
                    current_user["id"],
                    current_user["nombre_completo"],
                    f"Ticket {numero_ticket} - Orden: {ticket['orden_produccion']} - Cantidad: {item['cantidad_solicitada']}"
                ))
            except sqlite3.OperationalError as e:
                logger.warning(f"Error registrando en historial: {e}")
        
        conn.commit()
        conn.close()
        
        logger.info(f"Ticket {numero_ticket} creado exitosamente por {current_user['username']} con {len(items)} herramientas")
        return {
            "mensaje": "Ticket de compra creado exitosamente",
            "id": ticket_id,
            "numero_ticket": numero_ticket,
            "total_herramientas": len(items)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al crear ticket de compra: {e}")
        raise HTTPException(status_code=500, detail=f"Error al crear ticket: {str(e)}")

@app.get("/api/tickets")
async def listar_tickets(request: Request, estado: str = None, limit: int = 50):
    """Listar tickets de compra - Filtrado por rol del usuario"""
    try:
        current_user = get_current_user(request)
        require_auth(current_user)
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Construir query base
        query = """
            SELECT 
                t.id, t.numero_ticket, t.orden_produccion, t.justificacion,
                t.solicitante_id, t.solicitante_nombre, t.solicitante_rol, t.estado,
                t.fecha_solicitud, t.fecha_aprobacion, t.aprobador_nombre,
                t.comentarios_aprobador, t.fecha_entrega, t.entregado_por_nombre,
                COUNT(ti.id) as total_items,
                SUM(ti.cantidad_solicitada) as total_cantidad_solicitada
            FROM tickets_compra t
            LEFT JOIN ticket_items ti ON t.id = ti.ticket_id
        """
        
        params = []
        where_conditions = []
        
        # Filtrar por rol del usuario
        if current_user["rol"] == "admin":
            # Administradores ven todos los tickets
            pass
        elif current_user["rol"] in ["supervisor", "operador"]:
            # Supervisores y operadores solo ven sus propios tickets
            where_conditions.append("t.solicitante_id = ?")
            params.append(current_user["id"])
        
        # Filtrar por estado si se especifica
        if estado:
            where_conditions.append("t.estado = ?")
            params.append(estado)
        
        if where_conditions:
            query += " WHERE " + " AND ".join(where_conditions)
        
        query += " GROUP BY t.id ORDER BY t.fecha_solicitud DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        tickets = [dict(row) for row in cursor.fetchall()]
        
        # Obtener items de cada ticket
        for ticket in tickets:
            cursor.execute("""
                SELECT ti.id, ti.producto_id, ti.producto_nombre, ti.cantidad_solicitada, 
                       ti.cantidad_entregada, ti.precio_unitario
                FROM ticket_items ti
                WHERE ti.ticket_id = ?
                ORDER BY ti.producto_nombre
            """, (ticket["id"],))
            ticket["items"] = [dict(item) for item in cursor.fetchall()]
        
        conn.close()
        
        return {
            "tickets": tickets,
            "total": len(tickets)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al listar tickets: {e}")
        raise HTTPException(status_code=500, detail=f"Error al obtener tickets: {str(e)}")

@app.put("/api/tickets/{ticket_id}/aprobar")
async def aprobar_ticket(ticket_id: int, decision: dict, request: Request):
    """Aprobar o rechazar un ticket - Solo administradores"""
    try:
        current_user = get_current_user(request)
        require_admin(current_user)
        
        accion = decision.get("accion")  # "aprobar" o "rechazar"
        comentarios = decision.get("comentarios", "")
        
        if accion not in ["aprobar", "rechazar"]:
            raise HTTPException(status_code=400, detail="Acción debe ser 'aprobar' o 'rechazar'")
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Verificar que el ticket existe y está pendiente
        cursor.execute("""
            SELECT id, numero_ticket, estado, solicitante_nombre
            FROM tickets_compra 
            WHERE id = ?
        """, (ticket_id,))
        
        ticket = cursor.fetchone()
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket no encontrado")
        
        # Convertir a diccionario
        ticket = dict(ticket)
        
        if ticket["estado"] != "pendiente":
            raise HTTPException(status_code=400, detail="Solo se pueden aprobar/rechazar tickets pendientes")
        
        # Actualizar estado del ticket
        nuevo_estado = "aprobado" if accion == "aprobar" else "rechazado"
        fecha_aprobacion = datetime.now().isoformat() if accion == "aprobar" else None
        
        cursor.execute("""
            UPDATE tickets_compra 
            SET estado = ?, fecha_aprobacion = ?, aprobador_id = ?, aprobador_nombre = ?, comentarios_aprobador = ?
            WHERE id = ?
        """, (
            nuevo_estado,
            fecha_aprobacion,
            current_user["id"],
            current_user["nombre_completo"],
            comentarios,
            ticket_id
        ))
        
        # Registrar en historial
        try:
            cursor.execute("""
                INSERT INTO historial (accion, usuario_id, usuario_nombre, detalles)
                VALUES (?, ?, ?, ?)
            """, (
                f"ticket_{accion}",
                current_user["id"],
                current_user["nombre_completo"],
                f"Ticket {ticket['numero_ticket']} {accion} - Comentarios: {comentarios}"
            ))
        except sqlite3.OperationalError as e:
            logger.warning(f"Error registrando en historial: {e}")
        
        conn.commit()
        conn.close()
        
        logger.info(f"Ticket {ticket['numero_ticket']} {accion} por {current_user['username']}")
        return {
            "mensaje": f"Ticket {accion} exitosamente",
            "numero_ticket": ticket["numero_ticket"],
            "estado": nuevo_estado
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al {accion} ticket: {e}")
        raise HTTPException(status_code=500, detail=f"Error al procesar ticket: {str(e)}")

@app.put("/api/tickets/{ticket_id}/entregar")
async def entregar_ticket(ticket_id: int, entrega: dict, request: Request):
    """Entregar herramientas de un ticket aprobado - Solo administradores"""
    try:
        current_user = get_current_user(request)
        require_admin(current_user)
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Verificar que el ticket existe y está aprobado
        cursor.execute("""
            SELECT id, numero_ticket, estado, solicitante_nombre
            FROM tickets_compra 
            WHERE id = ?
        """, (ticket_id,))
        
        ticket = cursor.fetchone()
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket no encontrado")
        
        if ticket["estado"] != "aprobado":
            raise HTTPException(status_code=400, detail="Solo se pueden entregar tickets aprobados")
        
        # Obtener items del ticket
        cursor.execute("""
            SELECT ti.id, ti.producto_id, ti.producto_nombre, ti.cantidad_solicitada, ti.cantidad_entregada
            FROM ticket_items ti
            WHERE ti.ticket_id = ?
        """, (ticket_id,))
        
        items = [dict(item) for item in cursor.fetchall()]
        
        # Procesar entregas
        items_entregados = entrega.get("items", [])
        for item_entrega in items_entregados:
            item_id = item_entrega.get("item_id")
            cantidad_entregada = item_entrega.get("cantidad_entregada", 0)
            
            # Encontrar el item correspondiente
            item_ticket = next((item for item in items if item["id"] == item_id), None)
            if not item_ticket:
                continue
            
            # Verificar que no se entregue más de lo solicitado
            if cantidad_entregada > item_ticket["cantidad_solicitada"]:
                raise HTTPException(
                    status_code=400, 
                    detail=f"No se puede entregar más de lo solicitado para {item_ticket['producto_nombre']}"
                )
            
            # Verificar stock disponible antes de entregar
            cursor.execute("""
                SELECT cantidad FROM productos WHERE id = ?
            """, (item_ticket["producto_id"],))
            
            stock_result = cursor.fetchone()
            if not stock_result:
                raise HTTPException(
                    status_code=400,
                    detail=f"Producto {item_ticket['producto_nombre']} no encontrado en inventario"
                )
            
            stock_actual = stock_result["cantidad"]
            if stock_actual < cantidad_entregada:
                raise HTTPException(
                    status_code=400,
                    detail=f"Stock insuficiente para {item_ticket['producto_nombre']}. Disponible: {stock_actual}, Solicitado: {cantidad_entregada}"
                )
            
            # Actualizar cantidad entregada
            cursor.execute("""
                UPDATE ticket_items 
                SET cantidad_entregada = ?
                WHERE id = ?
            """, (cantidad_entregada, item_id))
            
            # Actualizar inventario si se entregó algo
            if cantidad_entregada > 0:
                cursor.execute("""
                    UPDATE productos 
                    SET cantidad = cantidad - ?
                    WHERE id = ?
                """, (cantidad_entregada, item_ticket["producto_id"]))
                
                # Registrar en historial
                try:
                    cursor.execute("""
                        INSERT INTO historial (accion, producto_id, usuario_id, usuario_nombre, detalles)
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        "entrega_ticket",
                        item_ticket["producto_id"],
                        current_user["id"],
                        current_user["nombre_completo"],
                        f"Ticket {ticket['numero_ticket']} - Entregado: {cantidad_entregada} unidades"
                    ))
                except sqlite3.OperationalError as e:
                    logger.warning(f"Error registrando en historial: {e}")
        
        # Verificar si todos los items fueron entregados
        cursor.execute("""
            SELECT 
                SUM(cantidad_solicitada) as total_solicitado,
                SUM(cantidad_entregada) as total_entregado
            FROM ticket_items 
            WHERE ticket_id = ?
        """, (ticket_id,))
        
        totales = dict(cursor.fetchone())
        nuevo_estado = "entregado" if totales["total_entregado"] >= totales["total_solicitado"] else "aprobado"
        
        # Actualizar estado del ticket
        fecha_entrega = datetime.now().isoformat() if nuevo_estado == "entregado" else None
        
        cursor.execute("""
            UPDATE tickets_compra 
            SET estado = ?, fecha_entrega = ?, entregado_por_id = ?, entregado_por_nombre = ?
            WHERE id = ?
        """, (
            nuevo_estado,
            fecha_entrega,
            current_user["id"],
            current_user["nombre_completo"],
            ticket_id
        ))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Ticket {ticket['numero_ticket']} entregado por {current_user['username']}")
        return {
            "mensaje": "Entrega procesada exitosamente",
            "numero_ticket": ticket["numero_ticket"],
            "estado": nuevo_estado,
            "items_entregados": len(items_entregados)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al entregar ticket: {e}")
        raise HTTPException(status_code=500, detail=f"Error al procesar entrega: {str(e)}")

@app.get("/api/tickets/{ticket_id}")
async def obtener_ticket(ticket_id: int, request: Request):
    """Obtener un ticket específico por ID"""
    try:
        current_user = get_current_user(request)
        require_auth(current_user)
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Obtener ticket principal
        cursor.execute("""
            SELECT 
                t.id, t.numero_ticket, t.orden_produccion, t.justificacion,
                t.solicitante_id, t.solicitante_nombre, t.solicitante_rol, t.estado,
                t.fecha_solicitud, t.fecha_aprobacion, t.aprobador_nombre,
                t.comentarios_aprobador, t.fecha_entrega, t.entregado_por_nombre
            FROM tickets_compra t
            WHERE t.id = ?
        """, (ticket_id,))
        
        ticket = cursor.fetchone()
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket no encontrado")
        
        # Convertir a diccionario
        ticket = dict(ticket)
        
        # Verificar permisos
        if current_user["rol"] not in ["admin"] and ticket["solicitante_id"] != current_user["id"]:
            raise HTTPException(status_code=403, detail="No tienes permisos para ver este ticket")
        
        # Obtener items del ticket
        cursor.execute("""
            SELECT ti.id, ti.producto_id, ti.producto_nombre, ti.cantidad_solicitada, 
                   ti.cantidad_entregada, ti.cantidad_devuelta, ti.precio_unitario
            FROM ticket_items ti
            WHERE ti.ticket_id = ?
            ORDER BY ti.producto_nombre
        """, (ticket_id,))
        
        ticket["items"] = [dict(item) for item in cursor.fetchall()]
        
        # Obtener fecha de devolución y usuario que devolvió desde el historial
        cursor.execute("""
            SELECT h.fecha, h.usuario_nombre
            FROM historial h
            WHERE h.accion IN ('devolucion_buen_estado', 'devolucion_mal_estado', 'devolucion')
            AND h.detalles LIKE ?
            ORDER BY h.fecha DESC
            LIMIT 1
        """, (f"%{ticket['numero_ticket']}%",))
        
        devolucion_result = cursor.fetchone()
        if devolucion_result:
            ticket["fecha_devolucion"] = devolucion_result[0]
            ticket["devuelto_por_nombre"] = devolucion_result[1]
        else:
            ticket["fecha_devolucion"] = None
            ticket["devuelto_por_nombre"] = None
        
        conn.close()
        
        return ticket
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al obtener ticket {ticket_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error al obtener ticket: {str(e)}")

def generar_pdf_ticket(ticket_data: dict) -> bytes:
    """Generar PDF del ticket con información completa"""
    try:
        # Crear archivo temporal
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            doc = SimpleDocTemplate(tmp_file.name, pagesize=A4)
            story = []
            
            # Estilos
            styles = getSampleStyleSheet()
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=18,
                spaceAfter=30,
                alignment=TA_CENTER,
                textColor=colors.darkblue
            )
            
            subtitle_style = ParagraphStyle(
                'CustomSubtitle',
                parent=styles['Heading2'],
                fontSize=14,
                spaceAfter=20,
                alignment=TA_CENTER,
                textColor=colors.darkblue
            )
            
            normal_style = styles['Normal']
            bold_style = ParagraphStyle(
                'Bold',
                parent=styles['Normal'],
                fontSize=12,
                spaceAfter=6,
                fontName='Helvetica-Bold'
            )
            
            # Título
            story.append(Paragraph("SISTEMA DE ALMACÉN", title_style))
            story.append(Paragraph("COMPROBANTE DE SOLICITUD", subtitle_style))
            story.append(Spacer(1, 20))
            
            # Información de generación
            story.append(Paragraph(f"<b>Documento generado:</b> {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", normal_style))
            story.append(Spacer(1, 15))
            
            # Información del ticket
            story.append(Paragraph(f"<b>Número de Ticket:</b> {ticket_data['numero_ticket']}", normal_style))
            story.append(Paragraph(f"<b>Orden de Producción:</b> {ticket_data['orden_produccion']}", normal_style))
            story.append(Paragraph(f"<b>Estado:</b> {ticket_data['estado'].upper()}", normal_style))
            story.append(Paragraph(f"<b>Justificación:</b> {ticket_data['justificacion']}", normal_style))
            story.append(Spacer(1, 15))
            
            # Información del solicitante
            story.append(Paragraph("<b>INFORMACIÓN DEL SOLICITANTE</b>", bold_style))
            story.append(Paragraph(f"<b>Nombre:</b> {ticket_data['solicitante_nombre']}", normal_style))
            story.append(Paragraph(f"<b>Rol:</b> {ticket_data['solicitante_rol']}", normal_style))
            story.append(Paragraph(f"<b>Fecha de Solicitud:</b> {ticket_data['fecha_solicitud']}", normal_style))
            story.append(Spacer(1, 15))
            
            # Información de aprobación (si existe)
            if ticket_data.get('aprobador_nombre'):
                story.append(Paragraph("<b>INFORMACIÓN DE APROBACIÓN</b>", bold_style))
                story.append(Paragraph(f"<b>Aprobado por:</b> {ticket_data['aprobador_nombre']}", normal_style))
                story.append(Paragraph(f"<b>Fecha de Aprobación:</b> {ticket_data['fecha_aprobacion']}", normal_style))
                if ticket_data.get('comentarios_aprobador'):
                    story.append(Paragraph(f"<b>Comentarios:</b> {ticket_data['comentarios_aprobador']}", normal_style))
                story.append(Spacer(1, 15))
            
            # Información de entrega (si existe)
            if ticket_data.get('entregado_por_nombre'):
                story.append(Paragraph("<b>INFORMACIÓN DE ENTREGA</b>", bold_style))
                story.append(Paragraph(f"<b>Entregado por:</b> {ticket_data['entregado_por_nombre']}", normal_style))
                story.append(Paragraph(f"<b>Fecha de Entrega:</b> {ticket_data['fecha_entrega']}", normal_style))
                story.append(Spacer(1, 15))
            
            # Información de devolución (si existe)
            if ticket_data.get('devuelto_por_nombre'):
                story.append(Paragraph("<b>INFORMACIÓN DE DEVOLUCIÓN</b>", bold_style))
                story.append(Paragraph(f"<b>Devuelto por:</b> {ticket_data['devuelto_por_nombre']}", normal_style))
                story.append(Paragraph(f"<b>Fecha de Devolución:</b> {ticket_data['fecha_devolucion']}", normal_style))
                story.append(Spacer(1, 15))
            
            # Tabla de herramientas
            story.append(Paragraph("<b>HERRAMIENTAS SOLICITADAS</b>", bold_style))
            
            if ticket_data.get('items'):
                # Preparar datos para la tabla
                table_data = [
                    ['Herramienta', 'Solicitado', 'Entregado', 'Devuelto', 'Precio Unit.']
                ]
                
                for item in ticket_data['items']:
                    cantidad_devuelta = item.get('cantidad_devuelta', 0) or 0
                    table_data.append([
                        item['producto_nombre'],
                        str(item['cantidad_solicitada']),
                        str(item.get('cantidad_entregada', 0) or 0),
                        str(cantidad_devuelta),
                        f"${item.get('precio_unitario', 0) or 0:.2f}"
                    ])
                
                # Crear tabla
                table = Table(table_data, colWidths=[2.5*inch, 1*inch, 1*inch, 1*inch, 1.2*inch])
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 12),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 1), (-1, -1), 10),
                    ('ALIGN', (1, 1), (-1, -1), 'CENTER'),  # Centrar números
                    ('ALIGN', (0, 1), (0, -1), 'LEFT'),      # Alinear texto a la izquierda
                ]))
                
                story.append(table)
                story.append(Spacer(1, 20))
            
            # Pie de página
            story.append(Paragraph("<b>NOTAS IMPORTANTES:</b>", bold_style))
            story.append(Paragraph("• Este documento es un comprobante oficial de la solicitud de herramientas.", normal_style))
            story.append(Paragraph("• La información contenida en este PDF no puede ser alterada.", normal_style))
            story.append(Paragraph("• Para consultas o aclaraciones, contacte al administrador del sistema.", normal_style))
            story.append(Paragraph(f"• Documento generado el: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", normal_style))
            
            # Generar PDF
            doc.build(story)
            
            # Leer el archivo generado
            with open(tmp_file.name, 'rb') as pdf_file:
                pdf_content = pdf_file.read()
            
            # Cerrar el documento para liberar el archivo
            doc = None
            
            # Eliminar archivo temporal (con manejo de errores)
            try:
                os.unlink(tmp_file.name)
            except OSError as e:
                logger.warning(f"No se pudo eliminar archivo temporal {tmp_file.name}: {e}")
            
            return pdf_content
            
    except Exception as e:
        logger.error(f"Error generando PDF: {e}")
        raise HTTPException(status_code=500, detail=f"Error generando PDF: {str(e)}")

@app.get("/api/tickets/{ticket_id}/pdf")
async def descargar_pdf_ticket(ticket_id: int, request: Request):
    """Descargar PDF del ticket"""
    try:
        current_user = get_current_user(request)
        require_auth(current_user)
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Obtener ticket principal
        cursor.execute("""
            SELECT 
                t.id, t.numero_ticket, t.orden_produccion, t.justificacion,
                t.solicitante_id, t.solicitante_nombre, t.solicitante_rol, t.estado,
                t.fecha_solicitud, t.fecha_aprobacion, t.aprobador_nombre,
                t.comentarios_aprobador, t.fecha_entrega, t.entregado_por_nombre
            FROM tickets_compra t
            WHERE t.id = ?
        """, (ticket_id,))
        
        ticket = cursor.fetchone()
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket no encontrado")
        
        # Convertir a diccionario
        ticket = dict(ticket)
        
        # Verificar permisos
        if current_user["rol"] not in ["admin"] and ticket["solicitante_id"] != current_user["id"]:
            raise HTTPException(status_code=403, detail="No tienes permisos para descargar este ticket")
        
        # Obtener items del ticket
        cursor.execute("""
            SELECT ti.id, ti.producto_id, ti.producto_nombre, ti.cantidad_solicitada, 
                   ti.cantidad_entregada, ti.cantidad_devuelta, ti.precio_unitario
            FROM ticket_items ti
            WHERE ti.ticket_id = ?
            ORDER BY ti.producto_nombre
        """, (ticket_id,))
        
        ticket["items"] = [dict(item) for item in cursor.fetchall()]
        
        # Obtener fecha de devolución y usuario que devolvió desde el historial
        cursor.execute("""
            SELECT h.fecha, h.usuario_nombre
            FROM historial h
            WHERE h.accion IN ('devolucion_buen_estado', 'devolucion_mal_estado', 'devolucion')
            AND h.detalles LIKE ?
            ORDER BY h.fecha DESC
            LIMIT 1
        """, (f"%{ticket['numero_ticket']}%",))
        
        devolucion_result = cursor.fetchone()
        if devolucion_result:
            ticket["fecha_devolucion"] = devolucion_result[0]
            ticket["devuelto_por_nombre"] = devolucion_result[1]
        else:
            ticket["fecha_devolucion"] = None
            ticket["devuelto_por_nombre"] = None
        
        conn.close()
        
        # Generar PDF
        pdf_content = generar_pdf_ticket(ticket)
        
        # Devolver PDF como respuesta
        return Response(
            content=pdf_content,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=ticket_{ticket['numero_ticket']}.pdf"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al generar PDF del ticket {ticket_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error al generar PDF: {str(e)}")

@app.post("/api/tickets/{ticket_id}/devolver")
async def devolver_ticket(ticket_id: int, devolucion: dict, request: Request):
    """Procesar devolución de herramientas mediante escaneo QR"""
    try:
        logger.info(f"🔄 Iniciando devolución para ticket {ticket_id}")
        logger.info(f"📦 Datos de devolución: {devolucion}")
        
        current_user = get_current_user(request)
        require_auth(current_user)
        
        logger.info(f"👤 Usuario autenticado: {current_user['username']} ({current_user['rol']})")
        
        # Verificar que el usuario sea supervisor u operador
        if current_user["rol"] not in ["supervisor", "operador"]:
            raise HTTPException(status_code=403, detail="Solo supervisores y operadores pueden devolver herramientas")
        
        logger.info("🔗 Conectando a base de datos...")
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Obtener ticket
        logger.info(f"📋 Obteniendo ticket {ticket_id}...")
        cursor.execute("""
            SELECT id, numero_ticket, estado, solicitante_id, solicitante_nombre
            FROM tickets_compra 
            WHERE id = ?
        """, (ticket_id,))
        
        ticket = cursor.fetchone()
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket no encontrado")
        
        ticket = dict(ticket)
        logger.info(f"✅ Ticket encontrado: {ticket['numero_ticket']} (estado: {ticket['estado']})")
        
        # Verificar que el ticket esté entregado
        if ticket["estado"] != "entregado":
            raise HTTPException(status_code=400, detail="Solo se pueden devolver tickets entregados")
        
        # Verificar que el usuario sea el solicitante o supervisor
        if current_user["rol"] != "supervisor" and ticket["solicitante_id"] != current_user["id"]:
            raise HTTPException(status_code=403, detail="Solo puedes devolver tus propios tickets")
        
        # Obtener producto escaneado
        codigo_escaneado = devolucion.get("codigo")
        if not codigo_escaneado:
            raise HTTPException(status_code=400, detail="Código de producto requerido")
        
        logger.info(f"🔍 Procesando código escaneado: {codigo_escaneado}")
        
        # Buscar el producto
        producto_id = None
        if "ID:" in codigo_escaneado:
            try:
                id_part = codigo_escaneado.split("|")[0]
                producto_id = int(id_part.replace("ID:", ""))
                logger.info(f"🎯 Producto ID extraído: {producto_id}")
            except (ValueError, IndexError):
                raise HTTPException(status_code=400, detail="Código QR inválido")
        
        if not producto_id:
            raise HTTPException(status_code=400, detail="No se pudo identificar el producto")
        
        # Verificar que el producto esté en el ticket
        logger.info(f"🔍 Verificando producto {producto_id} en ticket {ticket_id}...")
        cursor.execute("""
            SELECT ti.id, ti.producto_id, ti.producto_nombre, ti.cantidad_solicitada, 
                   ti.cantidad_entregada, ti.cantidad_devuelta, p.cantidad as stock_actual
            FROM ticket_items ti
            JOIN productos p ON ti.producto_id = p.id
            WHERE ti.ticket_id = ? AND ti.producto_id = ?
        """, (ticket_id, producto_id))
        
        item = cursor.fetchone()
        if not item:
            raise HTTPException(status_code=400, detail="Este producto no está en el ticket")
        
        item = dict(item)
        logger.info(f"✅ Producto encontrado en ticket: {item['producto_nombre']}")
        logger.info(f"📊 Cantidades - Entregada: {item['cantidad_entregada']}, Devuelta: {item['cantidad_devuelta']}")
        
        # Verificar que haya productos entregados para devolver
        if item["cantidad_entregada"] <= 0:
            raise HTTPException(status_code=400, detail="No hay productos entregados para devolver")
        
        # Calcular cantidad a devolver (por defecto 1, pero se puede especificar)
        cantidad_devolver = devolucion.get("cantidad", 1)
        if cantidad_devolver <= 0:
            raise HTTPException(status_code=400, detail="La cantidad a devolver debe ser mayor a 0")
        
        if cantidad_devolver > item["cantidad_entregada"]:
            raise HTTPException(status_code=400, detail=f"Solo se pueden devolver hasta {item['cantidad_entregada']} unidades")
        
        logger.info(f"📦 Cantidad a devolver: {cantidad_devolver}")
        
        # Obtener estado de la devolución (por defecto "buen_estado")
        estado_devolucion = devolucion.get("estado", "buen_estado")
        if estado_devolucion not in ["buen_estado", "mal_estado"]:
            raise HTTPException(status_code=400, detail="Estado de devolución inválido")
        
        logger.info(f"🏷️ Estado de devolución: {estado_devolucion}")
        
        # Procesar devolución - mantener contadores independientes
        cantidad_devuelta_actual = item["cantidad_devuelta"] if item["cantidad_devuelta"] is not None else 0
        nueva_cantidad_devuelta = cantidad_devuelta_actual + cantidad_devolver
        
        logger.info(f"🔄 Actualizando cantidad_devuelta: {cantidad_devuelta_actual} → {nueva_cantidad_devuelta}")
        
        # Solo actualizar cantidad_devuelta, mantener cantidad_entregada fija
        cursor.execute("""
            UPDATE ticket_items 
            SET cantidad_devuelta = ?
            WHERE id = ?
        """, (nueva_cantidad_devuelta, item["id"]))
        
        # Actualizar stock del producto solo si está en buen estado
        nuevo_stock = item["stock_actual"]
        if estado_devolucion == "buen_estado":
            nuevo_stock += cantidad_devolver
            logger.info(f"📈 Actualizando stock: {item['stock_actual']} → {nuevo_stock}")
            cursor.execute("""
                UPDATE productos 
                SET cantidad = ?, fecha_actualizacion = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (nuevo_stock, producto_id))
        
        # Si está en mal estado, no se actualiza el stock (se considera desecho)
        
        # Registrar en historial
        try:
            accion_historial = "devolucion_buen_estado" if estado_devolucion == "buen_estado" else "devolucion_mal_estado"
            detalles_historial = f"Devolución de ticket {ticket['numero_ticket']} - {cantidad_devolver} unidades ({estado_devolucion})"
            
            logger.info(f"📝 Registrando en historial: {accion_historial}")
            
            cursor.execute("""
                INSERT INTO historial (accion, producto_id, cantidad_anterior, cantidad_nueva, usuario_id, usuario_nombre, detalles)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                accion_historial, 
                producto_id, 
                item["stock_actual"], 
                nuevo_stock, 
                current_user["id"], 
                current_user["nombre_completo"],
                detalles_historial
            ))
        except sqlite3.OperationalError as e:
            logger.warning(f"Error registrando devolución en historial: {e}")
        
        # Verificar si todos los items fueron devueltos
        logger.info("🔍 Verificando estado del ticket...")
        cursor.execute("""
            SELECT 
                SUM(cantidad_solicitada) as total_solicitado,
                SUM(cantidad_entregada) as total_entregado,
                SUM(cantidad_devuelta) as total_devuelto
            FROM ticket_items 
            WHERE ticket_id = ?
        """, (ticket_id,))
        
        totales = dict(cursor.fetchone())
        total_entregado = totales["total_entregado"] or 0
        total_devuelto = totales["total_devuelto"] or 0
        
        logger.info(f"📊 Totales - Entregado: {total_entregado}, Devuelto: {total_devuelto}")
        
        # Si todo lo entregado fue devuelto, cambiar estado a "devuelto"
        nuevo_estado = "devuelto" if total_devuelto >= total_entregado and total_entregado > 0 else "entregado"
        
        if nuevo_estado == "devuelto":
            logger.info(f"🔄 Cambiando estado del ticket a: {nuevo_estado}")
            cursor.execute("""
                UPDATE tickets_compra 
                SET estado = ?
                WHERE id = ?
            """, (nuevo_estado, ticket_id))
        
        logger.info("💾 Guardando cambios en base de datos...")
        conn.commit()
        conn.close()
        
        logger.info(f"✅ Devolución procesada exitosamente: {cantidad_devolver} unidades de {item['producto_nombre']} en ticket {ticket['numero_ticket']} - Estado: {estado_devolucion}")
        
        mensaje_estado = "retornan al almacén" if estado_devolucion == "buen_estado" else "se consideran desecho"
        
        return {
            "mensaje": f"Devolución procesada: {cantidad_devolver} unidades de {item['producto_nombre']} ({mensaje_estado})",
            "numero_ticket": ticket["numero_ticket"],
            "producto": item["producto_nombre"],
            "cantidad_devolver": cantidad_devolver,
            "cantidad_entregada": item["cantidad_entregada"],
            "cantidad_devuelta": nueva_cantidad_devuelta,
            "estado_ticket": nuevo_estado,
            "estado_devolucion": estado_devolucion
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error al procesar devolución: {e}")
        raise HTTPException(status_code=500, detail=f"Error al procesar devolución: {str(e)}")

if __name__ == "__main__":
    import ssl
    import tempfile
    import os
    
    # Obtener puerto desde variable de entorno o usar 8443 por defecto
    PORT = int(os.getenv("PORT", 8443))
    
    # Crear certificado SSL autofirmado temporal
    def create_self_signed_cert():
        try:
            from cryptography import x509
            from cryptography.x509.oid import NameOID
            from cryptography.hazmat.primitives import hashes, serialization
            from cryptography.hazmat.primitives.asymmetric import rsa
            from datetime import datetime, timedelta
            
            # Generar clave privada
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048,
            )
            
            # Crear certificado
            subject = issuer = x509.Name([
                x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
                x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "State"),
                x509.NameAttribute(NameOID.LOCALITY_NAME, "City"),
                x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Inventario Local"),
                x509.NameAttribute(NameOID.COMMON_NAME, "localhost"),
            ])
            
            cert = x509.CertificateBuilder().subject_name(
                subject
            ).issuer_name(
                issuer
            ).public_key(
                private_key.public_key()
            ).serial_number(
                x509.random_serial_number()
            ).not_valid_before(
                datetime.utcnow()
            ).not_valid_after(
                datetime.utcnow() + timedelta(days=365)
            ).add_extension(
                x509.SubjectAlternativeName([
                    x509.DNSName("localhost"),
                    x509.IPAddress(ipaddress.IPv4Address("127.0.0.1")),
                    x509.IPAddress(ipaddress.IPv4Address("192.168.1.134")),
                ]),
                critical=False,
            ).sign(private_key, hashes.SHA256())
            
            # Guardar certificado y clave
            cert_path = tempfile.NamedTemporaryFile(delete=False, suffix='.pem')
            key_path = tempfile.NamedTemporaryFile(delete=False, suffix='.pem')
            
            cert_path.write(cert.public_bytes(serialization.Encoding.PEM))
            key_path.write(private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            ))
            
            cert_path.close()
            key_path.close()
            
            return cert_path.name, key_path.name
            
        except ImportError:
            print("⚠️  Para HTTPS, instale: pip install cryptography")
            return None, None
        except Exception as e:
            print(f"⚠️  Error generando certificado SSL: {e}")
            return None, None
    
    # Intentar crear certificado SSL
    print("🔧 Configurando servidor...")
    cert_file, key_file = create_self_signed_cert()
    
    # Obtener puerto desde variable de entorno
    port = int(os.getenv("PORT", "8000"))
    
    if cert_file and key_file:
        print("🔒 Iniciando servidor HTTPS...")
        print(f"🌐 Acceda desde: https://192.168.1.134:{port}")
        print(f"📱 Para dispositivos móviles: https://192.168.1.134:{port}")
        print(f"💻 Para PC local: https://localhost:{port}")
        uvicorn.run(
            app, 
            host="0.0.0.0", 
            port=port, 
            reload=False,  # Deshabilitar reload para evitar advertencias
            ssl_keyfile=key_file,
            ssl_certfile=cert_file
        )
    else:
        print("⚠️  Iniciando servidor HTTP (cámara limitada)")
        print(f"🌐 Acceda desde: http://localhost:{port} para usar la cámara")
        print("📱 Para dispositivos móviles: Use HTTPS (no disponible)")
        uvicorn.run(
            app, 
            host="0.0.0.0", 
            port=port, 
            reload=False  # Deshabilitar reload para evitar advertencias
        ) 