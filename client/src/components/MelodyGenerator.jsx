// client/src/components/MelodyGenerator.js
import React, { useState, useRef, useEffect } from 'react';
import {
  Box,
  Button,
  Grid,
  Paper,
  Typography,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  TextField,
  Chip,
  IconButton,
  Slider
} from '@mui/material';
import {
  PlayArrow,
  Stop,
  Piano,
  MusicNote,
  Download,
  VolumeUp,
  VolumeDown,
  VolumeMute
} from '@mui/icons-material';
import * as Tone from 'tone';
import axios from 'axios';
import toast from 'react-hot-toast';

const MelodyGenerator = ({  tempo, currentKey, masterGain, onMelodyGenerated, referenceFile }) => {
  const [scale, setScale] = useState('major');
  const [melodyBars, setMelodyBars] = useState(4);
  const [chordProgression, setChordProgression] = useState('');
  const [generatedMelody, setGeneratedMelody] = useState(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [melodyVolume, setMelodyVolume] = useState(70); // Individual volume for melodies (0-100)
  
  const synthRef = useRef(null);
  const partRef = useRef(null);
  const canvasRef = useRef(null);
  const melodyGainRef = useRef(null);

  const scales = ['major', 'minor', 'dorian', 'phrygian', 'lydian', 'mixolydian', 'aeolian', 'locrian'];
  
  useEffect(() => {
    // Initialize synth with melody-specific gain
    const initSynth = async () => {
      // Create melody-specific gain node
      const melodyGain = new Tone.Gain(melodyVolume / 100);
      melodyGainRef.current = melodyGain;
      
      // Connect to master gain if available, otherwise to destination
      if (masterGain) {
        melodyGain.connect(masterGain);
      } else {
        melodyGain.toDestination();
      }

      const synth = new Tone.PolySynth(Tone.Synth, {
        oscillator: {
          type: 'triangle'
        },
        envelope: {
          attack: 0.005,
          decay: 0.1,
          sustain: 0.3,
          release: 0.5
        }
      }).connect(melodyGain);
      
      synthRef.current = synth;
    };

    initSynth();

    return () => {
      if (partRef.current) {
        partRef.current.dispose();
      }
      if (synthRef.current) {
        synthRef.current.dispose();
      }
      if (melodyGainRef.current) {
        melodyGainRef.current.dispose();
      }
    };
  }, [masterGain]);

  useEffect(() => {
    // Update melody volume
    if (melodyGainRef.current) {
      melodyGainRef.current.gain.rampTo(melodyVolume / 100, 0.1);
    }
  }, [melodyVolume]);

  const generateMelody = async () => {
    setIsLoading(true);
    try {
      const chords = chordProgression ? chordProgression.split(',').map(c => c.trim()) : null;
      
      const response = await axios.post(`${import.meta.env.VITE_API_URL}/api/generate/melody`, {
        key: currentKey,
        scale,
        tempo,
        bars: melodyBars,
        chord_progression: chords
      });

      const melody = response.data;
      setGeneratedMelody(melody);
      
      // Create Tone.js part
      createMelodyPart(melody);
      
      // Draw piano roll
      drawPianoRoll(melody);
      
      // Notify parent
      onMelodyGenerated({
        ...melody,
        chordProgression: chords
      });

      toast.success('Melody generated!');
    } catch (error) {
      toast.error('Failed to generate melody');
      console.error(error);
    } finally {
      setIsLoading(false);
    }
  };

  const createMelodyPart = (melody) => {
    if (partRef.current) {
      partRef.current.dispose();
    }

    const notes = melody.notes.map((note, index) => ({
      note: Tone.Frequency(note, 'midi').toNote(),
      duration: melody.durations[index] * (60 / tempo),
      time: melody.durations.slice(0, index).reduce((a, b) => a + b, 0) * (60 / tempo)
    }));

    const part = new Tone.Part((time, note) => {
      synthRef.current.triggerAttackRelease(note.note, note.duration, time);
    }, notes);

    part.loop = true;
    part.loopEnd = melody.durations.reduce((a, b) => a + b, 0) * (60 / tempo);
    
    partRef.current = part;
  };

  const drawPianoRoll = (melody) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    const width = canvas.width;
    const height = canvas.height;
    
    // Clear canvas
    ctx.fillStyle = '#1e1e1e';
    ctx.fillRect(0, 0, width, height);
    
    // Get note range
    const minNote = Math.min(...melody.notes) - 2;
    const maxNote = Math.max(...melody.notes) + 2;
    const noteRange = maxNote - minNote;
    
    // Draw grid
    ctx.strokeStyle = '#333';
    ctx.lineWidth = 1;
    
    // Horizontal lines (notes)
    for (let i = 0; i <= noteRange; i++) {
      const y = (i / noteRange) * height;
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(width, y);
      ctx.stroke();
    }
    
    // Draw notes
    let currentTime = 0;
    const totalDuration = melody.durations.reduce((a, b) => a + b, 0);
    
    melody.notes.forEach((note, index) => {
      const duration = melody.durations[index];
      const x = (currentTime / totalDuration) * width;
      const w = (duration / totalDuration) * width - 2;
      const y = ((maxNote - note) / noteRange) * height;
      const h = height / noteRange - 2;
      
      // Note color based on pitch
      const hue = ((note - 60) * 10) % 360;
      ctx.fillStyle = `hsl(${hue}, 70%, 50%)`;
      ctx.fillRect(x, y, w, h);
      
      currentTime += duration;
    });
  };

  const handlePlayStop = () => {
    if (isPlaying) {
      Tone.Transport.stop();
      if (partRef.current) {
        partRef.current.stop();
      }
    } else {
      Tone.Transport.start();
      if (partRef.current) {
        partRef.current.start(0);
      }
    }
    setIsPlaying(!isPlaying);
  };

  const handleVolumeChange = (event, newValue) => {
    setMelodyVolume(newValue);
  };

  const handleMuteToggle = () => {
    if (melodyVolume > 0) {
      setMelodyVolume(0);
    } else {
      setMelodyVolume(70);
    }
  };

  const getVolumeIcon = () => {
    if (melodyVolume === 0) return <VolumeMute />;
    if (melodyVolume < 50) return <VolumeDown />;
    return <VolumeUp />;
  };

  const downloadMIDI = async () => {
    if (!generatedMelody || !generatedMelody.midi_url) return;
    
    try {
      window.open(`${import.meta.env.VITE_API_URL}${generatedMelody.midi_url}`, '_blank');
      toast.success('MIDI downloaded!');
    } catch (error) {
      toast.error('Failed to download MIDI');
    }
  };

  return (
    <Box>
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={12} md={2}>
          <FormControl fullWidth>
            <InputLabel>Scale</InputLabel>
            <Select value={scale} onChange={(e) => setScale(e.target.value)}>
              {scales.map(s => (
                <MenuItem key={s} value={s}>
                  {s.charAt(0).toUpperCase() + s.slice(1)}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </Grid>
        
        <Grid item xs={12} md={2}>
          <FormControl fullWidth>
            <InputLabel>Bars</InputLabel>
            <Select value={melodyBars} onChange={(e) => setMelodyBars(e.target.value)}>
              <MenuItem value={2}>2 Bars</MenuItem>
              <MenuItem value={4}>4 Bars</MenuItem>
              <MenuItem value={8}>8 Bars</MenuItem>
              <MenuItem value={16}>16 Bars</MenuItem>
            </Select>
          </FormControl>
        </Grid>
        
        <Grid item xs={12} md={3}>
          <TextField
            fullWidth
            label="Chord Progression (optional)"
            placeholder="e.g. I, V, vi, IV"
            value={chordProgression}
            onChange={(e) => setChordProgression(e.target.value)}
            helperText="Comma-separated chord symbols"
          />
        </Grid>

        {/* Melody Volume Control */}
        <Grid item xs={12} md={3}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <IconButton 
              onClick={handleMuteToggle}
              color="primary"
              size="small"
            >
              {getVolumeIcon()}
            </IconButton>
            <Typography variant="caption" sx={{ minWidth: 70 }}>
              Melody: {melodyVolume}
            </Typography>
            <Slider
              value={melodyVolume}
              onChange={handleVolumeChange}
              min={0}
              max={100}
              sx={{ 
                width: 80,
                '& .MuiSlider-thumb': {
                  color: '#2196F3'
                },
                '& .MuiSlider-track': {
                  color: '#2196F3'
                }
              }}
            />
          </Box>
        </Grid>
        
        <Grid item xs={12} md={2}>
          <Box sx={{ display: 'flex', gap: 1 }}>
            <Button
              variant="contained"
              onClick={generateMelody}
              disabled={isLoading}
              startIcon={<MusicNote />}
              fullWidth
            >
              Generate
            </Button>
            
            {generatedMelody && (
              <>
                <IconButton onClick={handlePlayStop} color="primary">
                  {isPlaying ? <Stop /> : <PlayArrow />}
                </IconButton>
                <IconButton onClick={downloadMIDI} color="secondary">
                  <Download />
                </IconButton>
              </>
            )}
          </Box>
        </Grid>
      </Grid>

      {/* Melody Visualization */}
      {generatedMelody && (
        <Paper sx={{ p: 2, bgcolor: '#2a2a2a' }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Typography variant="h6">Generated Melody</Typography>
            <Box sx={{ display: 'flex', gap: 1 }}>
              <Chip 
                label={`Volume: ${melodyVolume}%`} 
                size="small" 
                sx={{ bgcolor: '#2196F3', color: 'white' }}
              />
              <Chip label={`Key: ${currentKey} ${scale}`} />
              <Chip label={`${generatedMelody.notes.length} notes`} />
            </Box>
          </Box>
          
          <canvas
            ref={canvasRef}
            width={800}
            height={200}
            style={{
              width: '100%',
              height: 200,
              border: '1px solid #444',
              borderRadius: 4
            }}
          />
          
          <Box sx={{ mt: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
            <Piano fontSize="small" />
            <Typography variant="caption" color="text.secondary">
              Piano roll visualization - Higher notes appear at the top
            </Typography>
          </Box>
        </Paper>
      )}
    </Box>
  );
};

export default MelodyGenerator;