"""
AI Voice Calling Assistant - FastAPI Backend
Real-time voice communication with Google Gemini API
"""

import os
import json
import asyncio
import base64
from typing import Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse, Response
import google.generativeai as genai
from google.generativeai.types import GenerationConfig
import logging
from dotenv import load_dotenv
from gemini_voice_handler import GeminiVoiceHandler, SpeechToTextHandler, TextToSpeechHandler
from tts_handler import get_tts_handler

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="AI Voice Calling Assistant",
    description="Real-time voice communication with Google Gemini API",
    version="1.0.0"
)

# CORS middleware for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Google Gemini API Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    logger.error("GEMINI_API_KEY environment variable is not set!")
    raise ValueError("GEMINI_API_KEY must be set in environment variables")

genai.configure(api_key=GEMINI_API_KEY)

# Use Gemini 2.0 Flash for real-time voice - optimized for low latency
MODEL_NAME = "gemini-2.0-flash-exp"

# Initialize TTS handler (singleton)
tts_handler = get_tts_handler()

# Active connections manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}
        self.voice_handlers: dict[str, GeminiVoiceHandler] = {}
        self.audio_buffers: dict[str, list] = {}  # Buffer for streaming audio chunks

    async def connect(self, client_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        # Initialize voice handler for this client
        self.voice_handlers[client_id] = GeminiVoiceHandler(
            api_key=GEMINI_API_KEY,
            model_name=MODEL_NAME
        )
        self.voice_handlers[client_id].start_session()
        self.audio_buffers[client_id] = []  # Initialize audio buffer
        logger.info(f"Client {client_id} connected")

    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
        if client_id in self.voice_handlers:
            del self.voice_handlers[client_id]
        if client_id in self.audio_buffers:
            del self.audio_buffers[client_id]
        logger.info(f"Client {client_id} disconnected")

    async def send_message(self, client_id: str, message: dict):
        if client_id in self.active_connections:
            websocket = self.active_connections[client_id]
            await websocket.send_json(message)

    def get_voice_handler(self, client_id: str) -> Optional[GeminiVoiceHandler]:
        return self.voice_handlers.get(client_id)

    def add_audio_chunk(self, client_id: str, audio_data: bytes):
        """Add audio chunk to buffer for streaming"""
        if client_id not in self.audio_buffers:
            self.audio_buffers[client_id] = []
        self.audio_buffers[client_id].append(audio_data)

    def get_buffered_audio(self, client_id: str) -> bytes:
        """Get all buffered audio and clear buffer"""
        if client_id in self.audio_buffers and self.audio_buffers[client_id]:
            audio_data = b''.join(self.audio_buffers[client_id])
            self.audio_buffers[client_id] = []
            return audio_data
        return b''

manager = ConnectionManager()

# Health check endpoint
@app.get("/")
async def root():
    return {"status": "online", "service": "AI Voice Calling Assistant"}

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "model": MODEL_NAME,
        "active_connections": len(manager.active_connections)
    }

# Serve static JavaScript file
@app.get("/app.js")
async def serve_js():
    try:
        with open("static/app.js", "r", encoding="utf-8") as f:
            return Response(content=f.read(), media_type="application/javascript")
    except FileNotFoundError:
        return Response(content="console.error('app.js not found');", media_type="application/javascript", status_code=404)

# Serve frontend
@app.get("/app", response_class=HTMLResponse)
async def serve_frontend():
    try:
        with open("static/index.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(
            content="<h1>Frontend not found. Please ensure static/index.html exists.</h1>",
            status_code=404
        )

# WebSocket endpoint for real-time voice communication
@app.websocket("/ws/voice/{client_id}")
async def voice_websocket(websocket: WebSocket, client_id: str):
    await manager.connect(client_id, websocket)

    try:
        # Send connection success message
        await manager.send_message(client_id, {
            "type": "connection",
            "status": "connected",
            "message": "Voice assistant ready"
        })

        logger.info(f"Voice session initialized for client {client_id}")

        try:
            while True:
                # Receive message from client
                data = await websocket.receive_json()
                message_type = data.get("type")

                if message_type == "audio_chunk":
                    # Handle streaming audio chunk (real-time)
                    await handle_audio_chunk(client_id, data)

                elif message_type == "audio_complete":
                    # Handle complete audio for processing
                    await handle_audio_complete(client_id, data)

                elif message_type == "audio":
                    # Handle audio data (legacy support)
                    await handle_audio_message(client_id, data)

                elif message_type == "text":
                    # Handle text message (for testing or fallback)
                    await handle_text_message(client_id, data)

                elif message_type == "ping":
                    # Respond to ping for connection keep-alive
                    await manager.send_message(client_id, {
                        "type": "pong",
                        "timestamp": data.get("timestamp")
                    })

                elif message_type == "end_call":
                    # End the call gracefully
                    logger.info(f"Call ended by client {client_id}")
                    break

        except WebSocketDisconnect:
            logger.info(f"WebSocket disconnected for client {client_id}")
        except Exception as e:
            logger.error(f"Error in WebSocket communication: {str(e)}", exc_info=True)
            await manager.send_message(client_id, {
                "type": "error",
                "message": f"Communication error: {str(e)}"
            })

    except Exception as e:
        logger.error(f"Error initializing voice session: {str(e)}", exc_info=True)
        await manager.send_message(client_id, {
            "type": "error",
            "message": f"Failed to initialize AI assistant: {str(e)}"
        })

    finally:
        manager.disconnect(client_id)

