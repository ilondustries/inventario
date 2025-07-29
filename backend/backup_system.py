import sqlite3
import shutil
import os
import gzip
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import schedule
import threading
import time

class BackupManager:
    """Sistema completo de backup y recovery"""
    
    def __init__(self, db_path: str, backup_dir: str = "../backups"):
        self.db_path = db_path
        self.backup_dir = backup_dir
        self.max_backups = 30  # Mantener últimos 30 backups
        
        # Crear directorio de backups
        os.makedirs(backup_dir, exist_ok=True)
    
    def create_backup(self, backup_type: str = "manual") -> str:
        """Crear backup completo de la base de datos"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"backup_{backup_type}_{timestamp}.db"
        backup_path = os.path.join(self.backup_dir, backup_filename)
        
        try:
            # Hacer backup usando SQLite backup API
            source_conn = sqlite3.connect(self.db_path)
            backup_conn = sqlite3.connect(backup_path)
            
            # Backup completo
            source_conn.backup(backup_conn)
            
            source_conn.close()
            backup_conn.close()
            
            # Comprimir backup
            compressed_path = f"{backup_path}.gz"
            with open(backup_path, 'rb') as f_in:
                with gzip.open(compressed_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            # Eliminar archivo sin comprimir
            os.remove(backup_path)
            
            # Crear metadata del backup
            metadata = {
                "filename": os.path.basename(compressed_path),
                "backup_type": backup_type,
                "timestamp": timestamp,
                "original_size": os.path.getsize(self.db_path),
                "compressed_size": os.path.getsize(compressed_path),
                "created_at": datetime.now().isoformat()
            }
            
            metadata_path = f"{compressed_path}.json"
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            print(f"✅ Backup creado: {os.path.basename(compressed_path)}")
            self._cleanup_old_backups()
            
            return compressed_path
            
        except Exception as e:
            print(f"❌ Error creando backup: {e}")
            return None
    
    def restore_backup(self, backup_path: str) -> bool:
        """Restaurar base de datos desde backup"""
        try:
            # Verificar que el backup existe
            if not os.path.exists(backup_path):
                print(f"❌ Backup no encontrado: {backup_path}")
                return False
            
            # Crear backup de la DB actual antes de restaurar
            current_backup = self.create_backup("pre_restore")
            if not current_backup:
                print("❌ No se pudo hacer backup de seguridad")
                return False
            
            # Descomprimir backup si es necesario
            if backup_path.endswith('.gz'):
                temp_path = backup_path[:-3]  # Remover .gz
                with gzip.open(backup_path, 'rb') as f_in:
                    with open(temp_path, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                restore_path = temp_path
            else:
                restore_path = backup_path
            
            # Restaurar base de datos
            shutil.copy2(restore_path, self.db_path)
            
            # Limpiar archivo temporal si se descomprimió
            if backup_path.endswith('.gz'):
                os.remove(temp_path)
            
            print(f"✅ Base de datos restaurada desde: {os.path.basename(backup_path)}")
            return True
            
        except Exception as e:
            print(f"❌ Error restaurando backup: {e}")
            return False
    
    def list_backups(self) -> List[Dict]:
        """Listar todos los backups disponibles"""
        backups = []
        
        for filename in os.listdir(self.backup_dir):
            if filename.endswith('.db.gz'):
                backup_path = os.path.join(self.backup_dir, filename)
                metadata_path = f"{backup_path}.json"
                
                # Intentar cargar metadata
                metadata = {}
                if os.path.exists(metadata_path):
                    try:
                        with open(metadata_path, 'r') as f:
                            metadata = json.load(f)
                    except:
                        pass
                
                # Información básica del archivo
                stat_info = os.stat(backup_path)
                backup_info = {
                    "filename": filename,
                    "path": backup_path,
                    "size_mb": round(stat_info.st_size / (1024*1024), 2),
                    "created": datetime.fromtimestamp(stat_info.st_mtime).isoformat(),
                    **metadata
                }
                
                backups.append(backup_info)
        
        # Ordenar por fecha de creación (más reciente primero)
        backups.sort(key=lambda x: x.get("created", ""), reverse=True)
        return backups
    
    def _cleanup_old_backups(self):
        """Eliminar backups antiguos para mantener solo los más recientes"""
        backups = self.list_backups()
        
        if len(backups) > self.max_backups:
            backups_to_delete = backups[self.max_backups:]
            
            for backup in backups_to_delete:
                try:
                    os.remove(backup["path"])
                    # Eliminar metadata también
                    metadata_path = f"{backup['path']}.json"
                    if os.path.exists(metadata_path):
                        os.remove(metadata_path)
                    
                    print(f"🗑️ Backup antiguo eliminado: {backup['filename']}")
                except Exception as e:
                    print(f"❌ Error eliminando backup {backup['filename']}: {e}")
    
    def get_backup_stats(self) -> Dict:
        """Obtener estadísticas de backups"""
        backups = self.list_backups()
        
        if not backups:
            return {"total_backups": 0, "total_size_mb": 0}
        
        total_size = sum(backup.get("size_mb", 0) for backup in backups)
        
        backup_types = {}
        for backup in backups:
            backup_type = backup.get("backup_type", "unknown")
            backup_types[backup_type] = backup_types.get(backup_type, 0) + 1
        
        return {
            "total_backups": len(backups),
            "total_size_mb": round(total_size, 2),
            "oldest_backup": backups[-1]["created"] if backups else None,
            "newest_backup": backups[0]["created"] if backups else None,
            "backup_types": backup_types,
            "directory": self.backup_dir
        }

class AutoBackupScheduler:
    """Programador automático de backups"""
    
    def __init__(self, backup_manager: BackupManager):
        self.backup_manager = backup_manager
        self.scheduler_thread = None
        self.running = False
    
    def setup_schedule(self):
        """Configurar horarios de backup automático"""
        # Backup diario a las 2:00 AM
        schedule.every().day.at("02:00").do(
            self._create_scheduled_backup, "daily"
        )
        
        # Backup semanal los domingos a las 3:00 AM
        schedule.every().sunday.at("03:00").do(
            self._create_scheduled_backup, "weekly"
        )
        
        # Backup cada 6 horas
        schedule.every(6).hours.do(
            self._create_scheduled_backup, "auto_6h"
        )
    
    def _create_scheduled_backup(self, backup_type: str):
        """Crear backup programado"""
        try:
            print(f"🕒 Iniciando backup automático: {backup_type}")
            backup_path = self.backup_manager.create_backup(backup_type)
            if backup_path:
                print(f"✅ Backup automático completado: {backup_type}")
            else:
                print(f"❌ Error en backup automático: {backup_type}")
        except Exception as e:
            print(f"❌ Error en backup programado {backup_type}: {e}")
    
    def start_scheduler(self):
        """Iniciar el programador de backups"""
        if self.running:
            return
        
        self.setup_schedule()
        self.running = True
        
        def run_scheduler():
            while self.running:
                schedule.run_pending()
                time.sleep(60)  # Verificar cada minuto
        
        self.scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        self.scheduler_thread.start()
        
        print("🔄 Programador de backups iniciado")
    
    def stop_scheduler(self):
        """Detener el programador de backups"""
        self.running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        
        print("⏹️ Programador de backups detenido")

class DataExporter:
    """Exportador de datos para análisis externos"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
    
    def export_to_json(self, export_path: str = None) -> str:
        """Exportar todos los datos a JSON"""
        if not export_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            export_path = f"../exports/export_{timestamp}.json"
        
        os.makedirs(os.path.dirname(export_path), exist_ok=True)
        
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            export_data = {
                "export_timestamp": datetime.now().isoformat(),
                "database_path": self.db_path,
                "tables": {}
            }
            
            # Obtener lista de tablas
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            # Exportar cada tabla
            for table in tables:
                cursor.execute(f"SELECT * FROM {table}")
                rows = [dict(row) for row in cursor.fetchall()]
                export_data["tables"][table] = {
                    "count": len(rows),
                    "data": rows
                }
            
            conn.close()
            
            # Guardar JSON
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False, default=str)
            
            print(f"✅ Datos exportados a: {export_path}")
            return export_path
            
        except Exception as e:
            print(f"❌ Error exportando datos: {e}")
            return None
    
    def export_to_csv(self, table_name: str, export_path: str = None) -> str:
        """Exportar tabla específica a CSV"""
        import csv
        
        if not export_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            export_path = f"../exports/{table_name}_{timestamp}.csv"
        
        os.makedirs(os.path.dirname(export_path), exist_ok=True)
        
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute(f"SELECT * FROM {table_name}")
            rows = cursor.fetchall()
            
            if rows:
                with open(export_path, 'w', newline='', encoding='utf-8') as csvfile:
                    writer = csv.DictWriter(csvfile, fieldnames=rows[0].keys())
                    writer.writeheader()
                    for row in rows:
                        writer.writerow(dict(row))
                
                print(f"✅ Tabla {table_name} exportada a: {export_path}")
            else:
                print(f"⚠️ Tabla {table_name} está vacía")
            
            conn.close()
            return export_path
            
        except Exception as e:
            print(f"❌ Error exportando tabla {table_name}: {e}")
            return None

