#!/usr/bin/env python3
"""
Murf AI Voice Agent - Techfest IIT Bombay Hackathon
Real-time conversational AI with Murf Falcon TTS and Deepgram ASR
"""

import os
import sys
import asyncio
import json
from datetime import datetime
from dotenv import load_dotenv
import requests
import pyaudio
import wave
from deepgram import (
    DeepgramClient,
    LiveTranscriptionEvents,
    LiveOptions,
    Microphone,
)
from openai import OpenAI

# Load environment variables
load_dotenv()

# Configuration
class Config:
    MURF_API_KEY = os.getenv('MURF_API_KEY')
    DEEPGRAM_API_KEY = os.getenv('DEEPGRAM_API_KEY')
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    MURF_API_URL = 'https://api.murf.ai/v1/speech/generate'
    VOICE_ID = 'en-US-terrell'  # Murf voice ID
    SAMPLE_RATE = 16000

class VoiceAgent:
    def __init__(self):
        self.config = Config()
        self.conversation_history = []
        self.is_running = False
        self.deepgram_client = None
        self.openai_client = None
        
        # Validate API keys
        self._validate_config()
        
        # Initialize clients
        if self.config.DEEPGRAM_API_KEY:
            self.deepgram_client = DeepgramClient(self.config.DEEPGRAM_API_KEY)
        if self.config.OPENAI_API_KEY:
            self.openai_client = OpenAI(api_key=self.config.OPENAI_API_KEY)
    
    def _validate_config(self):
        """Validate required API keys"""
        if not self.config.MURF_API_KEY:
            raise ValueError("MURF_API_KEY not found in environment variables")
        if not self.config.DEEPGRAM_API_KEY:
            raise ValueError("DEEPGRAM_API_KEY not found in environment variables")
        print("✓ API keys validated successfully")
    
    def speak_with_murf(self, text):
        """
        Generate speech using Murf Falcon TTS API
        Returns audio data or saves to file
        """
        print(f"\n🎙️ Speaking: {text}")
        
        headers = {
            'Authorization': f'Bearer {self.config.MURF_API_KEY}',
            'Content-Type': 'application/json',
        }
        
        payload = {
            'voiceId': self.config.VOICE_ID,
            'text': text,
            'format': 'WAV',
            'sampleRate': self.config.SAMPLE_RATE,
            'speed': 1.0,
        }
        
        try:
            response = requests.post(
                self.config.MURF_API_URL,
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                # Save and play audio
                audio_file = f"output_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"
                with open(audio_file, 'wb') as f:
                    f.write(response.content)
                
                # Play audio
                self._play_audio(audio_file)
                print(f"✓ Audio saved and played: {audio_file}")
                return audio_file
            else:
                print(f"❌ Murf API Error: {response.status_code} - {response.text}")
                return None
        
        except Exception as e:
            print(f"❌ Error generating speech: {str(e)}")
            return None
    
    def _play_audio(self, filename):
        """Play audio file using pyaudio"""
        try:
            wf = wave.open(filename, 'rb')
            p = pyaudio.PyAudio()
            
            stream = p.open(
                format=p.get_format_from_width(wf.getsampwidth()),
                channels=wf.getnchannels(),
                rate=wf.getframerate(),
                output=True
            )
            
            data = wf.readframes(1024)
            while data:
                stream.write(data)
                data = wf.readframes(1024)
            
            stream.stop_stream()
            stream.close()
            p.terminate()
            wf.close()
        
        except Exception as e:
            print(f"❌ Error playing audio: {str(e)}")
    
    def get_ai_response(self, user_input):
        """
        Generate AI response using OpenAI or fallback logic
        """
        # Add user message to history
        self.conversation_history.append({
            'role': 'user',
            'content': user_input
        })
        
        if self.openai_client:
            try:
                # Use OpenAI for intelligent responses
                response = self.openai_client.chat.completions.create(
                    model='gpt-3.5-turbo',
                    messages=[
                        {'role': 'system', 'content': 'You are a helpful voice assistant. Keep responses concise and conversational.'},
                        *self.conversation_history
                    ],
                    max_tokens=150,
                    temperature=0.7
                )
                
                ai_response = response.choices[0].message.content
                self.conversation_history.append({
                    'role': 'assistant',
                    'content': ai_response
                })
                
                return ai_response
            
            except Exception as e:
                print(f"❌ OpenAI Error: {str(e)}")
        
        # Fallback responses if OpenAI not available
        return self._get_fallback_response(user_input)
    
    def _get_fallback_response(self, user_input):
        """Simple fallback responses when LLM is not available"""
        user_input_lower = user_input.lower()
        
        if 'hello' in user_input_lower or 'hi' in user_input_lower:
            return "Hello! I'm your AI voice assistant powered by Murf Falcon. How can I help you today?"
        elif 'how are you' in user_input_lower:
            return "I'm doing great! Thanks for asking. I'm here to assist you with anything you need."
        elif 'bye' in user_input_lower or 'goodbye' in user_input_lower:
            return "Goodbye! It was nice talking to you. Have a wonderful day!"
        elif 'time' in user_input_lower:
            current_time = datetime.now().strftime('%I:%M %p')
            return f"The current time is {current_time}."
        elif 'date' in user_input_lower:
            current_date = datetime.now().strftime('%B %d, %Y')
            return f"Today is {current_date}."
        else:
            return f"You said: {user_input}. I'm a voice assistant built with Murf Falcon TTS for the Techfest IIT Bombay hackathon. How can I help?"
    
    async def listen_and_respond(self):
        """
        Main conversation loop using Deepgram for real-time transcription
        """
        print("\n🎤 Voice Agent Started!")
        print("Speak into your microphone... (Say 'goodbye' to exit)\n")
        
        try:
            dg_connection = self.deepgram_client.listen.asynclive.v('1')
            
            async def on_message(self, result, **kwargs):
                sentence = result.channel.alternatives[0].transcript
                
                if len(sentence) == 0:
                    return
                
                if result.is_final:
                    print(f"\n👤 You: {sentence}")
                    
                    # Check for exit command
                    if 'goodbye' in sentence.lower() or 'bye' in sentence.lower():
                        print("\n👋 Ending conversation...")
                        self.is_running = False
                        return
                    
                    # Get AI response
                    response = self.get_ai_response(sentence)
                    print(f"🤖 Assistant: {response}")
                    
                    # Speak response using Murf
                    self.speak_with_murf(response)
            
            dg_connection.on(LiveTranscriptionEvents.Transcript, on_message)
            
            options = LiveOptions(
                model='nova-2',
                language='en-US',
                smart_format=True,
                encoding='linear16',
                channels=1,
                sample_rate=self.config.SAMPLE_RATE,
            )
            
            await dg_connection.start(options)
            
            # Use microphone for input
            microphone = Microphone(dg_connection.send)
            microphone.start()
            
            self.is_running = True
            
            # Keep running until stopped
            while self.is_running:
                await asyncio.sleep(0.1)
            
            # Cleanup
            microphone.finish()
            await dg_connection.finish()
        
        except Exception as e:
            print(f"❌ Error in conversation loop: {str(e)}")
    
    def start(self):
        """Start the voice agent"""
        print("="*60)
        print("  🎤 MURF AI VOICE AGENT - TECHFEST IIT BOMBAY")
        print("  Built using Murf Falcon - Fastest TTS API")
        print("="*60)
        
        # Initial greeting
        greeting = "Hello! I'm your AI voice assistant powered by Murf Falcon. How can I help you today?"
        self.speak_with_murf(greeting)
        
        # Start conversation loop
        asyncio.run(self.listen_and_respond())

def main():
    try:
        agent = VoiceAgent()
        agent.start()
    except KeyboardInterrupt:
        print("\n\n👋 Voice agent stopped by user")
    except Exception as e:
        print(f"\n❌ Fatal error: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()
