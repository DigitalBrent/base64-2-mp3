import base64, os, subprocess, tempfile
from pathlib import Path
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

class AudioIn(BaseModel):
    audio_base64: str
    extension: str | None = "wav"

class AudioOut(BaseModel):
    audio_mp3_base64: str
    mime_type: str = "audio/mpeg"
    file_name: str = "converted.mp3"

@app.post("/to-mp3", response_model=AudioOut)
def convert_audio(data: AudioIn):
    b64 = "".join(data.audio_base64.split()).split(",")[-1]
    if (pad := len(b64) % 4):
        b64 += "=" * (4 - pad)
    try:
        raw = base64.b64decode(b64)
    except Exception:
        raise HTTPException(400, "Invalid Base-64")

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp = Path(tmp_dir)
        src = tmp / f"input.{data.extension}"
        dst = tmp / "output.mp3"
        src.write_bytes(raw)

        cmd = [
            "ffmpeg", "-y", "-loglevel", "error",
            "-i", src, "-codec:a", "libmp3lame", "-qscale:a", "2", dst
        ]
        try:
            subprocess.run(cmd, check=True)
        except subprocess.CalledProcessError as e:
            raise HTTPException(500, f"FFmpeg error → {e.stderr}") from e

        mp3_b64 = base64.b64encode(dst.read_bytes()).decode()

    return AudioOut(audio_mp3_base64=mp3_b64)
