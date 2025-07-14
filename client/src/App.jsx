import React, { useState, useEffect } from 'react';
import axios from 'axios';
import * as Tone from 'tone';
import { 
  Box, 
  Container, 
  Paper, 
  AppBar, 
  Toolbar, 
  Typography, 
  Button,
  Grid,
  Slider,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  IconButton,
  Tabs,
  Tab,
  Chip,
  Alert
} from '@mui/material';
import {
  PlayArrow,
  Stop,
  Download,
  MusicNote,
  Piano,
  GraphicEq,
  Save,
  VolumeUp,
  VolumeDown,
  VolumeMute
} from '@mui/icons-material';
import toast, { Toaster } from 'react-hot-toast';

// Import components
import BeatGenerator from './components/BeatGenerator';
import MelodyGenerator from './components/MelodyGenerator';
import HarmonyPanel from './components/HarmonyPanel';
import AudioVisualizer from './components/AudioVisualizer';
import ProjectManager from './components/ProjectManager';

import MusicUploader from './components/MusicUploader';
import TrackCombiner from './components/TrackCombiner';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

function App() {
  const [currentTab, setCurrentTab] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [tempo, setTempo] = useState(120);
  const [masterVolume, setMasterVolume] = useState(80);
  const [currentProject, setCurrentProject] = useState({
    name: 'Untitled Project',
    beats: [],
    melodies: [],
    harmonies: [],
    tempo: 120,
    key: 'C',
    genre: 'hip-hop'
  });
  
  const [audioInitialized, setAudioInitialized] = useState(false);
  const [audioContextState, setAudioContextState] = useState('suspended');
  const [masterGain, setMasterGain] = useState(null);

  // Force audio initialization on first user interaction
  const initializeAudio = async () => {
    try {
      console.log('Initializing audio context...');
      
      // Ensure Tone.js context is started
      if (Tone.context.state !== 'running') {
        await Tone.start();
        console.log('Tone.js context started successfully');
      }
      
      // Create master gain node
      const gain = new Tone.Gain(masterVolume / 100).toDestination();
      setMasterGain(gain);
      
      // Set transport BPM
      Tone.Transport.bpm.value = tempo;
      
      // Update states
      setAudioInitialized(true);
      setAudioContextState(Tone.context.state);
      
      // Test audio with a quick beep
      const testOscillator = new Tone.Oscillator(440, 'sine').connect(gain);
      testOscillator.start();
      testOscillator.stop('+0.1');
      testOscillator.dispose();
      
      toast.success('Audio initialized successfully!');
      console.log('Audio initialization complete');
      
    } catch (error) {
      console.error('Failed to initialize audio:', error);
      toast.error(`Audio initialization failed: ${error.message}`);
    }
  };

  useEffect(() => {
    // Add multiple event listeners for user interaction
    const events = ['click', 'touchstart', 'keydown'];
    
    const handleUserInteraction = async (event) => {
      console.log('User interaction detected:', event.type);
      await initializeAudio();
      
      // Remove all event listeners after successful initialization
      events.forEach(eventName => {
        document.removeEventListener(eventName, handleUserInteraction);
      });
    };
    
    // Add event listeners
    events.forEach(eventName => {
      document.addEventListener(eventName, handleUserInteraction, { once: true });
    });
    
    // Monitor audio context state
    const checkAudioState = () => {
      if (Tone.context) {
        setAudioContextState(Tone.context.state);
      }
    };
    
    const intervalId = setInterval(checkAudioState, 1000);
    
    return () => {
      // Cleanup
      events.forEach(eventName => {
        document.removeEventListener(eventName, handleUserInteraction);
      });
      clearInterval(intervalId);
      
      if (Tone.Transport) {
        Tone.Transport.stop();
        Tone.Transport.cancel();
      }
      if (masterGain) {
        masterGain.dispose();
      }
    };
  }, []);

  useEffect(() => {
    if (audioInitialized && masterGain) {
      Tone.Transport.bpm.value = tempo;
      setCurrentProject(prev => ({ ...prev, tempo }));
    }
  }, [tempo, audioInitialized]);

  useEffect(() => {
    if (masterGain) {
      masterGain.gain.rampTo(masterVolume / 100, 0.1);
    }
  }, [masterVolume, masterGain]);

  useEffect(() => {
    const updatePlayState = () => {
      setIsPlaying(Tone.Transport.state === 'started');
    };

    if (Tone.Transport) {
      Tone.Transport.on('start', updatePlayState);
      Tone.Transport.on('stop', updatePlayState);
      
      return () => {
        Tone.Transport.off('start', updatePlayState);
        Tone.Transport.off('stop', updatePlayState);
      };
    }
  }, [audioInitialized]);

  const handleTabChange = (event, newValue) => {
    setCurrentTab(newValue);
  };

  const handlePlayStop = async () => {
    try {
      if (!audioInitialized) {
        await initializeAudio();
      }

      if (isPlaying) {
        Tone.Transport.stop();
      } else {
        Tone.Transport.start();
      }
    } catch (error) {
      console.error('Error controlling playback:', error);
      toast.error('Playback error. Please try clicking to enable audio first.');
    }
  };

  const handleVolumeChange = (event, newValue) => {
    setMasterVolume(newValue);
  };

  const handleMuteToggle = () => {
    if (masterVolume > 0) {
      setMasterVolume(0);
    } else {
      setMasterVolume(80);
    }
  };

  const getVolumeIcon = () => {
    if (masterVolume === 0) return <VolumeMute />;
    if (masterVolume < 50) return <VolumeDown />;
    return <VolumeUp />;
  };

  const handleSaveProject = async () => {
    try {
      const response = await axios.post(`${API_URL}/api/projects/save`, currentProject);
      toast.success('Project saved successfully!');
      setCurrentProject({ ...currentProject, id: response.data.id });
    } catch (error) {
      toast.error('Failed to save project');
      console.error(error);
    }
  };

  const handleExport = async (format = 'wav') => {
    try {
      const loadingToast = toast.loading('Exporting project...');
      
      const response = await axios.post(`${API_URL}/api/export`, {
        project: currentProject,
        format: format
      });
      
      toast.dismiss(loadingToast);
      
      const downloadUrl = `${API_URL}${response.data.download_url}`;
      const link = document.createElement('a');
      link.href = downloadUrl;
      link.download = response.data.filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      
      toast.success(`Export completed! ${response.data.files_exported} files exported.`);
    } catch (error) {
      toast.error('Export failed: ' + (error.response?.data?.detail || error.message));
      console.error(error);
    }
  };

  const updateProject = (updates) => {
    setCurrentProject(prev => ({ ...prev, ...updates }));
  };

  const handleForceAudioInit = async () => {
    await initializeAudio();
  };

  return (
    <Box sx={{ flexGrow: 1, bgcolor: '#121212', minHeight: '100vh', color: 'white' }}>
      <Toaster position="top-right" />
      
      {/* Audio Status Alert */}
      {!audioInitialized && (
        <Alert 
          severity="warning" 
          sx={{ 
            mb: 2, 
            bgcolor: '#333', 
            color: 'orange',
            '& .MuiAlert-icon': { color: 'orange' }
          }}
          action={
            <Button 
              color="inherit" 
              size="small" 
              onClick={handleForceAudioInit}
              sx={{ color: 'orange' }}
            >
              ENABLE AUDIO
            </Button>
          }
        >
          Audio Context: {audioContextState} - Click "ENABLE AUDIO" or anywhere on the page to activate sound
        </Alert>
      )}
      
      <AppBar position="static" sx={{ bgcolor: '#1e1e1e' }}>
        <Toolbar>
          <MusicNote sx={{ mr: 2 }} />
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            AI Music Producer
          </Typography>
          
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            {/* Audio Status Indicator */}
            <Chip 
              label={`Audio: ${audioContextState}`}
              color={audioInitialized ? 'success' : 'warning'}
              size="small"
            />
            
            {/* Master Volume Control */}
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mr: 2 }}>
              <IconButton 
                onClick={handleMuteToggle}
                color="primary"
                size="small"
              >
                {getVolumeIcon()}
              </IconButton>
              <Typography variant="caption" sx={{ minWidth: 40 }}>
                Vol: {masterVolume}
              </Typography>
              <Slider
                value={masterVolume}
                onChange={handleVolumeChange}
                min={0}
                max={100}
                sx={{ 
                  width: 80,
                  '& .MuiSlider-thumb': {
                    color: '#90caf9'
                  },
                  '& .MuiSlider-track': {
                    color: '#90caf9'
                  }
                }}
              />
            </Box>
            
            <Typography>BPM: {tempo}</Typography>
            <Slider
              value={tempo}
              onChange={(e, value) => setTempo(value)}
              min={60}
              max={200}
              sx={{ width: 100 }}
            />
            
            <IconButton 
              onClick={handlePlayStop} 
              color="primary"
              disabled={!audioInitialized}
            >
              {isPlaying ? <Stop /> : <PlayArrow />}
            </IconButton>
            
            <Button
              startIcon={<Save />}
              variant="outlined"
              onClick={handleSaveProject}
            >
              Save
            </Button>
            
            <Button
              startIcon={<Download />}
              variant="contained"
              onClick={() => handleExport('wav')}
              disabled={currentProject.beats.length === 0 && currentProject.melodies.length === 0 && currentProject.harmonies.length === 0}
            >
              Export
            </Button>
          </Box>
        </Toolbar>
      </AppBar>

      <Container maxWidth="xl" sx={{ mt: 3 }}>
        <Grid container spacing={3}>
          {/* Main Content Area */}
          <Grid item xs={12} md={9}>
            <Paper sx={{ p: 2, bgcolor: '#1e1e1e' }}>
              <Tabs value={currentTab} onChange={handleTabChange}>
                <Tab label="Beat Maker" icon={<GraphicEq />} />
                <Tab label="Melody Generator" icon={<Piano />} />
                <Tab label="Harmony" icon={<MusicNote />} />
                <Tab label="Projects" icon={<Save />} />
              </Tabs>
              
              <Box sx={{ mt: 3 }}>
                {currentTab === 0 && (
                  <BeatGenerator
                    tempo={tempo}
                    masterGain={masterGain}
                    audioInitialized={audioInitialized}
                    onBeatGenerated={(beat) => updateProject({ 
                      beats: [...currentProject.beats, beat] 
                    })}
                  />
                )}
                
                {currentTab === 1 && (
                  <MelodyGenerator
                    tempo={tempo}
                    currentKey={currentProject.key}
                    masterGain={masterGain}
                    audioInitialized={audioInitialized}
                    onMelodyGenerated={(melody) => updateProject({ 
                      melodies: [...currentProject.melodies, melody] 
                    })}
                  />
                )}
                
                {currentTab === 2 && (
                  <HarmonyPanel
                    currentKey={currentProject.key}
                    genre={currentProject.genre}
                    masterGain={masterGain}
                    audioInitialized={audioInitialized}
                    onHarmonySelected={(harmony) => updateProject({ 
                      harmonies: [...currentProject.harmonies, harmony] 
                    })}
                  />
                )}
                
                {currentTab === 3 && (
                  <ProjectManager
                    currentProject={currentProject}
                    onProjectLoad={setCurrentProject}
                  />
                )}
              </Box>
            </Paper>
          </Grid>
          
          {/* Side Panel */}
          <Grid item xs={12} md={3}>
            <Paper sx={{ p: 2, bgcolor: '#1e1e1e', mb: 2 }}>
              <Typography variant="h6" gutterBottom>
                Project Info
              </Typography>
              
              <FormControl fullWidth sx={{ mb: 2 }}>
                <InputLabel>Genre</InputLabel>
                <Select
                  value={currentProject.genre}
                  onChange={(e) => updateProject({ genre: e.target.value })}
                >
                  <MenuItem value="hip-hop">Hip-Hop</MenuItem>
                  <MenuItem value="rock">Rock</MenuItem>
                  <MenuItem value="jazz">Jazz</MenuItem>
                  <MenuItem value="electronic">Electronic</MenuItem>
                  <MenuItem value="pop">Pop</MenuItem>
                </Select>
              </FormControl>
              
              <FormControl fullWidth sx={{ mb: 2 }}>
                <InputLabel>Key</InputLabel>
                <Select
                  value={currentProject.key}
                  onChange={(e) => updateProject({ key: e.target.value })}
                >
                  {['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'].map(key => (
                    <MenuItem key={key} value={key}>{key}</MenuItem>
                  ))}
                </Select>
              </FormControl>
              
              <Box sx={{ mt: 2 }}>
                <Typography variant="subtitle2">Elements:</Typography>
                <Chip label={`${currentProject.beats.length} Beats`} sx={{ m: 0.5 }} />
                <Chip label={`${currentProject.melodies.length} Melodies`} sx={{ m: 0.5 }} />
                <Chip label={`${currentProject.harmonies.length} Harmonies`} sx={{ m: 0.5 }} />
              </Box>
              
              {!audioInitialized && (
                <Box sx={{ mt: 2, p: 1, bgcolor: '#333', borderRadius: 1 }}>
                  <Typography variant="caption" color="warning.main">
                    🔊 Audio disabled - Click "ENABLE AUDIO" to hear sounds
                  </Typography>
                </Box>
              )}
            </Paper>
            
            <Paper sx={{ p: 2, bgcolor: '#1e1e1e' }}>
              <Typography variant="h6" gutterBottom>
                Audio Visualizer
              </Typography>
              <AudioVisualizer isPlaying={isPlaying} />
            </Paper>
          </Grid>
        </Grid>
      </Container>
    </Box>
  );
}

export default App;