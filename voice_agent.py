#!/usr/bin/env python3
"""
Murf AI Voice Agent - Techfest IIT Bombay Hackathon
Real-time conversational AI with Murf Falcon TTS and Deepgram ASR
"""

import os
import sys
import asyncio
import json
from datetime import import datetime
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
    PERPLEXITY_API_KEY = os.getenv('PERPLEXITY_API_KEY')
    MURF_API_URL = 'https://api.murf.ai/v1/speech/generate'
    VOICE_ID = 'en-US-terrell'  # Murf voice ID
    SAMPLE_RATE = 16000


class VoiceAgent:
    def __init__(self):
        self.config = Config()
        self.conversation_history = []
        self.is_running = False
        self.deepgram_client = None
        self.perplexity_client = None
        
        # Validate API keys
        self._validate_config()
        
        # Initialize clients
        if self.config.DEEPGRAM_API_KEY:
            self.deepgram_client = DeepgramClient(self.config.DEEPGRAM_API_KEY)
        if self.config.PERPLEXITY_API_KEY:
            self.perplexity_client = OpenAI(
                api_key=self.config.PERPLEXITY_API_KEY,
                base_url="https://api.perplexity.ai"
            )
    
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
        }
        
        try:
            response = requests.post(
                self.config.MURF_API_URL,
                headers=headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            
            # Save audio file
            audio_file = f'output_{datetime.now().strftime("%Y%m%d_%H%M%S")}.wav'
            with open(audio_file, 'wb') as f:
                f.write(response.content)
            
            # Play audio
            self._play_audio(audio_file)
            
            # Clean up
            os.remove(audio_file)
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Error generating speech: {e}")
            if hasattr(e, 'response') and e.response:
                print(f"Response: {e.response.text}")
    
    def _play_audio(self, audio_file):
        """Play audio file using PyAudio"""
        try:
            wf = wave.open(audio_file, 'rb')
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
            print(f"❌ Error playing audio: {e}")
    
    async def listen_with_deepgram(self):
        """
        Listen to microphone using Deepgram ASR
        Returns transcribed text
        """
        print("\n🎤 Listening... (say 'goodbye' or 'bye' to exit)")
        
        try:
            dg_connection = self.deepgram_client.listen.live.v("1")
            
            transcription_complete = asyncio.Event()
            transcribed_text = []
            
            def on_message(self, result, **kwargs):
                sentence = result.channel.alternatives[0].transcript
                if len(sentence) == 0:
                    return
                
                if result.is_final:
                    transcribed_text.append(sentence)
                    print(f"You: {sentence}")
                    transcription_complete.set()
            
            def on_error(self, error, **kwargs):
                print(f"❌ Deepgram Error: {error}")
                transcription_complete.set()
            
            dg_connection.on(LiveTranscriptionEvents.Transcript, on_message)
            dg_connection.on(LiveTranscriptionEvents.Error, on_error)
            
            options = LiveOptions(
                model="nova-2",
                language="en-US",
                smart_format=True,
                interim_results=False,
                punctuate=True,
            )
            
            await dg_connection.start(options)
            
            microphone = Microphone(dg_connection.send)
            microphone.start()
            
            await transcription_complete.wait()
            
            microphone.finish()
            await dg_connection.finish()
            
            return ' '.join(transcribed_text).strip()
            
        except Exception as e:
            print(f"❌ Error during speech recognition: {e}")
            return ""
    
    def generate_response(self, user_input):
        """
        Generate intelligent response using Perplexity AI
        Falls back to simple responses if API not available
        """
        if self.perplexity_client:
            try:
                # Add to conversation history
                self.conversation_history.append({
                    "role": "user",
                    "content": user_input
                })
                
                # Generate response with Perplexity
                response = self.perplexity_client.chat.completions.create(
                    model="sonar",  # Use "sonar-pro" for better quality
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a helpful, friendly AI voice assistant. Keep responses concise and conversational."
                        },
                        *self.conversation_history
                    ],
                    temperature=0.7,
                    max_tokens=150,
                )
                
                ai_response = response.choices[0].message.content
                
                # Add AI response to history
                self.conversation_history.append({
                    "role": "assistant",
                    "content": ai_response
                })
                
                # Keep conversation history manageable
                if len(self.conversation_history) > 10:
                    self.conversation_history = self.conversation_history[-10:]
                
                return ai_response
                
            except Exception as e:
                print(f"⚠️ Perplexity API error: {e}")
                return self._fallback_response(user_input)
        else:
            return self._fallback_response(user_input)
    
    def _fallback_response(self, user_input):
        """Simple fallback responses when Perplexity is not available"""
        user_input_lower = user_input.lower()
        
        responses = {
            "hello": "Hello! How can I help you today?",
            "hi": "Hi there! What can I do for you?",
            "how are you": "I'm doing great! Thanks for asking. How about you?",
            "what's your name": "I'm your AI voice assistant, powered by Murf Falcon!",
            "help": "I can chat with you using natural conversation. Just speak naturally!",
        }
        
        for key, response in responses.items():
            if key in user_input_lower:
                return response
        
        return f"I heard you say: {user_input}. That's interesting! Tell me more."
    
    async def run(self):
        """Main conversation loop"""
        print("\n" + "="*60)
        print("🎤 Murf AI Voice Agent - Techfest IIT Bombay Hackathon")
        print("="*60)
        print("\nWelcome! I'm your AI voice assistant.")
        print("Powered by:")
        print("  • Murf Falcon TTS (Text-to-Speech)")
        print("  • Deepgram Nova-2 ASR (Speech Recognition)")
        print("  • Perplexity AI (Intelligent Responses)")
        print("\nSpeak naturally, and I'll respond!")
        print("Say 'goodbye' or 'bye' to exit.\n")
        
        # Initial greeting
        self.speak_with_murf("Hello! I'm your AI voice assistant. How can I help you today?")
        
        self.is_running = True
        
        while self.is_running:
            try:
                # Listen for user input
                user_input = await self.listen_with_deepgram()
                
                if not user_input:
                    continue
                
                # Check for exit commands
                if any(word in user_input.lower() for word in ['goodbye', 'bye', 'exit', 'quit']):
                    self.speak_with_murf("Goodbye! It was nice talking to you!")
                    self.is_running = False
                    break
                
                # Generate response
                ai_response = self.generate_response(user_input)
                
                # Speak response
                self.speak_with_murf(ai_response)
                
            except KeyboardInterrupt:
                print("\n\n⚠️ Interrupted by user")
                self.speak_with_murf("Goodbye!")
                self.is_running = False
                break
            except Exception as e:
                print(f"\n❌ Error in conversation loop: {e}")
                continue
        
        print("\n👋 Voice agent stopped. Thank you!")


def main():
    """Entry point"""
    try:
        agent = VoiceAgent()
        asyncio.run(agent.run())
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
