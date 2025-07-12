# server/models/harmony_suggester.py
import numpy as np
from typing import List, Dict

class HarmonySuggester:
    def __init__(self):
        self.progressions = {
            "pop": {
                "happy": [
                    ["I", "V", "vi", "IV"],
                    ["I", "vi", "IV", "V"],
                    ["I", "IV", "V", "I"],
                    ["I", "iii", "vi", "IV"]
                ],
                "sad": [
                    ["vi", "IV", "I", "V"],
                    ["i", "VII", "iv", "i"],
                    ["vi", "ii", "V", "I"],
                    ["i", "iv", "VII", "III"]
                ]
            },
            "jazz": {
                "happy": [
                    ["IMaj7", "vi7", "ii7", "V7"],
                    ["IMaj7", "VII7", "IIIMaj7", "VI7"],
                    ["IMaj7", "ii7", "V7", "IMaj7"],
                    ["IMaj7", "IV7", "iii7", "vi7"]
                ],
                "sad": [
                    ["i7", "iv7", "VII7", "IIIMaj7"],
                    ["i7", "ii°7", "V7", "i7"],
                    ["vi7", "ii7", "V7", "IMaj7"],
                    ["i7", "iv7", "i7", "V7"]
                ]
            },
            "rock": {
                "happy": [
                    ["I", "IV", "V", "I"],
                    ["I", "V", "IV", "I"],
                    ["I", "bVII", "IV", "I"],
                    ["I", "vi", "IV", "V"]
                ],
                "sad": [
                    ["i", "bVII", "bVI", "V"],
                    ["i", "iv", "i", "V"],
                    ["vi", "IV", "I", "V"],
                    ["i", "bIII", "bVII", "i"]
                ]
            }
        }
        
        self.chord_colors = {
            "I": "#4CAF50",
            "ii": "#2196F3", 
            "iii": "#9C27B0",
            "IV": "#FF9800",
            "V": "#F44336",
            "vi": "#795548",
            "vii°": "#607D8B"
        }
    
    def suggest(self, key: str = "C", genre: str = "pop", 
                mood: str = "happy", bars: int = 4) -> List[Dict]:
        """Suggest chord progressions"""
        
        # Get progressions for genre and mood
        if genre not in self.progressions:
            genre = "pop"
        if mood not in self.progressions[genre]:
            mood = "happy"
            
        base_progressions = self.progressions[genre][mood]
        
        suggestions = []
        
        for prog in base_progressions:
            # Extend progression to match bar count
            extended_prog = []
            while len(extended_prog) < bars:
                extended_prog.extend(prog)
            extended_prog = extended_prog[:bars]
            
            # Calculate harmonic interest score
            unique_chords = len(set(extended_prog))
            has_dominant = "V" in extended_prog or "V7" in extended_prog
            score = unique_chords * 20 + (30 if has_dominant else 0)
            
            # Add color coding
            colors = [self.chord_colors.get(chord.replace("Maj7", "").replace("7", "").replace("°", ""), "#888") 
                     for chord in extended_prog]
            
            suggestions.append({
                "chords": extended_prog,
                "key": key,
                "score": score,
                "colors": colors,
                "description": self._get_progression_description(extended_prog)
            })
        
        # Sort by score
        suggestions.sort(key=lambda x: x["score"], reverse=True)
        
        return suggestions
    
    def _get_progression_description(self, progression: List[str]) -> str:
        """Generate description for chord progression"""
        if progression == ["I", "V", "vi", "IV"]:
            return "The 'pop progression' - used in countless hit songs"
        elif progression == ["I", "vi", "IV", "V"]:
            return "Classic '50s progression - doo-wop style"
        elif progression == ["i", "bVII", "bVI", "V"]:
            return "Andalusian cadence - dramatic and powerful"
        elif "ii7" in progression and "V7" in progression:
            return "Jazz ii-V-I movement - sophisticated and smooth"
        else:
            return "A compelling progression with strong voice leading"