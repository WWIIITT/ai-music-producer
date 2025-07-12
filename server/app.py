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
import zipfile
import tempfile

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

class ExportRequest(BaseModel):
    project: dict
    format: str = "wav"

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

@app.post("/api/export")
async def export_project(request: ExportRequest):
    """Export project to audio/MIDI files"""
    try:
        project = request.project
        export_format = request.format
        
        # Create temporary directory for export files
        with tempfile.TemporaryDirectory() as temp_dir:
            export_files = []
            
            # Export beats
            if project.get("beats"):
                for i, beat in enumerate(project["beats"]):
                    if "pattern" in beat:
                        pattern = np.array(beat["pattern"])
                        audio_path = audio_proc.pattern_to_audio(
                            pattern,
                            tempo=beat.get("tempo", 120),
                            output_dir=temp_dir
                        )
                        # Rename with descriptive name
                        beat_name = f"beat_{i+1}_{beat.get('genre', 'unknown')}.wav"
                        beat_path = os.path.join(temp_dir, beat_name)
                        os.rename(audio_path, beat_path)
                        export_files.append(beat_path)
            
            # Export melodies
            if project.get("melodies"):
                for i, melody in enumerate(project["melodies"]):
                    if "notes" in melody and "durations" in melody:
                        # Export as MIDI
                        midi_path = audio_proc.melody_to_midi(
                            melody,
                            tempo=melody.get("tempo", 120),
                            output_dir=temp_dir
                        )
                        melody_name = f"melody_{i+1}_{melody.get('key', 'C')}_{melody.get('scale', 'major')}.mid"
                        melody_midi_path = os.path.join(temp_dir, melody_name)
                        os.rename(midi_path, melody_midi_path)
                        export_files.append(melody_midi_path)
                        
                        # Also export as audio if requested
                        if export_format in ["wav", "both"]:
                            audio_path = audio_proc.midi_to_audio(melody_midi_path)
                            audio_name = f"melody_{i+1}_{melody.get('key', 'C')}_{melody.get('scale', 'major')}.wav"
                            melody_audio_path = os.path.join(temp_dir, audio_name)
                            os.rename(audio_path, melody_audio_path)
                            export_files.append(melody_audio_path)
            
            # Export harmonies
            if project.get("harmonies"):
                for i, harmony in enumerate(project["harmonies"]):
                    if "progression" in harmony and "chords" in harmony["progression"]:
                        chords = harmony["progression"]["chords"]
                        audio_path = audio_proc.chords_to_audio(
                            chords,
                            tempo=120,
                            output_dir=temp_dir
                        )
                        harmony_name = f"harmony_{i+1}_{len(chords)}chords.wav"
                        harmony_path = os.path.join(temp_dir, harmony_name)
                        os.rename(audio_path, harmony_path)
                        export_files.append(harmony_path)
            
            if not export_files:
                raise HTTPException(status_code=400, detail="No exportable content found in project")
            
            # Create ZIP file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            project_name = project.get("name", "Untitled_Project").replace(" ", "_")
            zip_filename = f"{project_name}_{timestamp}.zip"
            zip_path = os.path.join("./temp", zip_filename)
            
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file_path in export_files:
                    zipf.write(file_path, os.path.basename(file_path))
        
        return {
            "download_url": f"/api/download/{zip_filename}",
            "filename": zip_filename,
            "files_exported": len(export_files)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/download/{filename}")
async def download_export(filename: str):
    """Download exported project files"""
    file_path = f"./temp/{filename}"
    if os.path.exists(file_path):
        return FileResponse(
            file_path, 
            media_type="application/zip",
            filename=filename
        )
    raise HTTPException(status_code=404, detail="Export file not found")

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

@app.delete("/api/projects/{project_id}")
async def delete_project(project_id: str):
    """Delete a project"""
    db = await get_database()
    result = await db.projects.delete_one({"_id": project_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Project not found")
    return {"message": "Project deleted"}

# Create temp directory if it doesn't exist
os.makedirs("./temp", exist_ok=True)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)