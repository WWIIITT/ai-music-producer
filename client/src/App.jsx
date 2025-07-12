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
} from '@mui/material';
import {
  PlayArrow,
  Stop,
  Download,
  MusicNote,
  Piano,
  GraphicEq,
  Save
} from '@mui/icons-material';
import toast, { Toaster } from 'react-hot-toast';

// Import components
import BeatGenerator from './components/BeatGenerator';
import MelodyGenerator from './components/MelodyGenerator';
import HarmonyPanel from './components/HarmonyPanel';
import AudioVisualizer from './components/AudioVisualizer';
import ProjectManager from './components/ProjectManager';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

function App() {
  const [currentTab, setCurrentTab] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [tempo, setTempo] = useState(120);
  const [currentProject, setCurrentProject] = useState({
    name: 'Untitled Project',
    beats: [],
    melodies: [],
    harmonies: [],
    tempo: 120,
    key: 'C',
    genre: 'hip-hop'
  });
  
  const [audioContext, setAudioContext] = useState(null);
  const [transport, setTransport] = useState(null);

  useEffect(() => {
    // Initialize Tone.js
    const initAudio = async () => {
      await Tone.start();
      setAudioContext(Tone.context);
      setTransport(Tone.Transport);
      Tone.Transport.bpm.value = tempo;
    };
    
    initAudio();
    
    return () => {
      Tone.Transport.stop();
      Tone.Transport.cancel();
    };
  }, []);

  useEffect(() => {
    if (transport) {
      Tone.Transport.bpm.value = tempo;
    }
  }, [tempo, transport]);

  const handleTabChange = (event, newValue) => {
    setCurrentTab(newValue);
  };

  const handlePlayStop = () => {
    if (isPlaying) {
      Tone.Transport.stop();
      setIsPlaying(false);
    } else {
      Tone.Transport.start();
      setIsPlaying(true);
    }
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
      toast.loading('Exporting project...');
      // In a real implementation, this would combine all tracks
      // and export to the specified format
      const response = await axios.post(`${API_URL}/api/export`, {
        project: currentProject,
        format: format
      });
      
      // Download the file
      window.open(response.data.download_url, '_blank');
      toast.success('Export completed!');
    } catch (error) {
      toast.error('Export failed');
      console.error(error);
    }
  };

  const updateProject = (updates) => {
    setCurrentProject(prev => ({ ...prev, ...updates }));
  };

  return (
    <Box sx={{ flexGrow: 1, bgcolor: '#121212', minHeight: '100vh', color: 'white' }}>
      <Toaster position="top-right" />
      
      <AppBar position="static" sx={{ bgcolor: '#1e1e1e' }}>
        <Toolbar>
          <MusicNote sx={{ mr: 2 }} />
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            AI Music Producer
          </Typography>
          
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Typography>BPM: {tempo}</Typography>
            <Slider
              value={tempo}
              onChange={(e, value) => setTempo(value)}
              min={60}
              max={200}
              sx={{ width: 100 }}
            />
            
            <IconButton onClick={handlePlayStop} color="primary">
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
                    onBeatGenerated={(beat) => updateProject({ 
                      beats: [...currentProject.beats, beat] 
                    })}
                  />
                )}
                
                {currentTab === 1 && (
                  <MelodyGenerator
                    tempo={tempo}
                    currentKey={currentProject.key}
                    onMelodyGenerated={(melody) => updateProject({ 
                      melodies: [...currentProject.melodies, melody] 
                    })}
                  />
                )}
                
                {currentTab === 2 && (
                  <HarmonyPanel
                    currentKey={currentProject.key}
                    genre={currentProject.genre}
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