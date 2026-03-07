import { useEffect, useState, useCallback, useRef } from 'react';
import socketService from '../services/socketService';

// Initialize socket immediately (before any component renders)
const initializeSocket = (serverUrl, userId) => {
  if (!socketService.getSocket()) {
    socketService.connect(serverUrl, userId);
  }
};

export const useSocket = (serverUrl, userId) => {
  const [isConnected, setIsConnected] = useState(false);
  const [sessionId, setSessionId] = useState(null);

  // Connect immediately, not in useEffect
  initializeSocket(serverUrl, userId);

  useEffect(() => {
    const handleConnection = (data) => {
      setIsConnected(true);
      setSessionId(data.sessionId);
    };

    const handleDisconnect = () => {
      setIsConnected(false);
    };

    socketService.on('CONNECTION_ESTABLISHED', handleConnection);
    socketService.on('disconnect', handleDisconnect);

    return () => {
      socketService.off('CONNECTION_ESTABLISHED', handleConnection);
      socketService.off('disconnect', handleDisconnect);
    };
  }, [serverUrl, userId]);

  return {
    isConnected,
    sessionId,
    socket: socketService
  };
};

export const useSocketEvent = (eventName, callback) => {
  const callbackRef = useRef(callback);

  // Update ref when callback changes
  useEffect(() => {
    callbackRef.current = callback;
  }, [callback]);

  useEffect(() => {
    const handler = (...args) => {
      callbackRef.current(...args);
    };

    socketService.on(eventName, handler);

    return () => {
      socketService.off(eventName, handler);
    };
  }, [eventName]);
};
