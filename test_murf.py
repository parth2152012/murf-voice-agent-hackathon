#!/usr/bin/env python3
"""
Test script for Murf API
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

MURF_API_KEY = os.getenv('MURF_API_KEY')
MURF_API_URL = 'https://api.murf.ai/v1/speech/generate'

headers = {
    'api-key': MURF_API_KEY,
    'Content-Type': 'application/json',
}

payload = {
    'voiceId': 'en-US-terrell',
    'text': 'Hello world, its a mee mario',
    'format': 'mp3',
    'sampleRate': 24000,
}

print("Testing Murf API...")
print(f"API Key: {MURF_API_KEY[:10]}...")
print(f"Payload: {payload}")

try:
    response = requests.post(
        MURF_API_URL,
        headers=headers,
        json=payload,
        timeout=30
    )

    print(f"Status Code: {response.status_code}")
    print(f"Response Headers: {dict(response.headers)}")

    if response.status_code == 200:
        print("✅ Success!")
        print(f"Response size: {len(response.content)} bytes")
        print(f"Raw response: {response.text[:200]}...")

        try:
            json_response = response.json()
            print(f"JSON response: {json_response}")

            if 'audioFile' in json_response:
                audio_url = json_response['audioFile']
                print(f"Audio URL: {audio_url}")

                # Download the actual audio file
                audio_response = requests.get(audio_url)
                if audio_response.status_code == 200:
                    with open('test_audio.wav', 'wb') as f:
                        f.write(audio_response.content)

                    # Check file header
                    with open('test_audio.wav', 'rb') as f:
                        header = f.read(12)
                        print(f"File header: {header}")
                        if header.startswith(b'RIFF'):
                            print("✅ This is a WAV file")
                        elif header.startswith(b'ID3') or header[0:2] == b'\xff\xfb':
                            print("⚠️ This is an MP3 file")
                        else:
                            print("❓ Unknown format")
                else:
                    print(f"Failed to download audio: {audio_response.status_code}")
            else:
                print("No audioFile in response")
        except Exception as e:
            print(f"Failed to parse JSON: {e}")
    else:
        print("❌ Error!")
        print(f"Response: {response.text}")

except Exception as e:
    print(f"❌ Exception: {e}")
