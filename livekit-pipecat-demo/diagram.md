# LiveKit + Pipecat Demo - System Architecture

## Flow Diagram

```
🎤 Browser Mic
    ↓ (WebRTC Audio Stream)
📡 LiveKit Server
    ↓ (Room Audio Subscription)
🤖 Pipecat Agent
    ↓ (Audio Processing Pipeline)
    ┌─────────────────────────────────┐
    │  STT (Deepgram)                │
    │  "Hello world" → Text           │
    └─────────────────────────────────┘
    ↓
    ┌─────────────────────────────────┐
    │  Echo Modifier                 │
    │  "Hello world" + "...got it"   │
    └─────────────────────────────────┘
    ↓
    ┌─────────────────────────────────┐
    │  TTS (OpenAI)                  │
    │  Text → Audio                  │
    └─────────────────────────────────┘
    ↓ (Processed Audio)
📡 LiveKit Server
    ↓ (WebRTC Audio Stream)
🔊 Browser Speaker
```

## Detailed Component Flow

### 1. Client Connection
```
Browser → Token Server → JWT Token → LiveKit Room Join
```

### 2. Audio Processing Pipeline
```
Mic Input → LiveKit Transport → STT Service → Text Processing → TTS Service → LiveKit Output → Speaker
```

### 3. Barge-in Support
```
User Speech (while agent speaking) → VAD Detection → Pipeline Interruption → New Processing Cycle
```

## Technology Stack

### LiveKit (Media Layer)
- **Role**: Real-time media routing and WebRTC transport
- **Handles**: Audio/video streaming, room management, scaling
- **Protocol**: WebRTC with adaptive bitrate

### Pipecat (Agent Layer)  
- **Role**: AI agent orchestration and processing
- **Handles**: STT, text processing, TTS, pipeline management
- **Pattern**: Declarative pipeline with functional frame processing

### Integration Points
1. **LiveKit Transport**: Pipecat joins LiveKit rooms as a participant
2. **Token Server**: Generates JWT tokens for secure room access
3. **VAD (Voice Activity Detection)**: Enables natural conversation flow
4. **Frame Processing**: Immutable audio/text frames flow through pipeline

## Latency Breakdown

```
Total Latency: 400-600ms (typical)

├── Browser → LiveKit: ~50ms (WebRTC)
├── LiveKit → Pipecat: ~20ms (local)
├── STT Processing: ~150-300ms (Deepgram API)
├── Text Modification: ~1ms (local)
├── TTS Processing: ~200-400ms (OpenAI API)
├── Pipecat → LiveKit: ~20ms (local)
└── LiveKit → Browser: ~50ms (WebRTC)
```

## Functional Programming Patterns

### Pipecat Pipeline (Declarative)
```python
Pipeline([
    transport.input(),    # Audio frames in
    stt_service,         # Audio → Text
    echo_modifier,       # Text → Modified Text  
    tts_service,         # Text → Audio
    transport.output(),  # Audio frames out
])
```

### Token Server (Controller → Processor → Accessor)
```python
# Controller: Business logic orchestration
generate_token_for_room() 
    ↓
# Processor: Validation and formatting
process_token_request()
    ↓  
# Accessor: LiveKit API interaction
create_livekit_token()
```

## Error Handling & Resilience

- **Connection Failures**: Automatic reconnection with exponential backoff
- **API Failures**: Graceful degradation and error logging  
- **Barge-in**: Pipeline interruption support for natural conversation
- **Token Expiry**: Configurable TTL with refresh capability
