# server/audio/processor.py - FIXED VERSION
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
        
        try:
            print(f"🥁 Converting pattern to audio: tempo={tempo}, shape={pattern.shape}")
            
            # Ensure output directory exists
            os.makedirs(output_dir, exist_ok=True)
            
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
                if drum_idx < pattern.shape[0] and drum_name in self.drum_samples:
                    drum_sample = self.drum_samples[drum_name]
                    
                    # Place hits
                    for step in range(pattern.shape[1]):
                        if pattern[drum_idx, step] > 0:
                            start_sample = int(step * beat_duration * self.sample_rate)
                            end_sample = min(start_sample + len(drum_sample), total_samples)
                            sample_end = end_sample - start_sample
                            
                            if sample_end > 0:
                                # Add with velocity
                                velocity = float(pattern[drum_idx, step])
                                audio[start_sample:end_sample] += drum_sample[:sample_end] * velocity
            
            # Normalize and prevent clipping
            if np.max(np.abs(audio)) > 0:
                audio = audio / np.max(np.abs(audio)) * 0.8
            
            # Save
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"beat_{tempo}bpm_{timestamp}.wav"
            filepath = os.path.join(output_dir, filename)
            sf.write(filepath, audio, self.sample_rate)
            
            print(f"✅ Beat audio saved: {filepath}")
            return filepath
            
        except Exception as e:
            print(f"❌ Error in pattern_to_audio: {str(e)}")
            import traceback
            traceback.print_exc()
            raise
    
    def melody_to_midi(self, melody_data: Dict, tempo: int = 120,
                      output_dir: str = "./temp") -> str:
        """Convert melody data to MIDI file - FIXED VERSION"""
        
        try:
            print(f"🎼 Converting melody to MIDI: tempo={tempo}")
            
            # Ensure output directory exists
            os.makedirs(output_dir, exist_ok=True)
            
            # Validate melody data
            if "notes" not in melody_data or "durations" not in melody_data:
                raise ValueError("Melody data must contain 'notes' and 'durations'")
            
            notes = melody_data["notes"]
            durations = melody_data["durations"]
            
            if len(notes) != len(durations):
                print(f"⚠️  Note/duration mismatch: {len(notes)} notes, {len(durations)} durations")
                # Trim to shorter length
                min_len = min(len(notes), len(durations))
                notes = notes[:min_len]
                durations = durations[:min_len]
            
            if not notes:
                raise ValueError("No notes to convert")
            
            print(f"🎵 Processing {len(notes)} notes")
            
            # Create MIDI object
            midi = pretty_midi.PrettyMIDI(initial_tempo=tempo)
            
            # Create instrument (Piano)
            instrument = pretty_midi.Instrument(program=0)
            
            # Convert durations to seconds (assuming durations are in beats)
            beat_duration = 60.0 / tempo  # seconds per beat
            
            # Add notes
            current_time = 0
            
            for i, (note_midi, duration) in enumerate(zip(notes, durations)):
                try:
                    # Ensure note is valid MIDI number
                    note_midi = int(note_midi)
                    if not (0 <= note_midi <= 127):
                        print(f"⚠️  Invalid MIDI note {note_midi}, clamping to valid range")
                        note_midi = max(0, min(127, note_midi))
                    
                    # Convert duration to seconds
                    duration_seconds = float(duration) * beat_duration
                    
                    if duration_seconds <= 0:
                        print(f"⚠️  Invalid duration {duration_seconds}, skipping note")
                        continue
                    
                    # Create note
                    velocity = 80  # Medium velocity
                    note_obj = pretty_midi.Note(
                        velocity=velocity,
                        pitch=note_midi,
                        start=current_time,
                        end=current_time + duration_seconds
                    )
                    instrument.notes.append(note_obj)
                    current_time += duration_seconds
                    
                except Exception as e:
                    print(f"⚠️  Error processing note {i}: {e}")
                    continue
            
            # Add instrument to MIDI
            midi.instruments.append(instrument)
            
            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            key = melody_data.get("key", "C")
            scale = melody_data.get("scale", "major")
            filename = f"melody_{key}_{scale}_{timestamp}.mid"
            filepath = os.path.join(output_dir, filename)
            
            # Save MIDI file
            midi.write(filepath)
            
            print(f"✅ MIDI saved: {filepath} ({len(instrument.notes)} notes, {current_time:.2f}s)")
            return filepath
            
        except Exception as e:
            print(f"❌ Error in melody_to_midi: {str(e)}")
            import traceback
            traceback.print_exc()
            raise
    
    def midi_to_audio(self, midi_path: str) -> str:
        """Convert MIDI to audio - IMPROVED VERSION"""
        
        try:
            print(f"🎹 Converting MIDI to audio: {midi_path}")
            
            # Load MIDI
            midi = pretty_midi.PrettyMIDI(midi_path)
            
            # Get total duration
            duration = midi.get_end_time()
            if duration <= 0:
                duration = 4.0  # Default 4 seconds
            
            samples = int(duration * self.sample_rate)
            audio = np.zeros(samples)
            
            print(f"🎵 MIDI duration: {duration:.2f}s, {len(midi.instruments)} instruments")
            
            # Render each note with improved synthesis
            for instrument in midi.instruments:
                print(f"🎶 Processing instrument with {len(instrument.notes)} notes")
                
                for note in instrument.notes:
                    # Generate more musical sound
                    freq = pretty_midi.note_number_to_hz(note.pitch)
                    start_sample = int(note.start * self.sample_rate)
                    end_sample = int(note.end * self.sample_rate)
                    
                    # Ensure valid sample range
                    start_sample = max(0, start_sample)
                    end_sample = min(samples, end_sample)
                    
                    if end_sample <= start_sample:
                        continue
                    
                    # Generate time array
                    note_samples = end_sample - start_sample
                    t = np.arange(note_samples) / self.sample_rate
                    
                    # Create more complex waveform (piano-like)
                    fundamental = np.sin(2 * np.pi * freq * t)
                    harmonic2 = 0.5 * np.sin(2 * np.pi * freq * 2 * t)
                    harmonic3 = 0.25 * np.sin(2 * np.pi * freq * 3 * t)
                    note_audio = (fundamental + harmonic2 + harmonic3) * 0.3
                    
                    # Apply realistic envelope (ADSR)
                    envelope = self._create_adsr_envelope(len(t), self.sample_rate)
                    note_audio *= envelope
                    
                    # Add velocity scaling
                    velocity_scale = note.velocity / 127.0
                    note_audio *= velocity_scale
                    
                    # Add to audio
                    try:
                        audio[start_sample:end_sample] += note_audio
                    except ValueError:
                        # Handle any remaining array size mismatches
                        min_len = min(len(audio[start_sample:end_sample]), len(note_audio))
                        audio[start_sample:start_sample + min_len] += note_audio[:min_len]
            
            # Normalize and prevent clipping
            if np.max(np.abs(audio)) > 0:
                audio = audio / np.max(np.abs(audio)) * 0.8
            
            # Save audio
            audio_path = midi_path.replace('.mid', '.wav')
            sf.write(audio_path, audio, self.sample_rate)
            
            print(f"✅ Audio saved: {audio_path}")
            return audio_path
            
        except Exception as e:
            print(f"❌ Error in midi_to_audio: {str(e)}")
            import traceback
            traceback.print_exc()
            raise
    
    def _create_adsr_envelope(self, length: int, sample_rate: int) -> np.ndarray:
        """Create ADSR envelope for more realistic sound"""
        
        # ADSR parameters (in seconds)
        attack_time = 0.01   # Very quick attack
        decay_time = 0.1     # Quick decay
        sustain_level = 0.7  # Sustain at 70%
        release_time = 0.3   # Gradual release
        
        # Convert to samples
        attack_samples = int(attack_time * sample_rate)
        decay_samples = int(decay_time * sample_rate)
        release_samples = int(release_time * sample_rate)
        
        envelope = np.ones(length)
        
        # Attack
        if attack_samples > 0 and attack_samples < length:
            envelope[:attack_samples] = np.linspace(0, 1, attack_samples)
        
        # Decay
        decay_end = attack_samples + decay_samples
        if decay_end < length:
            envelope[attack_samples:decay_end] = np.linspace(1, sustain_level, decay_samples)
        
        # Release
        release_start = max(0, length - release_samples)
        if release_start < length:
            envelope[release_start:] = np.linspace(
                envelope[release_start], 0, length - release_start
            )
        
        return envelope
    
    def chords_to_audio(self, chords: List[str], tempo: int = 120,
                       output_dir: str = "./temp") -> str:
        """Convert chord progression to audio - IMPROVED"""
        
        try:
            print(f"🎹 Converting chords to audio: {chords}")
            
            # Ensure output directory exists
            os.makedirs(output_dir, exist_ok=True)
            
            # Chord definitions (more complete)
            chord_notes = {
                "I": [60, 64, 67],      # C major
                "i": [60, 63, 67],      # C minor
                "ii": [62, 65, 69],     # D minor
                "II": [62, 66, 69],     # D major
                "iii": [64, 67, 71],    # E minor
                "III": [64, 68, 71],    # E major
                "IV": [65, 69, 72],     # F major
                "iv": [65, 68, 72],     # F minor
                "V": [67, 71, 74],      # G major
                "v": [67, 70, 74],      # G minor
                "vi": [69, 72, 76],     # A minor
                "VI": [69, 73, 76],     # A major
                "vii°": [71, 74, 77],   # B diminished
                "VII": [71, 75, 78],    # B major
                "bVII": [70, 74, 77],   # Bb major
                "bVI": [68, 72, 75],    # Ab major
                "bIII": [63, 67, 70],   # Eb major
            }
            
            # Calculate duration
            beat_duration = 60.0 / tempo
            chord_duration = beat_duration * 2  # Two beats per chord
            total_duration = len(chords) * chord_duration
            samples = int(total_duration * self.sample_rate)
            audio = np.zeros(samples)
            
            # Render each chord
            for i, chord in enumerate(chords):
                # Get base chord name
                base_chord = chord.replace("Maj7", "").replace("7", "").replace("°", "")
                
                if base_chord in chord_notes:
                    notes = chord_notes[base_chord].copy()
                    
                    # Add 7th if specified
                    if "7" in chord:
                        if "Maj7" in chord:
                            notes.append(notes[0] + 11)  # Major 7th
                        else:
                            notes.append(notes[0] + 10)  # Minor 7th
                    
                    # Calculate position
                    start_sample = int(i * chord_duration * self.sample_rate)
                    end_sample = int((i + 1) * chord_duration * self.sample_rate)
                    end_sample = min(end_sample, samples)
                    
                    if end_sample <= start_sample:
                        continue
                    
                    # Generate chord
                    t = np.arange(end_sample - start_sample) / self.sample_rate
                    chord_audio = np.zeros_like(t)
                    
                    for note in notes:
                        freq = pretty_midi.note_number_to_hz(note)
                        # Create richer sound with harmonics
                        wave = np.sin(2 * np.pi * freq * t) * 0.4
                        wave += np.sin(2 * np.pi * freq * 2 * t) * 0.1  # Octave
                        chord_audio += wave
                    
                    # Apply envelope
                    envelope = self._create_adsr_envelope(len(t), self.sample_rate)
                    chord_audio *= envelope
                    
                    # Add to audio
                    audio[start_sample:end_sample] += chord_audio
            
            # Normalize
            if np.max(np.abs(audio)) > 0:
                audio = audio / np.max(np.abs(audio)) * 0.8
            
            # Save
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"chords_{timestamp}.wav"
            filepath = os.path.join(output_dir, filename)
            sf.write(filepath, audio, self.sample_rate)
            
            print(f"✅ Chords audio saved: {filepath}")
            return filepath
            
        except Exception as e:
            print(f"❌ Error in chords_to_audio: {str(e)}")
            import traceback
            traceback.print_exc()
            raise
    
    # Keep all the drum synthesis methods from before...
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