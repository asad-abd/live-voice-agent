#!/usr/bin/env python3

"""
Simple LiveKit + Pipecat Demo Agent
POC for orchestration without requiring external APIs
"""

import asyncio
import os
import logging
import random
import time
import json
from typing import Optional

from pipecat.frames.frames import TextFrame
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineTask, PipelineParams
from pipecat.processors.frame_processor import FrameProcessor, FrameDirection
from pipecat.transports.livekit.transport import LiveKitTransport, LiveKitParams
from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.services.deepgram.stt import DeepgramSTTService

from livekit import api, rtc
import asyncio

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EchoModifyProcessor(FrameProcessor):
    """
    Echo + Modify processor that listens for speech and responds with the user's text + "...got it"
    Supports barge-in and proper transcript handling
    """
    
    def __init__(self, transport: LiveKitTransport):
        super().__init__()
        self.transport = transport
        self.response_count = 0
        self.last_user_transcript = ""
        self.speech_start_time = None
        self.is_speaking = False
        self._stream_task: Optional[asyncio.Task] = None
        
    async def process_frame(self, frame, direction: FrameDirection):
        await super().process_frame(frame, direction)

        # Log and forward ANY TextFrame coming from STT (final or partial)
        if isinstance(frame, TextFrame):
            text = (frame.text or "").strip()
            if not text:
                return

            is_final = getattr(frame, "is_final", True)
            logger.info(f"🎤 [DEEPGRAM] transcript (final={is_final}): '{text}'")

            # Forward to UI: partials as 'user_partial', finals as 'user_transcript'
            event_type = "user_transcript" if is_final else "user_partial"
            await self.send_data_message({
                "type": event_type,
                "text": text,
                "timestamp": time.time()
            })

            if not is_final:
                return

            # For finals, generate echo + modify and send immediately
            self.last_user_transcript = text
            self.speech_start_time = time.time()

            response = f"{text}...got it"
            self.response_count += 1

            await self.send_data_message({
                "type": "agent_speaking",
                "timestamp": time.time()
            })

            if self.speech_start_time:
                latency_ms = (time.time() - self.speech_start_time) * 1000
                logger.info(f"⏱️ [LATENCY] Response time: {latency_ms:.1f}ms")

            # Stream agent response as partials, then send final
            if self._stream_task and not self._stream_task.done():
                self._stream_task.cancel()
            self._stream_task = asyncio.create_task(self._stream_response(response))
            
    async def _stream_response(self, text: str) -> None:
        try:
            # Tokenize by words and stream cumulative text quickly
            parts = text.split()
            cumulative = []
            for word in parts:
                cumulative.append(word)
                await self.send_data_message({
                    "type": "agent_partial",
                    "text": " ".join(cumulative),
                    "timestamp": time.time()
                })
                await asyncio.sleep(0.05)

            await self.send_data_message({
                "type": "agent_response",
                "text": text,
                "timestamp": time.time()
            })
            logger.info(f"🤖 [AGENT] responded: '{text}'")
        except asyncio.CancelledError:
            pass
    
    async def send_data_message(self, message: dict):
        """Send message to React client via LiveKit data channel"""
        try:
            if self.transport is None:
                logger.warning("❌ [DATA CHANNEL] No transport")
                return

            message_json = json.dumps(message)

            # Preferred path: use transport's publish if available
            try:
                if hasattr(self.transport, 'publish_data'):
                    await self.transport.publish_data(message_json.encode('utf-8'), topic="agent-messages")
                    logger.debug(f"📡 [DATA CHANNEL] Sent via transport.publish_data: {message.get('type')}")
                    return
            except Exception as e:
                logger.debug(f"📡 publish_data fallback due to: {e}")

            # Resolve room with small retries to avoid race conditions
            room = None
            for _ in range(10):
                # common attributes across versions
                if getattr(self.transport, 'room', None):
                    room = self.transport.room
                if room is None and hasattr(self.transport, '_room') and getattr(self.transport, '_room'):
                    room = self.transport._room
                client = getattr(self.transport, 'client', None) or getattr(self.transport, '_client', None)
                if room is None and client is not None and getattr(client, 'room', None):
                    room = client.room
                if room and getattr(room, 'local_participant', None):
                    break
                await asyncio.sleep(0.1)

            if not (room and getattr(room, 'local_participant', None)):
                logger.warning("❌ [DATA CHANNEL] Room/local_participant unavailable after retries")
                return

            await room.local_participant.publish_data(
                message_json.encode('utf-8'),
                topic="agent-messages"
            )
            logger.debug(f"📡 [DATA CHANNEL] Sent via room.local_participant: {message.get('type')} ({len(message_json)} bytes)")
        except Exception as e:
            logger.error(f"❌ [DATA CHANNEL] Failed to send {message.get('type', 'unknown')}: {e}")

## Removed TTS simulator – we are text-only now

