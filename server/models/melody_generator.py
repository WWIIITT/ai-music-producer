# server/models/melody_generator.py
import numpy as np
from typing import List, Dict, Optional
import random

class MelodyGenerator:
    def __init__(self):
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
        
        # Rhythm patterns for different genres
        self.rhythm_patterns = {
            "default": [
                [1, 0.5, 0.5, 1, 1, 0.5, 0.5, 1],
                [0.5, 0.5, 0.5, 0.5, 1, 1, 1, 1],
                [0.25, 0.25, 0.5, 1, 0.5, 0.5, 1, 1],
                [1, 1, 0.5, 0.5, 0.5, 0.5, 1, 1]
            ],
            "jazz": [
                [0.75, 0.25, 1, 0.5, 0.5, 1, 0.5, 0.5],
                [1, 0.5, 0.25, 0.25, 1, 1, 0.5, 0.5],
                [0.5, 0.5, 0.5, 0.5, 0.75, 0.25, 1, 1]
            ],
            "electronic": [
                [0.25, 0.25, 0.25, 0.25, 0.5, 0.5, 0.5, 0.5],
                [0.5, 0.5, 0.5, 0.5, 0.25, 0.25, 0.25, 0.25],
                [1, 0.5, 0.5, 0.25, 0.25, 0.25, 0.25, 1]
            ]
        }
    
    def generate(self, key: str = "C", scale: str = "major", 
                 tempo: int = 120, bars: int = 4,
                 chord_progression: Optional[List[str]] = None,
                 reference: Optional[Dict] = None) -> Dict:
        """Generate melody based on parameters"""
        
        try:
            # Get scale notes
            root_midi = self.note_to_midi.get(key, 60)
            scale_notes = [root_midi + interval for interval in self.scale_intervals.get(scale, self.scale_intervals["major"])]
            
            # Extend scale to multiple octaves
            extended_scale = []
            for octave in [-1, 0, 1]:
                extended_scale.extend([note + (12 * octave) for note in scale_notes])
            
            # Filter to reasonable range (C3 to C6)
            extended_scale = [n for n in extended_scale if 48 <= n <= 84]
            
            # Generate rhythm pattern
            beats_per_bar = 4
            total_beats = beats_per_bar * bars
            
            # Choose rhythm patterns based on reference or genre
            if reference and "genre" in reference:
                genre = reference["genre"]
                patterns = self.rhythm_patterns.get(genre, self.rhythm_patterns["default"])
            else:
                patterns = self.rhythm_patterns["default"]
            
            # Generate durations
            durations = []
            current_beat = 0
            
            while current_beat < total_beats:
                pattern = random.choice(patterns)
                for duration in pattern:
                    if current_beat + duration <= total_beats:
                        durations.append(duration)
                        current_beat += duration
                    else:
                        # Fill remaining time
                        if total_beats - current_beat > 0:
                            durations.append(total_beats - current_beat)
                        current_beat = total_beats
                        break
            
            # Generate melody notes
            notes = self._generate_melody_notes(
                extended_scale, durations, chord_progression, root_midi, reference
            )
            
            return {
                "notes": notes,
                "durations": durations,
                "key": key,
                "scale": scale,
                "tempo": tempo
            }
            
        except Exception as e:
            print(f"Melody generation error: {str(e)}")
            # Return a simple fallback melody
            return {
                "notes": [60, 62, 64, 65, 67, 65, 64, 62] * bars,
                "durations": [0.5] * (8 * bars),
                "key": key,
                "scale": scale,
                "tempo": tempo
            }
    
    def _generate_melody_notes(self, scale_notes: List[int], durations: List[float],
                              chord_progression: Optional[List[str]], root: int,
                              reference: Optional[Dict]) -> List[int]:
        """Generate melody notes with musical logic"""
        
        notes = []
        
        # Starting note (often the root or fifth)
        current_note = random.choice([root, root + 7, root + 4])
        
        # Ensure starting note is in our scale
        if current_note not in scale_notes:
            current_note = min(scale_notes, key=lambda x: abs(x - current_note))
        
        # Generate notes
        for i, duration in enumerate(durations):
            # Determine melodic movement
            if random.random() < 0.7:  # 70% stepwise motion
                # Move by step
                current_idx = scale_notes.index(current_note)
                
                # Tend to resolve upward or downward
                if current_idx == 0:
                    direction = 1
                elif current_idx == len(scale_notes) - 1:
                    direction = -1
                else:
                    # Weighted random: prefer small movements
                    weights = [0.3, 0.4, 0.3]  # down, same, up
                    direction = random.choices([-1, 0, 1], weights=weights)[0]
                
                new_idx = current_idx + direction
                new_idx = max(0, min(new_idx, len(scale_notes) - 1))
                current_note = scale_notes[new_idx]
                
            else:  # 30% leaps
                # Leap to chord tone or interesting interval
                if chord_progression and i < len(chord_progression):
                    # Use chord tones
                    chord_notes = self._get_chord_notes(chord_progression[i % len(chord_progression)], root)
                    valid_chord_notes = [n for n in chord_notes if n in scale_notes]
                    if valid_chord_notes:
                        current_note = random.choice(valid_chord_notes)
                    else:
                        current_note = random.choice(scale_notes)
                else:
                    # Random leap within reasonable range
                    leap_size = random.choice([3, 4, 5, 7])  # thirds, fourths, fifths, octaves
                    direction = random.choice([-1, 1])
                    target = current_note + (leap_size * direction)
                    
                    # Find closest scale note
                    if scale_notes:
                        current_note = min(scale_notes, key=lambda x: abs(x - target))
            
            notes.append(current_note)
        
        # Apply melodic smoothing
        notes = self._smooth_melody(notes, scale_notes)
        
        return notes
    
    def _get_chord_notes(self, chord: str, key: int) -> List[int]:
        """Get MIDI notes for a chord"""
        # Chord intervals (simplified)
        chord_intervals = {
            "I": [0, 4, 7],      # Major triad
            "i": [0, 3, 7],      # Minor triad  
            "ii": [2, 5, 9],     # Minor triad from 2nd degree
            "iii": [4, 7, 11],   # Minor triad from 3rd degree
            "IV": [5, 9, 0],     # Major triad from 4th degree
            "V": [7, 11, 2],     # Major triad from 5th degree
            "vi": [9, 0, 4],     # Minor triad from 6th degree
            "vii°": [11, 2, 5],  # Diminished triad from 7th degree
            "VII": [10, 2, 5],   # Major triad from flat 7th
            "bVII": [10, 2, 5],  # Same as VII
            "III": [4, 8, 11],   # Major triad from 3rd degree
            "bIII": [3, 7, 10],  # Major triad from flat 3rd
            "bVI": [8, 0, 3],    # Major triad from flat 6th
        }
        
        if chord in chord_intervals:
            return [(key + interval) % 12 + 60 for interval in chord_intervals[chord]]
        
        # Default to major triad
        return [key, key + 4, key + 7]
    
    def _smooth_melody(self, notes: List[int], scale_notes: List[int]) -> List[int]:
        """Apply smoothing to make melody more musical"""
        if len(notes) < 3:
            return notes
        
        smoothed = notes.copy()
        
        # Smooth large leaps
        for i in range(1, len(notes) - 1):
            prev_note = notes[i - 1]
            curr_note = notes[i]
            next_note = notes[i + 1]
            
            # If there's a large leap followed by another large leap
            if abs(curr_note - prev_note) > 7 and abs(next_note - curr_note) > 7:
                # Find a passing note
                passing_notes = [n for n in scale_notes 
                               if min(prev_note, next_note) < n < max(prev_note, next_note)]
                if passing_notes:
                    smoothed[i] = random.choice(passing_notes)
        
        return smoothed