/**
 * LiveKit + Pipecat Demo Client - Simple POC Version
 * Demonstrates LiveKit + Pipecat orchestration without external APIs
 */

// Configuration constants
const CONFIG = {
    LIVEKIT_URL: 'ws://localhost:7880',
    TOKEN_SERVER_URL: 'http://localhost:8080/token',
    ROOM_NAME: 'test-room',
    USER_IDENTITY: 'demo-user'
};

// State management (functional approach)
const createAppState = () => ({
    room: null,
    isConnected: false,
    isMuted: false,
    latencyMeasurements: [],
    speechStartTime: null
});

let appState = createAppState();

// DOM element getters (functional)
const getElements = () => ({
    status: document.getElementById('status'),
    joinBtn: document.getElementById('joinBtn'),
    leaveBtn: document.getElementById('leaveBtn'),
    muteBtn: document.getElementById('muteBtn'),
    remoteAudio: document.getElementById('remoteAudio'),
    logContainer: document.getElementById('logContainer'),
    avgLatency: document.getElementById('avgLatency'),
    lastLatency: document.getElementById('lastLatency'),
    measurementCount: document.getElementById('measurementCount')
});

/**
 * Pure function to calculate average latency
 */
const calculateAverageLatency = (measurements) => 
    measurements.length === 0 ? 0 : 
    Math.round(measurements.reduce((sum, val) => sum + val, 0) / measurements.length);

/**
 * Pure function to format timestamp
 */
const formatTimestamp = () => new Date().toISOString();

/**
 * Pure function to create log entry
 */
const createLogEntry = (message, type = 'info') => {
    const timestamp = new Date().toLocaleTimeString();
    return `[${timestamp}] ${message}`;
};

/**
 * Functional logger with side effects contained
 */
const logger = {
    log: (message, type = 'info') => {
        console.log(message);
        const elements = getElements();
        const logEntry = document.createElement('div');
        logEntry.className = `log-entry ${type}`;
        logEntry.textContent = createLogEntry(message, type);
        elements.logContainer.appendChild(logEntry);
        elements.logContainer.scrollTop = elements.logContainer.scrollHeight;
    },
    
    info: (message) => logger.log(`ℹ️ ${message}`, 'info'),
    success: (message) => logger.log(`✅ ${message}`, 'success'),
    warning: (message) => logger.log(`⚠️ ${message}`, 'warning'),
    error: (message) => logger.log(`❌ ${message}`, 'error')
};

/**
 * Pure function to update UI state
 */
const updateUIState = (isConnected, isMuted = false) => {
    const elements = getElements();
    
    // Update status
    elements.status.textContent = isConnected ? 'Connected to room' : 'Disconnected';
    elements.status.className = `status ${isConnected ? 'connected' : 'disconnected'}`;
    
    // Update buttons
    elements.joinBtn.disabled = isConnected;
    elements.leaveBtn.disabled = !isConnected;
    elements.muteBtn.disabled = !isConnected;
    elements.muteBtn.textContent = isMuted ? 'Unmute' : 'Mute';
};

/**
 * Pure function to update latency display
 */
const updateLatencyDisplay = (measurements) => {
    const elements = getElements();
    const avgLatency = calculateAverageLatency(measurements);
    const lastLatency = measurements.length > 0 ? measurements[measurements.length - 1] : 0;
    
    elements.avgLatency.textContent = `${avgLatency} ms`;
    elements.lastLatency.textContent = `${lastLatency} ms`;
    elements.measurementCount.textContent = measurements.length.toString();
};

/**
 * Functional token fetcher
 */
