import psutil
import sqlite3
import time
from datetime import datetime
from typing import Dict, Any
import os

class SystemMonitor:
    """Monitor del sistema para alertas y diagnósticos"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        
    def get_system_health(self) -> Dict[str, Any]:
        """Obtener estado general del sistema"""
        return {
            "timestamp": datetime.now().isoformat(),
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory": self.get_memory_info(),
            "disk": self.get_disk_info(),
            "database": self.check_database_health(),
            "process": self.get_process_info()
        }
    
    def get_memory_info(self) -> Dict[str, Any]:
        """Información de memoria"""
        memory = psutil.virtual_memory()
        return {
            "total_gb": round(memory.total / (1024**3), 2),
            "available_gb": round(memory.available / (1024**3), 2),
            "percent_used": memory.percent,
            "status": "critical" if memory.percent > 90 else "warning" if memory.percent > 75 else "ok"
        }
    
    def get_disk_info(self) -> Dict[str, Any]:
        """Información de disco"""
        disk = psutil.disk_usage('/')
        return {
            "total_gb": round(disk.total / (1024**3), 2),
            "free_gb": round(disk.free / (1024**3), 2),
            "percent_used": round((disk.used / disk.total) * 100, 2),
            "status": "critical" if disk.free < 1024**3 else "warning" if disk.free < 5*(1024**3) else "ok"
        }
    
    def check_database_health(self) -> Dict[str, Any]:
        """Verificar salud de la base de datos"""
        try:
            start_time = time.time()
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Test de conectividad básico
            cursor.execute("SELECT COUNT(*) FROM productos")
            productos_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM usuarios")
            usuarios_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM sesiones WHERE activa = 1")
            sesiones_activas = cursor.fetchone()[0]
            
            response_time = round((time.time() - start_time) * 1000, 2)
            
            conn.close()
            
            return {
                "status": "healthy",
                "response_time_ms": response_time,
                "productos_count": productos_count,
                "usuarios_count": usuarios_count,
                "sesiones_activas": sesiones_activas,
                "db_size_mb": round(os.path.getsize(self.db_path) / (1024**2), 2)
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "response_time_ms": None
            }
    
    def get_process_info(self) -> Dict[str, Any]:
        """Información del proceso actual"""
        process = psutil.Process()
        return {
            "pid": process.pid,
            "cpu_percent": process.cpu_percent(),
            "memory_mb": round(process.memory_info().rss / (1024**2), 2),
            "threads": process.num_threads(),
            "uptime_hours": round((time.time() - process.create_time()) / 3600, 2)
        }

# Función para agregar al FastAPI main.py
def add_health_endpoints(app):
    """Agregar endpoints de salud al FastAPI app"""
    monitor = SystemMonitor("../data/almacen_main.db")
    
    @app.get("/health")
    async def health_check():
        """Health check básico"""
        return {"status": "ok", "timestamp": datetime.now().isoformat()}
    
    @app.get("/health/detailed")
    async def detailed_health_check():
        """Health check detallado - Solo para administradores"""
        return monitor.get_system_health()
    
    @app.get("/metrics")
    async def get_metrics():
        """Métricas para monitoring externo (Prometheus compatible)"""
        health = monitor.get_system_health()
        
        # Formato Prometheus
        metrics = f"""
# HELP cpu_percent CPU usage percentage
# TYPE cpu_percent gauge
cpu_percent {health['cpu_percent']}

# HELP memory_percent Memory usage percentage  
# TYPE memory_percent gauge
memory_percent {health['memory']['percent_used']}

# HELP disk_percent Disk usage percentage
# TYPE disk_percent gauge
disk_percent {health['disk']['percent_used']}

# HELP db_response_time_ms Database response time in milliseconds
# TYPE db_response_time_ms gauge
db_response_time_ms {health['database'].get('response_time_ms', 0)}

# HELP productos_total Total number of products
# TYPE productos_total counter
productos_total {health['database'].get('productos_count', 0)}

# HELP sesiones_activas_total Active sessions count
# TYPE sesiones_activas_total gauge
sesiones_activas_total {health['database'].get('sesiones_activas', 0)}
"""
        return Response(content=metrics.strip(), media_type="text/plain")