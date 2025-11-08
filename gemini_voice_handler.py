"""
Gemini Voice Handler - Advanced voice processing with Google Gemini API
Handles real-time voice interaction with speech-to-text and text-to-speech
"""

import asyncio
import base64
import logging
from typing import Optional, Callable
import google.generativeai as genai
from google.generativeai.types import GenerationConfig
import io

logger = logging.getLogger(__name__)

class GeminiVoiceHandler:
    """
    Handles voice interactions with Google Gemini API
    Provides speech-to-text, conversational AI, and text-to-speech capabilities
    """
    
    def __init__(self, api_key: str, model_name: str = "gemini-2.0-flash-exp"):
        """
        Initialize the Gemini Voice Handler
        
        Args:
            api_key: Google Gemini API key
            model_name: Model to use for generation
        """
        self.api_key = api_key
        self.model_name = model_name
        genai.configure(api_key=api_key)
        
        # Initialize model with optimized settings for conversation
        self.model = None  # Will be created after persona is set
        self.base_generation_config = GenerationConfig(
            temperature=0.9,
            top_p=0.95,
            top_k=40,
            max_output_tokens=2048,
        )

        self.chat = None
        self.conversation_history = []
        self.message_count = 0  # Track messages for greeting logic
        self.persona = None  # User-defined persona
        self.persona_set = False  # Track if persona has been configured
        
    def start_session(self):
        """Start a new conversation session"""
        self.conversation_history = []
        self.message_count = 0
        self.persona = None
        self.persona_set = False
        logger.info("Started new Gemini conversation session - waiting for persona setup")

    def set_persona(self, persona_description: str):
        """Set the AI persona based on user input"""
        self.persona = persona_description
        self.persona_set = True

        # Create system instruction based on persona
        system_instruction = f"""You are a {persona_description}. Fully embody this role in every response.

CRITICAL RULES:
1. Stay in character at ALL times - be the {persona_description}
2. Use appropriate terminology, tone, and expertise for this role
3. Keep responses concise (2-4 sentences) but professional
4. Be natural and conversational, not robotic
5. Never break character or mention you're an AI
6. Use industry-specific language and knowledge
7. Be helpful, professional, and engaging in your role

CONVERSATION STYLE:
- Respond directly without repeating greetings after the first message
- Vary your response style naturally
- Only occasionally add follow-up questions (20% of time)
- Use natural acknowledgments appropriate to your role
- Remember context from previous messages

Fully commit to being a {persona_description} and provide authentic, role-appropriate responses."""

        # Create the model with the persona
        self.model = genai.GenerativeModel(
            model_name=self.model_name,
            generation_config=self.base_generation_config,
            system_instruction=system_instruction
        )

        # Start chat with the model
        self.chat = self.model.start_chat(history=[])

        logger.info(f"Persona set to: {persona_description}")
        
    async def process_text(self, text: str) -> str:
        """
        Process text input and generate response

        Args:
            text: User's text input

        Returns:
            AI-generated response text
        """
        try:
            # Increment message count
            self.message_count += 1

            # First message - ask for persona
            if self.message_count == 1 and not self.persona_set:
                return "Hi! I'm your AI assistant. How would you like me to help you today? Tell me what role I should take - for example, I can be a medical customer care representative, real estate agent, personal assistant, or anything else you need!"

            # Second message - set persona based on user input
            if self.message_count == 2 and not self.persona_set:
                self.set_persona(text)
                return f"Perfect! I'm now your {text}. How can I assist you?"

            # Regular conversation
            if not self.chat:
                return "Please tell me what role you'd like me to take first."

            # Add to conversation history
            self.conversation_history.append({"role": "user", "content": text})

            # Generate response
            response = await asyncio.to_thread(
                self.chat.send_message,
                text
            )

            response_text = response.text

            # Add response to history
            self.conversation_history.append({"role": "assistant", "content": response_text})

            logger.info(f"Generated response: {response_text[:100]}...")
            return response_text

        except Exception as e:
            logger.error(f"Error processing text: {str(e)}", exc_info=True)
            return "I apologize, but I encountered an error processing your message. Could you please try again?"
    
    async def process_audio_to_text(self, audio_bytes: bytes, audio_format: str = "webm") -> str:
        """
        Convert audio to text using speech recognition
        
        Args:
            audio_bytes: Raw audio data
            audio_format: Audio format (webm, wav, mp3, etc.)
            
        Returns:
            Transcribed text
        """
        try:
            # For Gemini 2.0, we can use multimodal capabilities
            # Upload audio and get transcription
            
            # Create a file-like object
            audio_file = io.BytesIO(audio_bytes)
            audio_file.name = f"audio.{audio_format}"
            
            # Use Gemini to transcribe
            # Note: This is a simplified approach
            # In production, you might want to use Google Speech-to-Text API for better accuracy
            
            if not self.chat:
                self.start_session()
            
            # For now, we'll use a placeholder approach
            # In a full implementation with Gemini 2.0 Live API, audio would be processed directly
            logger.info(f"Processing audio ({len(audio_bytes)} bytes, format: {audio_format})")
            
            # Placeholder: Return a message indicating audio was received
            # In production, integrate with Google Speech-to-Text API or Gemini's audio capabilities
            return "[Audio received - transcription would appear here]"
            
        except Exception as e:
            logger.error(f"Error processing audio to text: {str(e)}", exc_info=True)
            return ""
    
    async def process_audio_conversation(
        self,
        audio_bytes: bytes,
        audio_format: str = "webm"
    ) -> str:
        """
        Process audio input and generate conversational response

        Args:
            audio_bytes: Raw audio data
            audio_format: Audio format

        Returns:
            AI-generated response text
        """
        try:
            # Note: Since we're using standard Gemini API without Live API,
            # we don't have built-in speech-to-text. In a production environment,
            # you would integrate Google Speech-to-Text API or similar service.

            # For demonstration, we'll provide intelligent fallback responses
            # that acknowledge the audio and provide helpful information

            if not self.chat:
                self.start_session()

            # Generate a contextual response
            # In production, replace this with actual STT + conversation
            responses = [
                "I'm listening! I can hear you speaking. In a full production setup, I would transcribe your speech and respond accordingly. For now, I'm here to help - what would you like to know?",
                "I received your audio message! While I'm currently set up for text responses, I'm ready to assist you. What can I help you with today?",
                "Hello! I can hear you. I'm an AI assistant powered by Google Gemini. How can I assist you today?",
                "I'm here and listening! Feel free to ask me anything - I can help with information, answer questions, or just have a conversation.",
                "Great to hear from you! I'm ready to help. What's on your mind?"
            ]

            # Use a simple counter to cycle through responses
            import random
            response = random.choice(responses)

            logger.info(f"Generated audio response: {response[:100]}...")
            return response

        except Exception as e:
            logger.error(f"Error in audio conversation: {str(e)}", exc_info=True)
            return "I apologize, but I had trouble processing your voice message. Please try again."
    
    def get_conversation_history(self) -> list:
        """Get the conversation history"""
        return self.conversation_history
    
    def clear_history(self):
        """Clear conversation history and start fresh"""
        self.conversation_history = []
        self.start_session()
        logger.info("Cleared conversation history")