const fetchToken = async (roomName, identity) => {
    try {
        const response = await fetch(`${CONFIG.TOKEN_SERVER_URL}?room=${roomName}&identity=${identity}`);
        if (!response.ok) {
            throw new Error(`Token server error: ${response.status}`);
        }
        const data = await response.json();
        return data.token;
    } catch (error) {
        logger.warning('Token server not available, using dev token');
        // Fallback dev token (generated with devkey/secret for test-room)
        return 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3NTc5MTYwMDAsImlzcyI6ImRldmtleSIsIm5iZiI6MTY5NDk0MTQ0MCwic3ViIjoiZGVtby11c2VyIiwidmlkZW8iOnsicm9vbSI6InRlc3Qtcm9vbSIsInJvb21Kb2luIjp0cnVlLCJjYW5QdWJsaXNoIjp0cnVlLCJjYW5TdWJzY3JpYmUiOnRydWV9fQ.Aw1oOQJwGZN9wL0QErKM6HI-Cq-5Qf6F2bKGp9Z7XYs';
    }
};

/**
 * Functional track subscriber
 */
const handleTrackSubscribed = (track, publication, participant) => {
    logger.info(`Track subscribed: ${track.kind} from ${participant.identity}`);
    
    if (track.kind === 'audio' && participant.identity !== CONFIG.USER_IDENTITY) {
        const elements = getElements();
        track.attach(elements.remoteAudio);
        elements.remoteAudio.style.display = 'block';
        
        // Measure latency if we have a speech start time
        if (appState.speechStartTime) {
            const latency = Date.now() - appState.speechStartTime;
            appState.latencyMeasurements = [...appState.latencyMeasurements, latency];
            updateLatencyDisplay(appState.latencyMeasurements);
            logger.success(`Latency measured: ${latency}ms`);
            appState.speechStartTime = null;
        }
    }
};

/**
 * Functional local track handler
 */
const handleLocalTrackPublished = (publication, track) => {
    logger.info(`Local track published: ${track.kind}`);
    
    if (track.kind === 'audio') {
        // Add voice activity detection
        track.on('vadDetected', () => {
            appState.speechStartTime = Date.now();
            logger.info('🎤 Speech detected - measuring latency...');
        });
    }
};

/**
 * Functional room event handlers
 */
const setupRoomEventHandlers = (room) => {
    // Connection events
    room.on('connected', () => {
        logger.success('Connected to LiveKit room');
        appState.isConnected = true;
        updateUIState(true);
    });
    
    room.on('disconnected', () => {
        logger.info('Disconnected from room');
        appState.isConnected = false;
        updateUIState(false);
    });
    
    // Participant events
    room.on('participantConnected', (participant) => {
        logger.info(`Participant joined: ${participant.identity}`);
    });
    
    room.on('participantDisconnected', (participant) => {
        logger.info(`Participant left: ${participant.identity}`);
    });
    
    // Track events
    room.on('trackSubscribed', handleTrackSubscribed);
    room.on('localTrackPublished', handleLocalTrackPublished);
    
    // Error handling
    room.on('connectionFailed', (error) => {
        logger.error(`Connection failed: ${error.message}`);
    });
    
    room.on('reconnecting', () => {
        logger.warning('Reconnecting...');
        getElements().status.textContent = 'Reconnecting...';
        getElements().status.className = 'status connecting';
    });
    
    room.on('reconnected', () => {
        logger.success('Reconnected successfully');
        updateUIState(true);
    });
};

/**
 * Main connection function (functional orchestration)
 */
const connectToRoom = async () => {
    try {
        logger.info('Requesting microphone access...');
        
        // Create room instance
        const room = new LiveKit.Room({
            adaptiveStream: true,
            dynacast: true,
        });
        
        // Setup event handlers
        setupRoomEventHandlers(room);
        
        // Get token
        const token = await fetchToken(CONFIG.ROOM_NAME, CONFIG.USER_IDENTITY);
        logger.info('Token obtained, connecting to room...');
        
        // Connect to room
        await room.connect(CONFIG.LIVEKIT_URL, token);
        
        // Enable microphone
        const localTracks = await LiveKit.createLocalTracks({
            audio: {
                autoGainControl: true,
                echoCancellation: true,
                noiseSuppression: true,
            },
            video: false
        });
        
        // Publish tracks
        const publishPromises = localTracks.map(track => 
            room.localParticipant.publishTrack(track)
        );
        
        await Promise.all(publishPromises);
        logger.success('Microphone enabled and track published');
        
        // Update app state
        appState = { ...appState, room, isConnected: true };
        
    } catch (error) {
        logger.error(`Connection error: ${error.message}`);
        throw error;
    }
};

