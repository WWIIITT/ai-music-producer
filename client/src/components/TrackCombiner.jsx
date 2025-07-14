// client/src/components/TrackCombiner.jsx
import React, { useState, useRef } from 'react';
import {
  Box,
  Button,
  Paper,
  Typography,
  Grid,
  Slider,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Checkbox,
  IconButton,
  Chip,
  Alert,
  Card,
  CardContent,
  Divider
} from '@mui/material';
import {
  Merge,
  PlayArrow,
  Stop,
  Download,
  GraphicEq,
  Piano,
  VolumeUp,
  Layers
} from '@mui/icons-material';
import * as Tone from 'tone';
import axios from 'axios';
import toast from 'react-hot-toast';

const TrackCombiner = ({ generatedTracks, tempo, masterGain, audioInitialized, onTracksCombined }) => {
  const [selectedTracks, setSelectedTracks] = useState({
    beat: null,
    melody: null
  });
  const [mixLevels, setMixLevels] = useState({
    beat: 70,
    melody: 80
  });
  const [isPlaying, setIsPlaying] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [combinedTrack, setCombinedTrack] = useState(null);
  
  const playerRef = useRef(null);

  const handleTrackSelect = (type, track) => {
    setSelectedTracks(prev => ({
      ...prev,
      [type]: track
    }));
  };

  const handleMixLevelChange = (type, value) => {
    setMixLevels(prev => ({
      ...prev,
      [type]: value
    }));
  };

  const combineTracks = async () => {
    if (!selectedTracks.beat || !selectedTracks.melody) {
      toast.error('Please select both a beat and a melody to combine');
      return;
    }

    setIsLoading(true);
    try {
      const response = await axios.post(
        `${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/combine/tracks`,
        {
          beat_file: selectedTracks.beat.audio_file,
          melody_file: selectedTracks.melody.audio_file,
          tempo: tempo,
          mix_levels: {
            beat: mixLevels.beat / 100,
            melody: mixLevels.melody / 100
          }
        }
      );

      const combined = {
        url: response.data.combined_url,
        filename: response.data.filename,
        timestamp: new Date().toISOString(),
        beat: selectedTracks.beat,
        melody: selectedTracks.melody,
        mixLevels: { ...mixLevels }
      };

      setCombinedTrack(combined);
      onTracksCombined(combined);
      toast.success('Tracks combined successfully!');
    } catch (error) {
      console.error('Combination error:', error);
      toast.error('Failed to combine tracks');
    } finally {
      setIsLoading(false);
    }
  };

  const handlePlayStop = async () => {
    if (!combinedTrack) return;

    if (isPlaying) {
      if (playerRef.current) {
        await playerRef.current.stop();
        playerRef.current.dispose();
        playerRef.current = null;
      }
      setIsPlaying(false);
    } else {
      try {
        const player = new Tone.Player({
          url: `${import.meta.env.VITE_API_URL || 'http://localhost:8000'}${combinedTrack.url}`,
          onload: () => {
            player.start();
            setIsPlaying(true);
          }
        });

        if (masterGain) {
          player.connect(masterGain);
        } else {
          player.toDestination();
        }

        playerRef.current = player;
      } catch (error) {
        console.error('Playback error:', error);
        toast.error('Failed to play combined track');
      }
    }
  };

  const downloadCombined = () => {
    if (!combinedTrack) return;
    
    const url = `${import.meta.env.VITE_API_URL || 'http://localhost:8000'}${combinedTrack.url}`;
    window.open(url, '_blank');
    toast.success('Download started!');
  };

  const formatTrackName = (track, type) => {
    if (type === 'beat') {
      return `Beat - ${track.genre || 'Unknown'} @ ${track.tempo || tempo} BPM`;
    } else if (type === 'melody') {
      return `Melody - ${track.key || 'C'} ${track.scale || 'major'}`;
    }
    return 'Unknown Track';
  };

  const hasAvailableTracks = generatedTracks.beats.length > 0 || generatedTracks.melodies.length > 0;

  return (
    <Box>
      <Grid container spacing={3}>
        {/* Track Selection */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3, bgcolor: '#2a2a2a', height: '100%' }}>
            <Typography variant="h6" gutterBottom>
              <GraphicEq sx={{ mr: 1, verticalAlign: 'middle' }} />
              Select Beat
            </Typography>
            
            {generatedTracks.beats.length > 0 ? (
              <List sx={{ maxHeight: 300, overflow: 'auto' }}>
                {generatedTracks.beats.map((beat, index) => (
                  <ListItem
                    key={index}
                    button
                    selected={selectedTracks.beat === beat}
                    onClick={() => handleTrackSelect('beat', beat)}
                    sx={{
                      mb: 1,
                      bgcolor: selectedTracks.beat === beat ? '#333' : 'transparent',
                      borderRadius: 1
                    }}
                  >
                    <ListItemIcon>
                      <Checkbox
                        checked={selectedTracks.beat === beat}
                        color="primary"
                      />
                    </ListItemIcon>
                    <ListItemText
                      primary={formatTrackName(beat, 'beat')}
                      secondary={
                        <Box sx={{ display: 'flex', gap: 1, mt: 0.5 }}>
                          <Chip label={`${beat.bars || 4} bars`} size="small" />
                          <Chip label={`Complexity: ${beat.complexity || 0.7}`} size="small" />
                        </Box>
                      }
                    />
                  </ListItem>
                ))}
              </List>
            ) : (
              <Alert severity="info">
                No beats generated yet. Go to Beat Maker to create some beats.
              </Alert>
            )}
          </Paper>
        </Grid>

        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3, bgcolor: '#2a2a2a', height: '100%' }}>
            <Typography variant="h6" gutterBottom>
              <Piano sx={{ mr: 1, verticalAlign: 'middle' }} />
              Select Melody
            </Typography>
            
            {generatedTracks.melodies.length > 0 ? (
              <List sx={{ maxHeight: 300, overflow: 'auto' }}>
                {generatedTracks.melodies.map((melody, index) => (
                  <ListItem
                    key={index}
                    button
                    selected={selectedTracks.melody === melody}
                    onClick={() => handleTrackSelect('melody', melody)}
                    sx={{
                      mb: 1,
                      bgcolor: selectedTracks.melody === melody ? '#333' : 'transparent',
                      borderRadius: 1
                    }}
                  >
                    <ListItemIcon>
                      <Checkbox
                        checked={selectedTracks.melody === melody}
                        color="primary"
                      />
                    </ListItemIcon>
                    <ListItemText
                      primary={formatTrackName(melody, 'melody')}
                      secondary={
                        <Box sx={{ display: 'flex', gap: 1, mt: 0.5 }}>
                          <Chip label={`${melody.notes?.length || 0} notes`} size="small" />
                          {melody.chordProgression && (
                            <Chip 
                              label={`Chords: ${melody.chordProgression.join('-')}`} 
                              size="small" 
                            />
                          )}
                        </Box>
                      }
                    />
                  </ListItem>
                ))}
              </List>
            ) : (
              <Alert severity="info">
                No melodies generated yet. Go to Melody Generator to create some melodies.
              </Alert>
            )}
          </Paper>
        </Grid>

        {/* Mix Controls */}
        <Grid item xs={12}>
          <Paper sx={{ p: 3, bgcolor: '#2a2a2a' }}>
            <Typography variant="h6" gutterBottom>
              <Layers sx={{ mr: 1, verticalAlign: 'middle' }} />
              Mix Levels
            </Typography>

            <Grid container spacing={3} sx={{ mt: 1 }}>
              <Grid item xs={12} md={6}>
                <Box>
                  <Typography gutterBottom>
                    Beat Volume: {mixLevels.beat}%
                  </Typography>
                  <Slider
                    value={mixLevels.beat}
                    onChange={(e, val) => handleMixLevelChange('beat', val)}
                    min={0}
                    max={100}
                    disabled={!selectedTracks.beat}
                    sx={{
                      '& .MuiSlider-thumb': {
                        color: '#f44336'
                      },
                      '& .MuiSlider-track': {
                        color: '#f44336'
                      }
                    }}
                  />
                </Box>
              </Grid>

              <Grid item xs={12} md={6}>
                <Box>
                  <Typography gutterBottom>
                    Melody Volume: {mixLevels.melody}%
                  </Typography>
                  <Slider
                    value={mixLevels.melody}
                    onChange={(e, val) => handleMixLevelChange('melody', val)}
                    min={0}
                    max={100}
                    disabled={!selectedTracks.melody}
                    sx={{
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
            </Grid>

            <Box sx={{ mt: 3, display: 'flex', gap: 2, justifyContent: 'center' }}>
              <Button
                variant="contained"
                size="large"
                startIcon={<Merge />}
                onClick={combineTracks}
                disabled={!selectedTracks.beat || !selectedTracks.melody || isLoading}
              >
                {isLoading ? 'Combining...' : 'Combine Tracks'}
              </Button>
            </Box>
          </Paper>
        </Grid>

        {/* Combined Result */}
        {combinedTrack && (
          <Grid item xs={12}>
            <Card sx={{ bgcolor: '#1e1e1e' }}>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Combined Track
                </Typography>
                
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
                  <IconButton
                    onClick={handlePlayStop}
                    color="primary"
                    size="large"
                    disabled={!audioInitialized}
                  >
                    {isPlaying ? <Stop /> : <PlayArrow />}
                  </IconButton>
                  
                  <Typography variant="body1" sx={{ flexGrow: 1 }}>
                    {combinedTrack.filename}
                  </Typography>
                  
                  <IconButton
                    onClick={downloadCombined}
                    color="secondary"
                  >
                    <Download />
                  </IconButton>
                </Box>

                <Divider sx={{ my: 2 }} />

                <Typography variant="body2" color="text.secondary">
                  Mix Details:
                </Typography>
                <Box sx={{ display: 'flex', gap: 2, mt: 1 }}>
                  <Chip 
                    label={`Beat: ${combinedTrack.mixLevels.beat}%`} 
                    size="small"
                    sx={{ bgcolor: '#f44336' }}
                  />
                  <Chip 
                    label={`Melody: ${combinedTrack.mixLevels.melody}%`} 
                    size="small"
                    sx={{ bgcolor: '#2196F3' }}
                  />
                  <Chip 
                    label={`${tempo} BPM`} 
                    size="small"
                    variant="outlined"
                  />
                </Box>
              </CardContent>
            </Card>
          </Grid>
        )}

        {!hasAvailableTracks && (
          <Grid item xs={12}>
            <Alert severity="warning">
              No tracks available to combine. Please generate some beats and melodies first!
            </Alert>
          </Grid>
        )}
      </Grid>
    </Box>
  );
};

export default TrackCombiner;