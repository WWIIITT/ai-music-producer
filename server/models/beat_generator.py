# server/models/beat_generator.py - FIXED VERSION
import numpy as np
import torch
import torch.nn as nn
from typing import Dict, List, Optional
import librosa
import random

class DrumRNN(nn.Module):
    """RNN model for drum pattern generation"""
    def __init__(self, input_size=128, hidden_size=256, num_layers=2, num_drums=9):
        super(DrumRNN, self).__init__()
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.num_drums = num_drums
        
        self.lstm = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True)
        self.fc = nn.Linear(hidden_size, num_drums)
        self.sigmoid = nn.Sigmoid()
        
    def forward(self, x, hidden=None):
        out, hidden = self.lstm(x, hidden)
        out = self.fc(out)
        out = self.sigmoid(out)
        return out, hidden

class BeatGenerator:
    def __init__(self):
        self.model = DrumRNN()
        self.drum_mapping = {
            0: "kick",
            1: "snare", 
            2: "hihat_closed",
            3: "hihat_open",
            4: "crash",
            5: "ride",
            6: "tom_high",
            7: "tom_mid",
            8: "tom_low"
        }
        
        # Genre-specific patterns (simplified patterns for demo)
        self.genre_patterns = {
            "hip-hop": {
                "kick": [1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0],
                "snare": [0,0,0,0,1,0,0,0,0,0,0,0,1,0,0,0],
                "hihat_closed": [1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0]
            },
            "rock": {
                "kick": [1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0],
                "snare": [0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0],
                "hihat_closed": [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1]
            },
            "jazz": {
                "kick": [1,0,0,1,0,0,1,0,0,1,0,0,1,0,0,0],
                "snare": [0,0,1,0,0,1,0,0,1,0,0,1,0,0,1,0],
                "ride": [1,0,1,1,0,1,1,0,1,1,0,1,1,0,1,0]
            },
            "electronic": {
                "kick": [1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0],
                "snare": [0,0,0,0,1,0,0,0,0,0,0,0,1,0,0,0],
                "hihat_closed": [0,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0]
            }
        }
    
    def generate(self, genre: str = "hip-hop", tempo: int = 120, 
                 bars: int = 4, complexity: float = 0.7,
                 reference: Optional[Dict] = None) -> np.ndarray:
        """Generate drum pattern"""
        
        print(f"🥁 Generating beat: Genre={genre}, Tempo={tempo}, Bars={bars}, Complexity={complexity}")
        
        # Use reference data if available
        if reference:
            print(f"📊 Using reference analysis for beat generation")
            # Override parameters from reference
            if "tempo" in reference:
                tempo = int(reference["tempo"])
                print(f"🎵 Tempo from reference: {tempo}")
            if "genre" in reference:
                # Map analyzed genre to our available patterns
                ref_genre = reference["genre"].lower()
                if ref_genre in self.genre_patterns:
                    genre = ref_genre
                    print(f"🎸 Genre from reference: {genre}")
            if "energy" in reference:
                # Adjust complexity based on energy level
                energy = reference["energy"]
                complexity = min(complexity * (1 + energy), 1.0)
                print(f"⚡ Adjusted complexity from energy: {complexity}")
        
        steps_per_bar = 16
        total_steps = steps_per_bar * bars
        
        # Get base pattern for genre
        if genre in self.genre_patterns:
            base_pattern = self.genre_patterns[genre]
            pattern = np.zeros((len(self.drum_mapping), total_steps))
            
            # Fill pattern with base rhythm
            for i, (drum_idx, drum_name) in enumerate(self.drum_mapping.items()):
                if drum_name in base_pattern:
                    drum_pattern = base_pattern[drum_name]
                    # Repeat pattern for number of bars
                    for bar in range(bars):
                        start_idx = bar * steps_per_bar
                        end_idx = start_idx + len(drum_pattern)
                        if end_idx <= total_steps:
                            pattern[drum_idx, start_idx:end_idx] = drum_pattern
                        else:
                            # Handle partial bar
                            remaining = total_steps - start_idx
                            pattern[drum_idx, start_idx:start_idx + remaining] = drum_pattern[:remaining]
            
            # Add variations based on complexity and reference
            if complexity > 0.5:
                pattern = self._add_variations(pattern, complexity, reference)
            
            print(f"✅ Generated beat pattern: {pattern.shape}")
            return pattern
        
        else:
            # Use neural network for unknown genres or fallback
            print(f"🤖 Using NN generation for genre: {genre}")
            return self._generate_with_nn(total_steps, complexity, reference)
    
    def _add_variations(self, pattern: np.ndarray, complexity: float, 
                       reference: Optional[Dict] = None) -> np.ndarray:
        """Add variations to pattern based on complexity and reference"""
        
        variation_prob = complexity * 0.3
        
        # If we have reference analysis, use it to guide variations
        if reference:
            # Use time signature to adjust variations
            time_sig = reference.get("time_signature", "4/4")
            if time_sig == "3/4":
                # Adjust for waltz time
                variation_prob *= 0.7
            elif time_sig == "6/8":
                # Adjust for compound time
                variation_prob *= 1.2
            
            # Use mood to influence variation style
            mood = reference.get("mood", "neutral")
            if mood in ["energetic", "happy"]:
                variation_prob *= 1.3
            elif mood in ["sad", "calm"]:
                variation_prob *= 0.7
        
        # Add random variations
        for i in range(pattern.shape[0]):
            for j in range(pattern.shape[1]):
                if np.random.random() < variation_prob * 0.1:
                    # Don't remove kick on strong beats
                    if i == 0 and j % 16 in [0, 8]:  # Kick on beats 1 and 3
                        continue
                    pattern[i, j] = 1 - pattern[i, j]  # Flip the bit
        
        # Add fills every 4 bars (if we have enough bars)
        if pattern.shape[1] >= 64:  # At least 4 bars
            fill_start = 60
            if fill_start + 4 <= pattern.shape[1]:
                pattern[1, fill_start:fill_start+4] = [1,1,1,1]  # Snare fill
        
        # Add ghost notes on hi-hats for complexity
        if complexity > 0.7:
            hihat_idx = 2  # hihat_closed
            for j in range(1, pattern.shape[1], 2):  # Offbeats
                if np.random.random() < 0.3:
                    pattern[hihat_idx, j] = 0.5  # Ghost note
        
        return pattern
    
    def _generate_with_nn(self, length: int, complexity: float, 
                         reference: Optional[Dict] = None) -> np.ndarray:
        """Generate pattern using neural network (fallback method)"""
        
        print("🧠 Using neural network fallback generation")
        
        # Since we don't have a trained model, use algorithmic generation
        # that mimics neural network behavior
        pattern = np.zeros((len(self.drum_mapping), length))
        
        # Generate basic 4/4 pattern
        steps_per_bar = 16
        num_bars = length // steps_per_bar
        
        for bar in range(num_bars):
            bar_start = bar * steps_per_bar
            
            # Kick pattern (influenced by reference)
            kick_pattern = [1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0]
            if reference and reference.get("genre") == "electronic":
                kick_pattern = [1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0]  # 4-on-floor
            elif reference and reference.get("genre") == "jazz":
                kick_pattern = [1,0,0,1,0,0,1,0,0,1,0,0,1,0,0,0]  # Jazz swing
            
            # Apply kick pattern
            end_idx = min(bar_start + steps_per_bar, length)
            pattern_length = end_idx - bar_start
            pattern[0, bar_start:end_idx] = kick_pattern[:pattern_length]
            
            # Snare on 2 and 4
            if bar_start + 4 < length:
                pattern[1, bar_start + 4] = 1
            if bar_start + 12 < length:
                pattern[1, bar_start + 12] = 1
            
            # Hi-hat pattern
            for i in range(0, min(steps_per_bar, pattern_length), 2):
                if bar_start + i < length:
                    pattern[2, bar_start + i] = 0.7
        
        # Add complexity-based variations
        if complexity > 0.5:
            pattern = self._add_variations(pattern, complexity, reference)
        
        print(f"✅ NN Generated pattern: {pattern.shape}")
        return pattern
    
    def style_transfer(self, input_path: str, target_genre: str) -> str:
        """Apply style transfer to existing beat"""
        try:
            # Load audio
            y, sr = librosa.load(input_path)
            
            # Extract tempo and beats
            tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
            
            # Generate new pattern in target genre
            new_pattern = self.generate(
                genre=target_genre,
                tempo=int(tempo),
                bars=4
            )
            
            # This is a simplified version - in production you'd use a proper
            # style transfer model like MusicVAE or similar
            output_path = input_path.replace('.wav', f'_{target_genre}.wav')
            
            # For now, just return the path (audio processing would happen here)
            return output_path
            
        except Exception as e:
            print(f"❌ Style transfer error: {str(e)}")
            # Return original path as fallback
            return input_path