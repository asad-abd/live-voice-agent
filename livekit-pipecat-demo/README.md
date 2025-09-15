# LiveKit + Pipecat Voice Agent Demo

Real-time voice agent with echo+modify responses and barge-in support.

## Quick Start

```bash
make setup && make demo
```

Browser opens at http://localhost:3000. Click "Join Room and Enable Mic" and speak.

## Configuration

**For real speech recognition**: Edit `agent/spawn_agent.py` line 197 and replace `"YOUR_DEEPGRAM_API_KEY"` with your actual Deepgram API key.

## Features

- ✅ Real-time voice interaction
- ✅ Echo + modify responses ("...got it" suffix)  
- ✅ Barge-in interruption support
- ✅ Latency measurement
- ✅ Message transcript display

## Architecture

```
React Client ←→ LiveKit Server ←→ Pipecat Agent ←→ Deepgram STT
```