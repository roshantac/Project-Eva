import { useState, useRef, useCallback } from 'react';

export const useAudioRecorder = () => {
  const [isRecording, setIsRecording] = useState(false);
  const [audioLevel, setAudioLevel] = useState(0);
  const mediaRecorderRef = useRef(null);
  const audioContextRef = useRef(null);
  const analyserRef = useRef(null);
  const streamRef = useRef(null);
  const chunksRef = useRef([]);
  const animationFrameRef = useRef(null);
  const recordingStartTimeRef = useRef(null);

  const startRecording = useCallback(async (onDataAvailable) => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          echoCancellation: true,
          noiseSuppression: false,  // Disable to avoid over-compression
          autoGainControl: true,
          sampleRate: 48000,  // Higher sample rate
          channelCount: 1      // Mono
        } 
      });
      
      // Log the actual audio track settings
      const audioTrack = stream.getAudioTracks()[0];
      const settings = audioTrack.getSettings();
      console.log('Audio track settings:', settings);

      streamRef.current = stream;

      // Try to use webm with opus, fallback to browser default
      let mimeType = 'audio/webm;codecs=opus';
      if (!MediaRecorder.isTypeSupported(mimeType)) {
        mimeType = 'audio/webm';
        if (!MediaRecorder.isTypeSupported(mimeType)) {
          mimeType = ''; // Use browser default
        }
      }

      const options = mimeType ? { 
        mimeType,
        audioBitsPerSecond: 256000  // 256 kbps for much better quality and larger file size
      } : {};
      const mediaRecorder = new MediaRecorder(stream, options);

      console.log('MediaRecorder created with mimeType:', mimeType || 'default');

      mediaRecorderRef.current = mediaRecorder;
      chunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        console.log('Audio data available:', event.data.size, 'bytes');
        if (event.data.size > 0) {
          chunksRef.current.push(event.data);
          // Send intermediate chunks as they come in (like Node.js version)
          if (onDataAvailable) {
            onDataAvailable(event.data, false);
          }
        }
      };

      mediaRecorder.onstop = () => {
        console.log('Recording stopped. Total chunks:', chunksRef.current.length);
        const totalSize = chunksRef.current.reduce((sum, chunk) => sum + chunk.size, 0);
        console.log('Total captured audio:', totalSize, 'bytes');
        
        if (onDataAvailable && chunksRef.current.length > 0) {
          const audioBlob = new Blob(chunksRef.current, { type: mimeType || 'audio/webm' });
          console.log('Final audio blob size:', audioBlob.size, 'bytes');
          onDataAvailable(audioBlob, true);
        } else {
          console.warn('No audio chunks captured!');
        }
      };

      mediaRecorder.onerror = (event) => {
        console.error('MediaRecorder error:', event.error);
      };

      const audioContext = new (window.AudioContext || window.webkitAudioContext)();
      const analyser = audioContext.createAnalyser();
      const source = audioContext.createMediaStreamSource(stream);
      
      analyser.fftSize = 256;
      source.connect(analyser);

      audioContextRef.current = audioContext;
      analyserRef.current = analyser;

      const updateAudioLevel = () => {
        if (!analyserRef.current) return;

        const dataArray = new Uint8Array(analyserRef.current.frequencyBinCount);
        analyserRef.current.getByteFrequencyData(dataArray);

        const average = dataArray.reduce((a, b) => a + b) / dataArray.length;
        setAudioLevel(average / 255);

        animationFrameRef.current = requestAnimationFrame(updateAudioLevel);
      };

      updateAudioLevel();

      // Start recording - request data every 100ms but accumulate all chunks
      // The final blob will be created when stop() is called
      mediaRecorder.start(100);
      setIsRecording(true);
      recordingStartTimeRef.current = Date.now();

      console.log('Recording started with timeslice: 100ms');
      return true;
    } catch (error) {
      console.error('Error starting recording:', error);
      return false;
    }
  }, []);

  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current && isRecording) {
      // Check minimum recording duration
      const recordingDuration = Date.now() - recordingStartTimeRef.current;
      console.log('Recording duration:', recordingDuration, 'ms');
      
      if (recordingDuration < 1000) {
        console.warn('Recording too short! Please record for at least 1 second.');
      }
      
      // Request any remaining data before stopping
      if (mediaRecorderRef.current.state === 'recording') {
        console.log('Requesting final data before stop...');
        mediaRecorderRef.current.requestData();
      }
      
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      setAudioLevel(0);

      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop());
        streamRef.current = null;
      }

      if (audioContextRef.current) {
        audioContextRef.current.close();
        audioContextRef.current = null;
      }

      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
        animationFrameRef.current = null;
      }

      analyserRef.current = null;
      mediaRecorderRef.current = null;
      chunksRef.current = [];
    }
  }, [isRecording]);

  const pauseRecording = useCallback(() => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.pause();
    }
  }, [isRecording]);

  const resumeRecording = useCallback(() => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.resume();
    }
  }, [isRecording]);

  return {
    isRecording,
    audioLevel,
    startRecording,
    stopRecording,
    pauseRecording,
    resumeRecording
  };
};
