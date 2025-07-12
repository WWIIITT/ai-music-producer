# server/audio/processor.py
import numpy as np
import librosa
import soundfile as sf
import pretty_midi
from typing import Dict, List, Optional
import os
from datetime import datetime

class AudioProcessor:
    def __init__(self):
        self.sample_rate = 44100
        self.drum_samples = {
            "kick": self._generate_kick(),
            "snare": self._generate_snare(),
            "hihat_closed": self._generate_hihat_closed(),
            "hihat_open": self._generate_hihat_open(),
            "crash": self._generate_crash(),
            "ride": self._generate_ride(),
            "tom_high": self._generate_tom(pitch=1.2),
            "tom_mid": self._generate_tom(pitch=1.0),
            "tom_low": self._generate_tom(pitch=0.8)
        }
    
    def pattern_to_audio(self, pattern: np.ndarray, tempo: int = 120, 
                        output_dir: str = "./temp") -> str:
        """Convert drum pattern to audio file"""
        
        # Calculate timing
        beat_duration = 60.0 / tempo / 4  # 16th note duration
        total_duration = pattern.shape[1] * beat_duration
        total_samples = int(total_duration * self.sample_rate)
        
        # Initialize audio buffer
        audio = np.zeros(total_samples)
        
        # Drum mapping
        drum_names = ["kick", "snare", "hihat_closed", "hihat_open", 
                     "crash", "ride", "tom_high", "tom_mid", "tom_low"]
        
        # Render each drum
        for drum_idx, drum_name in enumerate(drum_names):
            if drum_idx < pattern.shape[0]:
                drum_sample = self.drum_samples[drum_name]
                
                # Place hits
                for step in range(pattern.shape[1]):
                    if pattern[drum_idx, step] > 0:
                        start_sample = int(step * beat_duration * self.sample_rate)
                        end_sample = min(start_sample + len(drum_sample), total_samples)
                        sample_end = end_sample - start_sample
                        
                        # Add with velocity
                        velocity = pattern[drum_idx, step]
                        audio[start_sample:end_sample] += drum_sample[:sample_end] * velocity
        
        # Normalize
        audio = audio / np.max(np.abs(audio)) * 0.8
        
        # Save
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"beat_{tempo}bpm_{timestamp}.wav"
        filepath = os.path.join(output_dir, filename)
        sf.write(filepath, audio, self.sample_rate)
        
        return filepath
    
    def melody_to_midi(self, melody_data: Dict, tempo: int = 120,
                      output_dir: str = "./temp") -> str:
        """Convert melody data to MIDI file"""
        
        # Create MIDI object
        midi = pretty_midi.PrettyMIDI(initial_tempo=tempo)
        
        # Create instrument
        instrument = pretty_midi.Instrument(program=0)  # Piano
        
        # Add notes
        current_time = 0
        notes = melody_data["notes"]
        durations = melody_data["durations"]
        
        for note, duration in zip(notes, durations):
            # Create note
            velocity = 80
            note_obj = pretty_midi.Note(
                velocity=velocity,
                pitch=int(note),
                start=current_time,
                end=current_time + duration
            )
            instrument.notes.append(note_obj)
            current_time += duration
        
        # Add instrument to MIDI
        midi.instruments.append(instrument)
        
        # Save
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"melody_{melody_data['key']}_{melody_data['scale']}_{timestamp}.mid"
        filepath = os.path.join(output_dir, filename)
        midi.write(filepath)
        
        return filepath
    
    def midi_to_audio(self, midi_path: str) -> str:
        """Convert MIDI to audio (simplified version)"""
        # In production, you'd use FluidSynth or similar
        # For now, we'll create a simple sine wave version
        
        midi = pretty_midi.PrettyMIDI(midi_path)
        
        # Get total duration
        duration = midi.get_end_time()
        samples = int(duration * self.sample_rate)
        audio = np.zeros(samples)
        
        # Render each note
        for instrument in midi.instruments:
            for note in instrument.notes:
                # Generate sine wave for note
                freq = pretty_midi.note_number_to_hz(note.pitch)
                start_sample = int(note.start * self.sample_rate)
                end_sample = int(note.end * self.sample_rate)
                
                t = np.arange(end_sample - start_sample) / self.sample_rate
                note_audio = np.sin(2 * np.pi * freq * t) * 0.3
                
                # Apply envelope
                envelope = np.exp(-t * 2)  # Simple decay
                note_audio *= envelope
                
                # Add to audio
                audio[start_sample:end_sample] += note_audio
        
        # Normalize
        audio = audio / np.max(np.abs(audio)) * 0.8
        
        # Save
        audio_path = midi_path.replace('.mid', '.wav')
        sf.write(audio_path, audio, self.sample_rate)
        
        return audio_path
    
    def chords_to_audio(self, chords: List[str], tempo: int = 120,
                       output_dir: str = "./temp") -> str:
        """Convert chord progression to audio"""
        
        # Chord definitions (simplified)
        chord_notes = {
            "I": [60, 64, 67],      # C major
            "ii": [62, 65, 69],     # D minor
            "iii": [64, 67, 71],    # E minor
            "IV": [65, 69, 72],     # F major
            "V": [67, 71, 74],      # G major
            "vi": [69, 72, 76],     # A minor
            "vii°": [71, 74, 77],   # B diminished
        }
        
        # Calculate duration
        beat_duration = 60.0 / tempo
        chord_duration = beat_duration  # One chord per beat
        total_duration = len(chords) * chord_duration
        samples = int(total_duration * self.sample_rate)
        audio = np.zeros(samples)
        
        # Render each chord
        for i, chord in enumerate(chords):
            # Get base chord name (remove extensions)
            base_chord = chord.replace("Maj7", "").replace("7", "").replace("°", "")
            
            if base_chord in chord_notes:
                notes = chord_notes[base_chord]
                
                # Calculate position
                start_sample = int(i * chord_duration * self.sample_rate)
                end_sample = int((i + 1) * chord_duration * self.sample_rate)
                
                # Generate chord
                t = np.arange(end_sample - start_sample) / self.sample_rate
                chord_audio = np.zeros_like(t)
                
                for note in notes:
                    freq = pretty_midi.note_number_to_hz(note)
                    chord_audio += np.sin(2 * np.pi * freq * t) * 0.3
                
                # Apply envelope
                envelope = np.ones_like(t)
                envelope[:100] = np.linspace(0, 1, 100)  # Fade in
                envelope[-100:] = np.linspace(1, 0, 100)  # Fade out
                chord_audio *= envelope
                
                # Add to audio
                audio[start_sample:end_sample] += chord_audio
        
        # Normalize
        audio = audio / np.max(np.abs(audio)) * 0.8
        
        # Save
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"chords_{timestamp}.wav"
        filepath = os.path.join(output_dir, filename)
        sf.write(filepath, audio, self.sample_rate)
        
        return filepath
    
    def analyze(self, audio_path: str) -> Dict:
        """Analyze audio file"""
        
        # Load audio
        y, sr = librosa.load(audio_path)
        
        # Tempo and beat tracking
        tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
        
        # Key detection (simplified)
        chroma = librosa.feature.chroma_stft(y=y, sr=sr)
        key_profile = np.mean(chroma, axis=1)
        keys = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        estimated_key = keys[np.argmax(key_profile)]
        
        # Energy
        energy = np.mean(librosa.feature.rms(y=y))
        
        # Time signature (simplified - just detect 3/4 vs 4/4)
        beat_times = librosa.frames_to_time(beats, sr=sr)
        if len(beat_times) > 4:
            beat_intervals = np.diff(beat_times[:4])
            if np.std(beat_intervals) < 0.1:
                time_signature = "4/4"
            else:
                time_signature = "3/4"
        else:
            time_signature = "4/4"
        
        # Genre classification (simplified)
        # In production, you'd use a trained model
        spectral_centroid = np.mean(librosa.feature.spectral_centroid(y=y, sr=sr))
        if spectral_centroid > 3000:
            genre = "electronic"
        elif tempo > 140:
            genre = "rock"
        elif tempo < 100:
            genre = "jazz"
        else:
            genre = "pop"
        
        return {
            "tempo": float(tempo),
            "key": estimated_key,
            "genre": genre,
            "time_signature": time_signature,
            "energy": float(energy)
        }
    
    # Drum synthesis methods
    def _generate_kick(self, duration=0.5):
        """Generate kick drum sample"""
        t = np.linspace(0, duration, int(duration * self.sample_rate))
        # Start with low sine wave
        kick = np.sin(2 * np.pi * 60 * t)
        # Add pitch envelope
        pitch_env = np.exp(-35 * t)
        kick *= pitch_env
        # Add click
        click = np.random.normal(0, 0.1, len(t)) * np.exp(-100 * t)
        return kick + click
    
    def _generate_snare(self, duration=0.2):
        """Generate snare drum sample"""
        t = np.linspace(0, duration, int(duration * self.sample_rate))
        # Noise component
        snare = np.random.normal(0, 0.3, len(t))
        # Add tonal component
        tone = np.sin(2 * np.pi * 200 * t) * 0.5
        # Envelope
        envelope = np.exp(-20 * t)
        return (snare + tone) * envelope
    
    def _generate_hihat_closed(self, duration=0.05):
        """Generate closed hi-hat sample"""
        t = np.linspace(0, duration, int(duration * self.sample_rate))
        # High frequency noise
        hihat = np.random.normal(0, 0.2, len(t))
        # Filter (simplified - just envelope)
        envelope = np.exp(-50 * t)
        return hihat * envelope
    
    def _generate_hihat_open(self, duration=0.3):
        """Generate open hi-hat sample"""
        t = np.linspace(0, duration, int(duration * self.sample_rate))
        # High frequency noise
        hihat = np.random.normal(0, 0.25, len(t))
        # Longer envelope
        envelope = np.exp(-5 * t)
        return hihat * envelope
    
    def _generate_crash(self, duration=2.0):
        """Generate crash cymbal sample"""
        t = np.linspace(0, duration, int(duration * self.sample_rate))
        # Wide spectrum noise
        crash = np.random.normal(0, 0.3, len(t))
        # Add some metallic frequencies
        for freq in [3000, 4500, 6000, 8000]:
            crash += np.sin(2 * np.pi * freq * t) * 0.05
        # Long envelope
        envelope = np.exp(-1 * t)
        return crash * envelope
    
    def _generate_ride(self, duration=1.0):
        """Generate ride cymbal sample"""
        t = np.linspace(0, duration, int(duration * self.sample_rate))
        # Bell tone
        ride = np.sin(2 * np.pi * 800 * t) * 0.3
        # Add harmonics
        ride += np.sin(2 * np.pi * 1600 * t) * 0.15
        ride += np.sin(2 * np.pi * 2400 * t) * 0.1
        # Add some noise
        ride += np.random.normal(0, 0.05, len(t))
        # Envelope
        envelope = np.exp(-2 * t)
        return ride * envelope
    
    def _generate_tom(self, duration=0.4, pitch=1.0):
        """Generate tom sample"""
        t = np.linspace(0, duration, int(duration * self.sample_rate))
        # Base frequency adjusted by pitch
        base_freq = 100 * pitch
        tom = np.sin(2 * np.pi * base_freq * t)
        # Add harmonics
        tom += np.sin(2 * np.pi * base_freq * 2 * t) * 0.3
        # Add attack
        attack = np.random.normal(0, 0.1, len(t)) * np.exp(-50 * t)
        # Envelope
        envelope = np.exp(-8 * t)
        return (tom + attack) * envelope