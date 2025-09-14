"""
Configuration management for LiveKit Token Server
Functional approach to environment-based configuration
"""

import os
from dataclasses import dataclass
from typing import Optional

@dataclass(frozen=True)
class Config:
    """Immutable configuration object"""
    HOST: str
    PORT: int
    DEBUG: bool
    LIVEKIT_API_KEY: str
    LIVEKIT_API_SECRET: str
    TOKEN_TTL_HOURS: int

def get_env_var(key: str, default: Optional[str] = None, required: bool = True) -> str:
    """
    Pure function to get environment variable with validation
    
    Args:
        key: Environment variable name
        default: Default value if not found
        required: Whether the variable is required
        
    Returns:
        Environment variable value
        
    Raises:
        ValueError: If required variable is missing
    """
    value = os.getenv(key, default)
    
    if required and value is None:
        raise ValueError(f"Required environment variable {key} is not set")
    
    return value or ""

def parse_bool(value: str, default: bool = False) -> bool:
    """Pure function to parse boolean from string"""
    return value.lower() in ('true', '1', 'yes', 'on') if value else default

def parse_int(value: str, default: int) -> int:
    """Pure function to parse integer from string with fallback"""
    try:
        return int(value) if value else default
    except ValueError:
        return default

def create_config() -> Config:
    """
    Factory function to create configuration from environment
    
    Returns:
        Immutable Config object
    """
    return Config(
        HOST=get_env_var("HOST", "0.0.0.0", required=False),
        PORT=parse_int(get_env_var("PORT", "8080", required=False), 8080),
        DEBUG=parse_bool(get_env_var("DEBUG", "false", required=False)),
        LIVEKIT_API_KEY=get_env_var("LIVEKIT_API_KEY", "devkey", required=False),
        LIVEKIT_API_SECRET=get_env_var("LIVEKIT_API_SECRET", "secret", required=False),
        TOKEN_TTL_HOURS=parse_int(get_env_var("TOKEN_TTL_HOURS", "24", required=False), 24),
    )

# Singleton config instance (functional approach)
_config_instance: Optional[Config] = None

def get_config() -> Config:
    """
    Get or create configuration instance (memoized)
    
    Returns:
        Config instance
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = create_config()
    return _config_instance