class SpeechToTextHandler:
    """
    Handles speech-to-text conversion
    Can be extended to use Google Speech-to-Text API or other services
    """
    
    def __init__(self):
        self.supported_formats = ["webm", "wav", "mp3", "ogg", "flac"]
    
    async def transcribe(self, audio_bytes: bytes, audio_format: str = "webm") -> str:
        """
        Transcribe audio to text
        
        Args:
            audio_bytes: Raw audio data
            audio_format: Audio format
            
        Returns:
            Transcribed text
        """
        try:
            # Placeholder for actual speech-to-text implementation
            # In production, integrate with:
            # - Google Cloud Speech-to-Text API
            # - OpenAI Whisper
            # - Other STT services
            
            logger.info(f"Transcribing audio ({len(audio_bytes)} bytes, format: {audio_format})")
            
            # For now, return a placeholder
            return "[Transcription placeholder - integrate STT service here]"
            
        except Exception as e:
            logger.error(f"Error in transcription: {str(e)}", exc_info=True)
            return ""


class TextToSpeechHandler:
    """
    Handles text-to-speech conversion
    Can be extended to use Google Text-to-Speech API or other services
    """
    
    def __init__(self):
        self.voice_settings = {
            "language": "en-US",
            "voice_name": "en-US-Neural2-F",  # Female voice
            "speaking_rate": 1.0,
            "pitch": 0.0
        }
    
    async def synthesize(self, text: str) -> bytes:
        """
        Convert text to speech
        
        Args:
            text: Text to convert to speech
            
        Returns:
            Audio bytes
        """
        try:
            # Placeholder for actual text-to-speech implementation
            # In production, integrate with:
            # - Google Cloud Text-to-Speech API
            # - ElevenLabs
            # - Other TTS services
            
            logger.info(f"Synthesizing speech for text: {text[:50]}...")
            
            # For now, return empty bytes
            # The frontend will use Web Speech API as fallback
            return b""
            
        except Exception as e:
            logger.error(f"Error in speech synthesis: {str(e)}", exc_info=True)
            return b""
    
    def set_voice(self, voice_name: str):
        """Set the voice to use for synthesis"""
        self.voice_settings["voice_name"] = voice_name
    
    def set_speaking_rate(self, rate: float):
        """Set the speaking rate (0.25 to 4.0)"""
        self.voice_settings["speaking_rate"] = max(0.25, min(4.0, rate))

