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
import google.generativeai as genai

# Load environment variables
load_dotenv()


class Config:
    """Configuration class for API keys and settings"""

    MURF_API_KEY: str = os.getenv('MURF_API_KEY', '')
    DEEPGRAM_API_KEY: str = os.getenv('DEEPGRAM_API_KEY', '')
    GEMINI_API_KEY: str = os.getenv('GEMINI_API_KEY', '')
    
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
        self.conversation_history: List[str] = []
        self.is_running: bool = False
        self.input_mode: str = 'voice'  # 'voice' or 'text'
        self.deepgram_client: Optional[DeepgramClient] = None
        self.gemini_model = None
        self.audio_files_to_cleanup: List[str] = []

        # Validate API keys
        self._validate_config()

        # Initialize clients
        if self.config.DEEPGRAM_API_KEY:
            self.deepgram_client = DeepgramClient(self.config.DEEPGRAM_API_KEY)

        if self.config.GEMINI_API_KEY:
            genai.configure(api_key=self.config.GEMINI_API_KEY)
            self.gemini_model = genai.GenerativeModel('gemini-1.5-flash')
            print("✓ Gemini AI enabled for intelligent responses")
        else:
            print("⚠️  Gemini AI not configured - using fallback responses")
    
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
            'api-key': self.config.MURF_API_KEY,
            'Content-Type': 'application/json',
        }
        
        payload = {
            'voiceId': self.config.VOICE_ID,
            'text': text,
            'format': 'wav',
            'sampleRate': 16000,
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

            # Parse JSON response
            json_response = response.json()
            if 'audioFile' not in json_response:
                print("❌ No audioFile in response")
                return False

            audio_url = json_response['audioFile']
            print(f"📥 Downloading audio from: {audio_url[:50]}...")

            # Download the actual audio file
            audio_response = requests.get(audio_url, timeout=30)
            audio_response.raise_for_status()

            # Save audio file
            audio_file = f'output_{datetime.now().strftime("%Y%m%d_%H%M%S")}.mp3'
            self.audio_files_to_cleanup.append(audio_file)

            with open(audio_file, 'wb') as f:
                f.write(audio_response.content)

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
                    print(f"Response status: {e.response.status_code}")
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
        """Play audio file using system audio player (supports MP3)"""
        try:
            import subprocess
            import platform

            if platform.system() == 'Darwin':  # macOS
                subprocess.run(['afplay', audio_file], check=True)
            elif platform.system() == 'Linux':
                subprocess.run(['aplay', audio_file], check=True)  # or 'mpg123' for MP3
            elif platform.system() == 'Windows':
                # For Windows, could use winsound or another player
                print(f"⚠️ Audio playback not implemented for Windows. File saved: {audio_file}")
            else:
                print(f"⚠️ Audio playback not supported on this platform. File saved: {audio_file}")

        except subprocess.CalledProcessError as e:
            print(f"❌ Error playing audio: {e}")
        except FileNotFoundError:
            print(f"❌ Audio player not found. File saved: {audio_file}")
        except Exception as e:
            print(f"❌ Error playing audio: {e}")
    
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
        Generate intelligent response using Google Gemini AI
        Falls back to simple responses if API not available

        Args:
            user_input: User's spoken input

        Returns:
            str: Generated response
        """
        if self.gemini_model:
            try:
                print("💭 Thinking...")

                # Create conversation history for Gemini
                history = []
                for msg in self.conversation_history[-self.config.MAX_HISTORY_LENGTH:]:
                    if msg.startswith("User: "):
                        history.append({"role": "user", "parts": [msg[6:]]})
                    elif msg.startswith("Agent: "):
                        history.append({"role": "model", "parts": [msg[7:]]})

                # Add current user input
                history.append({"role": "user", "parts": [user_input]})

                # Create chat session with history
                chat = self.gemini_model.start_chat(history=history[:-1])  # Exclude current message

                # Generate response
                response = chat.send_message(
                    user_input,
                    generation_config=genai.types.GenerationConfig(
                        temperature=0.7,
                        max_output_tokens=150,
                    )
                )

                ai_response = response.text.strip()

                # Add to conversation history
                self.conversation_history.append(f"User: {user_input}")
                self.conversation_history.append(f"Agent: {ai_response}")

                # Keep conversation history manageable
                if len(self.conversation_history) > self.config.MAX_HISTORY_LENGTH * 2:
                    self.conversation_history = self.conversation_history[-self.config.MAX_HISTORY_LENGTH * 2:]

                return ai_response

            except Exception as e:
                print(f"⚠️  Gemini API error: {e}")
                return self._fallback_response(user_input)
        else:
            return self._fallback_response(user_input)
    
    def _fallback_response(self, user_input: str) -> str:
        """Smart fallback responses with conversation context"""
        user_input_lower = user_input.lower()

        # Check for specific keywords and patterns
        if any(word in user_input_lower for word in ["hello", "hi", "hey"]):
            return "Hello! I'm your AI voice assistant powered by Murf Falcon. How can I help you today?"

        if "how are you" in user_input_lower:
            return "I'm doing great! I'm excited to chat with you. What's on your mind?"

        if any(word in user_input_lower for word in ["name", "who are you"]):
            return "I'm your friendly AI voice assistant, built for the Techfest hackathon using Murf Falcon TTS!"

        if any(word in user_input_lower for word in ["help", "what can you do"]):
            return "I can have natural conversations with you! I use Google's Gemini AI for smart responses and Murf Falcon for voice synthesis."

        if any(word in user_input_lower for word in ["thank", "thanks"]):
            return "You're very welcome! I'm here whenever you need to chat."

        if any(word in user_input_lower for word in ["bye", "goodbye", "see you"]):
            return "Goodbye! It was great talking with you. Come back anytime!"

        # Check conversation history for context
        if len(self.conversation_history) > 0:
            # Look for repeated questions or patterns
            recent_messages = [msg.split(": ")[1] if ": " in msg else msg for msg in self.conversation_history[-4:] if msg.startswith("User:")]
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
    
    def get_text_input(self) -> str:
        """
        Get text input from user via keyboard

        Returns:
            str: User's text input
        """
        print("\n📝 Type your message (or 'quit' to exit):")
        try:
            user_input = input("> ").strip()
            if user_input:
                print(f"You: {user_input}")
                self._log_conversation("User", user_input)
            return user_input
        except (EOFError, KeyboardInterrupt):
            return "quit"

    def select_input_mode(self) -> str:
        """
        Ask user to select input mode (voice or text)

        Returns:
            str: Selected mode ('voice' or 'text')
        """
        print("\n" + "="*50)
        print("🎯 Choose Your Input Method")
        print("="*50)
        print("1. 🎤 Voice Input (speak to the assistant)")
        print("2. 📝 Text Input (type your messages)")
        print()

        while True:
            try:
                choice = input("Enter 1 for Voice or 2 for Text: ").strip()
                if choice == '1':
                    print("✅ Voice mode selected!")
                    return 'voice'
                elif choice == '2':
                    print("✅ Text mode selected!")
                    return 'text'
                else:
                    print("❌ Please enter 1 or 2")
            except (EOFError, KeyboardInterrupt):
                print("✅ Defaulting to voice mode")
                return 'voice'

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

        if self.gemini_model:
            print("   • Google Gemini AI (Intelligent Responses)")

        print("\n💡 Features:")
        print("   • Choose between voice or text input")
        print("   • Always get voice responses")
        print("   • Conversations are automatically logged")

        # Select input mode
        self.input_mode = self.select_input_mode()

        # Log session start
        self._log_conversation("System", "=" * 50)
        self._log_conversation("System", f"New conversation session started - Mode: {self.input_mode}")
        self._log_conversation("System", "=" * 50)

        # Initial greeting
        greeting = "Hello! I'm your AI voice assistant powered by Murf Falcon. How can I help you today?"
        self.speak_with_murf(greeting)

        self.is_running = True

        try:
            while self.is_running:
                try:
                    # Get user input based on selected mode
                    if self.input_mode == 'voice':
                        user_input = await self.listen_with_deepgram()
                        if not user_input:
                            print("⚠️  No input detected. Please try speaking again.")
                            continue
                    else:  # text mode
                        user_input = self.get_text_input()
                        if not user_input:
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

                    # Always speak response (voice output)
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
