#!/usr/bin/env python3
"""
Flask Backend for Murf AI Voice Agent
Provides REST API and WebSocket support for the React frontend
"""

import os
import asyncio
import json
import uuid
from datetime import datetime
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from dotenv import load_dotenv
import requests
import google.genai as genai
from deepgram import DeepgramClient

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Global variables
conversations = {}  # Store conversation history per session
gemini_model = None

class VoiceAgentAPI:
    """API wrapper for voice agent functionality"""

    def __init__(self):
        self.murf_api_key = os.getenv('MURF_API_KEY')
        self.deepgram_api_key = os.getenv('DEEPGRAM_API_KEY')
        self.gemini_api_key = os.getenv('GEMINI_API_KEY')

        # Initialize Gemini client
        if self.gemini_api_key:
            try:
                self.gemini_client = genai.Client(api_key=self.gemini_api_key)
            except Exception as e:
                print(f"Gemini client initialization failed: {e}")
                self.gemini_client = None
        else:
            self.gemini_client = None

        # Initialize Deepgram (skip for now due to compatibility issues)
        self.deepgram_client = None
        # if self.deepgram_api_key:
        #     try:
        #         self.deepgram_client = DeepgramClient(self.deepgram_api_key)
        #     except Exception as e:
        #         print(f"Deepgram initialization failed: {e}")
        #         self.deepgram_client = None

    def generate_response(self, user_input: str, conversation_history: list) -> str:
        """Generate AI response using Gemini with proper prompt engineering"""
        if not self.gemini_client:
            return self._fallback_response(user_input, conversation_history)

        try:
            # Create a system prompt for the AI assistant
            system_prompt = """You are Neha, a helpful and friendly AI voice assistant living in India for a hackathon project.
            You should:
            - Be warm, conversational, and culturally aware of Indian context.
            - Use Indian English expressions and be familiar with Indian culture, festivals, and daily life.
            - Be enthusiastic about Indian tech innovation, startups, and cultural diversity.
            - If asked to tell a story or be creative, you should provide a longer, more detailed response.
            - For normal questions, keep responses reasonably concise for a voice interface.
            - Show a friendly, approachable personality with Indian warmth.
            - Remember context from the conversation to avoid repetition.
            - Be enthusiastic about helping users with their Indian lifestyle and tech needs.

            You live in India and understand Indian culture, so you can reference Indian festivals, food, cities, and daily life naturally.
            This is for a voice interface, so responses should sound natural when spoken in an Indian accent."""

            # Build conversation context from history
            conversation_context = ""
            if conversation_history:
                # Add recent conversation history for context
                recent_history = conversation_history[-6:]  # Last 6 messages for context
                for msg in recent_history:
                    role = msg.get('role', 'user')
                    content = msg.get('parts', [''])[0] if msg.get('parts') else ''
                    if role == 'user':
                        conversation_context += f"User: {content}\n"
                    elif role == 'model':
                        conversation_context += f"Assistant: {content}\n"

            # Create the full prompt
            full_prompt = f"{system_prompt}\n\n{conversation_context}User: {user_input}\nAssistant:"

            # Generate response using the new API format
            response = self.gemini_client.models.generate_content(
                model="gemini-2.0-flash",
                contents=full_prompt
            )

            ai_response = response.text.strip()

            # Ensure response isn't empty and is reasonable length
            if not ai_response or len(ai_response) < 5:
                return self._fallback_response(user_input, conversation_history)

            return ai_response

        except Exception as e:
            print(f"Gemini API error: {e}")
            return self._fallback_response(user_input, conversation_history)

    def _fallback_response(self, user_input: str, conversation_history: list = None) -> str:
        """Smart fallback responses with conversation context"""
        user_input_lower = user_input.lower()

        # Check for specific keywords and patterns
        if any(word in user_input_lower for word in ["hello", "hi", "hey"]):
            return "Namaste! I'm Neha, your AI voice assistant in India. How can I help you today?"

        if "how are you" in user_input_lower:
            return "I'm doing great, thank you! It's wonderful to connect with you from India. What's on your mind?"

        if any(word in user_input_lower for word in ["name", "who are you"]):
            return "I'm Neha, your friendly AI voice assistant built for the Techfest IIT Bombay hackathon using Murf Falcon TTS!"

        if any(word in user_input_lower for word in ["help", "what can you do"]):
            return "I can have natural conversations with you! I understand Indian culture and use Google's Gemini AI for smart responses with Murf Falcon voice synthesis."

        if any(word in user_input_lower for word in ["thank", "thanks"]):
            return "You're most welcome! Dhanyavaad! I'm here whenever you need to chat."

        if any(word in user_input_lower for word in ["bye", "goodbye", "see you"]):
            return "Goodbye! It was wonderful talking with you. Dhanyavaad and take care!"

        # Check conversation history for context
        if conversation_history and len(conversation_history) > 0:
            # Look for repeated questions or patterns
            recent_messages = [msg.get('parts', [''])[0] for msg in conversation_history[-4:] if msg.get('role') == 'user']
            if len(set(recent_messages)) == 1 and len(recent_messages) > 1:
                return "I see you're asking the same question. Let me try a different approach - could you tell me more about what you're looking for?"

        # Default engaging responses based on input type
        if "?" in user_input:
            return f"That's a great question about '{user_input}'. While I'm still learning, I'd love to hear your thoughts on it!"

        if len(user_input.split()) > 10:
            return "That sounds interesting! You have a lot to say about that topic. Tell me more!"

        # Fun, engaging default responses
        default_responses = [
            f"I heard you say '{user_input}'. That's fascinating! What made you think about that?",
            f"'{user_input}' - I love hearing about that! Can you tell me more?",
            f"Thanks for sharing that with me! '{user_input}' sounds really interesting.",
            f"I appreciate you telling me about '{user_input}'. What's your favorite part?",
            f"That's really cool! '{user_input}' got me thinking. What's next on your mind?"
        ]

        # Use input length to select response variety
        response_index = len(user_input) % len(default_responses)
        return default_responses[response_index]

    def speak_with_murf(self, text: str) -> dict:
        """Generate speech using Murf API"""
        try:
            headers = {
                'api-key': self.murf_api_key,
                'Content-Type': 'application/json',
            }

            payload = {
                'voiceId': 'en-US-samantha',
                'text': text,
                'format': 'mp3',
                'sampleRate': 24000,
            }

            response = requests.post(
                'https://api.murf.ai/v1/speech/generate',
                headers=headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()

            json_response = response.json()
            if 'audioFile' in json_response:
                return {
                    'success': True,
                    'audio_url': json_response['audioFile'],
                    'text': text
                }

            return {'success': False, 'error': 'No audio URL in response'}

        except Exception as e:
            return {'success': False, 'error': str(e)}

# Initialize API
voice_agent = VoiceAgentAPI()

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

@app.route('/api/conversation', methods=['POST'])
def send_message():
    """Send a text message and get AI response"""
    try:
        data = request.get_json()
        user_message = data.get('message', '').strip()
        session_id = data.get('session_id', 'default')

        if not user_message:
            return jsonify({'error': 'No message provided'}), 400

        # Get or create conversation history
        if session_id not in conversations:
            conversations[session_id] = []

        # Add user message to history
        conversations[session_id].append({
            'role': 'user',
            'parts': [user_message]
        })

        # Generate AI response
        ai_response = voice_agent.generate_response(user_message, conversations[session_id])

        # Add AI response to history
        conversations[session_id].append({
            'role': 'model',
            'parts': [ai_response]
        })

        # Generate speech for AI response
        speech_result = voice_agent.speak_with_murf(ai_response)

        response_data = {
            'user_message': user_message,
            'ai_response': ai_response,
            'speech': speech_result,
            'timestamp': datetime.now().isoformat()
        }

        return jsonify(response_data)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/tts', methods=['POST'])
def text_to_speech():
    """Convert text to speech"""
    try:
        data = request.get_json()
        text = data.get('text', '').strip()

        if not text:
            return jsonify({'error': 'No text provided'}), 400

        speech_result = voice_agent.speak_with_murf(text)
        return jsonify(speech_result)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@socketio.on('connect')
def handle_connect():
    """Handle WebSocket connection"""
    print('Client connected')
    emit('status', {'message': 'Connected to voice agent'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle WebSocket disconnection"""
    print('Client disconnected')

@socketio.on('send_message')
def handle_message(data):
    """Handle real-time message via WebSocket"""
    try:
        user_message = data.get('message', '').strip()
        session_id = data.get('session_id', 'default')

        if not user_message:
            emit('error', {'message': 'No message provided'})
            return

        # Get or create conversation history
        if session_id not in conversations:
            conversations[session_id] = []

        # Add user message to history
        conversations[session_id].append({
            'role': 'user',
            'parts': [user_message]
        })

        # Generate AI response
        ai_response = voice_agent.generate_response(user_message, conversations[session_id])

        # Add AI response to history
        conversations[session_id].append({
            'role': 'model',
            'parts': [ai_response]
        })

        # Generate speech for AI response
        speech_result = voice_agent.speak_with_murf(ai_response)

        # Send response back to client
        emit('message_response', {
            'user_message': user_message,
            'ai_response': ai_response,
            'speech': speech_result,
            'timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        emit('error', {'message': str(e)})

if __name__ == '__main__':
    print("🚀 Starting Murf AI Voice Agent Backend...")
    print("📡 Flask server running on http://localhost:5000")
    print("🔌 WebSocket support enabled")
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
