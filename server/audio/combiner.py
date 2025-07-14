# server/audio/combiner.py
import numpy as np
import librosa
import soundfile as sf
from typing import Dict
import os
from datetime import datetime

class AudioCombiner:
    def __init__(self):
        self.sample_rate = 44100
        
    def combine(self, beat_path: str, melody_path: str, tempo: int = 120,
                mix_levels: Dict[str, float] = None, output_dir: str = "./temp") -> str:
        """Combine beat and melody tracks with proper mixing"""
        
        if mix_levels is None:
            mix_levels = {"beat": 0.7, "melody": 0.8}
        
        try:
            # Load audio files
            beat, sr_beat = librosa.load(beat_path, sr=self.sample_rate)
            melody, sr_melody = librosa.load(melody_path, sr=self.sample_rate)
            
            # Ensure same length (pad or trim)
            max_length = max(len(beat), len(melody))
            
            if len(beat) < max_length:
                beat = np.pad(beat, (0, max_length - len(beat)), mode='constant')
            else:
                beat = beat[:max_length]
                
            if len(melody) < max_length:
                melody = np.pad(melody, (0, max_length - len(melody)), mode='constant')
            else:
                melody = melody[:max_length]
            
            # Apply mix levels
            beat = beat * mix_levels.get("beat", 0.7)
            melody = melody * mix_levels.get("melody", 0.8)
            
            # Mix tracks
            mixed = beat + melody
            
            # Apply compression to prevent clipping
            mixed = self._apply_compression(mixed)
            
            # Normalize
            max_val = np.max(np.abs(mixed))
            if max_val > 0:
                mixed = mixed / max_val * 0.9
            
            # Apply subtle mastering effects
            mixed = self._apply_mastering(mixed)
            
            # Save combined audio
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"combined_{tempo}bpm_{timestamp}.wav"
            output_path = os.path.join(output_dir, filename)
            
            sf.write(output_path, mixed, self.sample_rate)
            
            return output_path
            
        except Exception as e:
            print(f"Combination error: {str(e)}")
            raise
    
    def _apply_compression(self, audio: np.ndarray, threshold: float = 0.7,
                          ratio: float = 4.0) -> np.ndarray:
        """Apply dynamic range compression"""
        # Simple soft-knee compressor
        compressed = audio.copy()
        
        # Find samples above threshold
        mask = np.abs(audio) > threshold
        
        # Apply compression
        compressed[mask] = np.sign(audio[mask]) * (
            threshold + (np.abs(audio[mask]) - threshold) / ratio
        )
        
        return compressed
    
    def _apply_mastering(self, audio: np.ndarray) -> np.ndarray:
        """Apply basic mastering effects"""
        # Add subtle saturation
        audio = np.tanh(audio * 0.8) / 0.8
        
        # Apply gentle high-frequency boost (simplified)
        # In production, use proper EQ
        
        return audio
    
    def combine_multiple(self, tracks: Dict[str, str], tempo: int = 120,
                        mix_levels: Dict[str, float] = None,
                        output_dir: str = "./temp") -> str:
        """Combine multiple tracks"""
        
        if not tracks:
            raise ValueError("No tracks provided")
        
        # Load all tracks
        loaded_tracks = {}
        max_length = 0
        
        for name, path in tracks.items():
            audio, sr = librosa.load(path, sr=self.sample_rate)
            loaded_tracks[name] = audio
            max_length = max(max_length, len(audio))
        
        # Pad all tracks to same length
        for name in loaded_tracks:
            if len(loaded_tracks[name]) < max_length:
                loaded_tracks[name] = np.pad(
                    loaded_tracks[name],
                    (0, max_length - len(loaded_tracks[name])),
                    mode='constant'
                )
        
        # Mix with levels
        mixed = np.zeros(max_length)
        
        for name, audio in loaded_tracks.items():
            level = mix_levels.get(name, 1.0) if mix_levels else 1.0
            mixed += audio * level
        
        # Apply processing
        mixed = self._apply_compression(mixed)
        
        # Normalize
        max_val = np.max(np.abs(mixed))
        if max_val > 0:
            mixed = mixed / max_val * 0.9
        
        # Save
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"combined_multi_{timestamp}.wav"
        output_path = os.path.join(output_dir, filename)
        
        sf.write(output_path, mixed, self.sample_rate)
        
        return output_path