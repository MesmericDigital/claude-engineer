import os
import shutil
import asyncio
import subprocess
import io
import base64
import websockets
import json
from PIL import Image
from pydub import AudioSegment
from pydub.playback import play

def is_installed(lib_name):
    return shutil.which(lib_name) is not None

async def text_chunker(text: str) -> AsyncIterable[str]:
    """Split text into chunks, ensuring to not break sentences."""
    splitters = (".", ",", "?", "!", ";", ":", "—", "-", "(", ")", "[", "]", "}", " ")
    buffer = ""
    
    for char in text:
        if buffer.endswith(splitters):
            yield buffer + " "
            buffer = char
        elif char in splitters:
            yield buffer + char + " "
            buffer = ""
        else:
            buffer += char

    if buffer:
        yield buffer + " "

async def stream_audio(audio_stream):
    """Stream audio data using mpv player."""
    if not is_installed("mpv"):
        console.print("mpv not found. Installing alternative audio playback...", style="bold yellow")
        # Fall back to pydub playback if mpv is not available
        audio_data = b''.join([chunk async for chunk in audio_stream])
        audio = AudioSegment.from_mp3(io.BytesIO(audio_data))
        play(audio)
        return

    mpv_process = subprocess.Popen(
        ["mpv", "--no-cache", "--no-terminal", "--", "fd://0"],
        stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )

    console.print("Started streaming audio", style="bold green")
    try:
        async for chunk in audio_stream:
            if chunk:
                mpv_process.stdin.write(chunk)
                mpv_process.stdin.flush()
    except Exception as e:
        console.print(f"Error during audio streaming: {str(e)}", style="bold red")
    finally:
        if mpv_process.stdin:
            mpv_process.stdin.close()
        mpv_process.wait()
