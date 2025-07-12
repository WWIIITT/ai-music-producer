// client/src/components/AudioVisualizer.js
import React, { useEffect, useRef } from 'react';
import { Box } from '@mui/material';
import * as Tone from 'tone';

const AudioVisualizer = ({ isPlaying }) => {
  const canvasRef = useRef(null);
  const animationRef = useRef(null);
  const analyserRef = useRef(null);

  useEffect(() => {
    // Create analyser
    const analyser = new Tone.Analyser('waveform', 256);
    Tone.Destination.connect(analyser);
    analyserRef.current = analyser;

    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
      analyser.dispose();
    };
  }, []);

  useEffect(() => {
    if (isPlaying) {
      startVisualization();
    } else {
      stopVisualization();
    }
  }, [isPlaying]);

  const startVisualization = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    const width = canvas.width;
    const height = canvas.height;

    const draw = () => {
      const values = analyserRef.current.getValue();
      
      // Clear canvas
      ctx.fillStyle = '#1e1e1e';
      ctx.fillRect(0, 0, width, height);
      
      // Draw waveform
      ctx.lineWidth = 2;
      ctx.strokeStyle = '#90caf9';
      ctx.beginPath();
      
      const sliceWidth = width / values.length;
      let x = 0;
      
      for (let i = 0; i < values.length; i++) {
        const v = (values[i] + 1) / 2; // Normalize to 0-1
        const y = v * height;
        
        if (i === 0) {
          ctx.moveTo(x, y);
        } else {
          ctx.lineTo(x, y);
        }
        
        x += sliceWidth;
      }
      
      ctx.stroke();
      
      // Draw frequency bars
      ctx.fillStyle = '#f48fb1';
      const barWidth = width / values.length * 2;
      
      for (let i = 0; i < values.length; i += 2) {
        const barHeight = (values[i] + 1) * height / 2;
        ctx.globalAlpha = 0.5;
        ctx.fillRect(i * barWidth / 2, height - barHeight, barWidth - 2, barHeight);
      }
      
      ctx.globalAlpha = 1;
      
      animationRef.current = requestAnimationFrame(draw);
    };
    
    draw();
  };

  const stopVisualization = () => {
    if (animationRef.current) {
      cancelAnimationFrame(animationRef.current);
    }
    
    // Clear canvas
    const canvas = canvasRef.current;
    if (canvas) {
      const ctx = canvas.getContext('2d');
      ctx.fillStyle = '#1e1e1e';
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      
      // Draw static line
      ctx.strokeStyle = '#444';
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.moveTo(0, canvas.height / 2);
      ctx.lineTo(canvas.width, canvas.height / 2);
      ctx.stroke();
    }
  };

  return (
    <Box sx={{ width: '100%', height: 150 }}>
      <canvas
        ref={canvasRef}
        width={300}
        height={150}
        style={{
          width: '100%',
          height: '100%',
          borderRadius: 4,
          border: '1px solid #333'
        }}
      />
    </Box>
  );
};

export default AudioVisualizer;
