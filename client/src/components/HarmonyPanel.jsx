// client/src/components/HarmonyPanel.js
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
  Card,
  CardContent,
  CardActions,
  Chip,
  IconButton,
  Slider
} from '@mui/material';
import {
  PlayArrow,
  Stop,
  Favorite,
  FavoriteBorder,
  VolumeUp,
  VolumeDown,
  VolumeMute
} from '@mui/icons-material';
import * as Tone from 'tone';
import axios from 'axios';
import toast from 'react-hot-toast';

const HarmonyPanel = ({ currentKey, genre, masterGain, onHarmonySelected }) => {
  const [mood, setMood] = useState('happy');
  const [harmonies, setHarmonies] = useState([]);
  const [favorites, setFavorites] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [playingIndex, setPlayingIndex] = useState(null);
  const [harmonyVolume, setHarmonyVolume] = useState(65); // Individual volume for harmonies (0-100)
  
  const harmonyGainRef = useRef(null);
  const synthRef = useRef(null);
  
  const moods = ['happy', 'sad', 'energetic', 'calm', 'mysterious', 'uplifting'];

  useEffect(() => {
    // Initialize harmony synth with harmony-specific gain
    const initHarmonySynth = async () => {
      // Create harmony-specific gain node
      const harmonyGain = new Tone.Gain(harmonyVolume / 100);
      harmonyGainRef.current = harmonyGain;
      
      // Connect to master gain if available, otherwise to destination
      if (masterGain) {
        harmonyGain.connect(masterGain);
      } else {
        harmonyGain.toDestination();
      }

      // Create synth for chords
      const synth = new Tone.PolySynth(Tone.Synth, {
        oscillator: {
          type: 'sawtooth'
        },
        envelope: {
          attack: 0.1,
          decay: 0.3,
          sustain: 0.7,
          release: 1.0
        }
      }).connect(harmonyGain);
      
      synthRef.current = synth;
    };

    initHarmonySynth();

    return () => {
      if (synthRef.current) {
        synthRef.current.dispose();
      }
      if (harmonyGainRef.current) {
        harmonyGainRef.current.dispose();
      }
    };
  }, [masterGain]);

  useEffect(() => {
    // Update harmony volume
    if (harmonyGainRef.current) {
      harmonyGainRef.current.gain.rampTo(harmonyVolume / 100, 0.1);
    }
  }, [harmonyVolume]);
  
  const suggestHarmonies = async () => {
    setIsLoading(true);
    try {
      const response = await axios.post(`${import.meta.env.VITE_API_URL}/api/suggest/harmony`, {
        key: currentKey,
        genre,
        mood,
        bars: 4
      });

      setHarmonies(response.data.suggestions);
      toast.success('Harmony suggestions generated!');
    } catch (error) {
      toast.error('Failed to generate harmonies');
      console.error(error);
    } finally {
      setIsLoading(false);
    }
  };

  const playHarmony = async (harmony, index) => {
    if (playingIndex === index) {
      // Stop playing
      await Tone.Transport.stop();
      setPlayingIndex(null);
    } else {
      // Play this harmony
      setPlayingIndex(index);
      
      // Play chord progression
      const chordDuration = '2n';
      let time = 0;
      
      harmony.progression.chords.forEach((chord, i) => {
        // Convert chord symbol to notes (simplified)
        const chordNotes = getChordNotes(chord, currentKey);
        
        Tone.Transport.schedule((t) => {
          synthRef.current.triggerAttackRelease(chordNotes, chordDuration, t);
        }, time);
        
        time += Tone.Time(chordDuration).toSeconds();
      });
      
      await Tone.Transport.start();
      
      // Auto-stop after progression plays
      setTimeout(() => {
        Tone.Transport.stop();
        setPlayingIndex(null);
      }, time * 1000);
    }
  };

  const getChordNotes = (chordSymbol, key) => {
    // Simplified chord to notes conversion
    const keyNote = Tone.Frequency(key + '3').toMidi();
    const chordIntervals = {
      'I': [0, 4, 7],
      'ii': [2, 5, 9],
      'iii': [4, 7, 11],
      'IV': [5, 9, 0],
      'V': [7, 11, 2],
      'vi': [9, 0, 4],
      'vii°': [11, 2, 5]
    };
    
    const baseChord = chordSymbol.replace(/Maj7|7|°/g, '');
    const intervals = chordIntervals[baseChord] || [0, 4, 7];
    
    return intervals.map(interval => 
      Tone.Frequency(keyNote + interval, 'midi').toNote()
    );
  };

  const toggleFavorite = (index) => {
    if (favorites.includes(index)) {
      setFavorites(favorites.filter(i => i !== index));
    } else {
      setFavorites([...favorites, index]);
      onHarmonySelected(harmonies[index]);
    }
  };

  const handleVolumeChange = (event, newValue) => {
    setHarmonyVolume(newValue);
  };

  const handleMuteToggle = () => {
    if (harmonyVolume > 0) {
      setHarmonyVolume(0);
    } else {
      setHarmonyVolume(65);
    }
  };

  const getVolumeIcon = () => {
    if (harmonyVolume === 0) return <VolumeMute />;
    if (harmonyVolume < 50) return <VolumeDown />;
    return <VolumeUp />;
  };

  return (
    <Box>
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={12} md={3}>
          <FormControl fullWidth>
            <InputLabel>Mood</InputLabel>
            <Select value={mood} onChange={(e) => setMood(e.target.value)}>
              {moods.map(m => (
                <MenuItem key={m} value={m}>
                  {m.charAt(0).toUpperCase() + m.slice(1)}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </Grid>
        
        <Grid item xs={12} md={3}>
          <Box sx={{ pt: 2 }}>
            <Chip label={`Key: ${currentKey}`} sx={{ mr: 1 }} />
            <Chip label={`Genre: ${genre}`} />
          </Box>
        </Grid>

        {/* Harmony Volume Control */}
        <Grid item xs={12} md={3}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <IconButton 
              onClick={handleMuteToggle}
              color="primary"
              size="small"
            >
              {getVolumeIcon()}
            </IconButton>
            <Typography variant="caption" sx={{ minWidth: 80 }}>
              Harmony: {harmonyVolume}
            </Typography>
            <Slider
              value={harmonyVolume}
              onChange={handleVolumeChange}
              min={0}
              max={100}
              sx={{ 
                width: 80,
                '& .MuiSlider-thumb': {
                  color: '#9C27B0'
                },
                '& .MuiSlider-track': {
                  color: '#9C27B0'
                }
              }}
            />
          </Box>
        </Grid>
        
        <Grid item xs={12} md={3}>
          <Button
            variant="contained"
            onClick={suggestHarmonies}
            disabled={isLoading}
            fullWidth
            sx={{ height: '100%' }}
          >
            Get Suggestions
          </Button>
        </Grid>
      </Grid>

      {/* Harmony Cards */}
      <Grid container spacing={2}>
        {harmonies.map((harmony, index) => (
          <Grid item xs={12} md={6} key={index}>
            <Card sx={{ bgcolor: '#2a2a2a' }}>
              <CardContent>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
                  <Typography variant="h6">
                    Suggestion {index + 1}
                  </Typography>
                  <Box sx={{ display: 'flex', gap: 1 }}>
                    <Chip 
                      label={`Score: ${harmony.progression.score}`} 
                      color="primary" 
                      size="small" 
                    />
                    {playingIndex === index && (
                      <Chip 
                        label={`Vol: ${harmonyVolume}%`} 
                        size="small" 
                        sx={{ bgcolor: '#9C27B0', color: 'white' }}
                      />
                    )}
                  </Box>
                </Box>
                
                <Box sx={{ display: 'flex', gap: 1, mb: 2, flexWrap: 'wrap' }}>
                  {harmony.progression.chords.map((chord, i) => (
                    <Chip
                      key={i}
                      label={chord}
                      sx={{
                        bgcolor: harmony.progression.colors[i],
                        color: 'white',
                        fontWeight: 'bold'
                      }}
                    />
                  ))}
                </Box>
                
                <Typography variant="body2" color="text.secondary">
                  {harmony.progression.description}
                </Typography>
              </CardContent>
              
              <CardActions>
                <IconButton 
                  onClick={() => playHarmony(harmony, index)}
                  color={playingIndex === index ? 'primary' : 'default'}
                >
                  {playingIndex === index ? <Stop /> : <PlayArrow />}
                </IconButton>
                
                <IconButton 
                  onClick={() => toggleFavorite(index)}
                  color={favorites.includes(index) ? 'secondary' : 'default'}
                >
                  {favorites.includes(index) ? <Favorite /> : <FavoriteBorder />}
                </IconButton>
                
                <Button 
                  size="small" 
                  onClick={() => onHarmonySelected(harmony)}
                >
                  Use This
                </Button>
              </CardActions>
            </Card>
          </Grid>
        ))}
      </Grid>
      
      {harmonies.length === 0 && !isLoading && (
        <Paper sx={{ p: 4, textAlign: 'center', bgcolor: '#2a2a2a' }}>
          <Typography color="text.secondary">
            Click "Get Suggestions" to generate harmony ideas
          </Typography>
        </Paper>
      )}
    </Box>
  );
};

export default HarmonyPanel;