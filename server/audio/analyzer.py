# server/audio/analyzer.py
import librosa
import numpy as np
from typing import Dict, List, Optional
import pretty_midi

class MusicAnalyzer:
    def __init__(self):
        self.keys = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        self.modes = ['major', 'minor']
        
    def analyze_deep(self, audio_path: str) -> Dict:
        """Perform deep analysis of audio file"""
        try:
            # Load audio
            y, sr = librosa.load(audio_path, sr=None)
            
            # Basic features
            tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
            
            # Key detection
            chroma = librosa.feature.chroma_stft(y=y, sr=sr)
            key, mode = self._detect_key(chroma)
            
            # Time signature
            time_signature = self._detect_time_signature(y, sr, beats)
            
            # Energy and dynamics
            rms = librosa.feature.rms(y=y)[0]
            energy = float(np.mean(rms))
            energy_variance = float(np.std(rms))
            
            # Spectral features for genre/mood
            spectral_centroid = np.mean(librosa.feature.spectral_centroid(y=y, sr=sr))
            spectral_rolloff = np.mean(librosa.feature.spectral_rolloff(y=y, sr=sr))
            zero_crossing_rate = np.mean(librosa.feature.zero_crossing_rate(y))
            
            # Genre classification
            genre = self._classify_genre(tempo, spectral_centroid, energy)
            
            # Mood detection
            mood = self._detect_mood(mode, energy, tempo)
            
            # Chord progression detection
            chord_progression = self._detect_chords(y, sr, key)
            
            # Structure analysis
            structure = self._analyze_structure(y, sr)
            
            return {
                "tempo": float(tempo),
                "key": key,
                "mode": mode,
                "time_signature": time_signature,
                "energy": energy,
                "energy_variance": energy_variance,
                "genre": genre,
                "mood": mood,
                "chord_progression": chord_progression,
                "spectral_centroid": float(spectral_centroid),
                "spectral_rolloff": float(spectral_rolloff),
                "zero_crossing_rate": float(zero_crossing_rate),
                "structure": structure,
                "duration": float(len(y) / sr)
            }
            
        except Exception as e:
            print(f"Analysis error: {str(e)}")
            # Return default values on error
            return {
                "tempo": 120.0,
                "key": "C",
                "mode": "major",
                "time_signature": "4/4",
                "energy": 0.5,
                "energy_variance": 0.1,
                "genre": "pop",
                "mood": "neutral",
                "chord_progression": ["I", "V", "vi", "IV"],
                "spectral_centroid": 2000.0,
                "spectral_rolloff": 4000.0,
                "zero_crossing_rate": 0.1,
                "structure": {"sections": ["intro", "verse", "chorus", "outro"]},
                "duration": 0.0
            }
    
    def _detect_key(self, chroma: np.ndarray) -> tuple:
        """Detect musical key from chroma features"""
        # Krumhansl-Schmuckler key-finding algorithm (simplified)
        chroma_avg = np.mean(chroma, axis=1)
        
        # Major and minor key profiles
        major_profile = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
        minor_profile = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17])
        
        # Correlation with each key
        max_corr = -1
        best_key = "C"
        best_mode = "major"
        
        for i in range(12):
            # Rotate profiles
            major_rot = np.roll(major_profile, i)
            minor_rot = np.roll(minor_profile, i)
            
            # Calculate correlation
            major_corr = np.corrcoef(chroma_avg, major_rot)[0, 1]
            minor_corr = np.corrcoef(chroma_avg, minor_rot)[0, 1]
            
            if major_corr > max_corr:
                max_corr = major_corr
                best_key = self.keys[i]
                best_mode = "major"
                
            if minor_corr > max_corr:
                max_corr = minor_corr
                best_key = self.keys[i]
                best_mode = "minor"
        
        return best_key, best_mode
    
    def _detect_time_signature(self, y: np.ndarray, sr: int, beats: np.ndarray) -> str:
        """Detect time signature"""
        if len(beats) < 8:
            return "4/4"
        
        # Calculate beat intervals
        beat_times = librosa.frames_to_time(beats, sr=sr)
        intervals = np.diff(beat_times)
        
        # Look for patterns
        avg_interval = np.mean(intervals)
        
        # Simple heuristic
        if avg_interval < 0.4:  # Fast beats
            return "4/4"
        elif avg_interval > 0.7:  # Slow beats
            return "3/4"
        else:
            # Check for regularity
            std_interval = np.std(intervals)
            if std_interval < 0.1:
                return "4/4"
            else:
                return "3/4"
    
    def _classify_genre(self, tempo: float, spectral_centroid: float, energy: float) -> str:
        """Simple genre classification based on features"""
        # This is a simplified heuristic - in production use ML model
        
        if tempo > 140 and spectral_centroid > 3000:
            return "electronic"
        elif tempo > 120 and energy > 0.7:
            return "rock"
        elif tempo < 100 and spectral_centroid < 2000:
            return "jazz"
        elif tempo > 85 and tempo < 115:
            return "hip-hop"
        else:
            return "pop"
    
    def _detect_mood(self, mode: str, energy: float, tempo: float) -> str:
        """Detect mood based on musical features"""
        if mode == "minor":
            if energy < 0.4:
                return "sad"
            elif tempo > 120:
                return "angry"
            else:
                return "mysterious"
        else:  # major
            if energy > 0.6 and tempo > 120:
                return "energetic"
            elif energy < 0.4:
                return "calm"
            elif tempo > 100:
                return "happy"
            else:
                return "uplifting"
    
    def _detect_chords(self, y: np.ndarray, sr: int, key: str) -> List[str]:
        """Detect chord progression (simplified)"""
        # This is a very simplified version
        # In production, use a proper chord recognition model
        
        # Common progressions by genre/mood
        common_progressions = [
            ["I", "V", "vi", "IV"],      # Pop progression
            ["I", "IV", "V", "I"],        # Classic
            ["i", "iv", "VII", "III"],    # Minor progression
            ["I", "vi", "IV", "V"],       # 50s progression
            ["ii", "V", "I", "I"],        # Jazz
        ]
        
        # For now, return a random common progression
        # In reality, this would analyze harmonic content
        return common_progressions[0]
    
    def _analyze_structure(self, y: np.ndarray, sr: int) -> Dict:
        """Analyze song structure"""
        # Segment the audio
        try:
            # Use spectral features to detect sections
            mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
            
            # Simple segmentation based on self-similarity
            sections = ["intro", "verse", "chorus", "verse", "chorus", "bridge", "chorus", "outro"]
            
            # Calculate approximate timestamps
            duration = len(y) / sr
            section_duration = duration / len(sections)
            
            structure = {
                "sections": sections,
                "timestamps": [i * section_duration for i in range(len(sections))],
                "total_sections": len(sections)
            }
            
            return structure
            
        except:
            return {
                "sections": ["intro", "main", "outro"],
                "timestamps": [0.0],
                "total_sections": 3
            }