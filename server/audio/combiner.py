# server/audio/combiner.py
import numpy as np
import soundfile as sf
from typing import Dict
import os
from datetime import datetime

class AudioCombiner:
    def __init__(self):
        self.sample_rate = 44100
    
    def combine(self, beat_path: str, melody_path: str, tempo: int = 120,
                mix_levels: Dict[str, float] = None, output_dir: str = "./temp") -> str:
        """Combine beat and melody tracks"""
        
        if mix_levels is None:
            mix_levels = {"beat": 0.7, "melody": 0.8}
        
        try:
            print(f"🎛️ Combining tracks: {beat_path} + {melody_path}")
            
            # Load audio files
            beat_audio, beat_sr = sf.read(beat_path)
            melody_audio, melody_sr = sf.read(melody_path)
            
            # Resample if necessary
            if beat_sr != self.sample_rate:
                beat_audio = self._resample(beat_audio, beat_sr, self.sample_rate)
            if melody_sr != self.sample_rate:
                melody_audio = self._resample(melody_audio, melody_sr, self.sample_rate)
            
            # Make mono if stereo
            if beat_audio.ndim > 1:
                beat_audio = np.mean(beat_audio, axis=1)
            if melody_audio.ndim > 1:
                melody_audio = np.mean(melody_audio, axis=1)
            
            # Match lengths (pad shorter track or trim longer track)
            max_length = max(len(beat_audio), len(melody_audio))
            min_length = min(len(beat_audio), len(melody_audio))
            
            # Option 1: Loop shorter track to match longer one
            if len(beat_audio) < max_length:
                beat_audio = self._loop_audio(beat_audio, max_length)
            if len(melody_audio) < max_length:
                melody_audio = self._loop_audio(melody_audio, max_length)
            
            # Option 2: Trim to shorter length (alternative approach)
            # beat_audio = beat_audio[:min_length]
            # melody_audio = melody_audio[:min_length]
            
            # Apply mix levels
            beat_mixed = beat_audio * mix_levels.get("beat", 0.7)
            melody_mixed = melody_audio * mix_levels.get("melody", 0.8)
            
            # Combine tracks
            combined = beat_mixed + melody_mixed
            
            # Normalize to prevent clipping
            if np.max(np.abs(combined)) > 0:
                combined = combined / np.max(np.abs(combined)) * 0.9
            
            # Save combined track
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"combined_{timestamp}.wav"
            output_path = os.path.join(output_dir, filename)
            
            sf.write(output_path, combined, self.sample_rate)
            print(f"✅ Combined track saved: {output_path}")
            
            return output_path
            
        except Exception as e:
            print(f"❌ Error combining tracks: {str(e)}")
            raise
    
    def _resample(self, audio: np.ndarray, original_sr: int, target_sr: int) -> np.ndarray:
        """Simple resampling (basic implementation)"""
        
        if original_sr == target_sr:
            return audio
        
        # Calculate resampling ratio
        ratio = target_sr / original_sr
        new_length = int(len(audio) * ratio)
        
        # Simple linear interpolation resampling
        old_indices = np.linspace(0, len(audio) - 1, len(audio))
        new_indices = np.linspace(0, len(audio) - 1, new_length)
        
        resampled = np.interp(new_indices, old_indices, audio)
        
        return resampled.astype(np.float32)
    
    def _loop_audio(self, audio: np.ndarray, target_length: int) -> np.ndarray:
        """Loop audio to reach target length"""
        
        if len(audio) >= target_length:
            return audio[:target_length]
        
        # Calculate how many full loops we need
        loops_needed = target_length // len(audio)
        remainder = target_length % len(audio)
        
        # Create looped audio
        looped = np.tile(audio, loops_needed)
        
        # Add partial loop if needed
        if remainder > 0:
            looped = np.concatenate([looped, audio[:remainder]])
        
        return looped
    
    def mix_multiple_tracks(self, track_paths: list, mix_levels: list = None, 
                           output_dir: str = "./temp") -> str:
        """Mix multiple audio tracks together"""
        
        if mix_levels is None:
            mix_levels = [1.0 / len(track_paths)] * len(track_paths)
        
        try:
            print(f"🎛️ Mixing {len(track_paths)} tracks")
            
            # Load all tracks
            tracks = []
            max_length = 0
            
            for path in track_paths:
                if os.path.exists(path):
                    audio, sr = sf.read(path)
                    
                    # Resample if necessary
                    if sr != self.sample_rate:
                        audio = self._resample(audio, sr, self.sample_rate)
                    
                    # Make mono
                    if audio.ndim > 1:
                        audio = np.mean(audio, axis=1)
                    
                    tracks.append(audio)
                    max_length = max(max_length, len(audio))
            
            if not tracks:
                raise ValueError("No valid tracks found")
            
            # Pad all tracks to same length
            for i in range(len(tracks)):
                if len(tracks[i]) < max_length:
                    tracks[i] = self._loop_audio(tracks[i], max_length)
            
            # Mix tracks
            mixed = np.zeros(max_length)
            for track, level in zip(tracks, mix_levels):
                mixed += track * level
            
            # Normalize
            if np.max(np.abs(mixed)) > 0:
                mixed = mixed / np.max(np.abs(mixed)) * 0.9
            
            # Save
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"mixed_{len(tracks)}tracks_{timestamp}.wav"
            output_path = os.path.join(output_dir, filename)
            
            sf.write(output_path, mixed, self.sample_rate)
            print(f"✅ Mixed track saved: {output_path}")
            
            return output_path
            
        except Exception as e:
            print(f"❌ Error mixing tracks: {str(e)}")
            raise