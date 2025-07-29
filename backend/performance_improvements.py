import sqlite3
from typing import Dict, Any, Optional, List
import time
import hashlib
import json
from functools import wraps
from datetime import datetime, timedelta

# 1. SISTEMA DE CACHE EN MEMORIA
class InMemoryCache:
    """Cache simple en memoria con TTL"""
    
    def __init__(self):
        self.cache = {}
        self.timestamps = {}
        self.default_ttl = 300  # 5 minutos
    
    def get(self, key: str) -> Optional[Any]:
        """Obtener valor del cache"""
        if key not in self.cache:
            return None
        
        # Verificar TTL
        if time.time() - self.timestamps[key] > self.default_ttl:
            self.delete(key)
            return None
        
        return self.cache[key]
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Guardar valor en cache"""
        self.cache[key] = value
        self.timestamps[key] = time.time()
    
    def delete(self, key: str) -> None:
        """Eliminar del cache"""
        self.cache.pop(key, None)
        self.timestamps.pop(key, None)
    
    def clear(self) -> None:
        """Limpiar todo el cache"""
        self.cache.clear()
        self.timestamps.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Estadísticas del cache"""
        current_time = time.time()
        valid_keys = sum(1 for key in self.timestamps 
                        if current_time - self.timestamps[key] <= self.default_ttl)
        
        return {
            "total_keys": len(self.cache),
            "valid_keys": valid_keys,
            "expired_keys": len(self.cache) - valid_keys,
            "memory_usage_keys": len(str(self.cache))
        }

# Instancia global de cache
app_cache = InMemoryCache()

# 2. DECORADOR PARA CACHEAR FUNCIONES
def cache_result(key_prefix: str, ttl: int = 300):
    """Decorador para cachear resultados de funciones"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generar clave única basada en argumentos
            key_data = f"{key_prefix}:{str(args)}:{str(sorted(kwargs.items()))}"
            cache_key = hashlib.md5(key_data.encode()).hexdigest()
            
            # Intentar obtener del cache
            cached_result = app_cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Ejecutar función y cachear resultado
            result = func(*args, **kwargs)
            app_cache.set(cache_key, result, ttl)
            
            return result
        return wrapper
    return decorator

# 3. OPTIMIZACIONES DE BASE DE DATOS
class DatabaseOptimizer:
    """Optimizaciones para consultas de base de datos"""
    
    @staticmethod
    def create_indexes(conn: sqlite3.Connection):
        """Crear índices para mejorar performance"""
        cursor = conn.cursor()
        
        # Índices para productos
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_productos_nombre ON productos(nombre)",
            "CREATE INDEX IF NOT EXISTS idx_productos_codigo_barras ON productos(codigo_barras)",
            "CREATE INDEX IF NOT EXISTS idx_productos_categoria ON productos(categoria)",
            "CREATE INDEX IF NOT EXISTS idx_productos_ubicacion ON productos(ubicacion)",
            "CREATE INDEX IF NOT EXISTS idx_productos_stock_bajo ON productos(cantidad, cantidad_minima)",
            
            # Índices para usuarios
            "CREATE INDEX IF NOT EXISTS idx_usuarios_username ON usuarios(username)",
            "CREATE INDEX IF NOT EXISTS idx_usuarios_activo ON usuarios(activo)",
            
            # Índices para sesiones
            "CREATE INDEX IF NOT EXISTS idx_sesiones_token ON sesiones(token)",
            "CREATE INDEX IF NOT EXISTS idx_sesiones_activa ON sesiones(activa)",
            "CREATE INDEX IF NOT EXISTS idx_sesiones_user_id ON sesiones(user_id)",
            
            # Índices para historial
            "CREATE INDEX IF NOT EXISTS idx_historial_fecha ON historial(fecha)",
            "CREATE INDEX IF NOT EXISTS idx_historial_usuario ON historial(usuario_id)",
            "CREATE INDEX IF NOT EXISTS idx_historial_tipo ON historial(tipo_accion)"
        ]
        
        for index_sql in indexes:
            try:
                cursor.execute(index_sql)
            except sqlite3.Error as e:
                print(f"Error creando índice: {e}")
        
        conn.commit()
    
    @staticmethod
    def optimize_database(db_path: str):
        """Optimizar base de datos"""
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        try:
            # Crear índices
            DatabaseOptimizer.create_indexes(conn)
            
            # Optimizar con VACUUM
            cursor.execute("VACUUM")
            
            # Analizar estadísticas
            cursor.execute("ANALYZE")
            
            # Configuraciones de performance
            cursor.execute("PRAGMA journal_mode = WAL")  # Write-Ahead Logging
            cursor.execute("PRAGMA synchronous = NORMAL")  # Balancear seguridad/performance
            cursor.execute("PRAGMA cache_size = 10000")  # Cache más grande
            cursor.execute("PRAGMA temp_store = memory")  # Usar memoria para temps
            
            conn.commit()
            print("✅ Base de datos optimizada correctamente")
            
        except Exception as e:
            print(f"❌ Error optimizando base de datos: {e}")
        finally:
            conn.close()

# 4. FUNCIONES CACHEADAS PARA CONSULTAS FRECUENTES
@cache_result("productos_all", ttl=60)  # Cache por 1 minuto
def get_productos_cached(db_path: str) -> List[Dict]:
    """Obtener todos los productos con cache"""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, codigo_barras, nombre, descripcion, cantidad, 
               cantidad_minima, ubicacion, categoria, precio_unitario,
               fecha_creacion, fecha_actualizacion
        FROM productos 
        ORDER BY nombre
    """)
    
    productos = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return productos

