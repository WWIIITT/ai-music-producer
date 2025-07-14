# server/app.py
from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import os
import shutil
from typing import List, Dict, Optional
import numpy as np
from pydantic import BaseModel
import asyncio
from datetime import datetime
import zipfile
import tempfile
import json

# Import our AI modules
from models.beat_generator import BeatGenerator
from models.melody_generator import MelodyGenerator
from models.harmony_suggester import HarmonySuggester
from models.song_generator import WholeSongGenerator
from audio.processor import AudioProcessor
from audio.analyzer import MusicAnalyzer
from audio.combiner import AudioCombiner
from audio.mp4_exporter import MP4Exporter

app = FastAPI(title="AI Music Producer API")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create necessary directories
os.makedirs("./temp", exist_ok=True)
os.makedirs("./data", exist_ok=True)
os.makedirs("./data/uploads", exist_ok=True)
os.makedirs("./data/analyzed", exist_ok=True)
os.makedirs("./data/generated", exist_ok=True)
os.makedirs("./data/songs", exist_ok=True)
os.makedirs("./data/videos", exist_ok=True)

# Initialize AI models
beat_gen = BeatGenerator()
melody_gen = MelodyGenerator()
harmony_suggest = HarmonySuggester()
song_gen = WholeSongGenerator()
audio_proc = AudioProcessor()
music_analyzer = MusicAnalyzer()
audio_combiner = AudioCombiner()
mp4_exporter = MP4Exporter()

# Request/Response Models
class BeatRequest(BaseModel):
    genre: str = "hip-hop"
    tempo: int = 120
    bars: int = 4
    complexity: float = 0.7
    reference_file: Optional[str] = None

class MelodyRequest(BaseModel):
    key: str = "C"
    scale: str = "major"
    tempo: int = 120
    bars: int = 4
    chord_progression: Optional[List[str]] = None
    reference_file: Optional[str] = None

class HarmonyRequest(BaseModel):
    key: str = "C"
    genre: str = "pop"
    mood: str = "happy"
    bars: int = 4

class SongRequest(BaseModel):
    style: str = "pop"
    tempo: int = 120
    key: str = "C"
    duration: int = 180
    variations: int = 1
    title: Optional[str] = None

class MP4ExportRequest(BaseModel):
    audio_file: str
    song_data: Dict
    visual_style: str = "waveform"
    title: str = "Generated Song"

class CombineRequest(BaseModel):
    beat_file: str
    melody_file: str
    tempo: int = 120
    mix_levels: Dict[str, float] = {"beat": 0.7, "melody": 0.8}

class ExportRequest(BaseModel):
    project: dict
    format: str = "wav"

class AudioAnalysisResponse(BaseModel):
    tempo: float
    key: str
    genre: str
    time_signature: str
    energy: float
    mood: str
    chord_progression: List[str]
    file_id: str

# API Endpoints
@app.get("/")
async def root():
    return {"message": "AI Music Producer API", "version": "1.0.0"}

