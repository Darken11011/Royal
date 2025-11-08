"""
Pyttsx3 Handler - Fully Offline Text-to-Speech
Provides voice synthesis without any internet connection required
"""

import logging
import io
import base64
from typing import Optional
import asyncio
import wave
import struct

logger = logging.getLogger(__name__)

class Pyttsx3Handler:
    """
    Handles text-to-speech conversion using pyttsx3
    Fully offline solution - no internet required
    """

    def __init__(self):
        """Initialize pyttsx3"""
        self.engine = None
        self.initialized = False
        self._initialize_tts()

    def _initialize_tts(self):
        """Initialize TTS (lazy loading)"""
        try:
            import pyttsx3
            self.engine = pyttsx3.init()

            # Configure voice settings
            voices = self.engine.getProperty('voices')
            # Try to use a female voice if available
            for voice in voices:
                if 'female' in voice.name.lower() or 'zira' in voice.name.lower() or 'aria' in voice.name.lower():
                    self.engine.setProperty('voice', voice.id)
                    break

            # Set speech rate (words per minute)
            self.engine.setProperty('rate', 175)  # Default is 200, slightly slower for clarity

            # Set volume (0.0 to 1.0)
            self.engine.setProperty('volume', 0.9)

            self.initialized = True
            logger.info("pyttsx3 initialized successfully (fully offline)")

        except ImportError:
            logger.error("pyttsx3 package not installed. Install with: pip install pyttsx3")
            self.initialized = False
        except Exception as e:
            logger.error(f"Error initializing pyttsx3: {str(e)}", exc_info=True)
            self.initialized = False
    
    async def synthesize(self, text: str, output_format: str = "wav") -> Optional[bytes]:
        """
        Convert text to speech

        Args:
            text: Text to convert to speech
            output_format: Audio format (wav)

        Returns:
            Audio bytes or None if failed
        """
        if not self.initialized:
            logger.error("TTS not initialized")
            return None

        try:
            # Run TTS in thread to avoid blocking
            audio_bytes = await asyncio.to_thread(self._generate_audio, text)
            return audio_bytes

        except Exception as e:
            logger.error(f"Error in speech synthesis: {str(e)}", exc_info=True)
            return None

    def _generate_audio(self, text: str) -> bytes:
        """Generate audio from text (blocking operation)"""
        import tempfile
        import os
        import time

        try:
            # Create a temporary file for audio output
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_path = temp_file.name

            try:
                # Generate speech to temporary file
                self.engine.save_to_file(text, temp_path)
                self.engine.runAndWait()

                # Wait a bit for file to be written
                time.sleep(0.1)

                # Check if file exists and has content
                max_retries = 10
                for i in range(max_retries):
                    if os.path.exists(temp_path) and os.path.getsize(temp_path) > 0:
                        break
                    time.sleep(0.1)

                # Read the audio file
                if os.path.exists(temp_path) and os.path.getsize(temp_path) > 0:
                    with open(temp_path, 'rb') as f:
                        audio_bytes = f.read()

                    logger.info(f"Generated audio: {len(audio_bytes)} bytes for text: {text[:50]}...")
                    return audio_bytes
                else:
                    logger.error(f"Audio file not generated or empty: {temp_path}")
                    return b""

            finally:
                # Clean up temporary file
                if os.path.exists(temp_path):
                    try:
                        time.sleep(0.1)  # Give time for file to be released
                        os.remove(temp_path)
                    except Exception as cleanup_error:
                        logger.warning(f"Could not cleanup temp file: {cleanup_error}")

        except Exception as e:
            logger.error(f"Error generating audio: {str(e)}", exc_info=True)
            return b""
    
    async def synthesize_base64(self, text: str) -> Optional[str]:
        """
        Convert text to speech and return as base64 string
        
        Args:
            text: Text to convert to speech
            
        Returns:
            Base64 encoded audio or None if failed
        """
        audio_bytes = await self.synthesize(text)
        if audio_bytes:
            return base64.b64encode(audio_bytes).decode('utf-8')
        return None


class FastTTSHandler:
    """
    Alternative: Faster TTS using Piper or similar
    Fallback if Coqui is too slow
    """
    
    def __init__(self):
        """Initialize Fast TTS"""
        self.initialized = False
        logger.info("Fast TTS handler initialized (placeholder)")
    
    async def synthesize(self, text: str) -> Optional[bytes]:
        """
        Convert text to speech using fast method
        
        Args:
            text: Text to convert to speech
            
        Returns:
            Audio bytes or None if failed
        """
        logger.warning("Fast TTS not implemented yet")
        return None


# Global TTS instance (singleton)
_tts_instance = None

def get_tts_handler() -> Pyttsx3Handler:
    """Get or create TTS handler instance"""
    global _tts_instance
    if _tts_instance is None:
        _tts_instance = Pyttsx3Handler()
    return _tts_instance

