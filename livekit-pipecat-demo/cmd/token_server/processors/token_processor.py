"""
Token Processor
Processing and formatting logic for LiveKit tokens
Pure functions for data transformation and validation
"""

import re
from typing import Dict, Optional, Tuple

def validate_room_name(room_name: str) -> str:
    """
    Pure function to validate and sanitize room name
    
    Args:
        room_name: Raw room name input
        
    Returns:
        Validated room name
        
    Raises:
        ValueError: If room name is invalid
    """
    if not room_name or not room_name.strip():
        raise ValueError("Room name cannot be empty")
    
    # Sanitize: remove extra spaces and convert to lowercase
    sanitized = room_name.strip().lower()
    
    # Validate format: alphanumeric, hyphens, underscores only
    if not re.match(r'^[a-z0-9_-]+$', sanitized):
        raise ValueError("Room name can only contain lowercase letters, numbers, hyphens, and underscores")
    
    # Length constraints
    if len(sanitized) < 3:
        raise ValueError("Room name must be at least 3 characters long")
    
    if len(sanitized) > 50:
        raise ValueError("Room name cannot exceed 50 characters")
    
    return sanitized

def validate_identity(identity: str) -> str:
    """
    Pure function to validate and sanitize user identity
    
    Args:
        identity: Raw identity input
        
    Returns:
        Validated identity
        
    Raises:
        ValueError: If identity is invalid
    """
    if not identity or not identity.strip():
        raise ValueError("Identity cannot be empty")
    
    # Sanitize: remove extra spaces
    sanitized = identity.strip()
    
    # Validate format: alphanumeric, hyphens, underscores, dots
    if not re.match(r'^[a-zA-Z0-9._-]+$', sanitized):
        raise ValueError("Identity can only contain letters, numbers, dots, hyphens, and underscores")
    
    # Length constraints
    if len(sanitized) < 2:
        raise ValueError("Identity must be at least 2 characters long")
    
    if len(sanitized) > 40:
        raise ValueError("Identity cannot exceed 40 characters")
    
    return sanitized

def validate_display_name(name: Optional[str]) -> Optional[str]:
    """
    Pure function to validate and sanitize display name
    
    Args:
        name: Raw display name input (optional)
        
    Returns:
        Validated display name or None
        
    Raises:
        ValueError: If display name is invalid
    """
    if not name:
        return None
    
    sanitized = name.strip()
    
    if not sanitized:
        return None
    
    # Length constraint for display names
    if len(sanitized) > 100:
        raise ValueError("Display name cannot exceed 100 characters")
    
    # Basic sanitization: remove control characters
    sanitized = re.sub(r'[\x00-\x1f\x7f]', '', sanitized)
    
    return sanitized if sanitized else None

def process_token_request(
    room_name: str, 
    identity: str, 
    name: Optional[str] = None
) -> Tuple[str, str, Optional[str]]:
    """
    Pure function to process and validate token request parameters
    
    Args:
        room_name: Raw room name
        identity: Raw identity
        name: Raw display name (optional)
        
    Returns:
        Tuple of (validated_room, validated_identity, validated_name)
        
    Raises:
        ValueError: If any parameter is invalid
    """
    validated_room = validate_room_name(room_name)
    validated_identity = validate_identity(identity)
    validated_name = validate_display_name(name)
    
    return validated_room, validated_identity, validated_name

def format_token_response(token: str) -> Dict[str, str]:
    """
    Pure function to format token response
    
    Args:
        token: JWT token string
        
    Returns:
        Formatted response dictionary
        
    Raises:
        ValueError: If token is invalid
    """
    if not token or not token.strip():
        raise ValueError("Token cannot be empty")
    
    # Basic JWT format validation (3 parts separated by dots)
    token_parts = token.split('.')
    if len(token_parts) != 3:
        raise ValueError("Invalid JWT token format")
    
    return {
        "token": token.strip(),
        "type": "Bearer",
        "algorithm": "HS256"
    }

def calculate_token_metadata(
    room_name: str, 
    identity: str, 
    ttl_hours: int
) -> Dict[str, any]:
    """
    Pure function to calculate token metadata
    
    Args:
        room_name: Room name
        identity: User identity
        ttl_hours: Token TTL in hours
        
    Returns:
        Metadata dictionary
    """
    return {
        "room": room_name,
        "identity": identity,
        "ttl_hours": ttl_hours,
        "permissions": {
            "can_publish": True,
            "can_subscribe": True,
            "can_publish_data": True
        }
    }

def create_token_log_entry(
    room_name: str, 
    identity: str, 
    success: bool = True, 
    error_message: Optional[str] = None
) -> Dict[str, any]:
    """
    Pure function to create structured log entry for token operations
    
    Args:
        room_name: Room name
        identity: User identity
        success: Whether operation was successful
        error_message: Error message if failed
        
    Returns:
        Structured log entry
    """
    from datetime import datetime
    
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "operation": "token_generation",
        "room": room_name,
        "identity": identity,
        "success": success
    }
    
    if not success and error_message:
        log_entry["error"] = error_message
    
    return log_entry
