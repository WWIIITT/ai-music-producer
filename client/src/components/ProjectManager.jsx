// client/src/components/ProjectManager.jsx
import React, { useState, useEffect } from 'react';
import {
  Box,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  Typography,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Paper,
  Chip,
  Divider
} from '@mui/material';
import {
  Delete,
  CloudDownload,
  Save,
  FolderOpen,
  Refresh
} from '@mui/icons-material';
import axios from 'axios';
import toast from 'react-hot-toast';

const ProjectManager = ({ currentProject, onProjectLoad }) => {
  const [projects, setProjects] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [saveDialogOpen, setSaveDialogOpen] = useState(false);
  const [projectName, setProjectName] = useState('');

  useEffect(() => {
    loadProjects();
  }, []);

  const loadProjects = async () => {
    setIsLoading(true);
    try {
      const response = await axios.get(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/projects`);
      setProjects(response.data.projects);
    } catch (error) {
      toast.error('Failed to load projects');
      console.error(error);
    } finally {
      setIsLoading(false);
    }
  };

  const saveProject = async () => {
    try {
      const projectToSave = {
        ...currentProject,
        name: projectName || currentProject.name
      };
      
      await axios.post(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/projects/save`, projectToSave);
      toast.success('Project saved!');
      setSaveDialogOpen(false);
      setProjectName('');
      loadProjects();
    } catch (error) {
      toast.error('Failed to save project');
      console.error(error);
    }
  };

  const loadProject = (project) => {
    onProjectLoad(project);
    toast.success(`Loaded: ${project.name}`);
  };

  const deleteProject = async (projectId) => {
    if (!window.confirm('Are you sure you want to delete this project?')) return;
    
    try {
      await axios.delete(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/projects/${projectId}`);
      toast.success('Project deleted');
      loadProjects();
    } catch (error) {
      toast.error('Failed to delete project');
      console.error(error);
    }
  };

  const getProjectStats = (project) => {
    const beatsCount = project.beats?.length || 0;
    const melodiesCount = project.melodies?.length || 0;
    const harmoniesCount = project.harmonies?.length || 0;
    const totalElements = beatsCount + melodiesCount + harmoniesCount;
    
    return { beatsCount, melodiesCount, harmoniesCount, totalElements };
  };

  const formatDate = (dateString) => {
    try {
      return new Date(dateString).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch {
      return 'Unknown date';
    }
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h5">Projects</Typography>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <IconButton onClick={loadProjects} disabled={isLoading}>
            <Refresh />
          </IconButton>
          <Button
            variant="contained"
            startIcon={<Save />}
            onClick={() => setSaveDialogOpen(true)}
          >
            Save Current
          </Button>
        </Box>
      </Box>

      {/* Current Project Info */}
      <Paper sx={{ bgcolor: '#2a2a2a', p: 2, mb: 2 }}>
        <Typography variant="h6" gutterBottom>
          Current Project: {currentProject.name}
        </Typography>
        <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
          <Chip label={`${currentProject.beats?.length || 0} Beats`} size="small" />
          <Chip label={`${currentProject.melodies?.length || 0} Melodies`} size="small" />
          <Chip label={`${currentProject.harmonies?.length || 0} Harmonies`} size="small" />
          <Chip label={`Key: ${currentProject.key}`} size="small" />
          <Chip label={`Genre: ${currentProject.genre}`} size="small" />
          <Chip label={`${currentProject.tempo} BPM`} size="small" />
        </Box>
      </Paper>

      <Divider sx={{ my: 2 }} />

      {/* Saved Projects */}
      <Typography variant="h6" sx={{ mb: 2 }}>
        Saved Projects ({projects.length})
      </Typography>

      <Paper sx={{ bgcolor: '#2a2a2a' }}>
        {projects.length > 0 ? (
          <List>
            {projects.map((project, index) => {
              const stats = getProjectStats(project);
              return (
                <ListItem 
                  key={project._id || index}
                  button
                  onClick={() => loadProject(project)}
                  sx={{ 
                    '&:hover': { bgcolor: '#333' },
                    borderBottom: index < projects.length - 1 ? '1px solid #444' : 'none'
                  }}
                >
                  <ListItemText
                    primary={
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Typography variant="subtitle1">
                          {project.name || 'Untitled Project'}
                        </Typography>
                        {stats.totalElements === 0 && (
                          <Chip label="Empty" size="small" color="warning" />
                        )}
                      </Box>
                    }
                    secondary={
                      <Box>
                        <Typography variant="body2" color="text.secondary">
                          Created: {formatDate(project.created_at)}
                        </Typography>
                        <Box sx={{ display: 'flex', gap: 1, mt: 0.5, flexWrap: 'wrap' }}>
                          {stats.beatsCount > 0 && (
                            <Chip label={`${stats.beatsCount} beats`} size="small" />
                          )}
                          {stats.melodiesCount > 0 && (
                            <Chip label={`${stats.melodiesCount} melodies`} size="small" />
                          )}
                          {stats.harmoniesCount > 0 && (
                            <Chip label={`${stats.harmoniesCount} harmonies`} size="small" />
                          )}
                          {project.key && (
                            <Chip label={project.key} size="small" variant="outlined" />
                          )}
                          {project.genre && (
                            <Chip label={project.genre} size="small" variant="outlined" />
                          )}
                        </Box>
                      </Box>
                    }
                  />
                  <ListItemSecondaryAction>
                    <IconButton 
                      edge="end" 
                      onClick={(e) => {
                        e.stopPropagation();
                        deleteProject(project._id);
                      }}
                      color="error"
                    >
                      <Delete />
                    </IconButton>
                  </ListItemSecondaryAction>
                </ListItem>
              );
            })}
          </List>
        ) : (
          <Box sx={{ p: 4, textAlign: 'center' }}>
            <FolderOpen sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
            <Typography color="text.secondary" variant="h6">
              No saved projects yet
            </Typography>
            <Typography color="text.secondary" variant="body2" sx={{ mt: 1 }}>
              Create some beats, melodies, or harmonies and save your first project!
            </Typography>
          </Box>
        )}
      </Paper>

      {/* Save Dialog */}
      <Dialog open={saveDialogOpen} onClose={() => setSaveDialogOpen(false)}>
        <DialogTitle>Save Project</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label="Project Name"
            fullWidth
            value={projectName}
            onChange={(e) => setProjectName(e.target.value)}
            placeholder={currentProject.name}
            helperText="Leave empty to keep current name"
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setSaveDialogOpen(false)}>Cancel</Button>
          <Button onClick={saveProject} variant="contained">Save</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default ProjectManager;