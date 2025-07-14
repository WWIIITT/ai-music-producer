// client/src/components/MusicUploader.jsx
import React, { useState, useRef } from 'react';
import {
  Box,
  Button,
  Paper,
  Typography,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  LinearProgress,
  Alert,
  Chip,
  Grid,
  Card,
  CardContent,
  Radio,
  RadioGroup,
  FormControlLabel
} from '@mui/material';
import {
  CloudUpload,
  AudioFile,
  CheckCircle,
  Error,
  RadioButtonChecked,
  RadioButtonUnchecked
} from '@mui/icons-material';
import axios from 'axios';
import toast from 'react-hot-toast';

const MusicUploader = ({ onFileAnalyzed, analyzedFiles, selectedReference, onReferenceSelect }) => {
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const fileInputRef = useRef(null);

  const handleFileSelect = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    // Validate file type
    const allowedTypes = ['audio/mp3', 'audio/wav', 'audio/ogg', 'audio/m4a', 'audio/flac', 'audio/mpeg'];
    if (!allowedTypes.includes(file.type)) {
      toast.error('Please upload an audio file (MP3, WAV, OGG, M4A, or FLAC)');
      return;
    }

    // Validate file size (max 50MB)
    const maxSize = 50 * 1024 * 1024;
    if (file.size > maxSize) {
      toast.error('File size must be less than 50MB');
      return;
    }

    setUploading(true);
    setUploadProgress(0);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await axios.post(
        `${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/upload/music`,
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data'
          },
          onUploadProgress: (progressEvent) => {
            const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
            setUploadProgress(progress);
          }
        }
      );

      toast.success('File uploaded and analyzed successfully!');
      onFileAnalyzed(response.data.analysis);
      
      // Clear file input
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    } catch (error) {
      console.error('Upload error:', error);
      toast.error(error.response?.data?.detail || 'Failed to upload file');
    } finally {
      setUploading(false);
      setUploadProgress(0);
    }
  };

  const formatDuration = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const getGenreColor = (genre) => {
    const colors = {
      'hip-hop': '#9C27B0',
      'rock': '#F44336',
      'jazz': '#2196F3',
      'electronic': '#00BCD4',
      'pop': '#FF9800'
    };
    return colors[genre] || '#757575';
  };

  const getMoodIcon = (mood) => {
    const icons = {
      'happy': '😊',
      'sad': '😢',
      'energetic': '⚡',
      'calm': '😌',
      'mysterious': '🌙',
      'uplifting': '🌟',
      'angry': '😠',
      'neutral': '😐'
    };
    return icons[mood] || '🎵';
  };

  return (
    <Box>
      <Grid container spacing={3}>
        {/* Upload Section */}
        <Grid item xs={12}>
          <Paper sx={{ p: 3, bgcolor: '#2a2a2a' }}>
            <Typography variant="h5" gutterBottom>
              Upload & Analyze Music
            </Typography>
            
            <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
              Upload a music file to analyze its structure, tempo, key, and mood. 
              Use it as a reference for generating similar beats and melodies.
            </Typography>

            <input
              ref={fileInputRef}
              type="file"
              accept="audio/*"
              style={{ display: 'none' }}
              onChange={handleFileSelect}
              disabled={uploading}
            />

            <Box sx={{ textAlign: 'center', py: 4 }}>
              <Button
                variant="contained"
                size="large"
                startIcon={<CloudUpload />}
                onClick={() => fileInputRef.current?.click()}
                disabled={uploading}
                sx={{ px: 4, py: 2 }}
              >
                {uploading ? 'Uploading...' : 'Choose Audio File'}
              </Button>

              <Typography variant="caption" display="block" sx={{ mt: 2, color: 'text.secondary' }}>
                Supported formats: MP3, WAV, OGG, M4A, FLAC (max 50MB)
              </Typography>
            </Box>

            {uploading && (
              <Box sx={{ mt: 3 }}>
                <LinearProgress variant="determinate" value={uploadProgress} />
                <Typography variant="body2" sx={{ mt: 1, textAlign: 'center' }}>
                  Uploading and analyzing... {uploadProgress}%
                </Typography>
              </Box>
            )}
          </Paper>
        </Grid>

        {/* Analyzed Files List */}
        {analyzedFiles.length > 0 && (
          <Grid item xs={12}>
            <Paper sx={{ p: 3, bgcolor: '#2a2a2a' }}>
              <Typography variant="h6" gutterBottom>
                Analyzed Files ({analyzedFiles.length})
              </Typography>

              <RadioGroup
                value={selectedReference || ''}
                onChange={(e) => onReferenceSelect(e.target.value)}
              >
                <List>
                  {analyzedFiles.map((file, index) => (
                    <ListItem 
                      key={file.file_id || index}
                      sx={{ 
                        mb: 2, 
                        bgcolor: '#1e1e1e', 
                        borderRadius: 2,
                        border: selectedReference === file.file_id ? '2px solid #90caf9' : 'none'
                      }}
                    >
                      <FormControlLabel
                        value={file.file_id}
                        control={<Radio />}
                        label=""
                        sx={{ mr: 2 }}
                      />
                      
                      <ListItemText
                        primary={
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            <AudioFile />
                            <Typography variant="subtitle1">
                              {file.file_id?.split('_').slice(1).join(' ').replace('.mp3', '').replace('.wav', '')}
                            </Typography>
                            {selectedReference === file.file_id && (
                              <Chip label="Selected as Reference" size="small" color="primary" />
                            )}
                          </Box>
                        }
                        secondary={
                          <Box sx={{ mt: 1 }}>
                            <Grid container spacing={2}>
                              <Grid item xs={12} sm={6} md={3}>
                                <Typography variant="caption" color="text.secondary">
                                  Key & Mode
                                </Typography>
                                <Typography variant="body2">
                                  {file.key} {file.mode}
                                </Typography>
                              </Grid>
                              
                              <Grid item xs={12} sm={6} md={3}>
                                <Typography variant="caption" color="text.secondary">
                                  Tempo
                                </Typography>
                                <Typography variant="body2">
                                  {Math.round(file.tempo)} BPM
                                </Typography>
                              </Grid>
                              
                              <Grid item xs={12} sm={6} md={3}>
                                <Typography variant="caption" color="text.secondary">
                                  Duration
                                </Typography>
                                <Typography variant="body2">
                                  {formatDuration(file.duration)}
                                </Typography>
                              </Grid>
                              
                              <Grid item xs={12} sm={6} md={3}>
                                <Typography variant="caption" color="text.secondary">
                                  Time Signature
                                </Typography>
                                <Typography variant="body2">
                                  {file.time_signature}
                                </Typography>
                              </Grid>
                            </Grid>

                            <Box sx={{ display: 'flex', gap: 1, mt: 2, flexWrap: 'wrap' }}>
                              <Chip 
                                label={file.genre} 
                                size="small" 
                                sx={{ 
                                  bgcolor: getGenreColor(file.genre),
                                  color: 'white'
                                }}
                              />
                              <Chip 
                                label={`${getMoodIcon(file.mood)} ${file.mood}`} 
                                size="small" 
                                variant="outlined"
                              />
                              <Chip 
                                label={`Energy: ${Math.round(file.energy * 100)}%`} 
                                size="small" 
                                variant="outlined"
                              />
                              {file.chord_progression && (
                                <Chip 
                                  label={`Chords: ${file.chord_progression.join(' - ')}`} 
                                  size="small" 
                                  variant="outlined"
                                />
                              )}
                            </Box>
                          </Box>
                        }
                      />
                    </ListItem>
                  ))}
                </List>
              </RadioGroup>

              {selectedReference && (
                <Alert severity="info" sx={{ mt: 2 }}>
                  The selected reference will be used to guide beat and melody generation. 
                  Switch to the Beat Maker or Melody Generator tabs to create music based on this reference.
                </Alert>
              )}
            </Paper>
          </Grid>
        )}
      </Grid>
    </Box>
  );
};

export default MusicUploader;