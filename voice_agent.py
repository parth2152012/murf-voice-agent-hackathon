#!/usr/bin/env python3
"""
Murf AI Voice Agent - Techfest IIT Bombay Hackathon
Real-time conversational AI with Murf Falcon TTS and Deepgram ASR

Author: Team Murf-250280
Improved Version: Enhanced error handling, logging, and user experience
"""

import os
import sys
import asyncio
import json
import time
from datetime import datetime
from dotenv import load_dotenv
import requests
import pyaudio
import wave
from typing import Optional, List, Dict
from deepgram import (
    DeepgramClient,
    LiveTranscriptionEvents,
    LiveOptions,
    Microphone,
)
from openai import OpenAI

# Load environment variables
load_dotenv()


class Config:
    """Configuration class for API keys and settings"""
    
    MURF_API_KEY: str = os.getenv('MURF_API_KEY', '')
    DEEPGRAM_API_KEY: str = os.getenv('DEEPGRAM_API_KEY', '')
    PERPLEXITY_API_KEY: str = os.getenv('PERPLEXITY_API_KEY', '')
    
    # API Endpoints
    MURF_API_URL: str = 'https://api.murf.ai/v1/speech/generate'
    
    # Voice Settings
    VOICE_ID: str = 'en-US-terrell'  # Murf Falcon voice ID
    SAMPLE_RATE: int = 16000
    
    # Conversation Settings
    MAX_HISTORY_LENGTH: int = 10  # Maximum conversation history to maintain
    LISTEN_TIMEOUT: int = 30  # Seconds before listening times out
    
    # Retry Settings
    MAX_RETRIES: int = 3
    RETRY_DELAY: int = 2  # Seconds between retries
    
    # Logging
    LOG_CONVERSATIONS: bool = True
    LOG_FILE: str = 'conversation_log.txt'


