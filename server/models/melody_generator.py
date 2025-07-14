# server/models/melody_generator.py - FIXED VERSION
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
        
        # Fixed rhythm patterns with proper durations
        self.rhythm_patterns = {
            "default": [
                [0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5],  # 8th notes
                [1.0, 0.5, 0.5, 1.0, 0.5, 0.5, 1.0],        # Mixed
                [0.25, 0.25, 0.5, 1.0, 0.5, 0.5, 0.5],      # With 16th notes
                [1.0, 1.0, 0.5, 0.5, 1.0, 1.0]              # Quarter and half notes
            ],
            "jazz": [
                [0.75, 0.25, 1.0, 0.5, 0.5, 1.0],           # Swing feel
                [1.0, 0.5, 0.25, 0.25, 1.0, 0.5, 0.5],      # Syncopated
                [0.5, 0.5, 0.5, 0.5, 0.75, 0.25, 1.0]       # Complex rhythm
            ],
            "electronic": [
                [0.25, 0.25, 0.25, 0.25, 0.5, 0.5, 0.5, 0.5], # 16th note patterns
                [0.5, 0.5, 0.5, 0.5, 0.25, 0.25, 0.25, 0.25], # Mixed electronic
                [1.0, 0.5, 0.5, 0.25, 0.25, 0.25, 0.25]       # Build patterns
            ],
            "hip-hop": [
                [0.5, 0.5, 1.0, 0.5, 0.5, 1.0],             # Hip-hop groove
                [0.25, 0.25, 0.5, 1.0, 0.5, 0.5, 0.5],      # With 16th notes
                [1.0, 0.5, 0.5, 0.5, 0.5, 1.0]              # Laid back
            ],
            "rock": [
                [0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5],  # Steady 8ths
                [1.0, 1.0, 0.5, 0.5, 1.0, 1.0],            # Power chords rhythm
                [0.5, 0.5, 1.0, 1.0, 0.5, 0.5]             # Rock groove
            ]
        }
    
    def generate(self, key: str = "C", scale: str = "major", 
                 tempo: int = 120, bars: int = 4,
                 chord_progression: Optional[List[str]] = None,
                 reference: Optional[Dict] = None) -> Dict:
        """Generate melody based on parameters"""
        
        try:
            print(f"🎵 Generating melody: Key={key}, Scale={scale}, Bars={bars}, Tempo={tempo}")
            
            # Get scale notes
            root_midi = self.note_to_midi.get(key, 60)
            scale_notes = [root_midi + interval for interval in self.scale_intervals.get(scale, self.scale_intervals["major"])]
            
            # Extend scale to multiple octaves for more range
            extended_scale = []
            for octave in [-1, 0, 1]:
                extended_scale.extend([note + (12 * octave) for note in scale_notes])
            
            # Filter to reasonable range (C3 to C6)
            extended_scale = [n for n in extended_scale if 48 <= n <= 84]
            extended_scale.sort()  # Ensure sorted order
            
            print(f"🎼 Scale notes: {extended_scale[:7]}... (total: {len(extended_scale)})")
            
            # Generate rhythm pattern based on reference or default
            durations = self._generate_durations(bars, reference)
            print(f"⏱️  Generated {len(durations)} notes with durations: {durations[:8]}...")
            
            # Generate melody notes
            notes = self._generate_melody_notes(
                extended_scale, durations, chord_progression, root_midi, reference, key, scale
            )
            
            print(f"🎶 Generated melody with {len(notes)} notes")
            
            return {
                "notes": notes,
                "durations": durations,
                "key": key,
                "scale": scale,
                "tempo": tempo,
                "total_duration": sum(durations)
            }
            
        except Exception as e:
            print(f"❌ Melody generation error: {str(e)}")
            import traceback
            traceback.print_exc()
            
            # Return a simple fallback melody
            fallback_notes = [60, 62, 64, 65, 67, 65, 64, 62] * bars
            fallback_durations = [0.5] * len(fallback_notes)
            
            return {
                "notes": fallback_notes,
                "durations": fallback_durations,
                "key": key,
                "scale": scale,
                "tempo": tempo,
                "total_duration": sum(fallback_durations)
            }
    
    def _generate_durations(self, bars: int, reference: Optional[Dict] = None) -> List[float]:
        """Generate rhythm durations for the melody"""
        
        beats_per_bar = 4
        total_beats = beats_per_bar * bars
        
        # Choose rhythm patterns based on reference or default
        if reference and "genre" in reference:
            genre = reference["genre"]
            patterns = self.rhythm_patterns.get(genre, self.rhythm_patterns["default"])
            print(f"🎵 Using {genre} rhythm patterns")
        else:
            patterns = self.rhythm_patterns["default"]
            print("🎵 Using default rhythm patterns")
        
        durations = []
        current_beat = 0
        attempts = 0
        max_attempts = 20
        
        while current_beat < total_beats and attempts < max_attempts:
            pattern = random.choice(patterns)
            
            for duration in pattern:
                if current_beat + duration <= total_beats:
                    durations.append(duration)
                    current_beat += duration
                else:
                    # Fill remaining time if there's a small gap
                    remaining = total_beats - current_beat
                    if remaining > 0.1:  # Only add if significant time remains
                        durations.append(remaining)
                    current_beat = total_beats
                    break
            
            attempts += 1
        
        # Ensure we have at least some notes
        if not durations:
            durations = [0.5] * (bars * 8)  # Fallback to 8th notes
        
        return durations
    
    def _generate_melody_notes(self, scale_notes: List[int], durations: List[float],
                              chord_progression: Optional[List[str]], root: int,
                              reference: Optional[Dict], key: str, scale: str) -> List[int]:
        """Generate melody notes with musical logic"""
        
        notes = []
        
        # Ensure we have scale notes
        if not scale_notes:
            scale_notes = [60, 62, 64, 65, 67, 69, 71]  # C major fallback
        
        # Starting note (tonic or dominant for stability)
        if root in scale_notes:
            current_note = root
        elif root + 7 in scale_notes:  # Fifth
            current_note = root + 7
        else:
            current_note = scale_notes[0]  # First available note
        
        print(f"🎯 Starting note: {current_note} (root: {root})")
        
        # Generate notes with improved logic
        for i, duration in enumerate(durations):
            
            # Determine movement probability based on position
            is_strong_beat = (i % 4 == 0)  # Every 4th note is strong
            is_phrase_end = ((i + 1) % 8 == 0)  # Every 8th note ends phrase
            
            if is_phrase_end:
                # Tend to resolve to stable tones at phrase ends
                stable_notes = [n for n in scale_notes if (n - root) % 12 in [0, 4, 7]]  # Tonic, third, fifth
                if stable_notes:
                    current_note = min(stable_notes, key=lambda x: abs(x - current_note))
                    
            elif is_strong_beat and chord_progression:
                # Use chord tones on strong beats
                chord_idx = (i // 4) % len(chord_progression)
                chord_notes = self._get_chord_notes(chord_progression[chord_idx], root)
                valid_chord_notes = [n for n in chord_notes if n in scale_notes]
                if valid_chord_notes:
                    current_note = min(valid_chord_notes, key=lambda x: abs(x - current_note))
                    
            else:
                # Regular melodic movement
                if random.random() < 0.7:  # 70% stepwise motion
                    current_note = self._stepwise_movement(current_note, scale_notes)
                else:  # 30% leaps
                    current_note = self._leap_movement(current_note, scale_notes, root)
            
            notes.append(current_note)
        
        # Apply final smoothing
        notes = self._smooth_melody(notes, scale_notes)
        
        return notes
    
    def _stepwise_movement(self, current_note: int, scale_notes: List[int]) -> int:
        """Move by step in the scale"""
        try:
            current_idx = scale_notes.index(current_note)
        except ValueError:
            # Current note not in scale, find closest
            current_note = min(scale_notes, key=lambda x: abs(x - current_note))
            current_idx = scale_notes.index(current_note)
        
        # Determine direction with some musical logic
        if current_idx <= 1:  # Near bottom, tend to go up
            direction = 1
        elif current_idx >= len(scale_notes) - 2:  # Near top, tend to go down
            direction = -1
        else:
            # Weighted random walk with slight upward bias
            direction = random.choices([-1, 0, 1], weights=[0.3, 0.2, 0.5])[0]
        
        new_idx = max(0, min(current_idx + direction, len(scale_notes) - 1))
        return scale_notes[new_idx]
    
    def _leap_movement(self, current_note: int, scale_notes: List[int], root: int) -> int:
        """Make a melodic leap"""
        # Prefer leaps to chord tones or interesting intervals
        target_intervals = [3, 4, 5, 8]  # Thirds, fourths, fifths, octaves (in semitones)
        direction = random.choice([-1, 1])
        interval = random.choice(target_intervals)
        
        target = current_note + (interval * direction)
        
        # Find closest scale note to target
        return min(scale_notes, key=lambda x: abs(x - target))
    
    def _get_chord_notes(self, chord: str, key: int) -> List[int]:
        """Get MIDI notes for a chord (improved)"""
        
        # Clean chord symbol
        chord_clean = chord.replace("Maj7", "").replace("7", "").replace("°", "").replace("m", "")
        
        # Roman numeral to interval mapping
        roman_to_interval = {
            "I": 0, "i": 0,
            "II": 2, "ii": 2,
            "III": 4, "iii": 4,
            "IV": 5, "iv": 5,
            "V": 7, "v": 7,
            "VI": 9, "vi": 9,
            "VII": 11, "vii": 11,
            "bII": 1, "bIII": 3, "bV": 6, "bVI": 8, "bVII": 10
        }
        
        # Get root interval
        root_interval = roman_to_interval.get(chord_clean, 0)
        chord_root = key + root_interval
        
        # Determine chord quality
        if chord.startswith(chord_clean.lower()) and chord_clean != "V":  # Minor chord
            intervals = [0, 3, 7]  # Minor triad
        elif "°" in chord:  # Diminished
            intervals = [0, 3, 6]  # Diminished triad
        else:  # Major
            intervals = [0, 4, 7]  # Major triad
        
        # Add 7th if specified
        if "7" in chord:
            if "Maj7" in chord:
                intervals.append(11)  # Major 7th
            else:
                intervals.append(10)  # Minor 7th
        
        return [chord_root + interval for interval in intervals]
    
    def _smooth_melody(self, notes: List[int], scale_notes: List[int]) -> List[int]:
        """Apply smoothing to make melody more musical"""
        if len(notes) < 3:
            return notes
        
        smoothed = notes.copy()
        
        # Smooth large leaps (more than an octave)
        for i in range(1, len(notes) - 1):
            prev_note = notes[i - 1]
            curr_note = notes[i]
            next_note = notes[i + 1]
            
            # If there's a large leap followed by another large leap in opposite direction
            leap1 = abs(curr_note - prev_note)
            leap2 = abs(next_note - curr_note)
            
            if leap1 > 12 and leap2 > 7:  # Large leaps
                # Find a better intermediate note
                mid_point = (prev_note + next_note) // 2
                better_note = min(scale_notes, key=lambda x: abs(x - mid_point))
                
                # Only replace if it creates smaller leaps
                if abs(better_note - prev_note) < leap1 and abs(next_note - better_note) < leap2:
                    smoothed[i] = better_note
        
        return smoothed