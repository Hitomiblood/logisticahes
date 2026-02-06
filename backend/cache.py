"""
Módulo de caché con Redis para LogísticaHES
"""
import json
import hashlib
import time
from typing import Optional, Any
from functools import wraps
from .config import REDIS_HOST, REDIS_PORT, REDIS_DB, CACHE_TTL

# Intentar importar redis, si no está disponible usar caché en memoria
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    print("⚠️ Redis no disponible, usando caché en memoria")

# Cliente Redis global
_redis_client: Optional[redis.Redis] = None

# Caché en memoria como fallback
_memory_cache: dict = {}


def get_redis_client() -> Optional[redis.Redis]:
    """Obtener cliente Redis, creándolo si no existe"""
    global _redis_client
    
    if not REDIS_AVAILABLE:
        return None
    
    if _redis_client is None:
        try:
            _redis_client = redis.Redis(
                host=REDIS_HOST,
                port=REDIS_PORT,
                db=REDIS_DB,
                decode_responses=True,
                socket_connect_timeout=2,
                socket_timeout=2
            )
            # Verificar conexión
            _redis_client.ping()
            print(f"✅ Conectado a Redis en {REDIS_HOST}:{REDIS_PORT}")
        except Exception as e:
            print(f"⚠️ No se pudo conectar a Redis: {e}")
            _redis_client = None
    
    return _redis_client


def generate_cache_key(prefix: str, **kwargs) -> str:
    """Generar clave de caché única basada en parámetros"""
    # Ordenar parámetros para consistencia
    sorted_params = sorted(kwargs.items())
    params_str = json.dumps(sorted_params, sort_keys=True)
    hash_suffix = hashlib.md5(params_str.encode()).hexdigest()[:12]
    return f"logistica:{prefix}:{hash_suffix}"


def cache_get(key: str) -> Optional[Any]:
    """Obtener valor de caché"""
    client = get_redis_client()
    
    if client:
        try:
            value = client.get(key)
            if value:
                return json.loads(value)
        except Exception as e:
            print(f"⚠️ Error leyendo caché: {e}")
    
# Fallback a memoria
    cached = _memory_cache.get(key)
    if cached:
        # Verificar TTL
        if cached.get('expires_at', 0) > time.time():
            return cached.get('value')
        else:
            # Expirado, eliminar
            del _memory_cache[key]
    return None


def cache_set(key: str, value: Any, ttl: int = CACHE_TTL) -> bool:
    """Guardar valor en caché"""
    client = get_redis_client()
    json_value = json.dumps(value)
    
    if client:
        try:
            client.setex(key, ttl, json_value)
            return True
        except Exception as e:
            print(f"⚠️ Error escribiendo caché: {e}")
    
    # Fallback a memoria con TTL
    if len(_memory_cache) > 1000:
        # Limpiar mitad del caché cuando está lleno
        keys = list(_memory_cache.keys())[:500]
        for k in keys:
            del _memory_cache[k]
    
    _memory_cache[key] = {
        'value': value,
        'expires_at': time.time() + ttl
    }
    return True


def cache_delete_pattern(pattern: str) -> int:
    """Eliminar claves que coincidan con patrón"""
    client = get_redis_client()
    deleted = 0
    
    if client:
        try:
            keys = client.keys(pattern)
            if keys:
                deleted = client.delete(*keys)
        except Exception as e:
            print(f"⚠️ Error eliminando caché: {e}")
    
    # También limpiar memoria
    keys_to_delete = [k for k in _memory_cache.keys() if pattern.replace("*", "") in k]
    for k in keys_to_delete:
        del _memory_cache[k]
        deleted += 1
    
    return deleted


def invalidate_operatividad_cache():
    """Invalidar todo el caché de operatividad"""
    return cache_delete_pattern("logistica:operatividad:*")


def invalidate_compras_cache():
    """Invalidar todo el caché de compras"""
    return cache_delete_pattern("logistica:compras:*")


def invalidate_costos_cache():
    """Invalidar todo el caché de costos"""
    return cache_delete_pattern("logistica:costos:*")


def invalidate_all_cache():
    """Invalidar todo el caché de logística"""
    return cache_delete_pattern("logistica:*")


def cached(prefix: str, ttl: int = CACHE_TTL):
    """Decorador para cachear resultados de funciones async"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generar clave de caché
            cache_key = generate_cache_key(prefix, **kwargs)
            
            # Intentar obtener de caché
            cached_value = cache_get(cache_key)
            if cached_value is not None:
                return cached_value
            
            # Ejecutar función y cachear resultado
            result = await func(*args, **kwargs)
            cache_set(cache_key, result, ttl)
            
            return result
        return wrapper
    return decorator


def get_cache_stats() -> dict:
    """Obtener estadísticas del caché"""
    client = get_redis_client()
    stats = {
        "redis_available": client is not None,
        "memory_cache_size": len(_memory_cache)
    }
    
    if client:
        try:
            info = client.info("memory")
            stats["redis_memory_used"] = info.get("used_memory_human", "N/A")
            stats["redis_keys"] = client.dbsize()
        except Exception as e:
            stats["redis_error"] = str(e)
    
    return stats
