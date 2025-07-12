// client/src/components/HarmonyPanel.js
import React, { useState } from 'react';
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
  IconButton
} from '@mui/material';
import {
  PlayArrow,
  Stop,
  Favorite,
  FavoriteBorder
} from '@mui/icons-material';
import * as Tone from 'tone';
import axios from 'axios';
import toast from 'react-hot-toast';

const HarmonyPanel = ({ currentKey, genre, onHarmonySelected }) => {
  const [mood, setMood] = useState('happy');
  const [harmonies, setHarmonies] = useState([]);
  const [favorites, setFavorites] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [playingIndex, setPlayingIndex] = useState(null);
  
  const moods = ['happy', 'sad', 'energetic', 'calm', 'mysterious', 'uplifting'];
  
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
      
      // Create a simple synth for chords
      const synth = new Tone.PolySynth(Tone.Synth).toDestination();
      
      // Play chord progression
      const chordDuration = '2n';
      let time = 0;
      
      harmony.progression.chords.forEach((chord, i) => {
        // Convert chord symbol to notes (simplified)
        const chordNotes = getChordNotes(chord, currentKey);
        
        Tone.Transport.schedule((t) => {
          synth.triggerAttackRelease(chordNotes, chordDuration, t);
        }, time);
        
        time += Tone.Time(chordDuration).toSeconds();
      });
      
      await Tone.Transport.start();
      
      // Auto-stop after progression plays
      setTimeout(() => {
        Tone.Transport.stop();
        setPlayingIndex(null);
        synth.dispose();
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

  return (
    <Box>
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={12} md={4}>
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
        
        <Grid item xs={12} md={4}>
          <Box sx={{ pt: 2 }}>
            <Chip label={`Key: ${currentKey}`} sx={{ mr: 1 }} />
            <Chip label={`Genre: ${genre}`} />
          </Box>
        </Grid>
        
        <Grid item xs={12} md={4}>
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
                  <Chip 
                    label={`Score: ${harmony.progression.score}`} 
                    color="primary" 
                    size="small" 
                  />
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