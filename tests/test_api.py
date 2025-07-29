import pytest
import httpx
import sqlite3
import tempfile
import os
from fastapi.testclient import TestClient
import sys
sys.path.append('../backend')

# Configuración de testing
@pytest.fixture
def test_db():
    """Crear base de datos temporal para testing"""
    db_fd, db_path = tempfile.mkstemp()
    
    # Crear esquema de base de datos
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Crear tablas básicas para testing
    cursor.execute("""
        CREATE TABLE usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            nombre_completo TEXT NOT NULL,
            rol TEXT DEFAULT 'operador',
            activo BOOLEAN DEFAULT 1
        )
    """)
    
    cursor.execute("""
        CREATE TABLE productos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo_barras TEXT UNIQUE,
            nombre TEXT NOT NULL,
            descripcion TEXT,
            cantidad INTEGER DEFAULT 0,
            cantidad_minima INTEGER DEFAULT 0,
            ubicacion TEXT,
            categoria TEXT,
            precio_unitario REAL
        )
    """)
    
    cursor.execute("""
        CREATE TABLE sesiones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            token TEXT UNIQUE NOT NULL,
            ip_address TEXT,
            user_agent TEXT,
            fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP,
            fecha_ultimo_acceso DATETIME DEFAULT CURRENT_TIMESTAMP,
            activa BOOLEAN DEFAULT 1,
            FOREIGN KEY (user_id) REFERENCES usuarios (id)
        )
    """)
    
    # Insertar usuario de prueba
    from security_improvements import hash_password_secure
    test_password_hash = hash_password_secure('test123')
    
    cursor.execute("""
        INSERT INTO usuarios (username, password_hash, nombre_completo, rol)
        VALUES (?, ?, ?, ?)
    """, ('testuser', test_password_hash, 'Usuario de Prueba', 'admin'))
    
    conn.commit()
    conn.close()
    
    yield db_path
    
    # Cleanup
    os.close(db_fd)
    os.unlink(db_path)

@pytest.fixture
def client(test_db):
    """Cliente de testing con base de datos temporal"""
    # Importar y configurar la app con DB de testing
    from main import app
    
    # Configurar path de DB temporal (esto requiere modificar main.py)
    app.state.test_db_path = test_db
    
    return TestClient(app)

class TestAuthentication:
    """Tests de autenticación"""
    
    def test_login_success(self, client):
        """Test de login exitoso"""
        response = client.post("/api/auth/login", json={
            "username": "testuser",
            "password": "test123"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "usuario" in data
        assert data["usuario"]["username"] == "testuser"
    
    def test_login_invalid_credentials(self, client):
        """Test de login con credenciales inválidas"""
        response = client.post("/api/auth/login", json={
            "username": "testuser",
            "password": "wrongpassword"
        })
        
        assert response.status_code == 401
    
    def test_login_missing_fields(self, client):
        """Test de login con campos faltantes"""
        response = client.post("/api/auth/login", json={
            "username": "testuser"
        })
        
        assert response.status_code == 400

class TestProductos:
    """Tests de gestión de productos"""
    
    def test_get_productos_unauthorized(self, client):
        """Test de obtener productos sin autenticación"""
        response = client.get("/api/productos")
        assert response.status_code == 401
    
    def test_create_producto_success(self, client):
        """Test de creación exitosa de producto"""
        # Primero hacer login
        login_response = client.post("/api/auth/login", json={
            "username": "testuser",
            "password": "test123"
        })
        
        # Obtener token/sesión del login
        # (esto depende de cómo manejes las sesiones)
        
        response = client.post("/api/productos", json={
            "nombre": "Martillo de Prueba",
            "descripcion": "Martillo para testing",
            "cantidad": 10,
            "cantidad_minima": 2,
            "precio_unitario": 25.50
        })
        
        # Nota: Este test necesita manejo de autenticación
        # assert response.status_code == 201
    
    def test_create_producto_invalid_data(self, client):
        """Test de creación con datos inválidos"""
        response = client.post("/api/productos", json={
            "descripcion": "Sin nombre"  # Falta campo requerido
        })
        
        assert response.status_code in [400, 401]

class TestSecurity:
    """Tests de seguridad"""
    
    def test_sql_injection_protection(self, client):
        """Test de protección contra SQL injection"""
        malicious_input = "'; DROP TABLE usuarios; --"
        
        response = client.post("/api/auth/login", json={
            "username": malicious_input,
            "password": "anypassword"
        })
        
        # Debe fallar el login, no causar error de SQL
        assert response.status_code == 401
    
    def test_rate_limiting(self, client):
        """Test de rate limiting en login"""
        # Hacer múltiples intentos fallidos
        for i in range(6):  # Más que el límite de 5
            response = client.post("/api/auth/login", json={
                "username": "testuser",
                "password": "wrongpassword"
            })
        
        # El último debe ser bloqueado
        # (esto requiere implementar rate limiting)
        # assert response.status_code == 429

class TestSystemHealth:
    """Tests de salud del sistema"""
    
    def test_health_check(self, client):
        """Test básico de health check"""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "ok"
    
    def test_metrics_endpoint(self, client):
        """Test de endpoint de métricas"""
        response = client.get("/metrics")
        
        assert response.status_code == 200
        assert "cpu_percent" in response.text

# Tests de integración más avanzados
class TestIntegration:
    """Tests de integración end-to-end"""
    
    def test_complete_workflow(self, client):
        """Test de flujo completo: login -> crear producto -> obtener productos"""
        # 1. Login
        login_response = client.post("/api/auth/login", json={
            "username": "testuser",
            "password": "test123"
        })
        assert login_response.status_code == 200
        
        # 2. Crear producto (requiere manejo de sesión)
        # 3. Obtener lista de productos
        # 4. Verificar que el producto creado está en la lista
        
        # Implementación completa requiere manejo de sesiones/tokens
        pass

# Configuración de pytest
if __name__ == "__main__":
    pytest.main([__file__, "-v"])