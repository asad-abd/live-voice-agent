# 🎙️ LiveKit + Pipecat Demo - ULTRA SIMPLE

**Real-time voice agent with LiveKit + Pipecat in just 2 commands!**

## 🚀 Quick Start

```bash
cd src/livekit-pipecat-demo

# First time: setup + demo
make setup && make demo

# Next time: just demo
make demo
```

**That's it!** Browser opens automatically at http://localhost:3000

## 🎤 How to Test

1. Click **"Join Room and Enable Mic"**
2. Grant microphone permissions
3. Say something - agent responds with "...got it"
4. Try interrupting the agent (barge-in test)

## 🛑 To Stop

```bash
make stop
```

## 💡 What This Does

- **LiveKit**: Real-time media routing (WebRTC)
- **Pipecat**: Voice agent pipeline (VAD + responses)
- **No API keys required** - pure orchestration demo!

## 🔧 Requirements

- **Docker** (for LiveKit server)
- **Python 3.8+** (for Pipecat agent)

## 📁 Architecture

```
Browser Client ←→ LiveKit Server ←→ Pipecat Agent
     ↑                 ↑                 ↑
  WebRTC Audio    Media Routing    Voice Processing
```

**Ultra simple. No complex setup. Just works.** 🚀