def create_livekit_token(
    api_key: str = "devkey", 
    api_secret: str = "secret", 
    room_name: str = "test-room", 
    identity: str = "pipecat-agent"
) -> str:
    """Create LiveKit JWT token with dev defaults"""
    return (api.AccessToken(api_key, api_secret)
            .with_identity(identity)
            .with_name("Simple Pipecat Agent")
            .with_grants(api.VideoGrants(
                room_join=True,
                room=room_name,
                can_publish=True,
                can_subscribe=True,
            ))
            .to_jwt())

def create_simple_transport(url: str, token: str, room_name: str) -> LiveKitTransport:
    """Create LiveKit transport for simple demo"""
    return LiveKitTransport(
        url=url,
        token=token,
        room_name=room_name,
        params=LiveKitParams(
            audio_in_enabled=True,
            audio_out_enabled=True,
            vad_analyzer=SileroVADAnalyzer(),
        ),
    )

def create_enhanced_pipeline(transport: LiveKitTransport) -> Pipeline:
    """
    Real microphone pipeline using Deepgram STT:
    Audio Input -> Deepgram STT -> Echo+Modify (text only) -> (optional) Output
    """
    stt_service = DeepgramSTTService(api_key="YOUR_DEEPGRAM_API_KEY")
    echo_processor = EchoModifyProcessor(transport)

    return Pipeline([
        transport.input(),   # LiveKit audio in
        stt_service,         # Real-time STT
        echo_processor,      # Generate echo+modify text response
        # transport.output() # No audio output needed for text-only demo
    ])

class STTSimulator(FrameProcessor):
    """
    Aggressive STT Simulator - generates transcripts from ANY audio activity
    Much more responsive for demo purposes
    """
    
    def __init__(self):
        super().__init__()
        self.transcript_counter = 0
        self.last_transcript_time = 0
        self.audio_frame_count = 0
        self.total_audio_duration = 0.0
        self.last_test_time = time.time()  # For periodic testing
        
        # Sample transcripts to simulate different user inputs
        self.sample_transcripts = [
            "Hello there",
            "How are you doing today", 
            "This is a test message",
            "Can you hear me clearly",
            "What's the weather like",
            "Tell me something interesting",
            "I'm testing the barge-in feature",
            "This system seems to be working well",
            "Let's try a longer message to see how it handles it",
            "Perfect, this is exactly what I wanted"
        ]
    
    async def process_frame(self, frame, direction: FrameDirection):
        await super().process_frame(frame, direction)
        
        # Log ALL non-audio frames for debugging
        if direction == FrameDirection.UPSTREAM:
            frame_type = type(frame).__name__
            if frame_type != "AudioRawFrame":
                logger.info(f"🔍 [FRAME DEBUG] Received: {frame_type}")
        
        # AGGRESSIVE audio processing - respond to ANY audio
        if isinstance(frame, AudioRawFrame) and direction == FrameDirection.UPSTREAM:
            self.audio_frame_count += 1
            
            # Calculate audio duration
            frame_duration = len(frame.audio) / (16000 * 1 * 2)  # 16kHz, 1 channel, 2 bytes per sample
            self.total_audio_duration += frame_duration
            
            # Log audio activity every 20 frames (more manageable)
            if self.audio_frame_count % 20 == 1:
                logger.info(f"🎵 [AUDIO ACTIVITY] Frame #{self.audio_frame_count}: {len(frame.audio)} bytes, duration: {frame_duration:.3f}s, total: {self.total_audio_duration:.1f}s")
            
            # VERY AGGRESSIVE: Generate transcript every 0.5 seconds of accumulated audio
            current_time = time.time()
            if (self.total_audio_duration >= 0.5 and 
                current_time - self.last_transcript_time >= 0.8):  # Very responsive
                
                await self._generate_transcript(current_time)
        
        # Also handle interruption frames
        elif isinstance(frame, InterruptionFrame) or (hasattr(frame, '__class__') and 'Interruption' in frame.__class__.__name__):
            current_time = time.time()
            logger.info(f"🔊 [VAD EVENT] {type(frame).__name__} detected!")
            
            # Generate transcript on interruption events too
            if current_time - self.last_transcript_time >= 0.5:
                await self._generate_transcript(current_time)
        
        # FALLBACK: Generate test transcript every 10 seconds even without audio (for debugging)
        current_time = time.time()
        if current_time - self.last_test_time >= 10.0:
            logger.info(f"🧪 [TEST TRIGGER] Generating periodic test transcript...")
            await self._generate_transcript(current_time)
            self.last_test_time = current_time
    
    async def _generate_transcript(self, current_time):
        """Generate and send a transcript"""
        # Select transcript based on counter for variety
        transcript = self.sample_transcripts[self.transcript_counter % len(self.sample_transcripts)]
        self.transcript_counter += 1
        
        logger.info(f"🎙️ [STT SIMULATOR] *** GENERATING TRANSCRIPT #{self.transcript_counter}: '{transcript}' ***")
        
        # Send transcript as TextFrame
        text_frame = TextFrame(text=transcript)
        await self.push_frame(text_frame)
        logger.info(f"➡️ [STT PIPELINE] *** SENT TRANSCRIPT TO ECHO PROCESSOR: '{transcript}' ***")
        
        # Reset timing and audio accumulation
        self.last_transcript_time = current_time
        self.total_audio_duration = 0.0

