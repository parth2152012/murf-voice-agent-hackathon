# 🎤 Murf AI Voice Agent - Techfest IIT Bombay Hackathon

> Built using Murf Falcon – the consistently fastest TTS API

A modern, interactive voice agent featuring a beautiful React frontend and powerful Python backend. Demonstrates the seamless integration of Murf Falcon TTS, Deepgram ASR, and Google Gemini AI for natural, intelligent conversations.

## 🏆 Hackathon Details

- **Event**: Techfest 2025-26 - Murf AI Voice Agent Hackathon
- **Institution**: IIT Bombay
- **Team ID**: Murf-250280
- **Category**: Voice-First AI Applications

## ✨ Features

- 🎨 **Modern React Frontend** with real-time chat interface
- 🎙️ **Real-time Speech Recognition** using Deepgram ASR
- 🗣️ **Natural Speech Synthesis** powered by Murf Falcon TTS API
- 🤖 **Intelligent Conversations** with Google Gemini AI
- 🔄 **Fallback Logic** for standalone operation without LLM
- 🔒 **Secure API Key Management** via environment variables
- ⚡ **WebSocket Communication** for real-time updates
- 📱 **Responsive Design** works on desktop and mobile
- 🎵 **Audio Playback** with automatic speech synthesis
- 📝 **Conversation History** with persistent sessions
- 🎯 **Multiple Input Modes** (text and voice)

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- Node.js 16+ and npm (for React frontend)
- Microphone and speakers (optional, text mode available)
- API keys for:
  - Murf AI (required for voice responses)
  - Deepgram (optional, for voice input)
  - Google Gemini (optional, for AI conversations)

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/parth2152012/murf-voice-agent-hackathon.git
cd murf-voice-agent-hackathon
```

2. **Backend Setup**
```bash
# Install Python dependencies
pip install -r requirements.txt
```

3. **Frontend Setup**
```bash
# Install React dependencies
cd frontend
npm install
cd ..
```

4. **Environment Configuration**
```bash
cp .env.example .env
```

Edit `.env` and add your API keys:
```env
MURF_API_KEY=your_murf_api_key_here
DEEPGRAM_API_KEY=your_deepgram_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here
```

### Getting API Keys

#### Murf AI API Key

1. Sign up at murf.ai
2. Navigate to API settings
3. Generate your Falcon TTS API key
4. New accounts get 1,000,000 free TTS characters

#### Deepgram API Key

1. Sign up at deepgram.com
2. Get free credits for the hackathon
3. Create an API key from the console

#### Google Gemini API Key

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with your Google account
3. Create a new API key
4. Copy the API key (free tier available with generous limits)
5. Gemini provides intelligent conversational AI responses

### Running the Application

#### Option 1: Web Interface (Recommended)
```bash
# Terminal 1: Start the Flask backend
python app.py

# Terminal 2: Start the React frontend
cd frontend
npm start
```

Then open http://localhost:3000 in your browser for the modern chat interface!

#### Option 2: Command Line Interface
```bash
python voice_agent.py
```

**Web Interface Features:**
- Modern chat UI with real-time messaging
- Text input with voice responses
- Connection status indicators
- Responsive design for mobile/desktop
- Auto-playing audio responses

**Command Line Features:**
- Voice input/output mode selection
- Direct microphone/speaker access
- Conversation logging to files

## 🧠 How It Works

**Web Interface Flow:**
React Frontend ↔ WebSocket/REST API ↔ Flask Backend ↔ AI Services

**Voice Processing Flow:**
Text Input → Gemini AI → Murf TTS API → Audio Response
Voice Input → Deepgram ASR → Gemini AI → Murf TTS API → Audio Response

**Architecture:**
- **Frontend**: React with Socket.IO for real-time communication
- **Backend**: Flask with Flask-SocketIO for API endpoints
- **AI Services**: Google Gemini for conversations, Murf for TTS, Deepgram for ASR

## 💡 Use Cases

- Customer Support Assistant - Natural voice-based help desk
- Language Learning Coach - Practice conversations with AI
- Accessibility Aid - Voice interface for visually impaired users
- Productivity Assistant - Voice-controlled task management
- Interactive Storytelling - Dynamic narrative experiences
- Educational Tools - Interactive learning with voice feedback

## 📁 Project Structure

```
murf-voice-agent-hackathon/
├── app.py                    # Flask backend with API endpoints
├── voice_agent.py           # CLI version of the voice agent
├── requirements.txt         # Python dependencies
├── .env.example            # Environment variables template
├── .gitignore              # Git ignore file
├── LICENSE                 # MIT License
├── README.md               # Project documentation
├── conversation_log.txt    # Auto-generated conversation logs
├── test_murf.py           # API testing script
└── frontend/               # React frontend
    ├── public/
    │   ├── index.html
    │   └── favicon.ico
    ├── src/
    │   ├── App.js         # Main React component
    │   ├── App.css        # Styling
    │   ├── index.js       # React entry point
    │   └── setupTests.js
    ├── package.json       # React dependencies
    └── README.md
