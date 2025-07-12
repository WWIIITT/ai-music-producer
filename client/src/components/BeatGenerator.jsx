// client/src/components/BeatGenerator.js
import React, { useState, useEffect, useRef } from 'react';
import {
  Box,
  Button,
  Grid,
  Paper,
  Typography,
  Slider,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  IconButton,
  Chip
} from '@mui/material';
import {
  PlayArrow,
  Stop,
  Refresh,
  VolumeUp,
  VolumeOff
} from '@mui/icons-material';
import * as Tone from 'tone';
import axios from 'axios';
import toast from 'react-hot-toast';

const BeatGenerator = ({ tempo, onBeatGenerated }) => {
  const [pattern, setPattern] = useState(null);
  const [genre, setGenre] = useState('hip-hop');
  const [complexity, setComplexity] = useState(0.7);
  const [bars, setBars] = useState(4);
  const [isPlaying, setIsPlaying] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [activeSteps, setActiveSteps] = useState([]);
  
  const sequencerRef = useRef(null);
  const samplerRef = useRef(null);

  const drumNames = ['Kick', 'Snare', 'Hi-Hat', 'Open Hat', 'Crash', 'Ride', 'Tom H', 'Tom M', 'Tom L'];
  const drumColors = ['#f44336', '#2196F3', '#4CAF50', '#FF9800', '#9C27B0', '#00BCD4', '#FFC107', '#795548', '#607D8B'];

  useEffect(() => {
    // Initialize drum sampler
    const sampler = new Tone.Sampler({
      urls: {
        C3: 'kick.wav',
        D3: 'snare.wav',
        E3: 'hihat_closed.wav',
        F3: 'hihat_open.wav',
        G3: 'crash.wav',
        A3: 'ride.wav',
        B3: 'tom_high.wav',
        C4: 'tom_mid.wav',
        D4: 'tom_low.wav'
      },
      baseUrl: '/samples/',
      onload: () => {
        console.log('Drums loaded');
      }
    }).toDestination();

    samplerRef.current = sampler;

    return () => {
      if (sequencerRef.current) {
        sequencerRef.current.dispose();
      }
      sampler.dispose();
    };
  }, []);

  const generateBeat = async () => {
    setIsLoading(true);
    try {
      const response = await axios.post(`${import.meta.env.VITE_API_URL}/api/generate/beat`, {
        genre,
        tempo,
        bars,
        complexity
      });

      const newPattern = response.data.pattern;
      setPattern(newPattern);
      
      // Update sequencer
      createSequencer(newPattern);
      
      // Notify parent
      onBeatGenerated({
        pattern: newPattern,
        genre,
        tempo,
        bars,
        audioUrl: response.data.audio_url
      });

      toast.success('Beat generated!');
    } catch (error) {
      toast.error('Failed to generate beat');
      console.error(error);
    } finally {
      setIsLoading(false);
    }
  };

  const createSequencer = (beatPattern) => {
    // Clear existing sequencer
    if (sequencerRef.current) {
      sequencerRef.current.stop();
      sequencerRef.current.dispose();
    }

    const numSteps = beatPattern[0].length;
    let currentStep = 0;

    const sequence = new Tone.Sequence((time, step) => {
      // Update active step visualization
      setActiveSteps([step]);

      // Play sounds for this step
      beatPattern.forEach((drumTrack, drumIndex) => {
        if (drumTrack[step] > 0) {
          const note = ['C3', 'D3', 'E3', 'F3', 'G3', 'A3', 'B3', 'C4', 'D4'][drumIndex];
          if (samplerRef.current && note) {
            samplerRef.current.triggerAttackRelease(note, '16n', time, drumTrack[step]);
          }
        }
      });

      currentStep = (currentStep + 1) % numSteps;
    }, [...Array(numSteps).keys()], '16n');

    sequence.start(0);
    sequencerRef.current = sequence;
  };

  const handlePlayStop = () => {
    if (isPlaying) {
      Tone.Transport.stop();
      setActiveSteps([]);
    } else {
      Tone.Transport.start();
    }
    setIsPlaying(!isPlaying);
  };

  const toggleStep = (drumIndex, stepIndex) => {
    if (!pattern) return;
    
    const newPattern = [...pattern];
    newPattern[drumIndex][stepIndex] = newPattern[drumIndex][stepIndex] > 0 ? 0 : 1;
    setPattern(newPattern);
    createSequencer(newPattern);
  };

  const clearPattern = () => {
    if (!pattern) return;
    
    const clearedPattern = pattern.map(track => track.map(() => 0));
    setPattern(clearedPattern);
    createSequencer(clearedPattern);
  };

  return (
    <Box>
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={12} md={3}>
          <FormControl fullWidth>
            <InputLabel>Genre</InputLabel>
            <Select value={genre} onChange={(e) => setGenre(e.target.value)}>
              <MenuItem value="hip-hop">Hip-Hop</MenuItem>
              <MenuItem value="rock">Rock</MenuItem>
              <MenuItem value="jazz">Jazz</MenuItem>
              <MenuItem value="electronic">Electronic</MenuItem>
            </Select>
          </FormControl>
        </Grid>
        
        <Grid item xs={12} md={3}>
          <FormControl fullWidth>
            <InputLabel>Bars</InputLabel>
            <Select value={bars} onChange={(e) => setBars(e.target.value)}>
              <MenuItem value={1}>1 Bar</MenuItem>
              <MenuItem value={2}>2 Bars</MenuItem>
              <MenuItem value={4}>4 Bars</MenuItem>
              <MenuItem value={8}>8 Bars</MenuItem>
            </Select>
          </FormControl>
        </Grid>
        
        <Grid item xs={12} md={3}>
          <Typography gutterBottom>Complexity</Typography>
          <Slider
            value={complexity}
            onChange={(e, val) => setComplexity(val)}
            min={0}
            max={1}
            step={0.1}
            marks
            valueLabelDisplay="auto"
          />
        </Grid>
        
        <Grid item xs={12} md={3}>
          <Box sx={{ display: 'flex', gap: 1 }}>
            <Button
              variant="contained"
              onClick={generateBeat}
              disabled={isLoading}
              startIcon={<Refresh />}
              fullWidth
            >
              Generate
            </Button>
            
            {pattern && (
              <IconButton onClick={handlePlayStop} color="primary">
                {isPlaying ? <Stop /> : <PlayArrow />}
              </IconButton>
            )}
          </Box>
        </Grid>
      </Grid>

      {/* Beat Grid */}
      {pattern && (
        <Paper sx={{ p: 2, bgcolor: '#2a2a2a' }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
            <Typography variant="h6">Beat Pattern</Typography>
            <Button size="small" onClick={clearPattern}>Clear</Button>
          </Box>
          
          <Box sx={{ overflowX: 'auto' }}>
            <Grid container spacing={0.5} sx={{ minWidth: pattern[0].length * 40 }}>
              {pattern.map((drumTrack, drumIndex) => (
                <Grid item xs={12} key={drumIndex}>
                  <Box sx={{ display: 'flex', alignItems: 'center' }}>
                    <Typography 
                      sx={{ 
                        width: 80, 
                        fontSize: '0.8rem',
                        color: drumColors[drumIndex] 
                      }}
                    >
                      {drumNames[drumIndex]}
                    </Typography>
                    
                    {drumTrack.map((step, stepIndex) => (
                      <Box
                        key={stepIndex}
                        onClick={() => toggleStep(drumIndex, stepIndex)}
                        sx={{
                          width: 32,
                          height: 32,
                          m: 0.25,
                          bgcolor: step > 0 ? drumColors[drumIndex] : '#444',
                          opacity: step > 0 ? step : 0.3,
                          border: activeSteps.includes(stepIndex) ? '2px solid white' : 'none',
                          borderRadius: 1,
                          cursor: 'pointer',
                          transition: 'all 0.1s',
                          '&:hover': {
                            opacity: 0.8
                          }
                        }}
                      />
                    ))}
                  </Box>
                </Grid>
              ))}
              
              {/* Beat markers */}
              <Grid item xs={12}>
                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                  <Box sx={{ width: 80 }} />
                  {pattern[0].map((_, index) => (
                    <Typography
                      key={index}
                      sx={{
                        width: 32,
                        m: 0.25,
                        textAlign: 'center',
                        fontSize: '0.7rem',
                        color: index % 4 === 0 ? '#fff' : '#666'
                      }}
                    >
                      {index % 4 === 0 ? (index / 4) + 1 : '·'}
                    </Typography>
                  ))}
                </Box>
              </Grid>
            </Grid>
          </Box>
        </Paper>
      )}
    </Box>
  );
};

export default BeatGenerator;