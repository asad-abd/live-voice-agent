#!/usr/bin/env python3

"""
LiveKit Token Server
Provides JWT tokens for LiveKit room access
Architecture: Controller -> Processor -> Accessor pattern
"""

import uvicorn
from fastapi import FastAPI, Query, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from controllers.token_controller import generate_token_for_room
from utils.config import get_config

# Initialize FastAPI app
app = FastAPI(
    title="LiveKit Token Server",
    description="Generates JWT tokens for LiveKit room access",
    version="1.0.0"
)

# Configure CORS for browser clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For demo purposes - restrict in production
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

@app.get("/")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "livekit-token-server"}

@app.get("/token")
async def get_token(
    room: str = Query(..., description="Room name to join"),
    identity: str = Query(..., description="User identity"),
    name: str = Query(None, description="Display name (optional)")
):
    """
    Generate LiveKit access token for room join
    
    Query Parameters:
    - room: The room name to join
    - identity: Unique user identifier  
    - name: Optional display name
    
    Returns:
    - JSON with token field containing JWT
    """
    try:
        # Use controller to handle business logic
        token = await generate_token_for_room(
            room_name=room,
            identity=identity,
            name=name
        )
        
        return JSONResponse(
            content={"token": token},
            status_code=200
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Token generation failed: {str(e)}")

# --- Simple WebSocket broadcast hub for UI fallback ---
connections: set[WebSocket] = set()

async def _broadcast(message: str) -> None:
    stale: list[WebSocket] = []
    for ws in connections:
        try:
            await ws.send_text(message)
        except Exception:
            stale.append(ws)
    for ws in stale:
        try:
            await ws.close()
        except Exception:
            pass
        connections.discard(ws)

@app.websocket("/ws")
async def ws_endpoint(ws: WebSocket):
    await ws.accept()
    connections.add(ws)
    try:
        while True:
            # We don't expect messages from the client; keep connection alive
            await ws.receive_text()
    except WebSocketDisconnect:
        connections.discard(ws)
    except Exception:
        connections.discard(ws)

# Allow other processes (agent) to POST JSON and broadcast to WS listeners
@app.post("/broadcast")
async def http_broadcast(payload: dict):
    from json import dumps
    await _broadcast(dumps(payload))
    return {"status": "ok"}

def main():
    """Application entry point"""
    config = get_config()
    
    uvicorn.run(
        "main:app",
        host=config.HOST,
        port=config.PORT,
        reload=config.DEBUG,
        log_level="info" if not config.DEBUG else "debug"
    )

if __name__ == "__main__":
    main()
