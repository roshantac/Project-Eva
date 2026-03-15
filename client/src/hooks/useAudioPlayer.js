import { useState, useRef, useCallback } from 'react';

export const useAudioPlayer = () => {
  const [isPlaying, setIsPlaying] = useState(false);
  const audioContextRef = useRef(null);
  const sourceNodeRef = useRef(null);
  const audioQueueRef = useRef([]);
  const isProcessingRef = useRef(false);

  const initAudioContext = useCallback(() => {
    if (!audioContextRef.current) {
      audioContextRef.current = new (window.AudioContext || window.webkitAudioContext)();
    }
    return audioContextRef.current;
  }, []);

  const playAudioChunk = useCallback(async (audioData) => {
    try {
      const audioContext = initAudioContext();

      let arrayBuffer;
      if (audioData instanceof ArrayBuffer) {
        arrayBuffer = audioData;
      } else if (audioData instanceof Blob) {
        console.log('Converting Blob to ArrayBuffer, size:', audioData.size, 'bytes');
        arrayBuffer = await audioData.arrayBuffer();
      } else if (Buffer.isBuffer(audioData)) {
        arrayBuffer = audioData.buffer.slice(
          audioData.byteOffset,
          audioData.byteOffset + audioData.byteLength
        );
      } else {
        console.error('Unsupported audio data type:', typeof audioData);
        return;
      }

      console.log('Decoding audio data, size:', arrayBuffer.byteLength, 'bytes');
      const audioBuffer = await audioContext.decodeAudioData(arrayBuffer);
      console.log('Audio decoded successfully, duration:', audioBuffer.duration.toFixed(2), 'seconds');
      
      const source = audioContext.createBufferSource();
      source.buffer = audioBuffer;
      source.connect(audioContext.destination);

      sourceNodeRef.current = source;

      return new Promise((resolve) => {
        source.onended = () => {
          console.log('Audio playback finished');
          setIsPlaying(false);
          resolve();
        };

        source.start(0);
        setIsPlaying(true);
        console.log('Audio playback started');
      });
    } catch (error) {
      console.error('Error playing audio chunk:', error);
      console.error('Error details:', error.message);
      setIsPlaying(false);
    }
  }, [initAudioContext]);

  const queueAudioChunk = useCallback((audioData) => {
    audioQueueRef.current.push(audioData);
    processQueue();
  }, []);

  const processQueue = useCallback(async () => {
    if (isProcessingRef.current || audioQueueRef.current.length === 0) {
      return;
    }

    isProcessingRef.current = true;

    while (audioQueueRef.current.length > 0) {
      const audioData = audioQueueRef.current.shift();
      await playAudioChunk(audioData);
    }

    isProcessingRef.current = false;
  }, [playAudioChunk]);

  const playAudioBuffer = useCallback(async (audioBuffer) => {
    try {
      const audioContext = initAudioContext();
      const source = audioContext.createBufferSource();
      source.buffer = audioBuffer;
      source.connect(audioContext.destination);

      sourceNodeRef.current = source;

      return new Promise((resolve) => {
        source.onended = () => {
          setIsPlaying(false);
          resolve();
        };

        source.start(0);
        setIsPlaying(true);
      });
    } catch (error) {
      console.error('Error playing audio buffer:', error);
      setIsPlaying(false);
    }
  }, [initAudioContext]);

  const stopAudio = useCallback(() => {
    if (sourceNodeRef.current) {
      try {
        sourceNodeRef.current.stop();
      } catch (error) {
        console.error('Error stopping audio:', error);
      }
      sourceNodeRef.current = null;
    }

    audioQueueRef.current = [];
    isProcessingRef.current = false;
    setIsPlaying(false);
  }, []);

  const pauseAudio = useCallback(() => {
    if (audioContextRef.current && audioContextRef.current.state === 'running') {
      audioContextRef.current.suspend();
    }
  }, []);

  const resumeAudio = useCallback(() => {
    if (audioContextRef.current && audioContextRef.current.state === 'suspended') {
      audioContextRef.current.resume();
    }
  }, []);

  return {
    isPlaying,
    playAudioChunk,
    queueAudioChunk,
    playAudioBuffer,
    stopAudio,
    pauseAudio,
    resumeAudio
  };
};
