# server/audio/processor.py
import numpy as np
import soundfile as sf
from scipy.signal import butter, filtfilt
import tempfile
import os
from datetime import datetime
from typing import Dict, List, Optional
import mido
from mido import MidiFile, MidiTrack, Message

class AudioProcessor:
    def __init__(self):
        self.sample_rate = 44100
        self.bit_depth = 16
        
        # Drum sample synthesis parameters
        self.drum_samples = {
            "kick": {"freq": 60, "decay": 0.5, "type": "sine"},
            "snare": {"freq": 200, "decay": 0.2, "type": "noise"},
            "hihat": {"freq": 8000, "decay": 0.1, "type": "noise"},
            "crash": {"freq": 4000, "decay": 1.0, "type": "noise"},
            "ride": {"freq": 3000, "decay": 0.5, "type": "noise"}
        }
    
    def pattern_to_audio(self, pattern: np.ndarray, tempo: int = 120, 
                        output_dir: str = "./temp") -> str:
        """Convert drum pattern to audio file"""
        
        try:
            print(f"🥁 Converting pattern to audio: {pattern.shape}")
            
            # Calculate timing
            steps_per_beat = 4  # 16th notes
            beats_per_minute = tempo
            beats_per_second = beats_per_minute / 60
            seconds_per_step = 1 / (beats_per_second * steps_per_beat)
            
            # Calculate total duration
            num_steps = pattern.shape[1]
            total_duration = num_steps * seconds_per_step
            total_samples = int(total_duration * self.sample_rate)
            
            # Create audio buffer
            audio = np.zeros(total_samples)
            
            # Generate audio for each drum
            for drum_idx in range(pattern.shape[0]):
                drum_name = self._get_drum_name(drum_idx)
                
                for step_idx in range(num_steps):
                    velocity = pattern[drum_idx, step_idx]
                    
                    if velocity > 0:
                        # Calculate sample position
                        sample_pos = int(step_idx * seconds_per_step * self.sample_rate)
                        
                        # Generate drum sound
                        drum_audio = self._generate_drum_sound(drum_name, velocity)
                        
                        # Add to main audio buffer
                        end_pos = min(sample_pos + len(drum_audio), total_samples)
                        audio_len = end_pos - sample_pos
                        audio[sample_pos:end_pos] += drum_audio[:audio_len]
            
            # Normalize audio
            if np.max(np.abs(audio)) > 0:
                audio = audio / np.max(np.abs(audio)) * 0.8
            
            # Save to file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"beat_{timestamp}.wav"
            output_path = os.path.join(output_dir, filename)
            
            sf.write(output_path, audio, self.sample_rate)
            print(f"✅ Beat audio saved: {output_path}")
            
            return output_path
            
        except Exception as e:
            print(f"❌ Error converting pattern to audio: {str(e)}")
            raise
    
    def melody_to_midi(self, melody_data: Dict, tempo: int = 120, 
                      output_dir: str = "./temp") -> str:
        """Convert melody data to MIDI file"""
        
        try:
            print(f"🎹 Converting melody to MIDI")
            
            # Create MIDI file
            mid = MidiFile()
            track = MidiTrack()
            mid.tracks.append(track)
            
            # Set tempo
            track.append(Message('program_change', program=1, time=0))  # Piano
            
            # Calculate ticks per beat
            ticks_per_beat = mid.ticks_per_beat
            ticks_per_second = (tempo / 60) * ticks_per_beat
            
            current_time = 0
            notes = melody_data.get("notes", [])
            durations = melody_data.get("durations", [])
            
            for i, (note, duration) in enumerate(zip(notes, durations)):
                # Note on
                note_on_time = int(current_time * ticks_per_second) if i == 0 else 0
                track.append(Message('note_on', channel=0, note=int(note), 
                                   velocity=64, time=note_on_time))
                
                # Note off
                note_duration_ticks = int(duration * ticks_per_second)
                track.append(Message('note_off', channel=0, note=int(note), 
                                   velocity=64, time=note_duration_ticks))
                
                current_time += duration
            
            # Save MIDI file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"melody_{timestamp}.mid"
            output_path = os.path.join(output_dir, filename)
            
            mid.save(output_path)
            print(f"✅ MIDI saved: {output_path}")
            
            return output_path
            
        except Exception as e:
            print(f"❌ Error converting melody to MIDI: {str(e)}")
            raise
    
    def midi_to_audio(self, midi_path: str) -> str:
        """Convert MIDI file to audio (simplified version)"""
        
        try:
            print(f"🎵 Converting MIDI to audio: {midi_path}")
            
            # Load MIDI
            mid = MidiFile(midi_path)
            
            # Calculate duration
            total_time = 0
            for track in mid.tracks:
                track_time = 0
                for msg in track:
                    track_time += msg.time
                total_time = max(total_time, track_time)
            
            # Convert ticks to seconds
            tempo = 500000  # Default tempo (120 BPM)
            duration_seconds = mido.tick2second(total_time, mid.ticks_per_beat, tempo)
            
            # Generate simple sine wave audio from MIDI
            audio = self._midi_to_simple_audio(mid, duration_seconds)
            
            # Save audio file
            audio_path = midi_path.replace('.mid', '.wav')
            sf.write(audio_path, audio, self.sample_rate)
            print(f"✅ Audio saved: {audio_path}")
            
            return audio_path
            
        except Exception as e:
            print(f"❌ Error converting MIDI to audio: {str(e)}")
            raise
    
    def song_to_audio(self, song_data: Dict, output_dir: str = "./temp", 
                     suffix: str = "") -> str:
        """Convert complete song data to audio file"""
        
        try:
            print(f"🎼 Converting song to audio")
            
            sections = song_data.get("sections", [])
            if not sections:
                raise ValueError("No sections found in song data")
            
            # Calculate total duration
            total_duration = song_data.get("total_duration", 180)
            total_samples = int(total_duration * self.sample_rate)
            
            # Create audio buffer
            audio = np.zeros(total_samples)
            
            # Process each section
            for section in sections:
                start_time = section.get("start_time", 0)
                duration = section.get("duration", 8)
                section_type = section.get("type", "verse")
                
                # Calculate sample positions
                start_sample = int(start_time * self.sample_rate)
                end_sample = int((start_time + duration) * self.sample_rate)
                end_sample = min(end_sample, total_samples)
                
                if start_sample >= total_samples:
                    break
                
                # Generate section audio
                section_audio = self._generate_section_audio(section, duration)
                
                # Add to main buffer
                section_length = min(len(section_audio), end_sample - start_sample)
                audio[start_sample:start_sample + section_length] += section_audio[:section_length]
            
            # Normalize
            if np.max(np.abs(audio)) > 0:
                audio = audio / np.max(np.abs(audio)) * 0.8
            
            # Save file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            title = song_data.get("title", "song").replace(" ", "_")
            filename = f"{title}_{timestamp}{suffix}.wav"
            output_path = os.path.join(output_dir, filename)
            
            sf.write(output_path, audio, self.sample_rate)
            print(f"✅ Song audio saved: {output_path}")
            
            return output_path
            
        except Exception as e:
            print(f"❌ Error converting song to audio: {str(e)}")
            raise
    
    def chords_to_audio(self, chords: List[str], tempo: int = 120, 
                       output_dir: str = "./temp") -> str:
        """Convert chord progression to audio"""
        
        try:
            print(f"🎸 Converting chords to audio: {chords}")
            
            # Calculate timing
            chord_duration = 2.0  # 2 seconds per chord
            total_duration = len(chords) * chord_duration
            total_samples = int(total_duration * self.sample_rate)
            
            # Create audio buffer
            audio = np.zeros(total_samples)
            
            # Process each chord
            for i, chord in enumerate(chords):
                start_time = i * chord_duration
                start_sample = int(start_time * self.sample_rate)
                chord_samples = int(chord_duration * self.sample_rate)
                
                # Generate chord audio
                chord_audio = self._generate_chord_audio(chord, chord_duration)
                
                # Add to buffer
                end_sample = min(start_sample + len(chord_audio), total_samples)
                audio_len = end_sample - start_sample
                audio[start_sample:end_sample] += chord_audio[:audio_len]
            
            # Normalize
            if np.max(np.abs(audio)) > 0:
                audio = audio / np.max(np.abs(audio)) * 0.7
            
            # Save file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"chords_{timestamp}.wav"
            output_path = os.path.join(output_dir, filename)
            
            sf.write(output_path, audio, self.sample_rate)
            print(f"✅ Chord audio saved: {output_path}")
            
            return output_path
            
        except Exception as e:
            print(f"❌ Error converting chords to audio: {str(e)}")
            raise
    
    def _get_drum_name(self, drum_idx: int) -> str:
        """Get drum name from index"""
        drum_names = ["kick", "snare", "hihat", "hihat_open", "crash", 
                     "ride", "tom_high", "tom_mid", "tom_low"]
        return drum_names[drum_idx] if drum_idx < len(drum_names) else "kick"
    
    def _generate_drum_sound(self, drum_name: str, velocity: float = 1.0) -> np.ndarray:
        """Generate synthetic drum sound"""
        
        # Map drum names to basic types
        drum_map = {
            "kick": "kick",
            "snare": "snare", 
            "hihat": "hihat",
            "hihat_open": "hihat",
            "hihat_closed": "hihat",
            "crash": "crash",
            "ride": "ride",
            "tom_high": "kick",
            "tom_mid": "kick", 
            "tom_low": "kick"
        }
        
        drum_type = drum_map.get(drum_name, "kick")
        params = self.drum_samples.get(drum_type, self.drum_samples["kick"])
        
        duration = params["decay"]
        samples = int(duration * self.sample_rate)
        t = np.linspace(0, duration, samples)
        
        if params["type"] == "sine":
            # Generate sine wave (for kick)
            audio = np.sin(2 * np.pi * params["freq"] * t)
            # Add click for punch
            click = np.sin(2 * np.pi * params["freq"] * 3 * t[:samples//10])
            audio[:len(click)] += click * 0.5
        else:
            # Generate noise (for snare, hihat, etc.)
            audio = np.random.normal(0, 1, samples)
            # Filter for frequency content
            b, a = butter(4, params["freq"] / (self.sample_rate / 2), btype='high')
            audio = filtfilt(b, a, audio)
        
        # Apply envelope
        envelope = np.exp(-5 * t / duration)
        audio *= envelope
        
        # Apply velocity
        audio *= velocity
        
        return audio.astype(np.float32)
    
    def _midi_to_simple_audio(self, mid: MidiFile, duration: float) -> np.ndarray:
        """Convert MIDI to simple audio using sine waves"""
        
        total_samples = int(duration * self.sample_rate)
        audio = np.zeros(total_samples)
        
        # Track note events
        current_time = 0
        active_notes = {}
        
        for track in mid.tracks:
            track_time = 0
            
            for msg in track:
                track_time += mido.tick2second(msg.time, mid.ticks_per_beat, 500000)
                
                if msg.type == 'note_on' and msg.velocity > 0:
                    # Start note
                    freq = 440 * (2 ** ((msg.note - 69) / 12))  # A4 = 440Hz
                    active_notes[msg.note] = {
                        'freq': freq,
                        'start_time': track_time,
                        'velocity': msg.velocity / 127.0
                    }
                    
                elif msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
                    # End note
                    if msg.note in active_notes:
                        note_info = active_notes[msg.note]
                        note_duration = track_time - note_info['start_time']
                        
                        # Generate note audio
                        note_audio = self._generate_note_audio(
                            note_info['freq'],
                            note_duration,
                            note_info['velocity'],
                            note_info['start_time']
                        )
                        
                        # Add to main audio
                        start_sample = int(note_info['start_time'] * self.sample_rate)
                        end_sample = min(start_sample + len(note_audio), total_samples)
                        
                        if start_sample < total_samples:
                            audio_len = end_sample - start_sample
                            audio[start_sample:end_sample] += note_audio[:audio_len]
                        
                        del active_notes[msg.note]
        
        return audio.astype(np.float32)
    
    def _generate_note_audio(self, freq: float, duration: float, 
                           velocity: float, start_time: float) -> np.ndarray:
        """Generate audio for a single note"""
        
        samples = int(duration * self.sample_rate)
        t = np.linspace(0, duration, samples)
        
        # Generate sine wave
        audio = np.sin(2 * np.pi * freq * t) * velocity
        
        # Apply envelope
        attack_time = min(0.05, duration * 0.1)
        release_time = min(0.2, duration * 0.3)
        
        attack_samples = int(attack_time * self.sample_rate)
        release_samples = int(release_time * self.sample_rate)
        
        envelope = np.ones(samples)
        
        # Attack
        if attack_samples > 0:
            envelope[:attack_samples] = np.linspace(0, 1, attack_samples)
        
        # Release
        if release_samples > 0:
            envelope[-release_samples:] = np.linspace(1, 0, release_samples)
        
        audio *= envelope
        
        return audio.astype(np.float32)
    
    def _generate_section_audio(self, section: Dict, duration: float) -> np.ndarray:
        """Generate audio for a song section"""
        
        samples = int(duration * self.sample_rate)
        audio = np.zeros(samples)
        
        # Generate beat if available
        if "beat_pattern" in section:
            beat_pattern = np.array(section["beat_pattern"])
            beat_audio = self._pattern_to_simple_audio(beat_pattern, duration)
            audio += beat_audio[:len(audio)] * 0.6
        
        # Generate melody if available
        if "melody" in section:
            melody_audio = self._melody_to_simple_audio(section["melody"], duration)
            audio += melody_audio[:len(audio)] * 0.4
        
        return audio.astype(np.float32)
    
    def _pattern_to_simple_audio(self, pattern: np.ndarray, duration: float) -> np.ndarray:
        """Convert pattern to simple audio without saving"""
        
        samples = int(duration * self.sample_rate)
        audio = np.zeros(samples)
        
        steps_per_beat = 4
        beats_per_second = 2  # Simplified timing
        seconds_per_step = 1 / (beats_per_second * steps_per_beat)
        
        for drum_idx in range(pattern.shape[0]):
            drum_name = self._get_drum_name(drum_idx)
            
            for step_idx in range(pattern.shape[1]):
                velocity = pattern[drum_idx, step_idx]
                
                if velocity > 0:
                    sample_pos = int(step_idx * seconds_per_step * self.sample_rate)
                    
                    if sample_pos < samples:
                        drum_audio = self._generate_drum_sound(drum_name, velocity)
                        end_pos = min(sample_pos + len(drum_audio), samples)
                        audio_len = end_pos - sample_pos
                        audio[sample_pos:end_pos] += drum_audio[:audio_len]
        
        return audio
    
    def _melody_to_simple_audio(self, melody: Dict, duration: float) -> np.ndarray:
        """Convert melody to simple audio"""
        
        samples = int(duration * self.sample_rate)
        audio = np.zeros(samples)
        
        notes = melody.get("notes", [])
        durations = melody.get("durations", [])
        
        current_time = 0
        
        for note, note_duration in zip(notes, durations):
            if current_time >= duration:
                break
                
            # Generate note
            freq = 440 * (2 ** ((note - 69) / 12))
            note_audio = self._generate_note_audio(freq, note_duration, 0.5, current_time)
            
            # Add to audio
            start_sample = int(current_time * self.sample_rate)
            end_sample = min(start_sample + len(note_audio), samples)
            
            if start_sample < samples:
                audio_len = end_sample - start_sample
                audio[start_sample:end_sample] += note_audio[:audio_len]
            
            current_time += note_duration
        
        return audio
    
    def _generate_chord_audio(self, chord: str, duration: float) -> np.ndarray:
        """Generate audio for a chord"""
        
        samples = int(duration * self.sample_rate)
        t = np.linspace(0, duration, samples)
        
        # Simple chord mapping (just root + third + fifth)
        chord_intervals = {
            "I": [0, 4, 7],
            "ii": [2, 5, 9], 
            "iii": [4, 7, 11],
            "IV": [5, 9, 0],
            "V": [7, 11, 2],
            "vi": [9, 0, 4],
            "vii": [11, 2, 5]
        }
        
        # Get intervals for chord
        base_chord = chord.replace("Maj7", "").replace("7", "").replace("°", "")
        intervals = chord_intervals.get(base_chord, [0, 4, 7])
        
        # Generate chord tones
        audio = np.zeros(samples)
        base_freq = 220  # A3
        
        for interval in intervals:
            freq = base_freq * (2 ** (interval / 12))
            tone = np.sin(2 * np.pi * freq * t) * 0.3
            
            # Apply envelope
            envelope = np.exp(-2 * t / duration)
            tone *= envelope
            
            audio += tone
        
        return audio.astype(np.float32)