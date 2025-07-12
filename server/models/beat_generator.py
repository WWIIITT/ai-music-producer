# server/models/beat_generator.py
import numpy as np
import torch
import torch.nn as nn
from typing import Dict, List
import librosa

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
                 bars: int = 4, complexity: float = 0.7) -> np.ndarray:
        """Generate drum pattern"""
        
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
                        pattern[drum_idx, start_idx:start_idx + steps_per_bar] = drum_pattern
            
            # Add variations based on complexity
            if complexity > 0.5:
                # Add ghost notes
                pattern = self._add_variations(pattern, complexity)
            
            return pattern
        
        else:
            # Use neural network for unknown genres
            return self._generate_with_nn(total_steps, complexity)
    
    def _add_variations(self, pattern: np.ndarray, complexity: float) -> np.ndarray:
        """Add variations to pattern based on complexity"""
        variation_prob = complexity * 0.3
        
        # Add random hits
        for i in range(pattern.shape[0]):
            for j in range(pattern.shape[1]):
                if np.random.random() < variation_prob * 0.1:
                    pattern[i, j] = 1 - pattern[i, j]  # Flip the bit
        
        # Add fills every 4 bars
        if pattern.shape[1] >= 64:  # At least 4 bars
            fill_start = 60
            pattern[1, fill_start:fill_start+4] = [1,1,1,1]  # Snare fill
            
        return pattern
    
    def _generate_with_nn(self, length: int, complexity: float) -> np.ndarray:
        """Generate pattern using neural network"""
        with torch.no_grad():
            # Initialize with random seed
            batch_size = 1
            hidden = None
            
            # Start with a kick on beat 1
            pattern = torch.zeros(batch_size, length, len(self.drum_mapping))
            pattern[0, 0, 0] = 1  # Kick on first beat
            
            # Generate pattern step by step
            for i in range(1, length):
                # Use previous steps as input
                input_seq = pattern[:, max(0, i-16):i, :]
                
                # Pad if necessary
                if input_seq.shape[1] < 16:
                    padding = torch.zeros(batch_size, 16 - input_seq.shape[1], len(self.drum_mapping))
                    input_seq = torch.cat([padding, input_seq], dim=1)
                
                # Generate next step
                output, hidden = self.model(input_seq, hidden)
                next_step = output[:, -1, :]
                
                # Apply threshold based on complexity
                threshold = 1.0 - complexity
                pattern[0, i, :] = (next_step > threshold).float()
            
            return pattern[0].numpy()
    
    def style_transfer(self, input_path: str, target_genre: str) -> str:
        """Apply style transfer to existing beat"""
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