# LiveKit vs Pipecat Reflection

## What LiveKit Does Well
Handles WebRTC complexities, low-latency audio transport (~100ms), scaling, and network resilience. Docker setup is straightforward and token auth works well.

## What Pipecat Does Well  
Pipeline architecture for voice agents, built-in AI integrations (Deepgram, OpenAI), conversation flow with barge-in support, and VAD handling.

## Limitations When Combined
Latency stack-up (browser → LiveKit → Pipecat → APIs), multi-service complexity, external API dependencies, and debugging across systems.

## Production Split
**LiveKit**: Media transport, WebRTC, scaling, security  
**Pipecat**: AI logic, conversation flow, business rules  
Keep them loosely coupled with separate deployments and circuit breakers.
