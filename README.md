# 🎤 Murf AI Voice Agent - Techfest IIT Bombay Hackathon

> **Built using Murf Falcon – the consistently fastest TTS API**

A real-time conversational AI voice agent that demonstrates the power of Murf Falcon TTS combined with Deepgram ASR for natural, intelligent voice-driven interactions.

## 🏆 Hackathon Details

- **Event**: Techfest 2025-26 - Murf AI Voice Agent Hackathon
- **Institution**: IIT Bombay
- **Team ID**: Murf-250280
- **Category**: Voice-First AI Applications

## ✨ Features

- 🎙️ **Real-time Speech Recognition** using Deepgram ASR
- 🗣️ **Natural Speech Synthesis** powered by Murf Falcon TTS API
- 🤖 **Intelligent Conversations** with OpenAI GPT integration (optional)
- 💬 **Fallback Logic** for standalone operation without LLM
- 🔒 **Secure API Key Management** via environment variables
- ⚡ **Low Latency** real-time audio processing
- 🎵 **Audio Playback** with PyAudio
- 📝 **Conversation History** tracking

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- Microphone and speakers
- API keys for:
  - Murf AI (required)
  - Deepgram (required)
  - OpenAI (optional)

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/parth2152012/murf-voice-agent-hackathon.git
cd murf-voice-agent-hackathon
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Set up environment variables**
```bash
cp .env.example .env
```

Edit `.env` and add your API keys:
```env
MURF_API_KEY=your_murf_api_key_here
DEEPGRAM_API_KEY=your_deepgram_api_key_here
OPENAI_API_KEY=your_openai_api_key_here  # Optional
```

### Getting API Keys

#### Murf AI API Key
1. Sign up at [murf.ai](https://murf.ai)
2. Navigate to API settings
3. Generate your Falcon TTS API key
4. New accounts get **1,000,000 free TTS characters**

#### Deepgram API Key
1. Sign up at [deepgram.com](https://deepgram.com)
2. Get free credits for the hackathon
3. Create an API key from the console

#### OpenAI API Key (Optional)
1. Sign up at [openai.com](https://openai.com)
2. Generate API key from dashboard
3. Not required - app works with fallback responses

### Running the Application

```bash
python voice_agent.py
```

The voice agent will:
1. Validate your API keys
2. Start listening to your microphone
3. Greet you with Murf Falcon's natural voice
4. Begin conversational interaction

Say **"goodbye"** or **"bye"** to exit the application.

## 🎯 How It Works

```
┌─────────────┐      ┌──────────────┐      ┌─────────────┐
│  Microphone │─────▶│  Deepgram    │─────▶│   OpenAI    │
│   (Input)   │      │     ASR      │      │  GPT (LLM)  │
└─────────────┘      └──────────────┘      └─────────────┘
                            │                      │
                            ▼                      ▼
                     ┌──────────────┐      ┌─────────────┐
                     │  Text Input  │◀─────│  AI Response│
                     └──────────────┘      └─────────────┘
                            │
                            ▼
                     ┌──────────────┐
                     │ Murf Falcon  │
                     │   TTS API    │
                     └──────────────┘
                            │
                            ▼
                     ┌──────────────┐
                     │   Speakers   │
                     │   (Output)   │
                     └──────────────┘
```

## 💡 Use Cases

- **Customer Support Assistant** - Natural voice-based help desk
- **Language Learning Coach** - Practice conversations with AI
- **Accessibility Aid** - Voice interface for visually impaired users
- **Productivity Assistant** - Voice-controlled task management
- **Interactive Storytelling** - Dynamic narrative experiences

## 📁 Project Structure

```
murf-voice-agent-hackathon/
├── voice_agent.py       # Main application code
├── requirements.txt     # Python dependencies
├── .env.example        # Environment variables template
├── .gitignore          # Git ignore file
├── LICENSE             # MIT License
└── README.md           # This file
```

## 🛠️ Technical Stack

- **Language**: Python 3.8+
- **TTS**: Murf Falcon API
- **ASR**: Deepgram SDK
- **LLM**: OpenAI GPT-3.5 (optional)
- **Audio**: PyAudio
- **Async**: asyncio

## 🎬 Demo Video

[🎥 Watch Demo Video](YOUR_VIDEO_LINK_HERE)

> *Replace with your actual demo video link after recording*

## 📊 Performance

- **TTS Latency**: < 500ms (Murf Falcon)
- **ASR Accuracy**: 95%+ (Deepgram Nova-2)
- **Response Time**: ~1-2 seconds end-to-end
- **Character Usage**: Tracked per session

## 🔧 Configuration

You can customize the voice agent by modifying the `Config` class in `voice_agent.py`:

```python
class Config:
    MURF_API_KEY = os.getenv('MURF_API_KEY')
    DEEPGRAM_API_KEY = os.getenv('DEEPGRAM_API_KEY')
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    MURF_API_URL = 'https://api.murf.ai/v1/speech/generate'
    VOICE_ID = 'en-US-terrell'  # Change to your preferred voice
    SAMPLE_RATE = 16000
```

## 🐛 Troubleshooting

### Microphone not working
- Check system permissions for microphone access
- Verify PyAudio installation: `pip install --upgrade pyaudio`
- On Linux: `sudo apt-get install portaudio19-dev`

### API Key errors
- Verify `.env` file is in the project root
- Check API key format (no spaces or quotes)
- Ensure keys are valid and have credits

### Audio playback issues
- Update audio drivers
- Try different sample rates (8000, 16000, 22050, 44100)
- Check speaker/headphone connections

## 🤝 Contributing

This is a hackathon submission project. Feel free to fork and experiment!

## 📜 License

MIT License - see [LICENSE](LICENSE) file for details

## 👨‍💻 Author

**Parth Bavale**  
Team ID: Murf-250280  
Techfest IIT Bombay 2025-26

## 🙏 Acknowledgments

- **Murf AI** for providing the Falcon TTS API and free credits
- **Deepgram** for ASR capabilities and hackathon support
- **Techfest IIT Bombay** for organizing this amazing hackathon
- **OpenAI** for GPT API integration

## 📞 Support

For questions or issues:
- Open an issue on GitHub
- Contact: parthbb21@gmail.com

---

**Built using Murf Falcon – the consistently fastest TTS API** 🚀

*Submission for Techfest IIT Bombay - Murf AI Voice Agent Hackathon 2025-26*