# Funciones de integración con FastAPI
def setup_backup_system(db_path: str):
    """Configurar sistema completo de backup"""
    backup_manager = BackupManager(db_path)
    scheduler = AutoBackupScheduler(backup_manager)
    
    # Crear backup inicial
    backup_manager.create_backup("initial")
    
    # Iniciar programador
    scheduler.start_scheduler()
    
    print("🛡️ Sistema de backup configurado y activo")
    
    return backup_manager, scheduler

def add_backup_endpoints(app, backup_manager: BackupManager):
    """Agregar endpoints de backup al FastAPI app"""
    
    @app.post("/admin/backup/create")
    async def create_manual_backup():
        """Crear backup manual - Solo administradores"""
        backup_path = backup_manager.create_backup("manual")
        if backup_path:
            return {"status": "success", "backup_path": os.path.basename(backup_path)}
        else:
            return {"status": "error", "message": "No se pudo crear el backup"}
    
    @app.get("/admin/backup/list")
    async def list_backups():
        """Listar backups disponibles - Solo administradores"""
        return backup_manager.list_backups()
    
    @app.get("/admin/backup/stats")
    async def backup_stats():
        """Estadísticas de backups - Solo administradores"""
        return backup_manager.get_backup_stats()
    
    @app.post("/admin/backup/restore/{backup_filename}")
    async def restore_backup(backup_filename: str):
        """Restaurar desde backup - Solo administradores"""
        backup_path = os.path.join(backup_manager.backup_dir, backup_filename)
        success = backup_manager.restore_backup(backup_path)
        
        if success:
            return {"status": "success", "message": "Base de datos restaurada"}
        else:
            return {"status": "error", "message": "Error restaurando backup"}