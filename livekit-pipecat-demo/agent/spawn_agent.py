#!/usr/bin/env python3

"""
Simple LiveKit + Pipecat Demo Agent
POC for orchestration without requiring external APIs
"""

import asyncio
import os
import logging
import random
from typing import Optional

from pipecat.frames.frames import TextFrame, AudioRawFrame
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineTask, PipelineParams
from pipecat.processors.frame_processor import FrameProcessor, FrameDirection
from pipecat.transports.livekit.transport import LiveKitTransport, LiveKitParams
from pipecat.audio.vad.silero import SileroVADAnalyzer

from livekit import api

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleEchoProcessor(FrameProcessor):
    """
    Simple processor that responds to voice activity with scripted responses
    No external APIs required - pure POC for LiveKit + Pipecat orchestration
    """
    
    def __init__(self):
        super().__init__()
        self.response_count = 0
        self.scripted_responses = [
            "Got it!",
            "I hear you...got it",
            "Message received...got it", 
            "Understanding you...got it",
            "Copy that...got it",
            "Roger...got it",
            "Loud and clear...got it"
        ]
    
    async def process_frame(self, frame, direction: FrameDirection):
        await super().process_frame(frame, direction)
        
        # Respond to any audio input with scripted text responses
        if isinstance(frame, AudioRawFrame) and direction == FrameDirection.UPSTREAM:
            self.response_count += 1
            
            # Use different response patterns to demonstrate orchestration
            if self.response_count == 1:
                response = "Hello! I'm your Pipecat agent. I can hear you...got it"
            elif self.response_count <= 3:
                response = f"This is response number {self.response_count}...got it"
            else:
                # Use random scripted responses
                response = random.choice(self.scripted_responses)
            
            logger.info(f"🎤 Voice detected -> Responding: '{response}'")
            
            # Send text response (would normally go through TTS)
            text_frame = TextFrame(text=response)
            await self.push_frame(text_frame)

class TextToSpeechSimulator(FrameProcessor):
    """
    Simulates TTS by logging text that would be spoken
    In a real implementation, this would convert text to audio
    """
    
    async def process_frame(self, frame, direction: FrameDirection):
        await super().process_frame(frame, direction)
        
        if isinstance(frame, TextFrame) and frame.text.strip():
            logger.info(f"🔊 [TTS Simulator] Would speak: '{frame.text}'")
            
            # In a real TTS implementation, we would generate audio here
            # For this POC, we just log what would be spoken
            # The text frame continues through the pipeline

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

def create_simple_pipeline(transport: LiveKitTransport) -> Pipeline:
    """
    Create simple pipeline for POC demonstration
    Audio Input -> Echo Processor -> TTS Simulator -> Audio Output
    """
    echo_processor = SimpleEchoProcessor()
    tts_simulator = TextToSpeechSimulator()
    
    return Pipeline([
        transport.input(),     # Audio from LiveKit room
        echo_processor,        # Generate scripted responses
        tts_simulator,         # Simulate TTS (log what would be spoken)
        transport.output(),    # Audio back to LiveKit room
    ])

async def setup_event_handlers(transport: LiveKitTransport, task: PipelineTask) -> None:
    """Setup basic event handlers for the demo"""
    
    @transport.event_handler("on_first_participant_joined")
    async def on_first_participant_joined(transport, participant):
        logger.info(f"✅ Participant joined: {participant.identity}")
        welcome_frame = TextFrame("Welcome to the LiveKit Pipecat demo! Say something and I'll respond with 'got it'")
        await task.queue_frames([welcome_frame])

    @transport.event_handler("on_participant_disconnected")
    async def on_participant_disconnected(transport, participant):
        logger.info(f"👋 Participant left: {participant.identity}")

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
        
        # Create simple pipeline
        pipeline = create_simple_pipeline(transport)
        logger.info("✅ Created simple processing pipeline")
        
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
        logger.info("🎤 Agent ready! Join the room and speak to test the orchestration")
        logger.info("🔊 Agent will respond with scripted messages ending in '...got it'")
        
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