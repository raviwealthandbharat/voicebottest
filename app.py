import asyncio
import websockets
import os
import io
import google.generativeai as genai
from gtts import gTTS
from pydub import AudioSegment
import tempfile
import subprocess
from dotenv import load_dotenv
import wave

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-pro")

# Convert raw PCM to text using whisper or vosk/sphinx
def transcribe_audio(raw_bytes):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_wav:
        with wave.open(tmp_wav.name, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(8000)
            wf.writeframes(raw_bytes)

        try:
            import speech_recognition as sr
            r = sr.Recognizer()
            with sr.AudioFile(tmp_wav.name) as source:
                audio = r.record(source)
                text = r.recognize_google(audio)
                return text
        except Exception as e:
            print("Speech recognition failed:", e)
            return ""

# Convert text to 8kHz signed-integer mono PCM
def synthesize_speech(text):
    try:
        tts = gTTS(text)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as mp3_fp:
            tts.save(mp3_fp.name)

        sound = AudioSegment.from_mp3(mp3_fp.name)
        sound = sound.set_channels(1).set_frame_rate(8000)

        with tempfile.NamedTemporaryFile(delete=False, suffix=".raw") as raw_fp:
            sound.export(raw_fp.name, format="raw", codec="pcm_s16le")
            return open(raw_fp.name, "rb").read()

    except Exception as e:
        print("TTS error:", e)
        return b''

# Main handler
async def handle(websocket, path):
    print("✅ Client connected (Exotel)")

    buffer = b''
    goodbye_sent = False

    try:
        async for message in websocket:
            buffer += message
            if len(buffer) < 16000:  # ~1 second (20ms * 50 = 1s)
                continue

            user_text = transcribe_audio(buffer)
            buffer = b''  # Clear buffer

            print("🗣️ Heard:", user_text)

            if not user_text.strip():
                continue

            gemini_response = model.generate_content(user_text)
            bot_reply = gemini_response.text.strip()
            print("🤖 Reply:", bot_reply)

            audio = synthesize_speech(bot_reply)

            if audio:
                await websocket.send(audio)

            if "goodbye" in bot_reply.lower() or "thank you" in bot_reply.lower():
                goodbye_sent = True
                break

    except websockets.exceptions.ConnectionClosed:
        print("❌ Exotel disconnected")

    if goodbye_sent:
        await websocket.close()
        print("👋 Session ended")

# Start async server
async def main():
    async with websockets.serve(handle, "0.0.0.0", 10000):
        print("🚀 Exotel Voicebot running on ws://0.0.0.0:10000")
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
