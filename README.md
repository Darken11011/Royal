# 🎙️ AI Voice Calling Assistant

A complete end-to-end AI voice calling assistant application powered by Google Gemini API and FastAPI. This application enables real-time voice conversations with an AI assistant through a modern web interface.

## ✨ Features

- **Real-time Voice Communication**: Bidirectional audio streaming using WebSockets
- **Google Gemini Integration**: Powered by Gemini 2.0 Flash for fast, intelligent responses
- **Adaptive AI Personas**: AI adapts to any role (medical care, real estate, personal assistant, etc.)
- **Speech-to-Text**: Convert voice input to text using Web Speech API
- **Self-Hosted TTS**: High-quality voice synthesis using gTTS (Google Text-to-Speech)
- **Modern Web Interface**: Beautiful, responsive UI with real-time status updates
- **Text Chat Fallback**: Type messages when voice input is not available
- **Low Latency**: Optimized for real-time conversation flow
- **Connection Management**: Automatic reconnection and error handling

## 🏗️ Architecture

### Backend
- **FastAPI**: High-performance async web framework
- **WebSocket**: Real-time bidirectional communication
- **Google Gemini API**: AI-powered conversational responses
- **Python 3.8+**: Modern Python with async/await support

### Frontend
- **Vanilla JavaScript**: No framework dependencies
- **Web Audio API**: Audio recording and playback
- **Web Speech API**: Text-to-speech synthesis
- **WebSocket Client**: Real-time server communication

## 📋 Prerequisites

- Python 3.8 or higher
- Modern web browser (Chrome, Firefox, Edge, Safari)
- Microphone access for voice input
- Internet connection for Gemini API

## 🚀 Installation

### 1. Clone or Download the Project

```bash
cd c:\Users\ahada\Desktop\Pro
```

### 2. Create Virtual Environment (Recommended)

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

**Note:** The application uses gTTS (Google Text-to-Speech) which is lightweight and requires no model downloads.

Alternatively, you can run the installation script:
```bash
# Windows
install_tts.bat

# Linux/Mac
pip install gTTS>=2.5.0
```

### 4. Configure Environment (Optional)

Copy the example environment file and customize if needed:

```bash
copy .env.example .env
```

Add your Gemini API key to the `.env` file:

```
GEMINI_API_KEY=your_actual_api_key_here
GEMINI_MODEL=gemini-2.0-flash-exp
HOST=0.0.0.0
PORT=8000
```

Get your API key from: https://makersuite.google.com/app/apikey

## 🎯 Running the Application

### Start the Server

```bash
python main.py
```

Or using uvicorn directly:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

The server will start on `http://localhost:8000`

### Access the Application

Open your web browser and navigate to:

```
http://localhost:8000/app
```

## 📖 How to Use

### Voice Conversation

1. **Connect**: Click the "📞 Connect" button to establish a WebSocket connection
2. **Grant Permissions**: Allow microphone access when prompted by your browser
3. **Start Recording**: Click "🎤 Start Recording" and speak your message
4. **Stop Recording**: Click "⏹️ Stop Recording" when you're done speaking
5. **Listen**: The AI assistant will respond with both text and voice

### Text Chat

1. **Connect**: Establish connection as above
2. **Type Message**: Enter your message in the text input field
3. **Send**: Click "Send" or press Enter
4. **Listen**: The AI will respond with text and voice

### Disconnect

Click "📴 Disconnect" to end the conversation and close the connection.

## 🔧 API Endpoints

### HTTP Endpoints

- `GET /` - Health check and service status
- `GET /health` - Detailed health information
- `GET /app` - Serve the web application

### WebSocket Endpoint

- `WS /ws/voice/{client_id}` - Real-time voice communication

#### WebSocket Message Types

**Client to Server:**

```json
{
  "type": "audio",
  "audio": "base64_encoded_audio_data",
  "format": "webm",
  "timestamp": 1234567890
}
```

```json
{
  "type": "text",
  "text": "Your message here",
  "timestamp": 1234567890
}
```

**Server to Client:**

```json
{
  "type": "response",
  "text": "AI response text",
  "timestamp": 1234567890
}
```

```json
{
  "type": "status",
  "status": "processing",
  "message": "Processing your voice..."
}
```

## 🎨 Project Structure

```
Pro/
├── main.py                      # FastAPI application and WebSocket handler
├── gemini_voice_handler.py      # Gemini API integration and voice processing
├── config.py                    # Configuration management
├── requirements.txt             # Python dependencies
├── .env.example                 # Environment variables template
├── README.md                    # This file
└── static/
    ├── index.html              # Web application UI
    └── app.js                  # Frontend JavaScript logic
```

## 🔑 Key Components

### Backend Components

1. **main.py**: FastAPI application with WebSocket endpoints
2. **gemini_voice_handler.py**: Handles Gemini API interactions
3. **ConnectionManager**: Manages WebSocket connections and sessions

### Frontend Components

1. **index.html**: Modern, responsive UI
2. **app.js**: WebSocket client, audio recording, and UI logic

## 🛠️ Configuration Options

### Gemini Model Selection

The application uses `gemini-2.0-flash-exp` by default, optimized for:
- Low latency responses
- Real-time conversation
- High-quality text generation

You can change the model in `config.py` or `.env`:

```python
GEMINI_MODEL=gemini-2.0-flash-exp
```

### Audio Settings

Configure audio processing in the frontend (`app.js`):

```javascript
audio: {
    echoCancellation: true,
    noiseSuppression: true,
    autoGainControl: true
}
```

## 🐛 Troubleshooting

### Microphone Not Working

- Ensure browser has microphone permissions
- Check if another application is using the microphone
- Try refreshing the page and granting permissions again

### Connection Failed

- Verify the server is running on port 8000
- Check firewall settings
- Ensure WebSocket connections are not blocked

### No Voice Response

- Check browser console for errors
- Verify Web Speech API is supported in your browser
- Try adjusting system volume

### API Errors

- Verify the Gemini API key is correct
- Check internet connection
- Review server logs for detailed error messages

## 📊 Performance Optimization

- **WebSocket**: Maintains persistent connection for low latency
- **Async Processing**: Non-blocking I/O for concurrent requests
- **Audio Compression**: WebM format for efficient transmission
- **Gemini 2.0 Flash**: Optimized model for fast responses

## 🔒 Security Considerations

- API key is embedded in code (for development only)
- In production, use environment variables and secure key management
- Implement authentication for WebSocket connections
- Add rate limiting to prevent abuse
- Use HTTPS/WSS in production

## 🚀 Production Deployment

### Using Docker (Recommended)

Create a `Dockerfile`:

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build and run:

```bash
docker build -t ai-voice-assistant .
docker run -p 8000:8000 ai-voice-assistant
```

### Using Cloud Platforms

- **Heroku**: Add `Procfile` with `web: uvicorn main:app --host 0.0.0.0 --port $PORT`
- **AWS**: Deploy using Elastic Beanstalk or ECS
- **Google Cloud**: Use Cloud Run or App Engine
- **Azure**: Deploy to App Service

## 📝 License

This project is provided as-is for educational and development purposes.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## 📧 Support

For issues or questions, please check the troubleshooting section or create an issue in the repository.

## 🎉 Acknowledgments

- Google Gemini API for AI capabilities
- FastAPI for the excellent web framework
- Web Audio API and Web Speech API for browser audio features

---

**Enjoy your AI Voice Assistant! 🎙️✨**