async def setup_event_handlers(transport: LiveKitTransport, task: PipelineTask) -> None:
    """Setup basic event handlers for the demo"""
    
    @transport.event_handler("on_connected")
    async def on_connected(transport):
        logger.info(f"🔗 [CONNECTION] Agent connected to LiveKit room!")
    
    @transport.event_handler("on_disconnected")
    async def on_disconnected(transport):
        logger.info(f"❌ [CONNECTION] Agent disconnected from LiveKit room")
    
    @transport.event_handler("on_first_participant_joined")
    async def on_first_participant_joined(transport, participant):
        participant_id = participant if isinstance(participant, str) else getattr(participant, 'identity', str(participant))
        logger.info(f"✅ [PARTICIPANT] First participant joined: {participant_id}")
        logger.info(f"🎤 [AUDIO] Waiting for audio from participant...")
        welcome_frame = TextFrame("Welcome to the LiveKit Pipecat demo! Say something and I'll respond with 'got it'")
        await task.queue_frames([welcome_frame])

    @transport.event_handler("on_participant_disconnected")
    async def on_participant_disconnected(transport, participant):
        participant_id = participant if isinstance(participant, str) else getattr(participant, 'identity', str(participant))
        logger.info(f"👋 [PARTICIPANT] Participant left: {participant_id}")
    
    @transport.event_handler("on_track_published")
    async def on_track_published(transport, publication, participant):
        participant_id = participant if isinstance(participant, str) else getattr(participant, 'identity', str(participant))
        pub_kind = getattr(publication, 'kind', str(publication))
        logger.info(f"📡 [TRACK] Track published by {participant_id}: {pub_kind}")
        if pub_kind == "audio":
            logger.info(f"🎵 [AUDIO TRACK] Audio track published! Ready to receive audio data")
    
    @transport.event_handler("on_track_subscribed")
    async def on_track_subscribed(transport, track, publication, participant):
        participant_id = participant if isinstance(participant, str) else getattr(participant, 'identity', str(participant))
        track_kind = getattr(track, 'kind', str(track))
        logger.info(f"📡 [TRACK] Subscribed to {track_kind} track from {participant_id}")
        if track_kind == "audio":
            logger.info(f"🎵 [AUDIO SUBSCRIBE] Successfully subscribed to audio track!")

async def run_simple_agent(
    livekit_url: str = "ws://localhost:7880",
    room_name: str = "test-room"
) -> None:
    """
    Run simple agent for POC demonstration
    No external APIs required!
    """
    try:
        logger.info("🚀 Starting Simple LiveKit + Pipecat Agent...")
        logger.info("💡 No API keys required - this is a pure orchestration demo!")
        
        # Create token with dev credentials
        token = create_livekit_token(room_name=room_name)
        logger.info(f"✅ Generated token for room: {room_name}")
        
        # Create transport
        transport = create_simple_transport(livekit_url, token, room_name)
        logger.info(f"✅ Created transport for: {livekit_url}")
        
        # Create enhanced pipeline with STT simulation and echo+modify
        pipeline = create_enhanced_pipeline(transport)
        logger.info("✅ Created enhanced processing pipeline with echo+modify")
        
        # Create task with interruption support (for barge-in)
        task = PipelineTask(
            pipeline, 
            params=PipelineParams(
                allow_interruptions=True,  # Enables barge-in
                enable_metrics=True
            )
        )
        
        # Setup event handlers
        await setup_event_handlers(transport, task)
        
        # Start the agent
        logger.info("🎤 Agent ready! Join the room and speak to test the echo+modify feature")
        logger.info("🔊 Agent will echo what you say and add '...got it' suffix")
        logger.info("⚡ Barge-in supported - you can interrupt the agent while it's speaking")
        
        runner = PipelineRunner()
        await runner.run(task)
        
    except Exception as e:
        logger.error(f"❌ Agent error: {e}")
        raise

def main():
    """
    Entry point for simple agent demo
    """
    # Get configuration from environment or use defaults
    livekit_url = os.getenv("LIVEKIT_URL", "ws://localhost:7880")
    room_name = os.getenv("LIVEKIT_ROOM", "test-room")
    
    logger.info("=== Simple LiveKit + Pipecat Demo ===")
    logger.info(f"🌐 LiveKit URL: {livekit_url}")
    logger.info(f"🏠 Room: {room_name}")
    logger.info("🔧 Mode: Simple scripted responses (no APIs required)")
    logger.info("")
    logger.info("📋 This POC demonstrates:")
    logger.info("  ✅ LiveKit media routing")
    logger.info("  ✅ Pipecat agent orchestration") 
    logger.info("  ✅ Duplex communication with barge-in support")
    logger.info("  ✅ Voice activity detection")
    logger.info("  ✅ Response generation pipeline")
    logger.info("")
    
    # Run the simple agent
    asyncio.run(run_simple_agent(livekit_url, room_name))

if __name__ == "__main__":
    main()