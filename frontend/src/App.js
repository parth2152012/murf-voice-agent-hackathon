import { useState, useEffect, useRef } from 'react';
import io from 'socket.io-client';
import './App.css';

const socket = io('http://localhost:5000');

function App() {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isConnected, setIsConnected] = useState(false);
  const [isTyping, setIsTyping] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [inputMode, setInputMode] = useState('text'); // 'text' or 'voice'
  const [audioEnabled, setAudioEnabled] = useState(false);
  const [sessionId] = useState(() => Math.random().toString(36).substring(7));
  const messagesEndRef = useRef(null);
  const recognitionRef = useRef(null);
  const audioContextRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    // Initialize speech recognition
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      recognitionRef.current = new SpeechRecognition();
      recognitionRef.current.continuous = false;
      recognitionRef.current.interimResults = false;
      recognitionRef.current.lang = 'en-US';

      recognitionRef.current.onstart = () => {
        setIsRecording(true);
        console.log('Voice recognition started');
      };

      recognitionRef.current.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        setInputMessage(transcript);
        setIsRecording(false);
        console.log('Voice recognition result:', transcript);

        // Auto-send the message after a short delay
        setTimeout(() => {
          if (transcript.trim()) {
            setIsTyping(true);

            // Add user message immediately
            const userMessage = {
              id: Date.now(),
              user: transcript.trim(),
              timestamp: new Date().toISOString()
            };
            setMessages(prev => [...prev, userMessage]);

            // Send via WebSocket
            socket.emit('send_message', {
              message: transcript.trim(),
              session_id: sessionId
            });

            // Clear input after sending
            setInputMessage('');
          }
        }, 500); // Small delay to show the transcript briefly
      };

      recognitionRef.current.onerror = (event) => {
        console.error('Speech recognition error:', event.error);
        setIsRecording(false);
      };

      recognitionRef.current.onend = () => {
        setIsRecording(false);
        console.log('Voice recognition ended');
      };
    }

    // Socket connection
    socket.on('connect', () => {
      setIsConnected(true);
      console.log('Connected to server');
    });

    socket.on('disconnect', () => {
      setIsConnected(false);
      console.log('Disconnected from server');
    });

    socket.on('message_response', (data) => {
      setIsTyping(false);
      const messageId = Date.now();
      const newMessage = {
        id: messageId,
        user: data.user_message,
        ai: data.ai_response,
        speech: data.speech,
        timestamp: data.timestamp
      };
      setMessages(prev => [...prev, newMessage]);

      // Auto-play audio if available
      if (data.speech && data.speech.success && data.speech.audio_url) {
        playAudio(data.speech.audio_url, messageId);
      }
    });

    socket.on('error', (data) => {
      console.error('Socket error:', data.message);
      setIsTyping(false);
    });

    return () => {
      socket.off('connect');
      socket.off('disconnect');
      socket.off('message_response');
      socket.off('error');
      if (recognitionRef.current) {
        recognitionRef.current.stop();
      }
    };
  }, []);

  const enableAudio = async () => {
    try {
      // Create audio context to enable audio playback
      if (!audioContextRef.current) {
        audioContextRef.current = new (window.AudioContext || window.webkitAudioContext)();
      }

      // Resume audio context if suspended
      if (audioContextRef.current.state === 'suspended') {
        await audioContextRef.current.resume();
      }

      setAudioEnabled(true);
      console.log('Audio enabled successfully');
    } catch (error) {
      console.error('Error enabling audio:', error);
    }
  };

  const playAudio = async (audioUrl, messageId) => {
    try {
      // Enable audio context first
      await enableAudio();

      const audio = new Audio(audioUrl);
      audio.volume = 0.8; // Set volume to 80%

      // Add event listeners
      audio.onplay = () => {
        console.log('Audio started playing');
        // Update message to show audio is playing
        setMessages(prev => prev.map(msg =>
          msg.id === messageId ? { ...msg, audioPlaying: true } : msg
        ));
      };

      audio.onended = () => {
        console.log('Audio finished playing');
        // Update message to show audio finished
        setMessages(prev => prev.map(msg =>
          msg.id === messageId ? { ...msg, audioPlaying: false, audioPlayed: true } : msg
        ));
      };

      audio.onerror = (error) => {
        console.error('Audio playback error:', error);
        // Mark as failed to play
        setMessages(prev => prev.map(msg =>
          msg.id === messageId ? { ...msg, audioError: true } : msg
        ));
      };

      // Try to play the audio
      const playPromise = audio.play();

      if (playPromise !== undefined) {
        playPromise
          .then(() => {
            console.log('Audio started playing successfully');
          })
          .catch(error => {
            console.warn('Audio playback blocked:', error);
            // Mark as blocked - user can click to play manually
            setMessages(prev => prev.map(msg =>
              msg.id === messageId ? { ...msg, audioBlocked: true } : msg
            ));
          });
      }
    } catch (error) {
      console.error('Error creating audio:', error);
    }
  };

  const playAudioManually = (audioUrl, messageId) => {
    const audio = new Audio(audioUrl);
    audio.volume = 0.8;

    audio.onplay = () => {
      setMessages(prev => prev.map(msg =>
        msg.id === messageId ? { ...msg, audioPlaying: true, audioBlocked: false } : msg
      ));
    };

    audio.onended = () => {
      setMessages(prev => prev.map(msg =>
        msg.id === messageId ? { ...msg, audioPlaying: false, audioPlayed: true } : msg
      ));
    };

    audio.play().catch(console.error);
  };

  const sendMessage = async (e) => {
    e.preventDefault();
    if (!inputMessage.trim()) return;

    const message = inputMessage.trim();
    setInputMessage('');
    setIsTyping(true);

    // Add user message immediately
    const userMessage = {
      id: Date.now(),
      user: message,
      timestamp: new Date().toISOString()
    };
    setMessages(prev => [...prev, userMessage]);

    // Send via WebSocket
    socket.emit('send_message', {
      message: message,
      session_id: sessionId
    });
  };

  const startVoiceRecording = () => {
    if (recognitionRef.current && !isRecording) {
      try {
        recognitionRef.current.start();
      } catch (error) {
        console.error('Error starting voice recognition:', error);
      }
    }
  };

  const stopVoiceRecording = () => {
    if (recognitionRef.current && isRecording) {
      recognitionRef.current.stop();
    }
  };

  const toggleVoiceRecording = async () => {
    // Enable audio on first user interaction
    if (!audioEnabled) {
      await enableAudio();
    }

    if (isRecording) {
      stopVoiceRecording();
    } else {
      startVoiceRecording();
    }
  };

  const formatTime = (timestamp) => {
    return new Date(timestamp).toLocaleTimeString([], {
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <div className="App">
      <div className="chat-container">
        {/* Header */}
        <div className="chat-header">
          <div className="header-content">
            <h1>🎤 Murf AI Voice Agent</h1>
            <div className="status">
              <span className={`status-dot ${isConnected ? 'connected' : 'disconnected'}`}></span>
              <span>{isConnected ? 'Connected' : 'Disconnected'}</span>
            </div>
          </div>
          <div className="powered-by">
            <span>Powered by Murf Falcon TTS • Deepgram ASR • Google Gemini</span>
          </div>
        </div>

        {/* Messages */}
        <div className="messages-container">
          <div className="messages">
            {messages.length === 0 && (
              <div className="welcome-message">
                <div className="welcome-content">
                  <h2>Welcome to Murf AI Voice Agent! 🎉</h2>
                  <p>Click the microphone to speak naturally, or type your message. AI responses are spoken aloud using Murf Falcon TTS.</p>
                  <div className="features">
                    <div className="feature">
                      <span className="emoji">🎤</span>
                      <span>Voice Input</span>
                    </div>
                    <div className="feature">
                      <span className="emoji">🔊</span>
                      <span>Voice Output</span>
                    </div>
                    <div className="feature">
                      <span className="emoji">🤖</span>
                      <span>AI Conversations</span>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {messages.map((msg) => (
              <div key={msg.id} className="message-group">
                {/* User Message */}
                <div className="message user-message">
                  <div className="message-content">
                    <div className="message-text">{msg.user}</div>
                    <div className="message-time">{formatTime(msg.timestamp)}</div>
                  </div>
                  <div className="avatar user-avatar">👤</div>
                </div>

                {/* AI Response */}
                {msg.ai && (
                  <div className="message ai-message">
                    <div className="avatar ai-avatar">🎤</div>
                    <div className="message-content">
                      <div className="message-text">{msg.ai}</div>
                      <div className="message-time">{formatTime(msg.timestamp)}</div>
                      {msg.speech && msg.speech.success && (
                        <div className="audio-indicator">
                          {msg.audioPlaying ? (
                            <>
                              <span className="audio-icon">🔊</span>
                              <span>Playing...</span>
                            </>
                          ) : msg.audioPlayed ? (
                            <>
                              <span className="audio-icon">✅</span>
                              <span>Played</span>
                            </>
                          ) : msg.audioBlocked ? (
                            <button
                              className="play-audio-button"
                              onClick={() => playAudioManually(msg.speech.audio_url, msg.id)}
                              title="Click to play audio"
                            >
                              <span className="audio-icon">🔊</span>
                              <span>Click to play</span>
                            </button>
                          ) : msg.audioError ? (
                            <>
                              <span className="audio-icon">❌</span>
                              <span>Playback failed</span>
                            </>
                          ) : (
                            <>
                              <span className="audio-icon">🔊</span>
                              <span>Audio played</span>
                            </>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            ))}

            {/* Typing Indicator */}
            {isTyping && (
              <div className="message ai-message">
                <div className="avatar ai-avatar">🎤</div>
                <div className="message-content">
                  <div className="typing-indicator">
                    <span></span>
                    <span></span>
                    <span></span>
                  </div>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>
        </div>

        {/* Input */}
        <div className="input-container">
          <form onSubmit={sendMessage} className="input-form">
            <div className="input-wrapper">
              <button
                type="button"
                className={`mic-button ${isRecording ? 'recording' : ''}`}
                onClick={toggleVoiceRecording}
                disabled={!isConnected || !recognitionRef.current}
                title="Click to speak"
              >
                <span className="mic-icon">{isRecording ? '🎙️' : '🎤'}</span>
              </button>
              <input
                type="text"
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                placeholder={isRecording ? "Listening..." : "Type your message or click the mic to speak..."}
                className={`message-input ${isRecording ? 'recording' : ''}`}
                disabled={!isConnected}
              />
              <button
                type="submit"
                className="send-button"
                disabled={!inputMessage.trim() || !isConnected}
              >
                <span className="send-icon">📤</span>
                <span className="send-text">Send</span>
              </button>
            </div>
          </form>
          <div className="input-footer">
            <span>Built for Techfest IIT Bombay Hackathon • "Built using Murf Falcon – the consistently fastest TTS API"</span>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
