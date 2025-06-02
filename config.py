"""
Configuración del servidor MCP de Azure Pricing.

Este archivo puede ser sobreescrito mediante variables de entorno con prefijo MCP_
"""
from typing import List, Optional, Union
from pydantic import Field, field_validator, HttpUrl, validator
from pydantic_settings import BaseSettings, SettingsConfigDict
import os

# Valores por defecto
DEFAULT_HOST = '0.0.0.0'
DEFAULT_PORT = 8080
DEFAULT_LOG_LEVEL = 'INFO'

class Settings(BaseSettings):
    # Configuración del servidor
    MCP_HOST: str = Field(
        default=DEFAULT_HOST,
        description='Dirección IP para escuchar (ej: 0.0.0.0 para todas las interfaces)'
    )
    
    MCP_PORT: int = Field(
        default=DEFAULT_PORT,
        description='Puerto para el servidor',
        gt=0,
        lt=65536
    )
    
    MCP_DEBUG: bool = Field(
        default=True,
        description='Habilita el modo debug (no usar en producción)'
    )
    
    MCP_RELOAD: bool = Field(
        default=False,
        description='Habilita la recarga automática en desarrollo'
    )
    
    # Configuración de CORS
    CORS_ORIGINS: Union[str, List[str]] = Field(
        default='*',
        description='Orígenes permitidos para CORS (separados por comas o lista)'
    )
    
    # Configuración de logging
    LOG_LEVEL: str = Field(
        default=DEFAULT_LOG_LEVEL,
        description='Nivel de logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)'
    )
    
    # Configuración de Azure Retail Prices API
    AZURE_RETAIL_PRICES_URL: str = Field(
        default='https://prices.azure.com/api/retail/prices',
        description='URL base de la API de precios de Azure'
    )
    
    AZURE_API_VERSION: str = Field(
        default='2023-01-01-preview',
        description='Versión de la API de precios de Azure'
    )
    
    # Configuración de cálculos
    HOURS_IN_MONTH: int = Field(
        default=730,  # 24 horas * 365 días / 12 meses ≈ 730
        description='Horas en un mes (aprox. 24/7)',
        gt=0
    )
    
    # Configuración de alternativas
    MAX_ALTERNATIVES_TO_SHOW: int = Field(
        default=3,
        description='Número máximo de alternativas a mostrar',
        gt=0
    )
    
    # Configuración de precios
    PRICE_TYPE: str = Field(
        default='Consumption',
        description='Tipo de precio (ej: Consumption)'
    )
    
    # Configuración del modelo
    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        env_prefix='MCP_',
        case_sensitive=False,
        extra='ignore',
        validate_default=True,
        env_nested_delimiter='__'
    )
    
    # Validadores
    @field_validator('CORS_ORIGINS', mode='before')
    def parse_cors_origins(cls, v):
        if not v:
            return ['*']
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(',')]
        if isinstance(v, (list, set)):
            return list(v)
        return str(v).split(',')
    
    @field_validator('LOG_LEVEL')
    def validate_log_level(cls, v):
        if not v:
            return DEFAULT_LOG_LEVEL
        v = v.upper()
        valid_levels = {'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'}
        if v not in valid_levels:
            raise ValueError(f'Nivel de log inválido: {v}. Debe ser uno de: {", ".join(valid_levels)}')
        return v
    
    @field_validator('AZURE_RETAIL_PRICES_URL')
    def validate_azure_url(cls, v):
        if not v:
            v = 'https://prices.azure.com/api/retail/prices'
        v = str(v).strip()
        if not v.startswith(('http://', 'https://')):
            v = f'https://{v}'
        return v.rstrip('/')
    
    @field_validator('AZURE_API_VERSION')
    def validate_api_version(cls, v):
        if not v:
            return '2023-01-01-preview'
        v = str(v).strip()
        # Validar formato de versión (ej: 2023-01-01-preview)
        try:
            parts = v.split('-')
            if not all(part.isdigit() for part in parts[0].split('.')):
                raise ValueError()
        except (ValueError, AttributeError):
            # Si el formato no es válido, usar el valor por defecto
            return '2023-01-01-preview'
        return v
    
    @field_validator('PRICE_TYPE')
    def validate_price_type(cls, v):
        if not v:
            return 'Consumption'
        return str(v).strip()
    
    @field_validator('MCP_DEBUG', 'MCP_RELOAD', mode='before')
    def validate_bool(cls, v):
        if isinstance(v, str):
            v = v.lower()
            if v in ('true', '1', 'yes'):
                return True
            if v in ('false', '0', 'no', ''):
                return False
        return bool(v)

# Cargar configuración
try:
    settings = Settings()
except Exception as e:
    print(f"Error al cargar la configuración: {e}")
    raise

# Configuración de logging
import logging
from logging.config import dictConfig

logging_config = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'default': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
        'simple': {
            'format': '%(levelname)s: %(message)s'
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'default' if settings.MCP_DEBUG else 'simple',
            'stream': 'ext://sys.stdout',
        },
    },
    'loggers': {
        '': {  # root logger
            'handlers': ['console'],
            'level': settings.LOG_LEVEL,
            'propagate': True
        },
        'azure': {
            'level': 'WARNING',  # Reduce el ruido de las librerías de Azure
            'propagate': False
        },
        'urllib3': {
            'level': 'WARNING',  # Reduce el ruido de las peticiones HTTP
            'propagate': False
        },
    }
}

# Aplicar configuración de logging
dictConfig(logging_config)

# Configurar el logger para este módulo
logger = logging.getLogger(__name__)
logger.debug("Configuración cargada correctamente")
