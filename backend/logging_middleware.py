"""
Middleware para logging y manejo de errores globales
"""
import time
import logging
import sys
import json
from typing import Optional
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.middleware.base import BaseHTTPMiddleware
from .config import LOG_LEVEL, LOG_FORMAT, IS_PRODUCTION

# Configurar logging
logger = logging.getLogger("logistica_hesego")
logger.setLevel(getattr(logging, LOG_LEVEL))

# Handler para consola
handler = logging.StreamHandler(sys.stdout)

if LOG_FORMAT == "json":
    # Formato JSON para producción
    class JSONFormatter(logging.Formatter):
        def format(self, record):
            log_data = {
                "timestamp": self.formatTime(record, self.datefmt),
                "level": record.levelname,
                "logger": record.name,
                "message": record.getMessage(),
                "module": record.module,
                "function": record.funcName,
                "line": record.lineno
            }
            if record.exc_info:
                log_data["exception"] = self.formatException(record.exc_info)
            return json.dumps(log_data, ensure_ascii=False)
    
    handler.setFormatter(JSONFormatter())
else:
    # Formato de texto para desarrollo
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(funcName)s:%(lineno)d - %(message)s'
    )
    handler.setFormatter(formatter)

logger.addHandler(handler)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware para logging de requests"""
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Información del request
        logger.info(f"Request: {request.method} {request.url.path}")
        
        try:
            response = await call_next(request)
            
            # Calcular tiempo de procesamiento
            process_time = time.time() - start_time
            
            # Log de respuesta
            logger.info(
                f"Response: {request.method} {request.url.path} "
                f"Status={response.status_code} Time={process_time:.3f}s"
            )
            
            # Agregar header con tiempo de procesamiento
            response.headers["X-Process-Time"] = str(process_time)
            
            return response
            
        except Exception as e:
            process_time = time.time() - start_time
            logger.error(
                f"Error: {request.method} {request.url.path} "
                f"Time={process_time:.3f}s Error={str(e)}",
                exc_info=True
            )
            raise


async def global_exception_handler(request: Request, exc: Exception):
    """Manejador global de excepciones"""
    logger.error(
        f"Unhandled exception: {type(exc).__name__}: {str(exc)}",
        exc_info=True
    )
    
    if IS_PRODUCTION:
        # En producción, no exponer detalles internos
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "Internal Server Error",
                "message": "Ha ocurrido un error interno. Por favor contacte al administrador."
            }
        )
    else:
        # En desarrollo, mostrar detalles
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": type(exc).__name__,
                "message": str(exc),
                "type": str(type(exc))
            }
        )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Manejador de errores de validación"""
    logger.warning(f"Validation error: {exc.errors()}")
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation Error",
            "message": "Los datos proporcionados no son válidos",
            "details": exc.errors()
        }
    )


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Obtener logger para un módulo específico"""
    if name:
        return logging.getLogger(f"logistica_hesego.{name}")
    return logger
