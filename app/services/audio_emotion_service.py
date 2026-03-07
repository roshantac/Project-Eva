"""
Audio Emotion Detection Service using wav2vec2
Detects emotions directly from voice audio using local models

NOTE: Requires Python 3.11-3.13 (PyTorch not yet available for Python 3.14)
"""

import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional

from app.utils.logger import logger

# Try to import required libraries (only available on Python < 3.14)
try:
    import numpy as np
    import torch
    import torchaudio
    from transformers import Wav2Vec2FeatureExtractor, Wav2Vec2ForSequenceClassification
    DEPENDENCIES_AVAILABLE = True
except ImportError as e:
    DEPENDENCIES_AVAILABLE = False
    missing_lib = str(e).split("'")[1] if "'" in str(e) else "required libraries"
    logger.warning(f'⚠️ Audio emotion detection unavailable: {missing_lib} not installed')
    logger.info(f'   Current Python version: {sys.version_info.major}.{sys.version_info.minor}')
    if sys.version_info >= (3, 14):
        logger.info('   PyTorch requires Python 3.11-3.13')
        logger.info('   Audio emotion detection will be available when PyTorch supports Python 3.14')
    else:
        logger.info(f'   Install with: pip install transformers torch torchaudio')


class AudioEmotionService:
    """
    Service for detecting emotions from audio using wav2vec2 model (LOCAL ONLY)
    """
    
    def __init__(self):
        """Initialize audio emotion detection service"""
        self.enabled = False
        self.model = None
        self.feature_extractor = None
        self.device = None
        
        # Check if feature is enabled in config
        config_enabled = os.getenv('AUDIO_EMOTION_ENABLED', 'true').lower() == 'true'
        
        if not config_enabled:
            logger.info('Audio emotion detection disabled in config')
            return
        
        if not DEPENDENCIES_AVAILABLE:
            return
        
        # Model configuration
        self.model_name = os.getenv(
            'AUDIO_EMOTION_MODEL', 
            'ehcalabres/wav2vec2-lg-xlsr-en-speech-emotion-recognition'
        )
        
        # Emotion mapping from model output to our emotion types
        self.emotion_mapping = {
            'angry': 'angry',
            'calm': 'neutral',
            'disgust': 'angry',
            'fearful': 'anxious',
            'happy': 'happy',
            'neutral': 'neutral',
            'sad': 'sad',
            'surprised': 'excited'
        }
        
        self._initialize_model()
    
    def _initialize_model(self):
        """Initialize the wav2vec2 emotion detection model"""
        try:
            logger.info(f'📥 Loading audio emotion model: {self.model_name}')
            logger.info('   (First run will download ~1.2 GB, takes 2-5 minutes)')
            
            # Check if CUDA is available
            self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
            logger.info(f'   Using device: {self.device}')
            
            # Load feature extractor and model
            logger.debug('   Loading feature extractor...')
            self.feature_extractor = Wav2Vec2FeatureExtractor.from_pretrained(
                self.model_name,
                trust_remote_code=True
            )
            logger.debug('   Loading model...')
            self.model = Wav2Vec2ForSequenceClassification.from_pretrained(
                self.model_name,
                trust_remote_code=True
            )
            self.model.to(self.device)
            self.model.eval()
            
            self.enabled = True
            logger.info('✅ Audio emotion model loaded successfully')
            logger.info('   Emotions will be detected from voice tone and prosody')
            
        except Exception as error:
            import traceback
            logger.error(f'❌ Failed to load audio emotion model: {error}')
            logger.debug(f'   Traceback: {traceback.format_exc()}')
            logger.warning('   Audio emotion detection will be disabled')
            logger.info('   Text-based emotion detection will still work')
            self.enabled = False
    
    
    async def detect_emotion_from_audio(
        self, 
        audio_path: Path,
        sample_rate: int = 16000
    ) -> Dict[str, Any]:
        """
        Detect emotion from audio file using wav2vec2 model
        
        Args:
            audio_path: Path to audio file (WAV format, 16kHz recommended)
            sample_rate: Target sample rate for processing
            
        Returns:
            Dictionary with emotion, confidence, and raw scores
        """
        if not self.enabled:
            return {
                'emotion': None,
                'confidence': 0.0,
                'audio_emotion_detected': False,
                'error': 'Audio emotion detection not available'
            }
        
        try:
            logger.debug(f'Detecting emotion from audio: {audio_path}')
            
            # Load audio file using torchaudio
            waveform, sr = torchaudio.load(str(audio_path))
            
            # Convert to mono if stereo
            if waveform.shape[0] > 1:
                waveform = torch.mean(waveform, dim=0, keepdim=True)
            
            # Resample if needed
            if sr != sample_rate:
                resampler = torchaudio.transforms.Resample(sr, sample_rate)
                waveform = resampler(waveform)
            
            # Convert to numpy array
            audio = waveform.squeeze().numpy()
            
            # Check if audio is too short or silent
            if len(audio) < sample_rate * 0.5:  # Less than 0.5 seconds
                logger.warning('Audio too short for emotion detection')
                return {
                    'emotion': None,
                    'confidence': 0.0,
                    'audio_emotion_detected': False,
                    'error': 'Audio too short'
                }
            
            # Check if audio is silent
            if np.max(np.abs(audio)) < 0.01:
                logger.warning('Audio is silent or too quiet')
                return {
                    'emotion': None,
                    'confidence': 0.0,
                    'audio_emotion_detected': False,
                    'error': 'Audio is silent'
                }
            
            # Preprocess audio
            inputs = self.feature_extractor(
                audio, 
                sampling_rate=sample_rate, 
                return_tensors="pt", 
                padding=True
            )
            
            # Move to device
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            # Get predictions
            with torch.no_grad():
                logits = self.model(**inputs).logits
            
            # Get probabilities
            probabilities = torch.nn.functional.softmax(logits, dim=-1)
            predicted_id = torch.argmax(probabilities, dim=-1).item()
            confidence = probabilities[0][predicted_id].item()
            
            # Get emotion label
            predicted_emotion = self.model.config.id2label[predicted_id]
            
            # Map to our emotion types
            mapped_emotion = self.emotion_mapping.get(
                predicted_emotion.lower(), 
                'neutral'
            )
            
            # Get all emotion scores
            emotion_scores = {}
            for idx, prob in enumerate(probabilities[0].tolist()):
                emotion_label = self.model.config.id2label[idx]
                mapped_label = self.emotion_mapping.get(emotion_label.lower(), emotion_label)
                emotion_scores[mapped_label] = prob
            
            result = {
                'emotion': mapped_emotion,
                'confidence': confidence,
                'audio_emotion_detected': True,
                'raw_emotion': predicted_emotion,
                'all_scores': emotion_scores,
                'method': 'wav2vec2'
            }
            
            logger.info(f'🎤 Audio emotion detected: {mapped_emotion} (confidence: {confidence:.2f})')
            logger.debug(f'   Raw emotion: {predicted_emotion}')
            
            return result
            
        except Exception as error:
            logger.error(f'Error detecting emotion from audio: {error}')
            return {
                'emotion': None,
                'confidence': 0.0,
                'audio_emotion_detected': False,
                'error': str(error)
            }
    


# Singleton instance
audio_emotion_service = AudioEmotionService()
