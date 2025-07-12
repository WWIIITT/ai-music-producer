# server/models/melody_generator.py
import numpy as np
import torch
import torch.nn as nn
from typing import List, Dict, Optional
import music21

class MelodyLSTM(nn.Module):
    """LSTM model for melody generation"""
    def __init__(self, vocab_size=128, embedding_dim=128, hidden_dim=256, num_layers=2):
        super(MelodyLSTM, self).__init__()
        self.embedding = nn.Embedding(vocab_size, embedding_dim)
        self.lstm = nn.LSTM(embedding_dim, hidden_dim, num_layers, batch_first=True)
        self.fc = nn.Linear(hidden_dim, vocab_size)
        self.softmax = nn.Softmax(dim=-1)
        
    def forward(self, x, hidden=None):
        embed = self.embedding(x)
        out, hidden = self.lstm(embed, hidden)
        out = self.fc(out)
        return out, hidden

class MelodyGenerator:
    def __init__(self):
        self.model = MelodyLSTM()
        self.scale_intervals = {
            "major": [0, 2, 4, 5, 7, 9, 11],
            "minor": [0, 2, 3, 5, 7, 8, 10],
            "dorian": [0, 2, 3, 5, 7, 9, 10],
            "phrygian": [0, 1, 3, 5, 7, 8, 10],
            "lydian": [0, 2, 4, 6, 7, 9, 11],
            "mixolydian": [0, 2, 4, 5, 7, 9, 10],
            "aeolian": [0, 2, 3, 5, 7, 8, 10],
            "locrian": [0, 1, 3, 5, 6, 8, 10]
        }
        
        self.note_to_midi = {
            "C": 60, "C#": 61, "D": 62, "D#": 63,
            "E": 64, "F": 65, "F#": 66, "G": 67,
            "G#": 68, "A": 69, "A#": 70, "B": 71
        }
    
    def generate(self, key: str = "C", scale: str = "major", 
                 tempo: int = 120, bars: int = 4,
                 chord_progression: Optional[List[str]] = None) -> Dict:
        """Generate melody based on parameters"""
        
        # Get scale notes
        root_midi = self.note_to_midi.get(key, 60)
        scale_notes = [root_midi + interval for interval in self.scale_intervals[scale]]
        
        # Extend scale to multiple octaves
        extended_scale = []
        for octave in [-1, 0, 1]:
            extended_scale.extend([note + (12 * octave) for note in scale_notes])
        
        # Generate rhythm pattern
        beats_per_bar = 4
        total_beats = beats_per_bar * bars
        
        # Simple rhythm patterns
        rhythm_patterns = [
            [1, 0.5, 0.5, 1, 1, 0.5, 0.5, 1],  # Basic
            [0.5, 0.5, 0.5, 0.5, 1, 1, 1, 1],  # Mixed
            [0.25, 0.25, 0.5, 1, 0.5, 0.5, 1, 1],  # Syncopated
        ]
        
        # Choose random rhythm pattern
        rhythm = np.random.choice(rhythm_patterns)
        durations = []
        while sum(durations) < total_beats:
            durations.extend(rhythm)
        
        # Trim to exact length
        cumsum = np.cumsum(durations)
        durations = durations[:np.searchsorted(cumsum, total_beats)]
        if sum(durations) < total_beats:
            durations.append(total_beats - sum(durations))
        
        # Generate melody notes
        notes = []
        
        if chord_progression:
            # Generate melody following chord progression
            notes_per_chord = len(durations) // len(chord_progression)
            for chord in chord_progression:
                chord_notes = self._get_chord_notes(chord, key)
                for _ in range(notes_per_chord):
                    # Prefer chord tones
                    if np.random.random() < 0.7:
                        note = np.random.choice(chord_notes)
                    else:
                        note = np.random.choice(extended_scale)
                    notes.append(note)
        else:
            # Generate free melody
            current_note = root_midi
            for _ in range(len(durations)):
                # Stepwise motion with occasional leaps
                if np.random.random() < 0.7:
                    # Stepwise
                    direction = np.random.choice([-1, 1])
                    next_note_idx = extended_scale.index(current_note) + direction
                    next_note_idx = np.clip(next_note_idx, 0, len(extended_scale) - 1)
                    current_note = extended_scale[next_note_idx]
                else:
                    # Leap
                    current_note = np.random.choice(extended_scale)
                
                notes.append(current_note)
        
        return {
            "notes": notes,
            "durations": durations,
            "key": key,
            "scale": scale,
            "tempo": tempo
        }
    
    def _get_chord_notes(self, chord: str, key: str) -> List[int]:
        """Get MIDI notes for a chord"""
        # Simplified chord parsing
        root = self.note_to_midi.get(key, 60)
        
        chord_intervals = {
            "I": [0, 4, 7],      # Major triad
            "ii": [2, 5, 9],     # Minor triad
            "iii": [4, 7, 11],   # Minor triad
            "IV": [5, 9, 0],     # Major triad
            "V": [7, 11, 2],     # Major triad
            "vi": [9, 0, 4],     # Minor triad
            "vii°": [11, 2, 5],  # Diminished triad
        }
        
        if chord in chord_intervals:
            return [root + interval for interval in chord_intervals[chord]]
        
        # Default to major triad
        return [root, root + 4, root + 7]