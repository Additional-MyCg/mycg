# config/settings.py - REPLACE ENTIRE FILE
import os
import threading
import time
from pathlib import Path
from typing import List, Optional, Dict, Any
from pydantic_settings import BaseSettings
from pydantic import Field, validator
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import logging

logger = logging.getLogger(__name__)

class EnvironmentHandler(FileSystemEventHandler):
    """File system event handler for .env file changes"""
    
    def __init__(self, settings_instance):
        self.settings_instance = settings_instance
        self.last_modified = 0
        
    def on_modified(self, event):
        if event.is_directory:
            return
            
        if event.src_path.endswith('.env'):
            # Prevent multiple rapid reloads
            current_time = time.time()
            if current_time - self.last_modified < 1:  # 1 second cooldown
                return
                
            self.last_modified = current_time
            logger.info("🔄 .env file changed, reloading settings...")
            self.settings_instance._reload_settings()

class Settings(BaseSettings):
    """Enhanced settings with auto-reload and validation"""
    
    # AI Services
    openai_api_key: Optional[str] = Field(None, description="OpenAI API key for AI services")
    anthropic_api_key: Optional[str] = Field(None, description="Anthropic API key")
    google_vision_api_key: Optional[str] = Field(None, description="Google Vision API key")

    azure_openai_endpoint: Optional[str] = Field(None, description="Azure OpenAI endpoint")
    azure_openai_api_key: Optional[str] = Field(None, description="Azure OpenAI API key")
    azure_openai_deployment_name: Optional[str] = Field(None, description="Azure OpenAI deployment name")
    azure_openai_api_version: str = Field("2024-02-01", description="Azure OpenAI API version")
    use_azure_openai: bool = Field(False, description="Use Azure OpenAI instead of regular OpenAI")

    # WhatsApp/Messaging
    twilio_account_sid: Optional[str] = Field(None, description="Twilio Account SID")
    twilio_auth_token: Optional[str] = Field(None, description="Twilio Auth Token")
    whatsapp_number: Optional[str] = Field(None, description="WhatsApp Business number")
    whatsapp_verify_token: Optional[str] = Field(None, description="WhatsApp webhook verify token")
    
    # File Storage - Azure
    azure_storage_account: Optional[str] = Field(None, description="Azure Storage Account name")
    azure_storage_key: Optional[str] = Field(None, description="Azure Storage Account key")
    azure_storage_connection_string: Optional[str] = Field(None, description="Azure Storage connection string")
    azure_container_name: str = Field("mycg-documents", description="Azure Blob container name")
    azure_storage_endpoint: Optional[str] = Field(None, description="Azure Storage custom endpoint")
    
    # Redis Configuration
    redis_url: str = Field("redis://localhost:6379", description="Redis connection URL")
    redis_password: Optional[str] = Field(None, description="Redis password")
    redis_db: int = Field(0, description="Redis database number")
    redis_max_connections: int = Field(20, description="Redis max connections")
    
    # Node.js Backend
    node_backend_url: str = Field("http://localhost:3000", description="Node.js backend URL")
    node_backend_api_key: Optional[str] = Field(None, description="Node.js backend API key")
    node_backend_timeout: int = Field(30, description="Backend request timeout in seconds")
    
    # App Settings
    environment: str = Field("development", description="Application environment")
    debug: bool = Field(True, description="Debug mode")
    app_name: str = Field("MyCG AI Service", description="Application name")
    app_version: str = Field("1.0.0", description="Application version")
    
    # File Processing
    max_file_size: int = Field(10 * 1024 * 1024, description="Maximum file size in bytes")
    allowed_file_types: str = Field(
        "image/jpeg,image/png,application/pdf",
        description="Allowed file MIME types (comma-separated)"
    )

    temp_file_retention_hours: int = Field(24, description="Hours to retain temp files")
    
    # AI Model Settings
    default_ai_model: str = Field("gpt-4o", description="Default OpenAI model")
    max_tokens: int = Field(1000, description="Max tokens for AI responses")
    temperature: float = Field(0.3, description="AI model temperature")
    ai_request_timeout: int = Field(60, description="AI request timeout in seconds")
    ai_max_retries: int = Field(3, description="Max retries for AI requests")
    
    # Security Settings
    secret_key: str = Field("your-secret-key-change-in-production", description="Application secret key")
    allowed_origins: str = Field(
        "*", 
        description="CORS allowed origins (comma-separated)"
    )
    api_key_header: str = Field("X-API-Key", description="API key header name")
    enable_api_key_auth: bool = Field(False, description="Enable API key authentication")
    
    # Rate Limiting
    rate_limit_requests: int = Field(100, description="Rate limit requests per minute")
    rate_limit_whatsapp: int = Field(300, description="WhatsApp rate limit per minute")
    rate_limit_document: int = Field(20, description="Document processing rate limit per minute")
    
    # Logging Configuration
    log_level: str = Field("INFO", description="Logging level")
    log_file: Optional[str] = Field(None, description="Log file path")
    log_max_size: int = Field(10 * 1024 * 1024, description="Max log file size")
    log_backup_count: int = Field(5, description="Number of log backup files")
    enable_json_logging: bool = Field(False, description="Enable JSON structured logging")
    
    # Performance Settings
    worker_processes: int = Field(4, description="Number of worker processes")
    worker_connections: int = Field(1000, description="Worker connections")
    keepalive_timeout: int = Field(65, description="Keep-alive timeout")
    max_request_size: int = Field(50 * 1024 * 1024, description="Max request size")
    
    # Monitoring & Health
    health_check_interval: int = Field(30, description="Health check interval in seconds")
    enable_metrics: bool = Field(True, description="Enable metrics collection")
    metrics_port: int = Field(9000, description="Metrics server port")
    
    # Auto-reload Settings
    enable_auto_reload: bool = Field(True, description="Enable auto-reload of settings")
    auto_reload_delay: float = Field(1.0, description="Auto-reload delay in seconds")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"
        env_prefix = ""
        validate_assignment = True
        use_enum_values = True
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._observer = None
        self._env_handler = None
        self._original_values = {}
        self._callbacks = []
        
        self._store_original_values()
        
        if self.enable_auto_reload and self.environment == "development":
            self._setup_auto_reload()
    
    @validator('environment')
    def validate_environment(cls, v):
        allowed_envs = ['development', 'staging', 'production', 'testing']
        if v not in allowed_envs:
            raise ValueError(f'Environment must be one of {allowed_envs}')
        return v
    
    @validator('log_level')
    def validate_log_level(cls, v):
        allowed_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in allowed_levels:
            raise ValueError(f'Log level must be one of {allowed_levels}')
        return v.upper()
    
    @validator('max_file_size')
    def validate_max_file_size(cls, v):
        if v <= 0:
            raise ValueError('Max file size must be positive')
        if v > 100 * 1024 * 1024:  # 100MB
            raise ValueError('Max file size cannot exceed 100MB')
        return v
    
    @validator('temperature')
    def validate_temperature(cls, v):
        if not 0 <= v <= 2:
            raise ValueError('Temperature must be between 0 and 2')
        return v
    
    # @validator('allowed_file_types', pre=True)
    def parse_file_types(cls, v):
        """Parse file types from string or list"""
        if isinstance(v, str):
            # Handle empty string
            if not v.strip():
                return ["image/jpeg", "image/png", "application/pdf"]
            # Split by comma and clean
            return [ft.strip() for ft in v.split(',') if ft.strip()]
        elif isinstance(v, list):
            return v
        else:
            return ["image/jpeg", "image/png", "application/pdf"]
    
    def _store_original_values(self):
        self._original_values = {
            field: getattr(self, field) 
            for field in self.__fields__.keys()
        }

    def get_file_types_list(self) -> List[str]:
        """Get file types as a list"""
        if isinstance(self.allowed_file_types, str):
            return [ft.strip() for ft in self.allowed_file_types.split(',') if ft.strip()]
        return self.allowed_file_types

    def get_origins_list(self) -> List[str]:
        """Get origins as a list"""
        if isinstance(self.allowed_origins, str):
            if self.allowed_origins.strip() == "*":
                return ["*"]
            return [origin.strip() for origin in self.allowed_origins.split(',') if origin.strip()]
        return self.allowed_origins

    def _setup_auto_reload(self):
        try:
            env_file_path = Path(".env")
            if not env_file_path.exists():
                logger.warning("⚠️ .env file not found, auto-reload disabled")
                return
            
            self._env_handler = EnvironmentHandler(self)
            self._observer = Observer()
            self._observer.schedule(
                self._env_handler,
                path=str(env_file_path.parent),
                recursive=False
            )
            self._observer.start()
            logger.info("✅ Auto-reload enabled for .env file")
            
        except Exception as e:
            logger.error(f"❌ Failed to setup auto-reload: {e}")
    
    def _reload_settings(self):
        try:
            old_values = {
                field: getattr(self, field) 
                for field in self.__fields__.keys()
            }
            
            new_settings = Settings()
            
            changed_fields = []
            for field in self.__fields__.keys():
                old_value = old_values[field]
                new_value = getattr(new_settings, field)
                
                if old_value != new_value:
                    setattr(self, field, new_value)
                    changed_fields.append(field)
            
            if changed_fields:
                logger.info(f"🔄 Settings reloaded. Changed fields: {', '.join(changed_fields)}")
                
                for callback in self._callbacks:
                    try:
                        callback(changed_fields)
                    except Exception as e:
                        logger.error(f"❌ Settings callback error: {e}")
            else:
                logger.debug("📄 Settings file changed but no values updated")
                
        except Exception as e:
            logger.error(f"❌ Failed to reload settings: {e}")
    
    def add_reload_callback(self, callback):
        self._callbacks.append(callback)
    
    def remove_reload_callback(self, callback):
        if callback in self._callbacks:
            self._callbacks.remove(callback)
    
    def get_redis_config(self) -> Dict[str, Any]:
        config = {
            "url": self.redis_url,
            "db": self.redis_db,
            "max_connections": self.redis_max_connections,
            "decode_responses": True
        }
        
        if self.redis_password:
            config["password"] = self.redis_password
            
        return config
    
    def get_ai_config(self) -> Dict[str, Any]:
        return {
            "openai_api_key": self.openai_api_key,
            "azure_openai_endpoint": self.azure_openai_endpoint,
            "azure_openai_api_key": self.azure_openai_api_key,
            "azure_openai_deployment_name": self.azure_openai_deployment_name,
            "azure_openai_api_version": self.azure_openai_api_version,
            "use_azure_openai": self.use_azure_openai,
            "default_model": self.default_ai_model,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "timeout": self.ai_request_timeout,
            "max_retries": self.ai_max_retries
        }
    
    def get_file_config(self) -> Dict[str, Any]:
        return {
            "max_size": self.max_file_size,
            "allowed_types": self.get_file_types_list(),
            "retention_hours": self.temp_file_retention_hours
        }
    
    def is_production(self) -> bool:
        return self.environment == "production"
    
    def is_development(self) -> bool:
        return self.environment == "development"
    
    def is_testing(self) -> bool:
        return self.environment == "testing"
    
    def get_cors_config(self) -> Dict[str, Any]:
        return {
            "allow_origins": self.get_origins_list(),
            "allow_credentials": True,
            "allow_methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["*"]
        }

    def get_azure_config(self) -> Dict[str, Any]:
        """Get Azure storage configuration"""
        return {
            "account_name": self.azure_storage_account,
            "account_key": self.azure_storage_key,
            "connection_string": self.azure_storage_connection_string,
            "container_name": self.azure_container_name,
            "endpoint": self.azure_storage_endpoint
        }

    def validate_critical_settings(self) -> List[str]:
        issues = []
        
        if not self.openai_api_key and self.environment == "production":
            issues.append("OpenAI API key is required in production")
        
        if self.twilio_account_sid and not self.twilio_auth_token:
            issues.append("Twilio auth token is required when account SID is provided")
        
        if self.secret_key == "your-secret-key-change-in-production" and self.is_production():
            issues.append("Secret key must be changed in production")
        
        if self.azure_storage_account and not (self.azure_storage_key or self.azure_storage_connection_string):
            issues.append("Azure storage key or connection string is required when storage account is provided")
    
        return issues
    
    def export_config(self, mask_secrets: bool = True) -> Dict[str, Any]:
        config = {}
        
        for field_name, field_info in self.__fields__.items():
            value = getattr(self, field_name)
            
            if mask_secrets and any(secret in field_name.lower() for secret in ['key', 'token', 'password', 'secret']):
                if value:
                    config[field_name] = "***MASKED***"
                else:
                    config[field_name] = None
            else:
                config[field_name] = value
        
        return config
    
    def __del__(self):
        """Cleanup file watcher on instance destruction"""
        try:
            if hasattr(self, '_observer') and self._observer and self._observer.is_alive():
                self._observer.stop()
                self._observer.join()
        except Exception:
            pass  # Ignore cleanup errors

