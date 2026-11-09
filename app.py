import os, re, json, uuid, shutil, subprocess
from pathlib import Path
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, HttpUrl
import yt_dlp
from openai import OpenAI

ROOT = Path(__file__).parent
WORK = ROOT / "work"
WORK.mkdir(exist_ok=True)
app = FastAPI(title="Viral Clipper Pro")
app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")

class ClipRequest(BaseModel):
    url: HttpUrl
    clips: int = 3

def run(cmd):
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode:
        raise RuntimeError((p.stderr or p.stdout)[-2500:])
    return p.stdout

@app.get("/")
def home():
    return FileResponse(ROOT / "static" / "index.html")

@app.get("/health")
def health():
    return {"ok": True}

@app.post("/api/clip")
def create_clips(data: ClipRequest):
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(500, "Falta configurar OPENAI_API_KEY en el servidor.")
    job = uuid.uuid4().hex[:10]
    folder = WORK / job
    folder.mkdir(parents=True)
    source = folder / "source.mp4"
    try:
        opts = {
            "format": "bv*[ext=mp4]+ba[ext=m4a]/b[ext=mp4]/best",
            "outtmpl": str(source),
            "merge_output_format": "mp4",
            "noplaylist": True,
            "quiet": True,
            "no_warnings": True,
        }
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([str(data.url)])
        if not source.exists():
            candidates = list(folder.glob("source.*"))
            if not candidates:
                raise RuntimeError("No se pudo descargar el video.")
            source = candidates[0]
        audio = folder / "audio.mp3"
        run(["ffmpeg", "-y", "-i", str(source), "-vn", "-ac", "1", "-ar", "16000", str(audio)])
        client = OpenAI(api_key=api_key)
        with open(audio, "rb") as f:
            transcript = client.audio.transcriptions.create(model="whisper-1", file=f, response_format="verbose_json")
        duration = float(getattr(transcript, "duration", 0) or 0)
        segments = getattr(transcript, "segments", []) or []
        text = " ".join((getattr(s, "text", "") or "") for s in segments)
        if not text.strip():
            raise RuntimeError("No se pudo obtener una transcripción útil.")
        prompt = (
            "Selecciona hasta " + str(max(1, min(data.clips, 5))) +
            " momentos atractivos para clips verticales. Devuelve SOLO JSON: "
            '{"clips":[{"start":0,"end":30,"title":"...","reason":"...","score":85}]} '
            "Los tiempos deben estar dentro de la duración del video y cada clip durar 15 a 60 segundos. "
            "Transcripción: " + text[:18000]
        )
        result = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role":"user","content":prompt}],
            response_format={"type":"json_object"},
            temperature=0.3
        )
        chosen = json.loads(result.choices[0].message.content).get("clips", [])
        output = []
        for i, c in enumerate(chosen[:5], 1):
            start = max(0, float(c.get("start", 0)))
            end = min(duration or start + 60, float(c.get("end", start + 30)))
            if end - start < 5:
                continue
            target = folder / f"clip_{i}.mp4"
            run([
                "ffmpeg", "-y", "-ss", str(start), "-i", str(source),
                "-t", str(end-start), "-vf",
                "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1",
                "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
                "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", str(target)
            ])
            output.append({
                "title": str(c.get("title", f"Clip {i}")),
                "reason": str(c.get("reason", "Momento destacado")),
                "score": max(0, min(100, int(c.get("score", 70)))),
                "url": f"/api/download/{job}/{target.name}"
            })
        if not output:
            raise RuntimeError("La IA no encontró segmentos válidos para exportar.")
        return {"clips": output}
    except Exception as e:
        shutil.rmtree(folder, ignore_errors=True)
        raise HTTPException(400, f"No se pudieron crear los clips: {str(e)}")

@app.get("/api/download/{job}/{filename}")
def download(job: str, filename: str):
    if not re.fullmatch(r"[a-f0-9]{10}", job) or not re.fullmatch(r"clip_[1-5]\.mp4", filename):
        raise HTTPException(404, "Archivo no encontrado.")
    path = WORK / job / filename
    if not path.is_file():
        raise HTTPException(404, "El clip ya no está disponible.")
    return FileResponse(path, media_type="video/mp4", filename=filename)
