// Real-Time Voice Assistant - Client Side
let ws = null;
let mediaRecorder = null;
let audioStream = null;
let isRecording = false;
let audioContext = null;
let analyser = null;
let silenceTimeout = null;
let audioChunks = [];
let isSpeaking = false;
let recognition = null;
let currentTranscript = '';

const SILENCE_THRESHOLD = 0.01;
const SILENCE_DURATION = 1500; // 1.5 seconds of silence triggers processing
const CHUNK_INTERVAL = 250; // Send audio chunks every 250ms

// Initialize Web Speech API for speech recognition
if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    recognition = new SpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = 'en-US';

    recognition.onresult = (event) => {
        let interimTranscript = '';
        let finalTranscript = '';

        for (let i = event.resultIndex; i < event.results.length; i++) {
            const transcript = event.results[i][0].transcript;
            if (event.results[i].isFinal) {
                finalTranscript += transcript + ' ';
            } else {
                interimTranscript += transcript;
            }
        }

        if (finalTranscript) {
            currentTranscript = finalTranscript.trim();
            console.log('Final transcript:', currentTranscript);
            // Send the transcribed text to the AI
            sendTranscriptToAI(currentTranscript);
            currentTranscript = '';
        }
    };

    recognition.onerror = (event) => {
        console.error('Speech recognition error:', event.error);
        if (event.error === 'no-speech') {
            // Ignore no-speech errors
            return;
        }
    };

    recognition.onend = () => {
        // Restart if still recording
        if (isRecording && !isSpeaking) {
            try {
                recognition.start();
            } catch (e) {
                // Already started
            }
        }
    };
}

// DOM Elements
const micButton = document.getElementById('micButton');
const micLabel = document.getElementById('micLabel');
const status = document.getElementById('status');
const conversation = document.getElementById('conversation');
const waveIndicator = document.getElementById('waveIndicator');

// Generate unique client ID
const clientId = 'client_' + Math.random().toString(36).substr(2, 9);

// Auto-connect on page load
window.addEventListener('load', () => {
    setTimeout(connectWebSocket, 500);
});

function connectWebSocket() {
    updateStatus('connecting', 'Connecting...');

    // Dynamically determine WebSocket URL based on current location
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host; // includes hostname and port
    const wsUrl = `${protocol}//${host}/ws/voice/${clientId}`;

    console.log('Connecting to WebSocket:', wsUrl);
    ws = new WebSocket(wsUrl);
    
    ws.onopen = () => {
        updateStatus('ready', 'Ready - Tap to Talk');
        addMessage('system', 'Connected! Tap the microphone to start speaking.');
        micButton.disabled = false;
    };
    
    ws.onmessage = async (event) => {
        const data = JSON.parse(event.data);
        
        if (data.type === 'connection') {
            console.log('Connection established:', data.message);
        } else if (data.type === 'transcription') {
            addMessage('user', data.text);
        } else if (data.type === 'response') {
            addMessage('assistant', data.text);

            // Always speak the response, but handle recording state
            if (isRecording) {
                console.log('Response received while recording - pausing to speak');
                // Temporarily pause speech recognition to avoid feedback
                if (recognition) {
                    try {
                        recognition.stop();
                    } catch (e) {
                        // Already stopped
                    }
                }

                // Speak the response
                updateStatus('speaking', 'AI Speaking...');
                isSpeaking = true;

                if (data.audio) {
                    const audioFormat = data.audio_format || 'wav';
                    await playAudioResponse(data.audio, audioFormat);
                } else {
                    await speakTextAsync(data.text);
                }

                isSpeaking = false;

                // Resume speech recognition if still recording
                if (isRecording && recognition) {
                    try {
                        recognition.start();
                        updateStatus('listening', 'Listening...');
                    } catch (e) {
                        console.log('Recognition already started');
                    }
                } else {
                    updateStatus('listening', 'Listening...');
                }
            } else {
                // If microphone is off, speak the response normally
                updateStatus('speaking', 'AI Speaking...');
                isSpeaking = true;

                // Speak the response
                if (data.audio) {
                    const audioFormat = data.audio_format || 'wav';
                    await playAudioResponse(data.audio, audioFormat);
                } else {
                    await speakTextAsync(data.text);
                }

                isSpeaking = false;
                updateStatus('ready', 'Ready - Tap to Talk');
            }
        } else if (data.type === 'error') {
            updateStatus('error', 'Error: ' + data.message);
            addMessage('system', 'Error: ' + data.message);
        } else if (data.type === 'processing') {
            updateStatus('processing', 'Processing...');
        }
    };
    
    ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        updateStatus('error', 'Connection Error');
        addMessage('system', 'Connection error. Please refresh the page.');
    };
    
    ws.onclose = () => {
        updateStatus('error', 'Disconnected');
        addMessage('system', 'Connection closed. Please refresh the page.');
        micButton.disabled = true;
    };
}

async function toggleMicrophone() {
    if (isRecording) {
        stopRecording();
    } else {
        await startRecording();
    }
}

