# server/models/song_generator.py
import numpy as np
from typing import Dict, List, Optional
import random
from .beat_generator import BeatGenerator
from .melody_generator import MelodyGenerator
from .harmony_suggester import HarmonySuggester

class WholeSongGenerator:
    def __init__(self):
        self.beat_gen = BeatGenerator()
        self.melody_gen = MelodyGenerator()
        self.harmony_suggest = HarmonySuggester()
        
        # Song structure templates
        self.song_structures = {
            "pop": ["intro", "verse", "chorus", "verse", "chorus", "bridge", "chorus", "outro"],
            "rock": ["intro", "verse", "chorus", "verse", "chorus", "solo", "chorus", "outro"],
            "hip-hop": ["intro", "verse", "hook", "verse", "hook", "verse", "hook", "outro"],
            "jazz": ["intro", "head", "solo1", "solo2", "head", "outro"],
            "electronic": ["intro", "buildup", "drop", "breakdown", "buildup", "drop", "outro"]
        }
        
        # Section characteristics
        self.section_configs = {
            "intro": {"bars": 8, "complexity": 0.3, "energy": 0.4},
            "verse": {"bars": 16, "complexity": 0.5, "energy": 0.6},
            "chorus": {"bars": 16, "complexity": 0.8, "energy": 0.9},
            "hook": {"bars": 8, "complexity": 0.7, "energy": 0.8},
            "bridge": {"bars": 8, "complexity": 0.6, "energy": 0.7},
            "solo": {"bars": 32, "complexity": 0.9, "energy": 0.9},
            "buildup": {"bars": 16, "complexity": 0.7, "energy": 0.8},
            "drop": {"bars": 32, "complexity": 0.9, "energy": 1.0},
            "breakdown": {"bars": 16, "complexity": 0.3, "energy": 0.5},
            "outro": {"bars": 8, "complexity": 0.3, "energy": 0.3},
            "head": {"bars": 32, "complexity": 0.6, "energy": 0.7},
            "solo1": {"bars": 32, "complexity": 0.8, "energy": 0.8},
            "solo2": {"bars": 32, "complexity": 0.9, "energy": 0.9}
        }
    
    def generate_whole_song(self, style: str = "pop", tempo: int = 120, 
                           key: str = "C", total_duration: int = 180) -> Dict:
        """Generate a complete song structure with all elements"""
        
        print(f"🎵 Generating whole song: {style} in {key} at {tempo} BPM")
        
        # Get song structure
        structure = self.song_structures.get(style, self.song_structures["pop"])
        
        # Generate chord progression for the song
        chord_progression = self._generate_song_chords(key, style, len(structure))
        
        # Generate sections
        sections = []
        current_time = 0
        
        for i, section_type in enumerate(structure):
            config = self.section_configs.get(section_type, self.section_configs["verse"])
            
            # Generate beat for this section
            beat_pattern = self.beat_gen.generate(
                genre=style,
                tempo=tempo,
                bars=config["bars"],
                complexity=config["complexity"]
            )
            
            # Generate melody for this section
            section_chords = chord_progression[i % len(chord_progression)]
            melody_data = self.melody_gen.generate(
                key=key,
                scale="major" if style not in ["jazz"] else "minor",
                tempo=tempo,
                bars=config["bars"],
                chord_progression=section_chords
            )
            
            # Create section
            section = {
                "type": section_type,
                "start_time": current_time,
                "duration": config["bars"] * (240 / tempo),  # Duration in seconds
                "beat_pattern": beat_pattern.tolist(),
                "melody": melody_data,
                "chords": section_chords,
                "energy": config["energy"],
                "bars": config["bars"]
            }
            
            sections.append(section)
            current_time += section["duration"]
            
            # Stop if we've reached the target duration
            if current_time >= total_duration:
                break
        
        return {
            "style": style,
            "tempo": tempo,
            "key": key,
            "structure": structure,
            "sections": sections,
            "total_duration": current_time,
            "chord_progression": chord_progression
        }
    
    def _generate_song_chords(self, key: str, style: str, num_sections: int) -> List[List[str]]:
        """Generate chord progressions for each section"""
        
        # Get base progressions from harmony suggester
        progressions = self.harmony_suggest.suggest(
            key=key,
            genre=style,
            mood="happy",
            bars=4
        )
        
        if not progressions:
            # Fallback progressions
            base_prog = ["I", "V", "vi", "IV"]
        else:
            base_prog = progressions[0]["chords"]
        
        # Create variations for different sections
        section_progressions = []
        
        for i in range(num_sections):
            if i == 0 or i == num_sections - 1:  # Intro/Outro
                prog = base_prog[:2] * 2  # Simpler progression
            elif i % 2 == 1:  # Verses (odd indices)
                prog = base_prog
            else:  # Choruses/other sections
                # Add tension with secondary dominants
                prog = self._add_harmonic_tension(base_prog)
            
            section_progressions.append(prog)
        
        return section_progressions
    
    def _add_harmonic_tension(self, base_progression: List[str]) -> List[str]:
        """Add harmonic tension to progression"""
        enhanced = base_progression.copy()
        
        # Add some jazz chords or secondary dominants
        substitutions = {
            "I": ["IMaj7", "I6"],
            "V": ["V7", "V9"],
            "vi": ["vi7", "vim7"],
            "IV": ["IVMaj7", "IVadd9"]
        }
        
        for i, chord in enumerate(enhanced):
            if chord in substitutions and random.random() < 0.3:
                enhanced[i] = random.choice(substitutions[chord])
        
        return enhanced
    
    def generate_arrangement_variations(self, base_song: Dict, num_variations: int = 3) -> List[Dict]:
        """Generate multiple arrangement variations of the same song"""
        
        variations = []
        base_style = base_song["style"]
        
        # Different style variations
        style_variations = {
            "pop": ["acoustic", "electronic", "rock"],
            "rock": ["metal", "indie", "progressive"],
            "hip-hop": ["trap", "boom-bap", "experimental"],
            "electronic": ["house", "techno", "ambient"],
            "jazz": ["fusion", "bebop", "smooth"]
        }
        
        target_styles = style_variations.get(base_style, ["alternative", "remix", "acoustic"])
        
        for i in range(min(num_variations, len(target_styles))):
            variation = base_song.copy()
            variation["style"] = target_styles[i]
            variation["variation_id"] = i + 1
            
            # Modify sections for the new style
            modified_sections = []
            for section in variation["sections"]:
                modified_section = section.copy()
                
                # Regenerate beat with new style characteristics
                style_complexity = self._get_style_complexity(target_styles[i])
                modified_section["beat_pattern"] = self.beat_gen.generate(
                    genre=target_styles[i] if target_styles[i] in ["rock", "jazz", "electronic"] else base_style,
                    tempo=variation["tempo"],
                    bars=section["bars"],
                    complexity=style_complexity
                ).tolist()
                
                modified_sections.append(modified_section)
            
            variation["sections"] = modified_sections
            variations.append(variation)
        
        return variations
    
    def _get_style_complexity(self, style: str) -> float:
        """Get complexity factor for different styles"""
        complexity_map = {
            "acoustic": 0.4,
            "electronic": 0.8,
            "metal": 0.9,
            "ambient": 0.3,
            "trap": 0.7,
            "techno": 0.8,
            "fusion": 0.9,
            "indie": 0.5
        }
        return complexity_map.get(style, 0.6)