# Global settings instance
settings = Settings()

def get_settings() -> Settings:
    return settings

def reload_settings():
    global settings
    settings._reload_settings()

def configure_for_testing():
    global settings
    
    test_overrides = {
        "environment": "testing",
        "debug": True,
        "redis_url": "redis://localhost:6379/1",
        "enable_auto_reload": False,
        "openai_api_key": "test-key",
        "node_backend_url": "http://test-backend:3000"
    }
    
    for key, value in test_overrides.items():
        setattr(settings, key, value)
    
    return settings

def configure_for_production():
    global settings
    
    issues = settings.validate_critical_settings()
    if issues:
        error_msg = "Production configuration issues:\n" + "\n".join(f"- {issue}" for issue in issues)
        raise ValueError(error_msg)
    
    production_overrides = {
        "debug": False,
        "enable_auto_reload": False,
        "log_level": "INFO"
    }
    
    for key, value in production_overrides.items():
        setattr(settings, key, value)
    
    return settings

def setup_settings_handlers():
    def on_ai_settings_change(changed_fields):
        ai_fields = ['openai_api_key', 'default_ai_model', 'max_tokens', 'temperature']
        if any(field in changed_fields for field in ai_fields):
            logger.info("🤖 AI settings changed, reinitializing AI service...")
    
    def on_redis_settings_change(changed_fields):
        redis_fields = ['redis_url', 'redis_password', 'redis_db']
        if any(field in changed_fields for field in redis_fields):
            logger.info("🗃️ Redis settings changed, reconnecting...")
    
    def on_security_settings_change(changed_fields):
        security_fields = ['secret_key', 'allowed_origins', 'enable_api_key_auth']
        if any(field in changed_fields for field in security_fields):
            logger.warning("🔐 Security settings changed!")
    
    settings.add_reload_callback(on_ai_settings_change)
    settings.add_reload_callback(on_redis_settings_change)
    settings.add_reload_callback(on_security_settings_change)