@cache_result("estadisticas", ttl=30)  # Cache por 30 segundos
def get_estadisticas_cached(db_path: str) -> Dict[str, Any]:
    """Obtener estadísticas con cache"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Total productos
    cursor.execute("SELECT COUNT(*) FROM productos")
    total_productos = cursor.fetchone()[0]
    
    # Stock bajo
    cursor.execute("""
        SELECT COUNT(*) FROM productos 
        WHERE cantidad <= cantidad_minima AND cantidad_minima > 0
    """)
    stock_bajo = cursor.fetchone()[0]
    
    # Valor total
    cursor.execute("""
        SELECT COALESCE(SUM(cantidad * COALESCE(precio_unitario, 0)), 0) 
        FROM productos
    """)
    valor_total = cursor.fetchone()[0]
    
    # Sesiones activas
    cursor.execute("SELECT COUNT(*) FROM sesiones WHERE activa = 1")
    sesiones_activas = cursor.fetchone()[0]
    
    conn.close()
    
    return {
        "total_productos": total_productos,
        "stock_bajo": stock_bajo,
        "valor_total": valor_total,
        "sesiones_activas": sesiones_activas,
        "timestamp": datetime.now().isoformat()
    }

# 5. QUERY BUILDER PARA BÚSQUEDAS OPTIMIZADAS
class OptimizedSearch:
    """Búsquedas optimizadas con índices"""
    
    @staticmethod
    def search_productos(db_path: str, query: str, filters: Dict = None) -> List[Dict]:
        """Búsqueda optimizada de productos"""
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Query base optimizada
        sql = """
            SELECT id, codigo_barras, nombre, descripcion, cantidad, 
                   cantidad_minima, ubicacion, categoria, precio_unitario
            FROM productos 
            WHERE 1=1
        """
        params = []
        
        # Filtro de búsqueda de texto (usa índices)
        if query and query.strip():
            sql += """
                AND (
                    nombre LIKE ? 
                    OR codigo_barras LIKE ?
                    OR descripcion LIKE ?
                    OR ubicacion LIKE ?
                )
            """
            search_term = f"%{query.strip()}%"
            params.extend([search_term, search_term, search_term, search_term])
        
        # Filtros adicionales
        if filters:
            if filters.get("categoria"):
                sql += " AND categoria = ?"
                params.append(filters["categoria"])
            
            if filters.get("stock_bajo"):
                sql += " AND cantidad <= cantidad_minima"
            
            if filters.get("ubicacion"):
                sql += " AND ubicacion = ?"
                params.append(filters["ubicacion"])
        
        sql += " ORDER BY nombre LIMIT 1000"  # Limitar resultados
        
        cursor.execute(sql, params)
        resultados = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return resultados

# 6. MIDDLEWARE DE PERFORMANCE MONITORING
class PerformanceMiddleware:
    """Middleware para monitorear performance de requests"""
    
    def __init__(self):
        self.request_times = []
        self.slow_requests = []
    
    def start_timer(self) -> float:
        """Iniciar medición de tiempo"""
        return time.time()
    
    def end_timer(self, start_time: float, endpoint: str, 
                  threshold_ms: float = 1000) -> float:
        """Finalizar medición y registrar si es lenta"""
        duration_ms = (time.time() - start_time) * 1000
        
        self.request_times.append({
            "endpoint": endpoint,
            "duration_ms": duration_ms,
            "timestamp": datetime.now().isoformat()
        })
        
        # Registrar requests lentas
        if duration_ms > threshold_ms:
            self.slow_requests.append({
                "endpoint": endpoint,
                "duration_ms": duration_ms,
                "timestamp": datetime.now().isoformat()
            })
        
        return duration_ms
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de performance"""
        if not self.request_times:
            return {"message": "No hay datos de performance"}
        
        durations = [req["duration_ms"] for req in self.request_times[-100:]]  # Últimas 100
        
        return {
            "total_requests": len(self.request_times),
            "slow_requests": len(self.slow_requests),
            "avg_response_time_ms": sum(durations) / len(durations),
            "max_response_time_ms": max(durations),
            "min_response_time_ms": min(durations),
            "recent_slow_requests": self.slow_requests[-5:]  # Últimas 5 lentas
        }

# Instancia global
performance_monitor = PerformanceMiddleware()

# 7. FUNCIONES DE INTEGRACIÓN
def invalidate_cache_on_update():
    """Invalidar cache cuando se actualizan datos"""
    app_cache.delete("productos_all")
    app_cache.delete("estadisticas")

def setup_performance_optimizations(db_path: str):
    """Configurar todas las optimizaciones de performance"""
    print("🚀 Configurando optimizaciones de performance...")
    
    # Optimizar base de datos
    DatabaseOptimizer.optimize_database(db_path)
    
    # Configurar cache
    app_cache.clear()
    
    print("✅ Optimizaciones configuradas correctamente")