async function startRecording() {
    try {
        // Request microphone access
        audioStream = await navigator.mediaDevices.getUserMedia({
            audio: {
                echoCancellation: true,
                noiseSuppression: true,
                autoGainControl: true,
                sampleRate: 16000
            }
        });

        // Setup audio context for VAD
        audioContext = new (window.AudioContext || window.webkitAudioContext)({ sampleRate: 16000 });
        const source = audioContext.createMediaStreamSource(audioStream);
        analyser = audioContext.createAnalyser();
        analyser.fftSize = 2048;
        source.connect(analyser);

        // Setup MediaRecorder for continuous streaming
        const options = { mimeType: 'audio/webm;codecs=opus' };
        mediaRecorder = new MediaRecorder(audioStream, options);
        audioChunks = [];

        mediaRecorder.ondataavailable = async (event) => {
            if (event.data.size > 0 && ws && ws.readyState === WebSocket.OPEN) {
                audioChunks.push(event.data);

                // Send audio chunk immediately for real-time streaming
                const base64Audio = await blobToBase64(event.data);
                ws.send(JSON.stringify({
                    type: 'audio_chunk',
                    audio: base64Audio,
                    format: 'webm',
                    timestamp: Date.now()
                }));
            }
        };

        mediaRecorder.onstop = async () => {
            // Send final accumulated audio for processing
            if (audioChunks.length > 0) {
                const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
                const base64Audio = await blobToBase64(audioBlob);

                ws.send(JSON.stringify({
                    type: 'audio_complete',
                    audio: base64Audio,
                    format: 'webm',
                    timestamp: Date.now()
                }));

                audioChunks = [];
            }
        };

        // Start recording with time slices for continuous streaming
        mediaRecorder.start(CHUNK_INTERVAL);
        isRecording = true;

        // Start Web Speech API recognition
        if (recognition) {
            try {
                recognition.start();
                console.log('Speech recognition started');
            } catch (e) {
                console.log('Speech recognition already started');
            }
        }

        // Update UI
        micButton.classList.remove('inactive');
        micButton.classList.add('active');
        micLabel.textContent = 'Listening...';
        micLabel.classList.add('active');
        waveIndicator.classList.add('active');
        updateStatus('listening', 'Listening...');

        // Start Voice Activity Detection
        startVAD();

    } catch (error) {
        console.error('Error accessing microphone:', error);
        updateStatus('error', 'Microphone Error');
        addMessage('system', 'Could not access microphone. Please check permissions.');
    }
}

function stopRecording() {
    if (mediaRecorder && mediaRecorder.state !== 'inactive') {
        mediaRecorder.stop();
    }

    if (audioStream) {
        audioStream.getTracks().forEach(track => track.stop());
    }

    if (audioContext) {
        audioContext.close();
    }

    if (silenceTimeout) {
        clearTimeout(silenceTimeout);
    }

    // Stop speech recognition
    if (recognition) {
        try {
            recognition.stop();
            console.log('Speech recognition stopped');
        } catch (e) {
            // Already stopped
        }
    }

    // Stop any ongoing speech synthesis
    if ('speechSynthesis' in window) {
        window.speechSynthesis.cancel();
        console.log('Speech synthesis cancelled');
    }

    isRecording = false;
    isSpeaking = false; // Reset speaking flag

    // Update UI
    micButton.classList.remove('active');
    micButton.classList.add('inactive');
    micLabel.textContent = 'Tap to Talk';
    micLabel.classList.remove('active');
    waveIndicator.classList.remove('active');
    updateStatus('ready', 'Ready - Tap to Talk');
}

async function sendTranscriptToAI(transcript) {
    if (!transcript || !ws || ws.readyState !== WebSocket.OPEN) {
        return;
    }

    console.log('Sending transcript to AI:', transcript);

    // Display user's message
    addMessage('user', transcript);

    // Update status
    updateStatus('processing', 'Processing...');

    // Send to backend
    ws.send(JSON.stringify({
        type: 'text',
        text: transcript,
        timestamp: Date.now()
    }));
}

function startVAD() {
    const bufferLength = analyser.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);
    let silenceStart = null;
    let hasSpoken = false;
    let isProcessing = false;  // Prevent multiple simultaneous processing

    function checkAudioLevel() {
        if (!isRecording || isProcessing) return;

        analyser.getByteTimeDomainData(dataArray);

        // Calculate RMS (Root Mean Square) for audio level
        let sum = 0;
        for (let i = 0; i < bufferLength; i++) {
            const normalized = (dataArray[i] - 128) / 128;
            sum += normalized * normalized;
        }
        const rms = Math.sqrt(sum / bufferLength);

        // Check if user is speaking
        if (rms >= SILENCE_THRESHOLD) {
            hasSpoken = true;
            silenceStart = null;
        }

        // Check if audio level is below silence threshold AFTER user has spoken
        if (rms < SILENCE_THRESHOLD && hasSpoken && !isProcessing) {
            if (silenceStart === null) {
                silenceStart = Date.now();
            } else if (Date.now() - silenceStart > SILENCE_DURATION) {
                // Silence detected for long enough - process audio
                console.log('Silence detected - processing audio');
                if (audioChunks.length > 0) {
                    isProcessing = true;
                    processAccumulatedAudio().finally(() => {
                        isProcessing = false;
                        hasSpoken = false;
                    });
                }
                silenceStart = null;
            }
        }

        // Continue checking
        if (isRecording) {
            requestAnimationFrame(checkAudioLevel);
        }
    }

    checkAudioLevel();
}

