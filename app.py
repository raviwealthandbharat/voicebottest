import asyncio
import websockets
import json
import io
import os
import google.generativeai as genai
from gtts import gTTS
from pydub import AudioSegment
import speech_recognition as sr
from dotenv import load_dotenv

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Initialize Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-pro-latest")

recognizer = sr.Recognizer()

async def handle_call(websocket, path):
    print("🎧 Client connected")
    try:
        async for message in websocket:
            print("📥 Received audio")

            # Convert binary to AudioData
            try:
                audio_data = sr.AudioData(message, sample_rate=8000, sample_width=2)
                user_text = recognizer.recognize_google(audio_data)
                print(f"🗣️ User: {user_text}")
            except Exception as e:
                user_text = "Sorry, I couldn't understand you."
                print("Recognition error:", e)

            # Get Gemini Response
            try:
                response = model.generate_content(user_text)
                reply = response.text.strip()
            except Exception as e:
                reply = f"Sorry, there was an error: {str(e)}"
            print(f"🤖 Bot: {reply}")

            # Convert reply to audio
            try:
                tts = gTTS(reply)
                tts_fp = io.BytesIO()
                tts.write_to_fp(tts_fp)
                tts_fp.seek(0)

                audio = AudioSegment.from_file(tts_fp, format="mp3")
                audio = audio.set_frame_rate(8000).set_channels(1)
                raw_audio = audio.raw_data

                await websocket.send(raw_audio)
                print("📤 Sent audio response")
            except Exception as e:
                print("TTS error:", e)

    except websockets.exceptions.ConnectionClosed:
        print("🔌 Client disconnected")

# Start WebSocket server
start_server = websockets.serve(handle_call, "0.0.0.0", 10000)

print("🚀 Voicebot Gemini server running on ws://0.0.0.0:10000")
asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
