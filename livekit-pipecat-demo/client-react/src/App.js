import React, { useState, useCallback, useEffect, useRef } from 'react';
import {
  LiveKitRoom,
  RoomAudioRenderer,
  useRoomContext,
  useLocalParticipant,
  useDataChannel
} from '@livekit/components-react';
import './App.css';

// Configuration constants
const CONFIG = {
  LIVEKIT_URL: 'ws://localhost:7880',
  TOKEN_SERVER_URL: 'http://localhost:8080/token',
  ROOM_NAME: 'test-room',
  USER_IDENTITY: 'demo-user'
};

// Voice interaction component with message display and latency tracking
function VoiceInteraction({ onDisconnect }) {
  const room = useRoomContext();
  const { localParticipant } = useLocalParticipant();
  const [messages, setMessages] = useState([]);
  const [latencyMeasurements, setLatencyMeasurements] = useState([]);
  const [speechStartTime, setSpeechStartTime] = useState(null);
  const [isAgentSpeaking, setIsAgentSpeaking] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [agentTypingText, setAgentTypingText] = useState('');
  const messagesEndRef = useRef(null);

  // Auto-scroll to latest message
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Listen for data channel messages from agent
  useDataChannel('agent-messages', (data) => {
    try {
      // Handle LiveKit data channel message format
      let messageText;
      
      // Check if data has a payload property (LiveKit format)
      if (data && data.payload) {
        if (data.payload instanceof ArrayBuffer || data.payload instanceof Uint8Array) {
          messageText = new TextDecoder().decode(data.payload);
        } else if (typeof data.payload === 'string') {
          messageText = data.payload;
        } else {
          messageText = String(data.payload);
        }
      } 
      // Handle direct data formats
      else if (data instanceof ArrayBuffer || data instanceof Uint8Array) {
        messageText = new TextDecoder().decode(data);
      } else if (typeof data === 'string') {
        messageText = data;
      } else {
        // Try to convert to string if it's another type
        messageText = String(data);
      }
      
      const message = JSON.parse(messageText);
      console.log(`📨 [DATA CHANNEL] Received message type: ${message.type}`, message);
      
      if (message.type === 'agent_response') {
        console.log(`🤖 [UI] Adding agent response: "${message.text}"`);
        setAgentTypingText('');
        setMessages(prev => [...prev, {
          id: Date.now(),
          sender: 'Agent',
          text: message.text,
          timestamp: new Date().toLocaleTimeString()
        }]);
        
        // Calculate latency if we have a speech start time
        if (speechStartTime) {
          const latency = Date.now() - speechStartTime;
          setLatencyMeasurements(prev => [...prev, latency]);
          console.log(`⏱️ [LATENCY] Measured: ${latency}ms`);
          setSpeechStartTime(null);
        }
        
        setIsAgentSpeaking(false);
      } else if (message.type === 'agent_speaking') {
        console.log(`🗣️ [UI] Agent is now speaking...`);
        setIsAgentSpeaking(true);
      } else if (message.type === 'agent_partial') {
        setIsAgentSpeaking(true);
        setAgentTypingText(message.text);
      } else if (message.type === 'user_partial') {
        setIsSpeaking(true);
      } else if (message.type === 'user_transcript') {
        console.log(`👤 [UI] Adding user transcript: "${message.text}"`);
        setMessages(prev => [...prev, {
          id: Date.now(),
          sender: 'You',
          text: message.text,
          timestamp: new Date().toLocaleTimeString()
        }]);
        setSpeechStartTime(Date.now());
        setIsSpeaking(false);
      }
    } catch (error) {
      console.error('❌ [DATA CHANNEL] Error parsing message:', error);
      console.error('❌ [DATA CHANNEL] Data type:', typeof data, 'Data:', data);
    }
  });

  // Handle microphone toggle
  const toggleMic = useCallback(async () => {
    if (localParticipant) {
      try {
        const currentState = localParticipant.isMicrophoneEnabled;
        console.log(`Toggling microphone from ${currentState} to ${!currentState}`);
        
        if (currentState) {
          await localParticipant.setMicrophoneEnabled(false);
        } else {
          await localParticipant.setMicrophoneEnabled(true);
        }
        
        console.log(`Microphone toggled successfully to: ${!currentState}`);
      } catch (error) {
        console.error('Error toggling microphone:', error);
      }
    }
  }, [localParticipant]);

  // Calculate average latency
  const avgLatency = latencyMeasurements.length > 0 
    ? Math.round(latencyMeasurements.reduce((a, b) => a + b, 0) / latencyMeasurements.length)
    : 0;

  return (
    <div className="voice-interaction">
      {/* Status Bar */}
      <div className="status-bar">
        <div className="connection-status">
          <span className={`status-dot ${room.state === 'connected' ? 'connected' : 'disconnected'}`}></span>
          {room.state === 'connected' ? 'Connected' : 'Disconnected'}
        </div>
        
        <div className="latency-info">
          {latencyMeasurements.length > 0 && (
            <span>Avg Latency: {avgLatency}ms ({latencyMeasurements.length} measurements)</span>
          )}
        </div>
      </div>

      {/* Messages Display */}
      <div className="messages-container">
        <div className="messages-header">
          <h3>🗣️ Voice Conversation</h3>
          <p>Speak naturally - the agent will echo with "...got it"</p>
          <div className={`mic-modulator ${isSpeaking ? 'speaking' : 'silent'}`}>
            <span className="dot"></span>
            <span className="label">{isSpeaking ? 'Listening…' : 'Silent'}</span>
          </div>
        </div>
        
        <div className="messages-list">
          {messages.length === 0 ? (
            <div className="empty-messages">
              <p>Start speaking to begin the conversation...</p>
            </div>
          ) : (
            messages.map(message => (
              <div key={message.id} className={`message ${message.sender === 'You' ? 'user' : 'agent'}`}>
                <div className="message-header">
                  <span className="sender">{message.sender}</span>
                  <span className="timestamp">{message.timestamp}</span>
                </div>
                <div className="message-text">{message.text}</div>
              </div>
            ))
          )}
          {(isAgentSpeaking || agentTypingText) && (
            <div className="agent-typing">
              <span>{agentTypingText || 'Agent is responding...'}</span>
              <div className="typing-dots">
                <span></span><span></span><span></span>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Controls */}
      <div className="voice-controls">
        <button 
          className={`mic-button ${localParticipant?.isMicrophoneEnabled ? 'active' : 'muted'}`}
          onClick={toggleMic}
          title={localParticipant?.isMicrophoneEnabled ? 'Mute Microphone' : 'Unmute Microphone'}
        >
          {localParticipant?.isMicrophoneEnabled ? '🎤' : '🔇'}
          <span>{localParticipant?.isMicrophoneEnabled ? 'Mic On' : 'Mic Off'}</span>
        </button>
        
        <button 
          className="end-call-button"
          onClick={onDisconnect}
          title="End Call"
        >
          📞 End Call
        </button>
      </div>

      {/* Barge-in Instructions */}
      <div className="instructions-minimal">
        <p><strong>💡 Tip:</strong> You can interrupt the agent while it's speaking (barge-in)</p>
      </div>
    </div>
  );
}

// Main App component
function App() {
  const [token, setToken] = useState('');
  const [isConnecting, setIsConnecting] = useState(false);

  // Function to fetch token from server
  const fetchToken = useCallback(async () => {
    try {
      const response = await fetch(`${CONFIG.TOKEN_SERVER_URL}?room=${CONFIG.ROOM_NAME}&identity=${CONFIG.USER_IDENTITY}`);
      if (!response.ok) {
        throw new Error(`Token server error: ${response.status}`);
      }
      const data = await response.json();
      return data.token;
    } catch (error) {
      console.warn('Token server not available, using dev token');
      // Fallback dev token (generated with devkey/secret for test-room)
      return 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3NTc5MTYwMDAsImlzcyI6ImRldmtleSIsIm5iZiI6MTY5NDk0MTQ0MCwic3ViIjoiZGVtby11c2VyIiwidmlkZW8iOnsicm9vbSI6InRlc3Qtcm9vbSIsInJvb21Kb2luIjp0cnVlLCJjYW5QdWJsaXNoIjp0cnVlLCJjYW5TdWJzY3JpYmUiOnRydWV9fQ.Aw1oOQJwGZN9wL0QErKM6HI-Cq-5Qf6F2bKGp9Z7XYs';
    }
  }, []);

  // Handle room connection
  const handleConnect = useCallback(async () => {
    setIsConnecting(true);
    try {
      const newToken = await fetchToken();
      setToken(newToken);
    } catch (error) {
      console.error('Failed to get token:', error);
      alert('Failed to get token. Check console for details.');
    } finally {
      setIsConnecting(false);
    }
  }, [fetchToken]);

  // Handle disconnect
  const handleDisconnect = useCallback(() => {
    setToken('');
    console.log('Disconnected from LiveKit room');
  }, []);

  // If we have a token, render the LiveKit room
  if (token) {
    return (
      <div className="App">
        <LiveKitRoom
          video={false}
          audio={true}
          token={token}
          serverUrl={CONFIG.LIVEKIT_URL}
          data-lk-theme="light"
          onConnected={() => console.log('Connected to LiveKit room!')}
          onDisconnected={() => {
            console.log('Disconnected from LiveKit room');
            setToken('');
          }}
        >
          <RoomAudioRenderer />
          <VoiceInteraction onDisconnect={handleDisconnect} />
        </LiveKitRoom>
      </div>
    );
  }

  // Initial connection screen
  return (
    <div className="App">
      <header className="App-header">
        <h1>🎙️ LiveKit + Pipecat Demo</h1>
        <p>A simple voice demo using LiveKit and Pipecat</p>
      </header>

      <div className="connect-container">
        <div className="welcome-card">
          <div className="status disconnected">
            Ready to start voice conversation
          </div>

          <button
            onClick={handleConnect}
            disabled={isConnecting}
            className="connect-button"
          >
            {isConnecting ? (
              <>
                <span className="spinner"></span>
                Connecting...
              </>
            ) : (
              <>
                🎤 Join Room and Enable Mic
              </>
            )}
          </button>

          <div className="feature-list">
            <h3>Voice Features:</h3>
            <ul>
              <li>🔄 <strong>Echo + Modify:</strong> Agent repeats your words with "...got it"</li>
              <li>⚡ <strong>Barge-in Support:</strong> Interrupt the agent anytime</li>
              <li>📊 <strong>Latency Tracking:</strong> Real-time performance metrics</li>
              <li>💬 <strong>Message Display:</strong> See conversation transcript</li>
            </ul>
          </div>

          <div className="warning">
            <strong>🛡️ Microphone Required:</strong> Allow microphone access when prompted.
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