async function processAccumulatedAudio() {
    if (audioChunks.length === 0) return;

    updateStatus('processing', 'Processing...');

    // Stop the media recorder temporarily to get the accumulated audio
    if (mediaRecorder && mediaRecorder.state === 'recording') {
        mediaRecorder.stop();

        // Wait a bit for the stop event to process
        await new Promise(resolve => setTimeout(resolve, 100));

        // Restart recording if still in recording mode
        if (isRecording && audioStream) {
            audioChunks = [];
            mediaRecorder.start(CHUNK_INTERVAL);
            updateStatus('listening', 'Listening...');
        }
    }
}

async function blobToBase64(blob) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onloadend = () => {
            const base64 = reader.result.split(',')[1];
            resolve(base64);
        };
        reader.onerror = reject;
        reader.readAsDataURL(blob);
    });
}

async function playAudioResponse(base64Audio, audioFormat = 'wav') {
    return new Promise((resolve, reject) => {
        try {
            const audioData = atob(base64Audio);
            const arrayBuffer = new ArrayBuffer(audioData.length);
            const view = new Uint8Array(arrayBuffer);
            for (let i = 0; i < audioData.length; i++) {
                view[i] = audioData.charCodeAt(i);
            }

            // Determine MIME type based on format
            const mimeType = audioFormat === 'mp3' ? 'audio/mpeg' : 'audio/wav';
            const blob = new Blob([arrayBuffer], { type: mimeType });
            const url = URL.createObjectURL(blob);
            const audio = new Audio(url);

            audio.onended = () => {
                URL.revokeObjectURL(url);
                resolve();
            };

            audio.onerror = (error) => {
                console.error('Audio playback error:', error);
                URL.revokeObjectURL(url);
                reject(error);
            };

            audio.play().catch(err => {
                console.error('Error starting audio playback:', err);
                URL.revokeObjectURL(url);
                reject(err);
            });
        } catch (error) {
            console.error('Error playing audio:', error);
            reject(error);
        }
    });
}

function speakTextAsync(text) {
    return new Promise((resolve, reject) => {
        if (!('speechSynthesis' in window)) {
            resolve();
            return;
        }

        // Cancel any ongoing speech
        window.speechSynthesis.cancel();

        const utterance = new SpeechSynthesisUtterance(text);

        // Get available voices and select a natural-sounding one
        const voices = window.speechSynthesis.getVoices();

        // Prefer natural-sounding voices (Google, Microsoft Neural, etc.)
        const preferredVoices = [
            'Google US English',
            'Microsoft Aria Online (Natural) - English (United States)',
            'Microsoft Jenny Online (Natural) - English (United States)',
            'Samantha',  // macOS
            'Google UK English Female',
            'Microsoft Zira Desktop - English (United States)'
        ];

        // Find the best available voice
        let selectedVoice = null;
        for (const preferred of preferredVoices) {
            selectedVoice = voices.find(voice => voice.name === preferred);
            if (selectedVoice) break;
        }

        // Fallback to any English female voice
        if (!selectedVoice) {
            selectedVoice = voices.find(voice =>
                voice.lang.startsWith('en') && voice.name.toLowerCase().includes('female')
            );
        }

        // Final fallback to any English voice
        if (!selectedVoice) {
            selectedVoice = voices.find(voice => voice.lang.startsWith('en'));
        }

        if (selectedVoice) {
            utterance.voice = selectedVoice;
            console.log('Using voice:', selectedVoice.name);
        }

        // Natural speech settings
        utterance.rate = 1.1;      // Slightly faster for natural conversation
        utterance.pitch = 1.0;     // Normal pitch
        utterance.volume = 0.9;    // Slightly softer for comfort

        utterance.onend = () => {
            resolve();
        };

        utterance.onerror = (event) => {
            // Only log non-interrupted errors
            if (event.error !== 'interrupted') {
                console.error('Speech synthesis error:', event);
            }
            resolve();  // Resolve anyway to continue flow
        };

        window.speechSynthesis.speak(utterance);
    });
}

function speakText(text) {
    speakTextAsync(text);
}

// Load voices when they become available
if ('speechSynthesis' in window) {
    // Chrome loads voices asynchronously
    window.speechSynthesis.onvoiceschanged = () => {
        const voices = window.speechSynthesis.getVoices();
        console.log('Available voices:', voices.map(v => v.name));
    };

    // Trigger voice loading
    window.speechSynthesis.getVoices();
}

function updateStatus(state, text) {
    status.className = 'status ' + state;
    status.textContent = text;
}

function addMessage(type, text) {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message ' + type;
    messageDiv.textContent = text;
    conversation.appendChild(messageDiv);
    conversation.scrollTop = conversation.scrollHeight;
}

