// client/src/components/ProjectManager.js
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
  Paper
} from '@mui/material';
import {
  Delete,
  CloudDownload,
  Save,
  FolderOpen
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
      const response = await axios.get(`${import.meta.env.VITE_API_URL}/api/projects`);
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
      
      await axios.post(`${import.meta.env.VITE_API_URL}/api/projects/save`, projectToSave);
      toast.success('Project saved!');
      setSaveDialogOpen(false);
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
    if (!confirm('Are you sure you want to delete this project?')) return;
    
    try {
      await axios.delete(`${import.meta.env.VITE_API_URL}/api/projects/${projectId}`);
      toast.success('Project deleted');
      loadProjects();
    } catch (error) {
      toast.error('Failed to delete project');
      console.error(error);
    }
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
        <Typography variant="h5">Projects</Typography>
        <Button
          variant="contained"
          startIcon={<Save />}
          onClick={() => setSaveDialogOpen(true)}
        >
          Save Current
        </Button>
      </Box>

      <Paper sx={{ bgcolor: '#2a2a2a' }}>
        {projects.length > 0 ? (
          <List>
            {projects.map((project) => (
              <ListItem 
                key={project._id} 
                button
                onClick={() => loadProject(project)}
                sx={{ '&:hover': { bgcolor: '#333' } }}
              >
                <ListItemText
                  primary={project.name}
                  secondary={`Created: ${new Date(project.created_at).toLocaleDateString()} • ${project.beats?.length || 0} beats, ${project.melodies?.length || 0} melodies`}
                />
                <ListItemSecondaryAction>
                  <IconButton 
                    edge="end" 
                    onClick={(e) => {
                      e.stopPropagation();
                      deleteProject(project._id);
                    }}
                  >
                    <Delete />
                  </IconButton>
                </ListItemSecondaryAction>
              </ListItem>
            ))}
          </List>
        ) : (
          <Box sx={{ p: 4, textAlign: 'center' }}>
            <FolderOpen sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
            <Typography color="text.secondary">
              No saved projects yet
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