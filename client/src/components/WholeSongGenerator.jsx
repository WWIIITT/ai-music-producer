// client/src/components/WholeSongGenerator.jsx
import React, { useState, useRef } from 'react';
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
  Card,
  CardContent,
  CardActions,
  Chip,
  IconButton,
  LinearProgress,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Radio,
  RadioGroup,
  FormControlLabel
} from '@mui/material';
import {
  PlayArrow,
  Stop,
  Download,
  VideoFile,
  MusicNote,
  ExpandMore,
  Refresh,
  Movie,
  Timeline,
  Equalizer,
  Grain,
  Share
} from '@mui/icons-material';
import * as Tone from 'tone';
import axios from 'axios';
import toast from 'react-hot-toast';

const WholeSongGenerator = ({ tempo, masterGain, audioInitialized, onSongGenerated }) => {
  const [style, setStyle] = useState('pop');
  const [songTempo, setSongTempo] = useState(120);
  const [key, setKey] = useState('C');
  const [duration, setDuration] = useState(180);
  const [variations, setVariations] = useState(1);
  const [title, setTitle] = useState('');
  
  const [isGenerating, setIsGenerating] = useState(false);
  const [generatedSong, setGeneratedSong] = useState(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [generationProgress, setGenerationProgress] = useState(0);
  
  // MP4 Export
  const [mp4ExportDialog, setMp4ExportDialog] = useState(false);
  const [visualStyle, setVisualStyle] = useState('waveform');
  const [isExportingMp4, setIsExportingMp4] = useState(false);
  
  const playerRef = useRef(null);
  
  const styles = ['pop', 'rock', 'hip-hop', 'jazz', 'electronic', 'classical'];
  const keys = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'];
  
  const visualStyles = [
    { value: 'waveform', label: 'Waveform', icon: <Timeline />, description: 'Classic audio waveform visualization' },
    { value: 'spectrum', label: 'Spectrum', icon: <Equalizer />, description: 'Frequency spectrum analyzer' },
    { value: 'particles', label: 'Particles', icon: <Grain />, description: 'Dynamic particle system' }
  ];

  const generateWholeSong = async () => {
    if (!audioInitialized) {
      toast.error('Please enable audio first by clicking anywhere on the page');
      return;
    }

    setIsGenerating(true);
    setGenerationProgress(0);
    
    try {
      console.log('🎵 Starting whole song generation...');
      
      // Simulate progress for better UX
      const progressInterval = setInterval(() => {
        setGenerationProgress(prev => {
          if (prev >= 90) {
            clearInterval(progressInterval);
            return 90;
          }
          return prev + 10;
        });
      }, 500);

      const response = await axios.post(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/generate/whole-song`, {
        style,
        tempo: songTempo,
        key,
        duration,
        variations,
        title: title || undefined
      });

      clearInterval(progressInterval);
      setGenerationProgress(100);

      const songData = response.data;
      setGeneratedSong(songData);
      
      // Notify parent component
      if (onSongGenerated) {
        onSongGenerated(songData);
      }
      
      toast.success(`🎵 Complete song generated! "${songData.title}"`);
      
      // Auto-play if audio is initialized
      if (audioInitialized && songData.audio_url) {
        setTimeout(() => {
          playPreview(songData.audio_url);
        }, 1000);
      }
      
    } catch (error) {
      console.error('Song generation error:', error);
      const errorMessage = error.response?.data?.detail || error.message || 'Unknown error';
      toast.error(`Failed to generate song: ${errorMessage}`);
    } finally {
      setIsGenerating(false);
      setTimeout(() => setGenerationProgress(0), 2000);
    }
  };

  const playPreview = async (audioUrl) => {
    try {
      if (isPlaying && playerRef.current) {
        await playerRef.current.stop();
        playerRef.current.dispose();
        playerRef.current = null;
        setIsPlaying(false);
        return;
      }

      if (!audioInitialized) {
        toast.error('Audio not initialized');
        return;
      }

      const player = new Tone.Player({
        url: audioUrl,
        onload: () => {
          console.log('Song loaded, starting playback');
          player.start();
          setIsPlaying(true);
        },
        onstop: () => {
          setIsPlaying(false);
        },
        onerror: (error) => {
          console.error('Player error:', error);
          toast.error('Failed to load audio');
          setIsPlaying(false);
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
      toast.error('Failed to play song');
      setIsPlaying(false);
    }
  };

  const downloadSong = (audioUrl, filename) => {
    try {
      const link = document.createElement('a');
      link.href = audioUrl;
      link.download = filename || 'generated_song.wav';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      toast.success('Download started!');
    } catch (error) {
      console.error('Download error:', error);
      toast.error('Download failed');
    }
  };

  const exportToMp4 = async () => {
    if (!generatedSong || !generatedSong.audio_url) {
      toast.error('No song to export');
      return;
    }

    setIsExportingMp4(true);
    
    try {
      // Extract filename from audio URL
      const audioFileName = generatedSong.audio_url.split('/').pop();
      
      const response = await axios.post(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/export/mp4`, {
        audio_file: audioFileName,
        song_data: generatedSong.song_data,
        visual_style: visualStyle,
        title: generatedSong.title
      });

      const mp4Data = response.data;
      
      // Open download link
      window.open(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}${mp4Data.mp4_url}`, '_blank');
      
      toast.success(`🎬 MP4 video created! (${visualStyle} style)`);
      setMp4ExportDialog(false);
      
    } catch (error) {
      console.error('MP4 export error:', error);
      toast.error('Failed to create MP4: ' + (error.response?.data?.detail || error.message));
    } finally {
      setIsExportingMp4(false);
    }
  };

  const formatDuration = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const getSectionColor = (sectionType) => {
    const colors = {
      intro: '#4CAF50',
      verse: '#2196F3', 
      chorus: '#FF9800',
      bridge: '#9C27B0',
      outro: '#607D8B',
      solo: '#F44336',
      hook: '#FF5722',
      buildup: '#3F51B5',
      drop: '#E91E63',
      breakdown: '#795548'
    };
    return colors[sectionType] || '#757575';
  };

  return (
    <Box>
      <Grid container spacing={3}>
        {/* Generation Controls */}
        <Grid item xs={12}>
          <Paper sx={{ p: 3, bgcolor: '#2a2a2a' }}>
            <Typography variant="h5" gutterBottom>
              🎵 Whole Song Generator
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
              Generate complete songs with multiple sections, variations, and export as MP4 videos.
            </Typography>

            <Grid container spacing={2}>
              <Grid item xs={12} md={3}>
                <TextField
                  fullWidth
                  label="Song Title (optional)"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="My Awesome Song"
                />
              </Grid>

              <Grid item xs={12} md={2}>
                <FormControl fullWidth>
                  <InputLabel>Style</InputLabel>
                  <Select value={style} onChange={(e) => setStyle(e.target.value)}>
                    {styles.map(s => (
                      <MenuItem key={s} value={s}>
                        {s.charAt(0).toUpperCase() + s.slice(1)}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>

              <Grid item xs={12} md={2}>
                <FormControl fullWidth>
                  <InputLabel>Key</InputLabel>
                  <Select value={key} onChange={(e) => setKey(e.target.value)}>
                    {keys.map(k => (
                      <MenuItem key={k} value={k}>{k}</MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>

              <Grid item xs={12} md={2}>
                <TextField
                  fullWidth
                  label="Tempo (BPM)"
                  type="number"
                  value={songTempo}
                  onChange={(e) => setSongTempo(parseInt(e.target.value))}
                  inputProps={{ min: 60, max: 200 }}
                />
              </Grid>

              <Grid item xs={12} md={2}>
                <TextField
                  fullWidth
                  label="Duration (seconds)"
                  type="number"
                  value={duration}
                  onChange={(e) => setDuration(parseInt(e.target.value))}
                  inputProps={{ min: 60, max: 600 }}
                />
              </Grid>

              <Grid item xs={12} md={1}>
                <TextField
                  fullWidth
                  label="Variations"
                  type="number"
                  value={variations}
                  onChange={(e) => setVariations(parseInt(e.target.value))}
                  inputProps={{ min: 1, max: 3 }}
                />
              </Grid>
            </Grid>

            <Box sx={{ mt: 3, display: 'flex', gap: 2, justifyContent: 'center', flexWrap: 'wrap' }}>
              <Button
                variant="contained"
                size="large"
                startIcon={isGenerating ? <Refresh /> : <MusicNote />}
                onClick={generateWholeSong}
                disabled={isGenerating || !audioInitialized}
                sx={{ px: 4, py: 1.5 }}
              >
                {isGenerating ? 'Generating...' : 'Generate Whole Song'}
              </Button>

              {generatedSong && (
                <>
                  <IconButton
                    onClick={() => playPreview(generatedSong.audio_url)}
                    color="primary"
                    size="large"
                    disabled={!audioInitialized}
                  >
                    {isPlaying ? <Stop /> : <PlayArrow />}
                  </IconButton>

                  <Button
                    variant="outlined"
                    startIcon={<Download />}
                    onClick={() => downloadSong(generatedSong.audio_url, `${generatedSong.title}.wav`)}
                  >
                    Download WAV
                  </Button>

                  <Button
                    variant="outlined"
                    startIcon={<VideoFile />}
                    onClick={() => setMp4ExportDialog(true)}
                    color="secondary"
                  >
                    Export MP4
                  </Button>
                </>
              )}
            </Box>

            {isGenerating && (
              <Box sx={{ mt: 3 }}>
                <Typography variant="body2" gutterBottom>
                  Generating song... {generationProgress}%
                </Typography>
                <LinearProgress variant="determinate" value={generationProgress} />
              </Box>
            )}
          </Paper>
        </Grid>

        {/* Audio Status Alert */}
        {!audioInitialized && (
          <Grid item xs={12}>
            <Alert severity="warning">
              ⚠️ Audio not initialized. Click "ENABLE AUDIO" in the top banner to enable song generation and playback.
            </Alert>
          </Grid>
        )}

        {/* Generated Song Display */}
        {generatedSong && (
          <Grid item xs={12}>
            <Card sx={{ bgcolor: '#1e1e1e' }}>
              <CardContent>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2, flexWrap: 'wrap', gap: 1 }}>
                  <Typography variant="h6">
                    🎼 {generatedSong.title}
                  </Typography>
                  <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                    <Chip label={generatedSong.style} color="primary" />
                    <Chip label={`${formatDuration(generatedSong.duration)}`} />
                    <Chip label={`${generatedSong.sections} sections`} />
                    <Chip label={`${key} @ ${songTempo} BPM`} variant="outlined" />
                  </Box>
                </Box>

                {/* Song Structure */}
                {generatedSong.structure && (
                  <Accordion sx={{ bgcolor: '#2a2a2a', mb: 2 }}>
                    <AccordionSummary expandIcon={<ExpandMore />}>
                      <Typography>Song Structure</Typography>
                    </AccordionSummary>
                    <AccordionDetails>
                      <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                        {generatedSong.structure.map((section, index) => (
                          <Chip
                            key={index}
                            label={`${index + 1}. ${section}`}
                            sx={{
                              bgcolor: getSectionColor(section),
                              color: 'white',
                              fontWeight: 'bold'
                            }}
                          />
                        ))}
                      </Box>
                      <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
                        Total Duration: {formatDuration(generatedSong.duration)} | 
                        Sections: {generatedSong.sections} | 
                        Style: {generatedSong.style}
                      </Typography>
                    </AccordionDetails>
                  </Accordion>
                )}

                {/* Variations */}
                {generatedSong.variations && generatedSong.variations.length > 0 && (
                  <Accordion sx={{ bgcolor: '#2a2a2a' }}>
                    <AccordionSummary expandIcon={<ExpandMore />}>
                      <Typography>Style Variations ({generatedSong.variations.length})</Typography>
                    </AccordionSummary>
                    <AccordionDetails>
                      <Grid container spacing={2}>
                        {generatedSong.variations.map((variation, index) => (
                          <Grid item xs={12} md={4} key={index}>
                            <Card sx={{ bgcolor: '#333' }}>
                              <CardContent>
                                <Typography variant="h6">
                                  Variation {variation.variation_id}
                                </Typography>
                                <Chip label={variation.style} size="small" />
                              </CardContent>
                              <CardActions>
                                <IconButton 
                                  onClick={() => playPreview(variation.audio_url)}
                                  color="primary"
                                  size="small"
                                >
                                  <PlayArrow />
                                </IconButton>
                                <Button 
                                  size="small"
                                  onClick={() => downloadSong(variation.audio_url, `${generatedSong.title}_${variation.style}.wav`)}
                                >
                                  Download
                                </Button>
                              </CardActions>
                            </Card>
                          </Grid>
                        ))}
                      </Grid>
                    </AccordionDetails>
                  </Accordion>
                )}
              </CardContent>
            </Card>
          </Grid>
        )}
      </Grid>

      {/* MP4 Export Dialog */}
      <Dialog open={mp4ExportDialog} onClose={() => setMp4ExportDialog(false)} maxWidth="md" fullWidth>
        <DialogTitle>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Movie />
            Export as MP4 Video
          </Box>
        </DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
            Create a music video with audio visualization. Choose your preferred visual style:
          </Typography>

          <RadioGroup value={visualStyle} onChange={(e) => setVisualStyle(e.target.value)}>
            <Grid container spacing={2}>
              {visualStyles.map((style) => (
                <Grid item xs={12} md={4} key={style.value}>
                  <Card sx={{ 
                    bgcolor: visualStyle === style.value ? '#1976d2' : '#2a2a2a',
                    cursor: 'pointer',
                    border: visualStyle === style.value ? '2px solid #90caf9' : 'none'
                  }}>
                    <CardContent>
                      <FormControlLabel
                        value={style.value}
                        control={<Radio />}
                        label={
                          <Box>
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                              {style.icon}
                              <Typography variant="h6">{style.label}</Typography>
                            </Box>
                            <Typography variant="body2" color="text.secondary">
                              {style.description}
                            </Typography>
                          </Box>
                        }
                      />
                    </CardContent>
                  </Card>
                </Grid>
              ))}
            </Grid>
          </RadioGroup>

          {generatedSong && (
            <Alert severity="info" sx={{ mt: 3 }}>
              Video will be created for: "{generatedSong.title}" ({formatDuration(generatedSong.duration)})
            </Alert>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setMp4ExportDialog(false)}>Cancel</Button>
          <Button
            variant="contained"
            onClick={exportToMp4}
            disabled={isExportingMp4}
            startIcon={<VideoFile />}
          >
            {isExportingMp4 ? 'Creating Video...' : 'Create MP4'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default WholeSongGenerator;