/**
 * Disconnect function (functional cleanup)
 */
const disconnectFromRoom = async () => {
    if (appState.room) {
        await appState.room.disconnect();
        appState = createAppState();
        getElements().remoteAudio.style.display = 'none';
        logger.info('Disconnected from room');
    }
};

/**
 * Toggle mute function (functional state update)
 */
const toggleMute = async () => {
    if (appState.room && appState.isConnected) {
        const audioTrack = appState.room.localParticipant.getTrackByKind('audio');
        if (audioTrack) {
            const newMutedState = !appState.isMuted;
            await audioTrack.setMuted(newMutedState);
            appState = { ...appState, isMuted: newMutedState };
            updateUIState(true, newMutedState);
            logger.info(`Microphone ${newMutedState ? 'muted' : 'unmuted'}`);
        }
    }
};

/**
 * Event listener setup (functional approach)
 */
const setupEventListeners = () => {
    const elements = getElements();
    
    // Debug: Test if button exists
    console.log('DEBUG: Join button found =', !!elements.joinBtn);
    
    elements.joinBtn.addEventListener('click', async () => {
        console.log('DEBUG: Join button clicked!');
        logger.info('🚀 Join button clicked - starting connection...');
        
        try {
            elements.joinBtn.disabled = true;
            elements.status.textContent = 'Connecting...';
            elements.status.className = 'status connecting';
            await connectToRoom();
        } catch (error) {
            logger.error(`Connection failed: ${error.message}`);
            elements.joinBtn.disabled = false;
            updateUIState(false);
        }
    });
    
    elements.leaveBtn.addEventListener('click', disconnectFromRoom);
    elements.muteBtn.addEventListener('click', toggleMute);
    
    // Cleanup on page unload
    window.addEventListener('beforeunload', disconnectFromRoom);
};

/**
 * Application initialization (functional entry point)
 */
const initializeApp = () => {
    logger.info('LiveKit + Pipecat Demo Client initialized');
    logger.info(`Room: ${CONFIG.ROOM_NAME}`);
    logger.info(`LiveKit URL: ${CONFIG.LIVEKIT_URL}`);
    
    updateUIState(false);
    setupEventListeners();
    
    // Debug: Log current state
    console.log('DEBUG: window.LiveKitReady =', window.LiveKitReady);
    console.log('DEBUG: typeof LiveKit =', typeof LiveKit);
    console.log('DEBUG: LiveKit object =', window.LiveKit);
    
    // Check if LiveKit is available
    if (!window.LiveKitReady || typeof LiveKit === 'undefined') {
        logger.error('LiveKit client library not loaded');
        const elements = getElements();
        elements.status.textContent = '❌ LiveKit library not loaded. Refresh page.';
        elements.status.className = 'status disconnected';
        return;
    }
    
    logger.success('LiveKit library loaded successfully!');
    logger.info('Ready to connect! Click "Join Room and Enable Mic" to start.');
};

// Wait for both DOM and LiveKit to be ready
function waitForLiveKitAndInit() {
    if (typeof window.LiveKitReady !== 'undefined' && window.LiveKitReady && typeof LiveKit !== 'undefined') {
        initializeApp();
    } else {
        // Check every 100ms for LiveKit to be ready
        setTimeout(waitForLiveKitAndInit, 100);
    }
}

// Initialize when DOM is ready and LiveKit is loaded
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', waitForLiveKitAndInit);
} else {
    waitForLiveKitAndInit();
}
