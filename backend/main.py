from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
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

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Crear directorio de datos si no existe
os.makedirs("../data", exist_ok=True)

app = FastAPI(
    title="Sistema de Almacén Local",
    description="API para gestión de inventario en red local",
    version="1.0.0"
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

# Función para obtener conexión a la base de datos
def get_db_connection():
    try:
        conn = sqlite3.connect("../data/almacen.db", timeout=60.0)  # Aumentar timeout a 60 segundos
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
        
        # Crear índices para rendimiento
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_productos_nombre ON productos(nombre)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_productos_ubicacion ON productos(ubicacion)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_historial_producto ON historial(producto_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_usuarios_username ON usuarios(username)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_sesiones_token ON sesiones(token)')
        
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

@app.post("/api/productos")
async def crear_producto(producto: dict, request: Request):
    """Crear un nuevo producto"""
    try:
        logger.info(f"Intentando crear producto: {producto}")
        
        # Obtener usuario actual
        current_user = get_current_user(request)
        if not current_user:
            raise HTTPException(status_code=401, detail="No autenticado")
        
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
async def actualizar_producto(producto_id: int, producto: dict):
    """Actualizar un producto existente"""
    try:
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
        """, ("actualizar", producto_id, cantidad_anterior, producto.get("cantidad", 0), "admin", "Administrador"))
        
        conn.commit()
        conn.close()
        
        return {"mensaje": "Herramienta actualizada exitosamente"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al actualizar herramienta: {str(e)}")

@app.delete("/api/productos/{producto_id}")
async def eliminar_producto(producto_id: int):
    """Eliminar un producto"""
    try:
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
        """, ("eliminar", producto_id, 0, 0, "admin", "Administrador"))
        
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

# Inicializar base de datos al arrancar
@app.on_event("startup")
async def startup_event():
    init_database()
    print("✅ Base de datos inicializada")
    print("🚀 Servidor listo en http://localhost:8000")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True) 