```

## 🔧 Technical Stack

**Backend (Python/Flask):**
- Framework: Flask 3.0 + Flask-SocketIO 5.3
- AI: Google Gemini AI (google-generativeai)
- TTS: Murf Falcon API
- ASR: Deepgram SDK
- Real-time: Python SocketIO
- Audio: System audio playback

**Frontend (React):**
- Framework: React 18 with Hooks
- UI: Modern chat interface with CSS
- Real-time: Socket.IO client
- Audio: Web Audio API
- Responsive: Mobile-first design

**APIs & Services:**
- Murf AI Falcon TTS (voice synthesis)
- Deepgram Nova-2 ASR (speech recognition)
- Google Gemini 1.5 Flash (conversational AI)

## 📹 Demo Video

🎥 Watch Demo Video - Replace with your actual demo video link after recording

## 📊 Performance

- TTS Latency: < 500ms (Murf Falcon)
- ASR Accuracy: 95%+ (Deepgram Nova-2)
- Response Time: ~1-2 seconds end-to-end
- Character Usage: Tracked per session

## ⚙️ Configuration

**Environment Variables (.env):**
```env
MURF_API_KEY=your_murf_api_key_here
DEEPGRAM_API_KEY=your_deepgram_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here
```

**Backend Configuration (app.py):**
- Modify the `VoiceAgentAPI` class for custom AI logic
- Adjust Flask-SocketIO settings for production deployment
- Configure CORS settings for different domains

**Frontend Configuration (frontend/src/App.js):**
- Update Socket.IO connection URL for production
- Modify UI colors and branding
- Add additional features like voice recording

## 🐛 Troubleshooting

### Microphone not working

- Check system permissions for microphone access
- Verify PyAudio installation: pip install --upgrade pyaudio
- On Linux: sudo apt-get install portaudio19-dev

### API Key errors

- Verify .env file is in the project root
- Check API key format (no spaces or quotes)
- Ensure keys are valid and have credits

### Audio playback issues

- Update audio drivers
- Try different sample rates (8000, 16000, 22050, 44100)
- Check speaker/headphone connections

## 🤝 Contributing

This is a hackathon submission project. Feel free to fork and experiment!

## 📄 License

MIT License - see LICENSE file for details

## 👤 Author

Parth Bavale
Team ID: Murf-250280
Techfest IIT Bombay 2025-26

## 🙏 Acknowledgments

- **Murf AI** for providing the Falcon TTS API and free credits
- **Deepgram** for ASR capabilities and hackathon support
- **Google AI** for Gemini API and intelligent conversations
- **Techfest IIT Bombay** for organizing this amazing hackathon
- **React & Flask communities** for excellent frameworks

## 📞 Support

For questions or issues:
- Open an issue on GitHub
- Contact: parthbb21@gmail.com

---

Built using Murf Falcon – the consistently fastest TTS API 🚀

Submission for Techfest IIT Bombay - Murf AI Voice Agent Hackathon 2025-26