@app.post("/api/upload/music")
async def upload_music(file: UploadFile = File(...)):
    """Upload music file for analysis and reference"""
    try:
        # Validate file type
        allowed_extensions = ['.mp3', '.wav', '.ogg', '.m4a', '.flac']
        file_ext = os.path.splitext(file.filename)[1].lower()
        if file_ext not in allowed_extensions:
            raise HTTPException(status_code=400, detail=f"File type {file_ext} not supported")
        
        # Save file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_id = f"{timestamp}_{file.filename.replace(' ', '_')}"
        file_path = os.path.join("./data/uploads", file_id)
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Analyze the file
        analysis = await analyze_uploaded_music(file_path, file_id)
        
        return {
            "message": "File uploaded and analyzed successfully",
            "file_id": file_id,
            "analysis": analysis
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def analyze_uploaded_music(file_path: str, file_id: str) -> Dict:
    """Analyze uploaded music file"""
    try:
        # Perform deep analysis
        analysis = music_analyzer.analyze_deep(file_path)
        
        # Save analysis results
        analysis_path = os.path.join("./data/analyzed", f"{file_id}_analysis.json")
        with open(analysis_path, "w") as f:
            json.dump(analysis, f, indent=2)
        
        analysis["file_id"] = file_id
        return analysis
        
    except Exception as e:
        print(f"Analysis error: {str(e)}")
        raise

@app.get("/api/analyzed-files")
async def get_analyzed_files():
    """Get list of analyzed music files"""
    try:
        analyzed_files = []
        analysis_dir = "./data/analyzed"
        
        if os.path.exists(analysis_dir):
            for filename in os.listdir(analysis_dir):
                if filename.endswith("_analysis.json"):
                    with open(os.path.join(analysis_dir, filename), "r") as f:
                        analysis = json.load(f)
                        analyzed_files.append(analysis)
        
        return {"files": analyzed_files}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/generate/beat")
async def generate_beat(request: BeatRequest):
    """Generate a drum beat pattern"""
    try:
        # Check if reference file is provided
        reference_analysis = None
        if request.reference_file:
            analysis_path = os.path.join("./data/analyzed", f"{request.reference_file}_analysis.json")
            if os.path.exists(analysis_path):
                with open(analysis_path, "r") as f:
                    reference_analysis = json.load(f)
                    # Override parameters with reference
                    request.tempo = int(reference_analysis.get("tempo", request.tempo))
                    request.genre = reference_analysis.get("genre", request.genre)
        
        # Generate beat pattern
        pattern = beat_gen.generate(
            genre=request.genre,
            tempo=request.tempo,
            bars=request.bars,
            complexity=request.complexity,
            reference=reference_analysis
        )
        
        # Convert to audio
        audio_path = audio_proc.pattern_to_audio(
            pattern, 
            tempo=request.tempo,
            output_dir="./temp"
        )
        
        return {
            "pattern": pattern.tolist(),
            "audio_url": f"/api/audio/{os.path.basename(audio_path)}",
            "tempo": request.tempo,
            "genre": request.genre
        }
        
    except Exception as e:
        print(f"Beat generation error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/generate/melody")
async def generate_melody(request: MelodyRequest):
    """Generate a melody based on parameters"""
    try:
        # Check if reference file is provided
        reference_analysis = None
        if request.reference_file:
            analysis_path = os.path.join("./data/analyzed", f"{request.reference_file}_analysis.json")
            if os.path.exists(analysis_path):
                with open(analysis_path, "r") as f:
                    reference_analysis = json.load(f)
                    # Override parameters with reference
                    request.key = reference_analysis.get("key", request.key)
                    request.tempo = int(reference_analysis.get("tempo", request.tempo))
                    if not request.chord_progression and "chord_progression" in reference_analysis:
                        request.chord_progression = reference_analysis["chord_progression"]
        
        # Generate melody
        melody_data = melody_gen.generate(
            key=request.key,
            scale=request.scale,
            tempo=request.tempo,
            bars=request.bars,
            chord_progression=request.chord_progression,
            reference=reference_analysis
        )
        
        # Convert to MIDI
        midi_path = audio_proc.melody_to_midi(
            melody_data,
            tempo=request.tempo,
            output_dir="./temp"
        )
        
        # Also create audio preview
        audio_path = audio_proc.midi_to_audio(midi_path)
        
        # Store generated file info
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        generated_info = {
            "type": "melody",
            "midi_file": os.path.basename(midi_path),
            "audio_file": os.path.basename(audio_path),
            "data": melody_data,
            "timestamp": timestamp
        }
        
        info_path = os.path.join("./data/generated", f"melody_{timestamp}.json")
        with open(info_path, "w") as f:
            json.dump(generated_info, f, indent=2)
        
        return {
            "notes": melody_data["notes"],
            "durations": melody_data["durations"],
            "key": melody_data["key"],
            "scale": melody_data["scale"],
            "midi_url": f"/api/midi/{os.path.basename(midi_path)}",
            "audio_url": f"/api/audio/{os.path.basename(audio_path)}",
            "file_id": f"melody_{timestamp}"
        }
        
    except Exception as e:
        print(f"Melody generation error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/generate/whole-song")
async def generate_whole_song(request: SongRequest):
    """Generate a complete song with multiple sections"""
    try:
        print(f"🎵 Starting whole song generation: {request.style}")
        
        # Generate main song
        song_data = song_gen.generate_whole_song(
            style=request.style,
            tempo=request.tempo,
            key=request.key,
            total_duration=request.duration
        )
        
        # Generate title if not provided
        if not request.title:
            request.title = f"{request.style.title()} Song in {request.key}"
        
        song_data["title"] = request.title
        
        # Generate variations if requested
        variations = []
        if request.variations > 1:
            variations = song_gen.generate_arrangement_variations(
                song_data, 
                num_variations=request.variations - 1
            )
        
        # Convert song sections to audio
        audio_path = audio_proc.song_to_audio(
            song_data,
            output_dir="./temp"
        )
        
        # Process variations
        variation_data = []
        for i, variation in enumerate(variations):
            var_audio_path = audio_proc.song_to_audio(
                variation,
                output_dir="./temp",
                suffix=f"_var{i+1}"
            )
            variation_data.append({
                "variation_id": variation["variation_id"],
                "style": variation["style"],
                "audio_url": f"/api/audio/{os.path.basename(var_audio_path)}"
            })
        
        # Save song data
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        song_id = f"song_{timestamp}"
        
        song_info = {
            "song_id": song_id,
            "title": request.title,
            "song_data": song_data,
            "variations": variation_data,
            "timestamp": timestamp
        }
        
        song_path = os.path.join("./data/songs", f"{song_id}.json")
        with open(song_path, "w") as f:
            json.dump(song_info, f, indent=2)
        
        return {
            "title": request.title,
            "style": request.style,
            "tempo": request.tempo,
            "key": request.key,
            "duration": song_data["total_duration"],
            "sections": len(song_data["sections"]),
            "structure": song_data["structure"],
            "audio_url": f"/api/audio/{os.path.basename(audio_path)}",
            "variations": variation_data,
            "song_data": song_data,
            "song_id": song_id
        }
        
    except Exception as e:
        print(f"Song generation error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/export/mp4")
async def export_mp4(request: MP4ExportRequest):
    """Export song as MP4 video with visualization"""
    try:
        print(f"🎬 Starting MP4 export: {request.visual_style}")
        
        # Find audio file
        audio_path = os.path.join("./temp", request.audio_file)
        if not os.path.exists(audio_path):
            raise HTTPException(status_code=404, detail="Audio file not found")
        
        # Generate MP4
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        mp4_filename = f"{request.title.replace(' ', '_')}_{request.visual_style}_{timestamp}.mp4"
        mp4_path = os.path.join("./data/videos", mp4_filename)
        
        # Create music video
        final_mp4_path = mp4_exporter.create_music_video(
            audio_path=audio_path,
            song_data=request.song_data,
            output_path=mp4_path,
            style=request.visual_style
        )
        
        return {
            "mp4_url": f"/api/video/{os.path.basename(final_mp4_path)}",
            "filename": os.path.basename(final_mp4_path),
            "visual_style": request.visual_style,
            "title": request.title
        }
        
    except Exception as e:
        print(f"MP4 export error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/combine/tracks")
async def combine_tracks(request: CombineRequest):
    """Combine beat and melody tracks"""
    try:
        # Get file paths
        beat_path = os.path.join("./temp", request.beat_file)
        melody_path = os.path.join("./temp", request.melody_file)
        
        if not os.path.exists(beat_path) or not os.path.exists(melody_path):
            raise HTTPException(status_code=404, detail="Track files not found")
        
        # Combine audio
        output_path = audio_combiner.combine(
            beat_path=beat_path,
            melody_path=melody_path,
            tempo=request.tempo,
            mix_levels=request.mix_levels,
            output_dir="./temp"
        )
        
        return {
            "combined_url": f"/api/audio/{os.path.basename(output_path)}",
            "filename": os.path.basename(output_path)
        }
        
    except Exception as e:
        print(f"Combination error: {str(e)}")
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
        print(f"Harmony suggestion error: {str(e)}")
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
                        melody_name = f"melody_{i+1}.mid"
                        melody_midi_path = os.path.join(temp_dir, melody_name)
                        os.rename(midi_path, melody_midi_path)
                        export_files.append(melody_midi_path)
                        
                        # Also export as audio
                        if export_format in ["wav", "both"]:
                            audio_path = audio_proc.midi_to_audio(melody_midi_path)
                            audio_name = f"melody_{i+1}.wav"
                            melody_audio_path = os.path.join(temp_dir, audio_name)
                            os.rename(audio_path, melody_audio_path)
                            export_files.append(melody_audio_path)
            
            # Export songs
            if project.get("songs"):
                for i, song in enumerate(project["songs"]):
                    if "audio_url" in song:
                        src_filename = song["audio_url"].split("/")[-1]
                        src_path = os.path.join("./temp", src_filename)
                        if os.path.exists(src_path):
                            dst_name = f"song_{i+1}_{song.get('title', 'untitled')}.wav"
                            dst_path = os.path.join(temp_dir, dst_name)
                            shutil.copy(src_path, dst_path)
                            export_files.append(dst_path)
            
            # Export combined tracks if available
            if project.get("combined_tracks"):
                for i, track in enumerate(project["combined_tracks"]):
                    if "file" in track:
                        src_path = os.path.join("./temp", track["file"])
                        if os.path.exists(src_path):
                            dst_name = f"combined_{i+1}.wav"
                            dst_path = os.path.join(temp_dir, dst_name)
                            shutil.copy(src_path, dst_path)
                            export_files.append(dst_path)
            
            if not export_files:
                raise HTTPException(status_code=400, detail="No exportable content found")
            
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

@app.get("/api/video/{filename}")
async def get_video(filename: str):
    """Serve MP4 video files"""
    file_path = f"./data/videos/{filename}"
    if os.path.exists(file_path):
        return FileResponse(file_path, media_type="video/mp4")
    raise HTTPException(status_code=404, detail="Video file not found")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)