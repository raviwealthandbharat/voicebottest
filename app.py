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

            try:
                audio_data = sr.AudioData(message, sample_rate=8000, sample_width=2)
                user_text = recognizer.recognize_google(audio_data)
                print(f"🗣️ User: {user_text}")
            except Exception as e:
                user_text = "Sorry, I couldn't understand you."
                print("Recognition error:", e)

            try:
                response = model.generate_content(user_text)
                reply = response.text.strip()
            except Exception as e:
                reply = f"Sorry, there was an error: {str(e)}"
            print(f"🤖 Bot: {reply}")

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

async def main():
    print("🚀 Starting Voicebot server on ws://0.0.0.0:10000")
    async with websockets.serve(handle_call, "0.0.0.0", 10000):
        await asyncio.Future()  # Run forever

if __name__ == "__main__":
    asyncio.run(main())
