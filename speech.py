import os
import speech_recognition as sr
import websockets
import json
import base64
import io
from PIL import Image
from pydub import AudioSegment
from pydub.playback import play
import asyncio
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize recognizer and microphone as None
recognizer = None
microphone = None

# 11 Labs TTS
tts_enabled = True
use_tts = False
ELEVEN_LABS_API_KEY = os.getenv('ELEVEN_LABS_API_KEY')
VOICE_ID = 'YOUR VOICE ID'
MODEL_ID = 'eleven_turbo_v2_5'

def initialize_speech_recognition():
    global recognizer, microphone
    recognizer = sr.Recognizer()
    microphone = sr.Microphone()
    
    # Adjust for ambient noise
    with microphone as source:
        recognizer.adjust_for_ambient_noise(source, duration=1)
    
    logging.info("Speech recognition initialized")

async def voice_input(max_retries=3):
    global recognizer, microphone

    for attempt in range(max_retries):
        # Reinitialize speech recognition objects before each attempt
        initialize_speech_recognition()

        try:
            with microphone as source:
                console.print("Listening... Speak now.", style="bold green")
                audio = recognizer.listen(source, timeout=5)
                
            console.print("Processing speech...", style="bold yellow")
            text = recognizer.recognize_google(audio)
            console.print(f"You said: {text}", style="cyan")
            return text.lower()
        except sr.WaitTimeoutError:
            console.print(f"No speech detected. Attempt {attempt + 1} of {max_retries}.", style="bold red")
            logging.warning(f"No speech detected. Attempt {attempt + 1} of {max_retries}")
        except sr.UnknownValueError:
            console.print(f"Speech was unintelligible. Attempt {attempt + 1} of {max_retries}.", style="bold red")
            logging.warning(f"Speech was unintelligible. Attempt {attempt + 1} of {max_retries}")
        except sr.RequestError as e:
            console.print(f"Could not request results from speech recognition service; {e}", style="bold red")
            logging.error(f"Could not request results from speech recognition service; {e}")
            return None
        except Exception as e:
            console.print(f"Unexpected error in voice input: {str(e)}", style="bold red")
            logging.error(f"Unexpected error in voice input: {str(e)}")
            return None
        
        # Add a short delay between attempts
        await asyncio.sleep(1)
    
    console.print("Max retries reached. Returning to text input mode.", style="bold red")
    logging.info("Max retries reached in voice input. Returning to text input mode.")
    return None

def cleanup_speech_recognition():
    global recognizer, microphone
    recognizer = None
    microphone = None
    logging.info('Speech recognition objects cleaned up')

async def text_to_speech(text):
    if not ELEVEN_LABS_API_KEY:
        console.print("ElevenLabs API key not found. Text-to-speech is disabled.", style="bold yellow")
        console.print(text)
        return

    uri = f"wss://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}/stream-input?model_id={MODEL_ID}"
    
    try:
        async with websockets.connect(uri, extra_headers={'xi-api-key': ELEVEN_LABS_API_KEY}) as websocket:
            # Send initial message
            await websocket.send(json.dumps({
                "text": " ",
                "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
                "xi_api_key": ELEVEN_LABS_API_KEY,
            }))

            # Set up listener for audio chunks
            async def listen():
                while True:
                    try:
                        message = await websocket.recv()
                        data = json.loads(message)
                        if data.get("audio"):
                            yield base64.b64decode(data["audio"])
                        elif data.get('isFinal'):
                            break
                    except websockets.exceptions.ConnectionClosed:
                        logging.error("WebSocket connection closed unexpectedly")
                        break
                    except Exception as e:
                        logging.error(f"Error processing audio message: {str(e)}")
                        break

            # Start audio streaming task
            stream_task = asyncio.create_task(stream_audio(listen()))

            # Send text in chunks
            async for chunk in text_chunker(text):
                try:
                    await websocket.send(json.dumps({"text": chunk, "try_trigger_generation": True}))
                except Exception as e:
                    logging.error(f"Error sending text chunk: {str(e)}")
                    break

            # Send closing message
            await websocket.send(json.dumps({"text": ""}))

            # Wait for streaming to complete
            await stream_task

    except websockets.exceptions.InvalidStatusCode as e:
        logging.error(f"Failed to connect to ElevenLabs API: {e}")
        console.print(f"Failed to connect to ElevenLabs API: {e}", style="bold red")
        console.print("Fallback: Printing the text instead.", style="bold yellow")
        console.print(text)
    except Exception as e:
        logging.error(f"Error in text-to-speech: {str(e)}")
        console.print(f"Error in text-to-speech: {str(e)}", style="bold red")
        console.print("Fallback: Printing the text instead.", style="bold yellow")
        console.print(text)