async def handle_audio_chunk(client_id: str, data: dict):
    """Handle streaming audio chunk (real-time)"""
    try:
        audio_data = data.get("audio")  # Base64 encoded audio chunk

        if not audio_data:
            return

        # Decode and buffer the audio chunk
        audio_bytes = base64.b64decode(audio_data)
        manager.add_audio_chunk(client_id, audio_bytes)

        logger.debug(f"Buffered audio chunk for client {client_id} ({len(audio_bytes)} bytes)")

    except Exception as e:
        logger.error(f"Error handling audio chunk: {str(e)}", exc_info=True)

async def handle_audio_complete(client_id: str, data: dict):
    """Handle complete audio for processing"""
    try:
        # Get all buffered audio
        buffered_audio = manager.get_buffered_audio(client_id)

        # Also get the final audio from the message
        audio_data = data.get("audio")
        audio_format = data.get("format", "webm")

        if audio_data:
            final_audio = base64.b64decode(audio_data)
            # Combine buffered audio with final audio
            complete_audio = buffered_audio + final_audio if buffered_audio else final_audio
        else:
            complete_audio = buffered_audio

        if not complete_audio or len(complete_audio) < 100:
            logger.warning(f"No sufficient audio data for client {client_id}")
            return

        # Get voice handler for this client
        voice_handler = manager.get_voice_handler(client_id)
        if not voice_handler:
            logger.error(f"No voice handler found for client {client_id}")
            return

        # NOTE: Audio processing is handled by frontend Web Speech API
        # Backend just logs that audio was received
        # The frontend will send the transcribed text via 'text' message type
        logger.info(f"Received complete audio for client {client_id} ({len(complete_audio)} bytes)")

        # Don't send any response here - wait for the transcribed text from frontend

    except Exception as e:
        logger.error(f"Error handling complete audio: {str(e)}", exc_info=True)
        await manager.send_message(client_id, {
            "type": "error",
            "message": f"Audio processing error: {str(e)}"
        })

async def handle_audio_message(client_id: str, data: dict):
    """Handle incoming audio data and process with Gemini"""
    try:
        audio_data = data.get("audio")  # Base64 encoded audio
        audio_format = data.get("format", "webm")

        if not audio_data:
            logger.warning(f"No audio data received from client {client_id}")
            return

        # Decode base64 audio
        audio_bytes = base64.b64decode(audio_data)

        # NOTE: Audio processing is handled by frontend Web Speech API
        # Backend just logs that audio was received
        # The frontend will send the transcribed text via 'text' message type
        logger.info(f"Received audio for client {client_id} ({len(audio_bytes)} bytes)")

        # Don't send any response here - wait for the transcribed text from frontend

    except Exception as e:
        logger.error(f"Error handling audio message: {str(e)}", exc_info=True)
        await manager.send_message(client_id, {
            "type": "error",
            "message": f"Audio processing error: {str(e)}"
        })

async def handle_text_message(client_id: str, data: dict):
    """Handle text message and generate response"""
    try:
        text = data.get("text", "").strip()

        if not text:
            return

        logger.info(f"Received text from client {client_id}: {text}")

        # Get voice handler for this client
        voice_handler = manager.get_voice_handler(client_id)
        if not voice_handler:
            logger.error(f"No voice handler found for client {client_id}")
            return

        # Send processing status
        await manager.send_message(client_id, {
            "type": "processing",
            "message": "Thinking..."
        })

        # Generate response using Gemini
        response_text = await voice_handler.process_text(text)

        # Send response back to client (browser will handle TTS)
        response_message = {
            "type": "response",
            "text": response_text,
            "timestamp": data.get("timestamp")
        }

        await manager.send_message(client_id, response_message)

        logger.info(f"Sent response to client {client_id}: {response_text[:100]}...")

    except Exception as e:
        logger.error(f"Error handling text message: {str(e)}", exc_info=True)
        await manager.send_message(client_id, {
            "type": "error",
            "message": f"Text processing error: {str(e)}"
        })

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")