class VoiceAgent:
    """Main Voice Agent class handling speech recognition, generation, and TTS"""
    
    def __init__(self):
        self.config = Config()
        self.conversation_history: List[Dict[str, str]] = []
        self.is_running: bool = False
        self.deepgram_client: Optional[DeepgramClient] = None
        self.perplexity_client: Optional[OpenAI] = None
        self.audio_files_to_cleanup: List[str] = []
        
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
            print("✓ Perplexity AI enabled for intelligent responses")
        else:
            print("⚠️  Perplexity AI not configured - using fallback responses")
    
    def _validate_config(self) -> None:
        """Validate required API keys and configuration"""
        if not self.config.MURF_API_KEY:
            raise ValueError(
                "❌ MURF_API_KEY not found in environment variables.\n"
                "Please add it to your .env file."
            )
        if not self.config.DEEPGRAM_API_KEY:
            raise ValueError(
                "❌ DEEPGRAM_API_KEY not found in environment variables.\n"
                "Please add it to your .env file."
            )
        print("✓ API keys validated successfully")
    
    def _log_conversation(self, speaker: str, message: str) -> None:
        """Log conversation to file for demo video creation"""
        if not self.config.LOG_CONVERSATIONS:
            return
        
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_entry = f"[{timestamp}] {speaker}: {message}\n"
            
            with open(self.config.LOG_FILE, 'a', encoding='utf-8') as f:
                f.write(log_entry)
        except Exception as e:
            print(f"⚠️  Failed to log conversation: {e}")
    
    def speak_with_murf(self, text: str, retry_count: int = 0) -> bool:
        """
        Generate and play speech using Murf Falcon TTS API with retry logic
        
        Args:
            text: Text to convert to speech
            retry_count: Current retry attempt (for internal use)
        
        Returns:
            bool: True if successful, False otherwise
        """
        print(f"\n🎙️  Speaking: {text}")
        self._log_conversation("Agent", text)
        
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
        
        audio_file = None
        
        try:
            print("⏳ Generating speech...")
            response = requests.post(
                self.config.MURF_API_URL,
                headers=headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            
            # Save audio file
            audio_file = f'output_{datetime.now().strftime("%Y%m%d_%H%M%S")}.wav'
            self.audio_files_to_cleanup.append(audio_file)
            
            with open(audio_file, 'wb') as f:
                f.write(response.content)
            
            print("▶️  Playing audio...")
            # Play audio
            self._play_audio(audio_file)
            
            return True
            
        except requests.exceptions.Timeout:
            print("❌ Request timed out")
            if retry_count < self.config.MAX_RETRIES:
                print(f"🔄 Retrying... ({retry_count + 1}/{self.config.MAX_RETRIES})")
                time.sleep(self.config.RETRY_DELAY)
                return self.speak_with_murf(text, retry_count + 1)
            return False
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Error generating speech: {e}")
            if hasattr(e, 'response') and e.response:
                try:
                    error_data = e.response.json()
                    print(f"API Error: {error_data}")
                except:
                    print(f"Response: {e.response.text}")
            
            if retry_count < self.config.MAX_RETRIES:
                print(f"🔄 Retrying... ({retry_count + 1}/{self.config.MAX_RETRIES})")
                time.sleep(self.config.RETRY_DELAY)
                return self.speak_with_murf(text, retry_count + 1)
            return False
            
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            return False
        
        finally:
            # Clean up audio file
            if audio_file and os.path.exists(audio_file):
                try:
                    os.remove(audio_file)
                    if audio_file in self.audio_files_to_cleanup:
                        self.audio_files_to_cleanup.remove(audio_file)
                except Exception as e:
                    print(f"⚠️  Failed to clean up audio file: {e}")
    
    def _play_audio(self, audio_file: str) -> None:
        """Play audio file using PyAudio with proper resource management"""
        wf = None
        p = None
        stream = None
        
        try:
            wf = wave.open(audio_file, 'rb')
            p = pyaudio.PyAudio()
            
            stream = p.open(
                format=p.get_format_from_width(wf.getsampwidth()),
                channels=wf.getnchannels(),
                rate=wf.getframerate(),
                output=True
            )
            
            # Read and play audio in chunks
            chunk_size = 1024
            data = wf.readframes(chunk_size)
            
            while data:
                stream.write(data)
                data = wf.readframes(chunk_size)
            
        except Exception as e:
            print(f"❌ Error playing audio: {e}")
        
        finally:
            # Ensure proper cleanup
            if stream:
                try:
                    stream.stop_stream()
                    stream.close()
                except:
                    pass
            
            if p:
                try:
                    p.terminate()
                except:
                    pass
            
            if wf:
                try:
                    wf.close()
                except:
                    pass
    
    async def listen_with_deepgram(self) -> str:
        """
        Listen to microphone using Deepgram ASR with improved error handling
        
        Returns:
            str: Transcribed text from speech
        """
        print("\n🎤 Listening... (say 'goodbye' or 'bye' to exit)")
        
        dg_connection = None
        microphone = None
        
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
            
            # Wait for transcription with timeout
            try:
                await asyncio.wait_for(
                    transcription_complete.wait(),
                    timeout=self.config.LISTEN_TIMEOUT
                )
            except asyncio.TimeoutError:
                print("⏱️  Listening timed out. Please try again.")
                return ""
            
            result = ' '.join(transcribed_text).strip()
            
            # Log user input
            if result:
                self._log_conversation("User", result)
            
            return result
            
        except Exception as e:
            print(f"❌ Error during speech recognition: {e}")
            return ""
        
        finally:
            # Clean up resources
            if microphone:
                try:
                    microphone.finish()
                except:
                    pass
            
            if dg_connection:
                try:
                    await dg_connection.finish()
                except:
                    pass
    
    def generate_response(self, user_input: str) -> str:
        """
        Generate intelligent response using Perplexity AI
        Falls back to simple responses if API not available
        
        Args:
            user_input: User's spoken input
        
        Returns:
            str: Generated response
        """
        if self.perplexity_client:
            try:
                # Add to conversation history
                self.conversation_history.append({
                    "role": "user",
                    "content": user_input
                })
                
                print("💭 Thinking...")
                
                # Generate response with Perplexity
                response = self.perplexity_client.chat.completions.create(
                    model="sonar",
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "You are a helpful, friendly AI voice assistant built for voice conversations. "
                                "Keep responses concise (2-3 sentences), natural, and conversational. "
                                "Avoid long explanations unless specifically asked."
                            )
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
                if len(self.conversation_history) > self.config.MAX_HISTORY_LENGTH:
                    self.conversation_history = self.conversation_history[-self.config.MAX_HISTORY_LENGTH:]
                
                return ai_response
                
            except Exception as e:
                print(f"⚠️  Perplexity API error: {e}")
                return self._fallback_response(user_input)
        else:
            return self._fallback_response(user_input)
    
    def _fallback_response(self, user_input: str) -> str:
        """Simple fallback responses when Perplexity is not available"""
        user_input_lower = user_input.lower()
        
        responses = {
            "hello": "Hello! How can I help you today?",
            "hi": "Hi there! What can I do for you?",
            "how are you": "I'm doing great! Thanks for asking. How about you?",
            "what's your name": "I'm your AI voice assistant, powered by Murf Falcon TTS!",
            "what is your name": "I'm your AI voice assistant, powered by Murf Falcon TTS!",
            "help": "I can chat with you using natural conversation. Just speak naturally!",
            "what can you do": "I can have conversations with you using voice. I listen with Deepgram and speak with Murf Falcon!",
        }
        
        for key, response in responses.items():
            if key in user_input_lower:
                return response
        
        return f"I heard you say: {user_input}. That's interesting! Tell me more, or ask me something else."
    
    def _cleanup_resources(self) -> None:
        """Clean up any remaining resources"""
        print("\n🧹 Cleaning up resources...")
        
        # Clean up any remaining audio files
        for audio_file in self.audio_files_to_cleanup:
            try:
                if os.path.exists(audio_file):
                    os.remove(audio_file)
                    print(f"   Removed: {audio_file}")
            except Exception as e:
                print(f"   ⚠️  Failed to remove {audio_file}: {e}")
        
        self.audio_files_to_cleanup.clear()
    
    async def run(self) -> None:
        """Main conversation loop with enhanced error handling"""
        print("\n" + "="*70)
        print("🎤 Murf AI Voice Agent - Techfest IIT Bombay Hackathon")
        print("="*70)
        print("\nWelcome! I'm your AI voice assistant.")
        print("\n🔊 Powered by:")
        print("   • Murf Falcon TTS (Text-to-Speech) - Consistently fastest TTS API")
        print("   • Deepgram Nova-2 ASR (Speech Recognition)")
        
        if self.perplexity_client:
            print("   • Perplexity AI (Intelligent Responses)")
        
        print("\n💡 Tips:")
        print("   • Speak clearly and naturally")
        print("   • Say 'goodbye' or 'bye' to exit")
        print("   • Conversations are automatically logged to conversation_log.txt")
        print()
        
        # Log session start
        self._log_conversation("System", "=" * 50)
        self._log_conversation("System", "New conversation session started")
        self._log_conversation("System", "=" * 50)
        
        # Initial greeting
        greeting = "Hello! I'm your AI voice assistant powered by Murf Falcon. How can I help you today?"
        self.speak_with_murf(greeting)
        
        self.is_running = True
        
        try:
            while self.is_running:
                try:
                    # Listen for user input
                    user_input = await self.listen_with_deepgram()
                    
                    if not user_input:
                        print("⚠️  No input detected. Please try speaking again.")
                        continue
                    
                    # Check for exit commands
                    exit_words = ['goodbye', 'bye', 'exit', 'quit', 'stop']
                    if any(word in user_input.lower() for word in exit_words):
                        farewell = "Goodbye! It was nice talking to you. Thank you for using Murf Falcon!"
                        self.speak_with_murf(farewell)
                        self.is_running = False
                        break
                    
                    # Generate response
                    ai_response = self.generate_response(user_input)
                    
                    # Speak response
                    if ai_response:
                        self.speak_with_murf(ai_response)
                    else:
                        print("⚠️  Failed to generate response. Please try again.")
                    
                except KeyboardInterrupt:
                    print("\n\n⚠️  Interrupted by user")
                    interrupt_msg = "Goodbye! Conversation interrupted."
                    self.speak_with_murf(interrupt_msg)
                    self.is_running = False
                    break
                    
                except Exception as e:
                    print(f"\n❌ Error in conversation loop: {e}")
                    print("Continuing to next interaction...")
                    continue
        
        finally:
            # Log session end
            self._log_conversation("System", "=" * 50)
            self._log_conversation("System", "Conversation session ended")
            self._log_conversation("System", "=" * 50 + "\n")
            
            # Clean up resources
            self._cleanup_resources()
            
            print("\n" + "="*70)
            print("👋 Voice agent stopped. Thank you for using Murf Falcon TTS!")
            print("="*70)
            
            if self.config.LOG_CONVERSATIONS:
                print(f"\n📝 Conversation log saved to: {self.config.LOG_FILE}")
                print("   Use this log for your demo video!\n")


def main():
    """Entry point with comprehensive error handling"""
    try:
        print("\n🚀 Initializing Murf AI Voice Agent...\n")
        agent = VoiceAgent()
        
        print("✅ Initialization complete!\n")
        asyncio.run(agent.run())
        
    except ValueError as e:
        print(f"\n❌ Configuration Error: {e}")
        print("\nPlease check your .env file and ensure all required API keys are present.")
        sys.exit(1)
        
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
        sys.exit(0)
        
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        print("\nPlease check the error message above and try again.")
        print("If the issue persists, ensure all dependencies are installed:")
        print("   pip install -r requirements.txt\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
