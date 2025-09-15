"""
LiveKit Accessor
Handles direct interactions with LiveKit API
Pure functions for token generation
"""

from datetime import datetime, timedelta
from typing import Optional
from livekit import api

def create_access_token(api_key: str, api_secret: str) -> api.AccessToken:
    """
    Pure function to create LiveKit AccessToken instance
    
    Args:
        api_key: LiveKit API key
        api_secret: LiveKit API secret
        
    Returns:
        AccessToken instance
    """
    return api.AccessToken(api_key, api_secret)

def configure_token_identity(
    token: api.AccessToken, 
    identity: str, 
    name: Optional[str] = None
) -> api.AccessToken:
    """
    Pure function to configure token identity
    
    Args:
        token: AccessToken instance
        identity: User identity
        name: Optional display name
        
    Returns:
        Configured AccessToken instance
    """
    configured_token = token.with_identity(identity)
    
    if name:
        configured_token = configured_token.with_name(name)
        
    return configured_token

def configure_room_grants(
    token: api.AccessToken,
    room_name: str,
    ttl_hours: int = 24
) -> api.AccessToken:
    """
    Pure function to configure room access grants
    
    Args:
        token: AccessToken instance
        room_name: Room name to grant access to
        ttl_hours: Token time-to-live in hours
        
    Returns:
        AccessToken with room grants configured
    """
    # Calculate expiration time
    expiration = datetime.now() + timedelta(hours=ttl_hours)
    
    # Configure grants for room access
    grants = api.VideoGrants(
        room_join=True,
        room=room_name,
        can_publish=True,
        can_subscribe=True,
        can_publish_data=True
    )
    
    return token.with_grants(grants).with_ttl(timedelta(hours=ttl_hours))

def generate_jwt_token(token: api.AccessToken) -> str:
    """
    Pure function to generate JWT from AccessToken
    
    Args:
        token: Configured AccessToken instance
        
    Returns:
        JWT token string
    """
    return token.to_jwt()

def create_livekit_token(
    api_key: str,
    api_secret: str,
    room_name: str,
    identity: str,
    name: Optional[str] = None,
    ttl_hours: int = 24
) -> str:
    """
    Functional composition for LiveKit token creation
    
    Args:
        api_key: LiveKit API key
        api_secret: LiveKit API secret
        room_name: Room name
        identity: User identity
        name: Optional display name
        ttl_hours: Token time-to-live in hours
        
    Returns:
        JWT token string
        
    Raises:
        ValueError: If parameters are invalid
    """
    if not api_key or not api_secret:
        raise ValueError("API key and secret are required")
    
    if not room_name or not identity:
        raise ValueError("Room name and identity are required")
    
    if ttl_hours <= 0 or ttl_hours > 168:  # Max 1 week
        raise ValueError("TTL must be between 1 and 168 hours")
    
    # Functional composition
    token = create_access_token(api_key, api_secret)
    token = configure_token_identity(token, identity, name)
    token = configure_room_grants(token, room_name, ttl_hours)
    
    return generate_jwt_token(token)
