# server/audio/mp4_exporter.py
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from moviepy.editor import VideoFileClip, AudioFileClip, CompositeVideoClip
import librosa
import cv2
import tempfile
import os
from typing import Dict, Optional
import soundfile as sf

class MP4Exporter:
    def __init__(self):
        self.sample_rate = 44100
        self.fps = 30
        self.resolution = (1920, 1080)  # HD resolution
    
    def create_music_video(self, audio_path: str, song_data: Dict, 
                          output_path: str, style: str = "waveform") -> str:
        """Create MP4 music video with audio and visuals"""
        
        print(f"🎬 Creating MP4 music video: {style}")
        
        try:
            # Load audio
            audio, sr = librosa.load(audio_path, sr=self.sample_rate)
            duration = len(audio) / sr
            
            # Create temporary video file
            with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_video:
                temp_video_path = temp_video.name
            
            # Generate video based on style
            if style == "waveform":
                self._create_waveform_video(audio, duration, temp_video_path, song_data)
            elif style == "spectrum":
                self._create_spectrum_video(audio_path, duration, temp_video_path, song_data)
            elif style == "particles":
                self._create_particle_video(audio, duration, temp_video_path, song_data)
            else:
                self._create_waveform_video(audio, duration, temp_video_path, song_data)
            
            # Combine video with audio
            final_path = self._combine_audio_video(audio_path, temp_video_path, output_path)
            
            # Cleanup
            if os.path.exists(temp_video_path):
                os.remove(temp_video_path)
            
            print(f"✅ MP4 created: {final_path}")
            return final_path
            
        except Exception as e:
            print(f"❌ MP4 creation error: {str(e)}")
            raise
    
    def _create_waveform_video(self, audio: np.ndarray, duration: float, 
                              output_path: str, song_data: Dict):
        """Create waveform visualization video"""
        
        # Setup video writer
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, self.fps, self.resolution)
        
        # Calculate frames
        total_frames = int(duration * self.fps)
        samples_per_frame = len(audio) // total_frames if total_frames > 0 else len(audio)
        
        # Colors based on style
        colors = self._get_style_colors(song_data.get("style", "pop"))
        
        for frame_idx in range(total_frames):
            # Create frame
            frame = np.zeros((self.resolution[1], self.resolution[0], 3), dtype=np.uint8)
            
            # Get audio segment for this frame
            start_sample = frame_idx * samples_per_frame
            end_sample = min(start_sample + samples_per_frame * 10, len(audio))  # Look ahead for smoother animation
            
            if start_sample < len(audio):
                audio_segment = audio[start_sample:end_sample]
                
                # Draw waveform
                self._draw_waveform(frame, audio_segment, colors, frame_idx, total_frames)
                
                # Add song info
                self._draw_song_info(frame, song_data, frame_idx, total_frames)
            
            # Write frame
            out.write(frame)
        
        out.release()
    
    def _create_spectrum_video(self, audio_path: str, duration: float, 
                              output_path: str, song_data: Dict):
        """Create spectrum analyzer visualization"""
        
        # Load audio for spectral analysis
        audio, sr = librosa.load(audio_path, sr=self.sample_rate)
        
        # Compute spectrograms
        hop_length = 512
        n_fft = 2048
        stft = librosa.stft(audio, hop_length=hop_length, n_fft=n_fft)
        magnitude = np.abs(stft)
        
        # Setup video writer
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, self.fps, self.resolution)
        
        total_frames = int(duration * self.fps)
        frames_per_stft = len(magnitude[0]) // total_frames if total_frames > 0 else 1
        
        colors = self._get_style_colors(song_data.get("style", "pop"))
        
        for frame_idx in range(total_frames):
            frame = np.zeros((self.resolution[1], self.resolution[0], 3), dtype=np.uint8)
            
            # Get spectral data for this frame
            stft_idx = min(frame_idx * frames_per_stft, len(magnitude[0]) - 1)
            spectrum = magnitude[:, stft_idx]
            
            # Draw spectrum analyzer
            self._draw_spectrum(frame, spectrum, colors, frame_idx, total_frames)
            
            # Add song info
            self._draw_song_info(frame, song_data, frame_idx, total_frames)
            
            out.write(frame)
        
        out.release()
    
    def _create_particle_video(self, audio: np.ndarray, duration: float, 
                              output_path: str, song_data: Dict):
        """Create particle system visualization"""
        
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, self.fps, self.resolution)
        
        # Initialize particles
        num_particles = 100
        particles = self._init_particles(num_particles)
        
        total_frames = int(duration * self.fps)
        samples_per_frame = len(audio) // total_frames if total_frames > 0 else len(audio)
        
        colors = self._get_style_colors(song_data.get("style", "pop"))
        
        for frame_idx in range(total_frames):
            frame = np.zeros((self.resolution[1], self.resolution[0], 3), dtype=np.uint8)
            
            # Get audio energy for this frame
            start_sample = frame_idx * samples_per_frame
            end_sample = min(start_sample + samples_per_frame, len(audio))
            
            if start_sample < len(audio):
                audio_segment = audio[start_sample:end_sample]
                energy = np.mean(np.abs(audio_segment))
                
                # Update and draw particles
                particles = self._update_particles(particles, energy)
                self._draw_particles(frame, particles, colors, energy)
            
            # Add song info
            self._draw_song_info(frame, song_data, frame_idx, total_frames)
            
            out.write(frame)
        
        out.release()
    
    def _draw_waveform(self, frame: np.ndarray, audio: np.ndarray, 
                      colors: Dict, frame_idx: int, total_frames: int):
        """Draw waveform on frame"""
        
        h, w = frame.shape[:2]
        center_y = h // 2
        
        # Downsample audio to fit frame width
        if len(audio) > w:
            step = len(audio) // w
            audio_downsampled = audio[::step][:w]
        else:
            audio_downsampled = np.pad(audio, (0, w - len(audio)), mode='constant')
        
        # Normalize and scale
        if np.max(np.abs(audio_downsampled)) > 0:
            audio_downsampled = audio_downsampled / np.max(np.abs(audio_downsampled))
        
        # Draw waveform
        prev_y = center_y
        for x, sample in enumerate(audio_downsampled):
            y = int(center_y + sample * (h // 4))  # Scale to quarter height
            
            # Draw line from previous point
            cv2.line(frame, (x-1, prev_y), (x, y), colors["primary"], 2)
            prev_y = y
        
        # Draw center line
        cv2.line(frame, (0, center_y), (w, center_y), colors["secondary"], 1)
    
    def _draw_spectrum(self, frame: np.ndarray, spectrum: np.ndarray, 
                      colors: Dict, frame_idx: int, total_frames: int):
        """Draw spectrum analyzer"""
        
        h, w = frame.shape[:2]
        
        # Use lower frequencies for better visualization
        spectrum = spectrum[:len(spectrum)//4]  # Use bottom quarter of spectrum
        
        if len(spectrum) == 0:
            return
        
        # Normalize
        if np.max(spectrum) > 0:
            spectrum = spectrum / np.max(spectrum)
        
        # Draw bars
        bar_width = w // len(spectrum)
        
        for i, magnitude in enumerate(spectrum):
            bar_height = int(magnitude * h * 0.8)  # Scale to 80% of frame height
            x = i * bar_width
            
            # Color based on frequency (low = red, high = blue)
            color_intensity = int(255 * magnitude)
            color = (
                min(255, color_intensity),  # Blue
                min(255, color_intensity // 2),  # Green
                max(0, 255 - color_intensity)   # Red
            )
            
            cv2.rectangle(frame, (x, h - bar_height), (x + bar_width - 1, h), color, -1)
    
    def _draw_particles(self, frame: np.ndarray, particles: np.ndarray, 
                       colors: Dict, energy: float):
        """Draw particle system"""
        
        h, w = frame.shape[:2]
        
        for particle in particles:
            x, y, vx, vy, life = particle
            
            if life > 0:
                # Draw particle
                radius = max(1, int(life * 10 * energy))
                color = colors["primary"]
                cv2.circle(frame, (int(x), int(y)), radius, color, -1)
    
    def _draw_song_info(self, frame: np.ndarray, song_data: Dict, 
                       frame_idx: int, total_frames: int):
        """Draw song information overlay"""
        
        h, w = frame.shape[:2]
        
        # Song title (if available)
        title = song_data.get("title", f"{song_data.get('style', 'Generated')} Song")
        
        # Progress bar
        progress = frame_idx / total_frames if total_frames > 0 else 0
        bar_width = w // 2
        bar_height = 10
        bar_x = w // 4
        bar_y = h - 50
        
        # Draw progress bar background
        cv2.rectangle(frame, (bar_x, bar_y), (bar_x + bar_width, bar_y + bar_height), (50, 50, 50), -1)
        
        # Draw progress
        progress_width = int(bar_width * progress)
        cv2.rectangle(frame, (bar_x, bar_y), (bar_x + progress_width, bar_y + bar_height), (0, 255, 100), -1)
        
        # Draw text
        font = cv2.FONT_HERSHEY_SIMPLEX
        cv2.putText(frame, title, (50, 50), font, 1, (255, 255, 255), 2)
        
        # Draw style and tempo info
        info_text = f"Style: {song_data.get('style', 'Unknown')} | Tempo: {song_data.get('tempo', 120)} BPM | Key: {song_data.get('key', 'C')}"
        cv2.putText(frame, info_text, (50, h - 100), font, 0.7, (200, 200, 200), 1)
    
    def _get_style_colors(self, style: str) -> Dict:
        """Get color scheme based on music style"""
        
        color_schemes = {
            "pop": {"primary": (255, 100, 150), "secondary": (100, 255, 200)},
            "rock": {"primary": (50, 50, 255), "secondary": (255, 50, 50)},
            "hip-hop": {"primary": (255, 200, 50), "secondary": (150, 50, 255)},
            "jazz": {"primary": (100, 150, 255), "secondary": (255, 150, 100)},
            "electronic": {"primary": (0, 255, 255), "secondary": (255, 0, 255)},
            "classical": {"primary": (200, 200, 255), "secondary": (255, 200, 200)}
        }
        
        return color_schemes.get(style, color_schemes["pop"])
    
    def _init_particles(self, num_particles: int) -> np.ndarray:
        """Initialize particle system"""
        
        # [x, y, vx, vy, life]
        particles = np.random.rand(num_particles, 5)
        
        # Scale positions to screen
        particles[:, 0] *= self.resolution[0]  # x
        particles[:, 1] *= self.resolution[1]  # y
        
        # Random velocities
        particles[:, 2] = (np.random.rand(num_particles) - 0.5) * 4  # vx
        particles[:, 3] = (np.random.rand(num_particles) - 0.5) * 4  # vy
        
        # Life
        particles[:, 4] = np.random.rand(num_particles)
        
        return particles
    
    def _update_particles(self, particles: np.ndarray, energy: float) -> np.ndarray:
        """Update particle positions and properties"""
        
        # Update positions
        particles[:, 0] += particles[:, 2] * (1 + energy * 5)  # x += vx
        particles[:, 1] += particles[:, 3] * (1 + energy * 5)  # y += vy
        
        # Update life
        particles[:, 4] -= 0.01  # Decay life
        
        # Reset dead particles
        dead_mask = particles[:, 4] <= 0
        particles[dead_mask, 0] = np.random.rand(np.sum(dead_mask)) * self.resolution[0]
        particles[dead_mask, 1] = np.random.rand(np.sum(dead_mask)) * self.resolution[1]
        particles[dead_mask, 4] = 1.0  # Reset life
        
        # Wrap around screen edges
        particles[:, 0] = particles[:, 0] % self.resolution[0]
        particles[:, 1] = particles[:, 1] % self.resolution[1]
        
        return particles
    
    def _combine_audio_video(self, audio_path: str, video_path: str, output_path: str) -> str:
        """Combine audio and video using moviepy"""
        
        try:
            # Load video and audio
            video_clip = VideoFileClip(video_path)
            audio_clip = AudioFileClip(audio_path)
            
            # Set audio to video
            final_clip = video_clip.set_audio(audio_clip)
            
            # Write final video
            final_clip.write_videofile(
                output_path,
                codec='libx264',
                audio_codec='aac',
                fps=self.fps,
                verbose=False,
                logger=None
            )
            
            # Close clips
            video_clip.close()
            audio_clip.close()
            final_clip.close()
            
            return output_path
            
        except Exception as e:
            print(f"❌ Error combining audio/video: {str(e)}")
            raise