"""
Token Controller
Core business logic for LiveKit token generation
Orchestrates processors and accessors
"""

import logging
from typing import Optional

from processors.token_processor import (
    process_token_request,
    format_token_response,
    calculate_token_metadata,
    create_token_log_entry
)
from accessors.livekit_accessor import create_livekit_token
from utils.config import get_config

# Configure logging
logger = logging.getLogger(__name__)

async def generate_token_for_room(
    room_name: str,
    identity: str,
    name: Optional[str] = None
) -> str:
    """
    Core business logic for generating LiveKit room access tokens
    
    Orchestrates:
    1. Input validation and processing (processor)
    2. Token generation (accessor)
    3. Response formatting (processor)
    4. Logging (processor)
    
    Args:
        room_name: Name of the room to join
        identity: Unique user identifier
        name: Optional display name
        
    Returns:
        JWT token string
        
    Raises:
        ValueError: If input validation fails
        Exception: If token generation fails
    """
    config = get_config()
    
    try:
        # Step 1: Process and validate input parameters (processor)
        validated_room, validated_identity, validated_name = process_token_request(
            room_name, identity, name
        )
        
        logger.info(f"Processing token request for room: {validated_room}, identity: {validated_identity}")
        
        # Step 2: Generate token metadata for logging (processor)
        token_metadata = calculate_token_metadata(
            validated_room, validated_identity, config.TOKEN_TTL_HOURS
        )
        
        # Step 3: Generate LiveKit JWT token (accessor)
        jwt_token = create_livekit_token(
            api_key=config.LIVEKIT_API_KEY,
            api_secret=config.LIVEKIT_API_SECRET,
            room_name=validated_room,
            identity=validated_identity,
            name=validated_name,
            ttl_hours=config.TOKEN_TTL_HOURS
        )
        
        # Step 4: Create success log entry (processor)
        log_entry = create_token_log_entry(
            validated_room, validated_identity, success=True
        )
        logger.info(f"Token generated successfully: {log_entry}")
        
        return jwt_token
        
    except ValueError as e:
        # Handle validation errors
        error_message = f"Validation error: {str(e)}"
        logger.warning(error_message)
        
        # Create error log entry (processor)
        log_entry = create_token_log_entry(
            room_name, identity, success=False, error_message=str(e)
        )
        logger.warning(f"Token generation failed: {log_entry}")
        
        raise ValueError(error_message)
        
    except Exception as e:
        # Handle unexpected errors
        error_message = f"Token generation failed: {str(e)}"
        logger.error(error_message)
        
        # Create error log entry (processor)
        log_entry = create_token_log_entry(
            room_name, identity, success=False, error_message=str(e)
        )
        logger.error(f"Unexpected error: {log_entry}")
        
        raise Exception(error_message)

async def validate_token_request(
    room_name: str,
    identity: str,
    name: Optional[str] = None
) -> dict:
    """
    Business logic for validating token requests without generating tokens
    
    Args:
        room_name: Name of the room
        identity: User identity
        name: Optional display name
        
    Returns:
        Validation result dictionary
        
    Raises:
        ValueError: If validation fails
    """
    try:
        # Use processor for validation
        validated_room, validated_identity, validated_name = process_token_request(
            room_name, identity, name
        )
        
        config = get_config()
        
        # Calculate metadata (processor)
        metadata = calculate_token_metadata(
            validated_room, validated_identity, config.TOKEN_TTL_HOURS
        )
        
        return {
            "valid": True,
            "room": validated_room,
            "identity": validated_identity,
            "name": validated_name,
            "metadata": metadata
        }
        
    except ValueError as e:
        logger.warning(f"Token request validation failed: {str(e)}")
        raise

async def get_token_configuration() -> dict:
    """
    Business logic for retrieving token server configuration
    
    Returns:
        Configuration information (non-sensitive)
    """
    config = get_config()
    
    return {
        "server": "livekit-token-server",
        "version": "1.0.0",
        "default_ttl_hours": config.TOKEN_TTL_HOURS,
        "max_ttl_hours": 168,  # 1 week
        "supported_features": [
            "room_join",
            "audio_publish",
            "audio_subscribe",
            "data_publish"
        ]
    }
