# server/app.py
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import os
from typing import List, Dict, Optional
import numpy as np
from pydantic import BaseModel
import asyncio
from datetime import datetime

# Import our AI modules
from models.beat_generator import BeatGenerator
from models.melody_generator import MelodyGenerator
from models.harmony_suggester import HarmonySuggester
from audio.processor import AudioProcessor
from api.database import get_database

app = FastAPI(title="AI Music Producer API")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize AI models
beat_gen = BeatGenerator()
melody_gen = MelodyGenerator()
harmony_suggest = HarmonySuggester()
audio_proc = AudioProcessor()

# Request/Response Models
class BeatRequest(BaseModel):
    genre: str = "hip-hop"
    tempo: int = 120
    bars: int = 4
    complexity: float = 0.7

class MelodyRequest(BaseModel):
    key: str = "C"
    scale: str = "major"
    tempo: int = 120
    bars: int = 4
    chord_progression: Optional[List[str]] = None

class HarmonyRequest(BaseModel):
    key: str = "C"
    genre: str = "pop"
    mood: str = "happy"
    bars: int = 4

class AudioAnalysisResponse(BaseModel):
    tempo: float
    key: str
    genre: str
    time_signature: str
    energy: float

# API Endpoints
@app.get("/")
async def root():
    return {"message": "AI Music Producer API", "version": "1.0.0"}

@app.post("/api/generate/beat")
async def generate_beat(request: BeatRequest):
    """Generate a drum beat pattern"""
    try:
        # Generate beat pattern
        pattern = beat_gen.generate(
            genre=request.genre,
            tempo=request.tempo,
            bars=request.bars,
            complexity=request.complexity
        )
        
        # Convert to audio
        audio_path = audio_proc.pattern_to_audio(
            pattern, 
            tempo=request.tempo,
            output_dir="./temp"
        )
        
        # Save to database
        db = await get_database()
        beat_doc = {
            "type": "beat",
            "genre": request.genre,
            "tempo": request.tempo,
            "pattern": pattern.tolist(),
            "audio_path": audio_path,
            "created_at": datetime.utcnow()
        }
        result = await db.beats.insert_one(beat_doc)
        
        return {
            "id": str(result.inserted_id),
            "pattern": pattern.tolist(),
            "audio_url": f"/api/audio/{os.path.basename(audio_path)}"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/generate/melody")
async def generate_melody(request: MelodyRequest):
    """Generate a melody based on parameters"""
    try:
        # Generate melody
        melody_data = melody_gen.generate(
            key=request.key,
            scale=request.scale,
            tempo=request.tempo,
            bars=request.bars,
            chord_progression=request.chord_progression
        )
        
        # Convert to MIDI
        midi_path = audio_proc.melody_to_midi(
            melody_data,
            tempo=request.tempo,
            output_dir="./temp"
        )
        
        # Also create audio preview
        audio_path = audio_proc.midi_to_audio(midi_path)
        
        return {
            "notes": melody_data["notes"],
            "durations": melody_data["durations"],
            "midi_url": f"/api/midi/{os.path.basename(midi_path)}",
            "audio_url": f"/api/audio/{os.path.basename(audio_path)}"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/suggest/harmony")
async def suggest_harmony(request: HarmonyRequest):
    """Suggest chord progressions"""
    try:
        progressions = harmony_suggest.suggest(
            key=request.key,
            genre=request.genre,
            mood=request.mood,
            bars=request.bars
        )
        
        # Generate audio previews for top 3 progressions
        previews = []
        for i, prog in enumerate(progressions[:3]):
            audio_path = audio_proc.chords_to_audio(
                prog["chords"],
                tempo=120,
                output_dir="./temp"
            )
            previews.append({
                "progression": prog,
                "audio_url": f"/api/audio/{os.path.basename(audio_path)}"
            })
        
        return {"suggestions": previews}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/analyze/audio")
async def analyze_audio(file: UploadFile = File(...)):
    """Analyze uploaded audio file"""
    try:
        # Save uploaded file
        temp_path = f"./temp/{file.filename}"
        with open(temp_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # Analyze audio
        analysis = audio_proc.analyze(temp_path)
        
        # Clean up
        os.remove(temp_path)
        
        return AudioAnalysisResponse(**analysis)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/style-transfer")
async def style_transfer(
    file: UploadFile = File(...),
    target_genre: str = "jazz"
):
    """Apply style transfer to uploaded audio"""
    try:
        # Save uploaded file
        temp_path = f"./temp/{file.filename}"
        with open(temp_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # Apply style transfer
        output_path = beat_gen.style_transfer(
            input_path=temp_path,
            target_genre=target_genre
        )
        
        # Clean up input
        os.remove(temp_path)
        
        return {
            "original_filename": file.filename,
            "styled_audio_url": f"/api/audio/{os.path.basename(output_path)}"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/audio/{filename}")
async def get_audio(filename: str):
    """Serve audio files"""
    file_path = f"./temp/{filename}"
    if os.path.exists(file_path):
        return FileResponse(file_path, media_type="audio/wav")
    raise HTTPException(status_code=404, detail="Audio file not found")

@app.get("/api/midi/{filename}")
async def get_midi(filename: str):
    """Serve MIDI files"""
    file_path = f"./temp/{filename}"
    if os.path.exists(file_path):
        return FileResponse(file_path, media_type="audio/midi")
    raise HTTPException(status_code=404, detail="MIDI file not found")

@app.get("/api/projects")
async def get_projects():
    """Get all saved projects"""
    db = await get_database()
    projects = await db.projects.find().to_list(100)
    return {"projects": projects}

@app.post("/api/projects/save")
async def save_project(project_data: dict):
    """Save a music project"""
    db = await get_database()
    project_data["created_at"] = datetime.utcnow()
    result = await db.projects.insert_one(project_data)
    return {"id": str(result.inserted_id), "message": "Project saved"}

# Create temp directory if it doesn't exist
os.makedirs("./temp", exist_ok=True)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)