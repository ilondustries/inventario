import bcrypt
import secrets
from datetime import datetime, timedelta
import jwt
from typing import Optional

# 1. MEJORA CRÍTICA: Hash de contraseñas con bcrypt
def hash_password_secure(password: str) -> str:
    """Hash seguro de contraseña con bcrypt y salt automático"""
    # bcrypt genera salt automáticamente y es resistente a rainbow tables
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def verify_password_secure(password: str, hashed: str) -> bool:
    """Verificar contraseña con bcrypt"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

# 2. MEJORA: JWT tokens para API (opcional pero profesional)
JWT_SECRET = secrets.token_urlsafe(32)  # En producción, usar variable de entorno
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 8

def create_jwt_token(user_id: int, username: str) -> str:
    """Crear JWT token para autenticación API"""
    payload = {
        "user_id": user_id,
        "username": username,
        "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS),
        "iat": datetime.utcnow()
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def verify_jwt_token(token: str) -> Optional[dict]:
    """Verificar y decodificar JWT token"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

# 3. MEJORA: Rate limiting para login
class LoginRateLimiter:
    def __init__(self):
        self.attempts = {}  # {ip: [timestamp, timestamp, ...]}
        self.max_attempts = 5
        self.window_minutes = 15
    
    def is_blocked(self, ip_address: str) -> bool:
        """Verificar si una IP está bloqueada por demasiados intentos"""
        now = datetime.utcnow()
        window_start = now - timedelta(minutes=self.window_minutes)
        
        if ip_address not in self.attempts:
            return False
        
        # Limpiar intentos antiguos
        self.attempts[ip_address] = [
            attempt for attempt in self.attempts[ip_address] 
            if attempt > window_start
        ]
        
        return len(self.attempts[ip_address]) >= self.max_attempts
    
    def record_attempt(self, ip_address: str):
        """Registrar un intento de login fallido"""
        if ip_address not in self.attempts:
            self.attempts[ip_address] = []
        
        self.attempts[ip_address].append(datetime.utcnow())

# 4. MEJORA: Validación robusta de inputs
import re
from typing import Union

def validate_input(value: Union[str, int, float], field_name: str, 
                  min_length: int = 0, max_length: int = 255,
                  pattern: str = None, required: bool = True) -> str:
    """Validación robusta de inputs con sanitización"""
    
    if value is None or (isinstance(value, str) and not value.strip()):
        if required:
            raise ValueError(f"{field_name} es requerido")
        return ""
    
    # Convertir a string y limpiar
    clean_value = str(value).strip()
    
    # Validar longitud
    if len(clean_value) < min_length:
        raise ValueError(f"{field_name} debe tener al menos {min_length} caracteres")
    
    if len(clean_value) > max_length:
        raise ValueError(f"{field_name} no puede exceder {max_length} caracteres")
    
    # Validar patrón si se proporciona
    if pattern and not re.match(pattern, clean_value):
        raise ValueError(f"{field_name} tiene formato inválido")
    
    return clean_value

# Patrones comunes
PATTERNS = {
    'username': r'^[a-zA-Z0-9_]{3,20}$',
    'email': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
    'codigo_barras': r'^[a-zA-Z0-9]{6,20}$',
    'ubicacion': r'^[A-Z]\d{2}$'  # Ej: A01, B15
}