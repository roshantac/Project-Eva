"""
Emotion detection engine for analyzing user emotions
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional
from app.config.constants import (
    EmotionType,
    SentimentType,
    EMOTION_KEYWORDS
)
from app.utils.logger import logger


class EmotionEngine:
    """Engine for detecting and analyzing emotions in text and audio"""
    
    def __init__(self, llm_service, audio_emotion_service=None):
        self.llm_service = llm_service
        self.audio_emotion_service = audio_emotion_service
        self.emotion_keywords = self._initialize_emotion_keywords()
    
    def _initialize_emotion_keywords(self) -> Dict[EmotionType, list]:
        """Initialize emotion keywords with emojis"""
        return {
            EmotionType.HAPPY: [
                'happy', 'joy', 'excited', 'great', 'wonderful', 'amazing',
                'love', 'fantastic', 'excellent', 'glad', 'delighted',
                '😊', '😄', '🎉'
            ],
            EmotionType.SAD: [
                'sad', 'unhappy', 'depressed', 'down', 'miserable', 'upset',
                'crying', 'tears', 'heartbroken', 'lonely',
                '😢', '😭', '💔'
            ],
            EmotionType.ANXIOUS: [
                'anxious', 'worried', 'nervous', 'stressed', 'panic', 'fear',
                'scared', 'overwhelmed', 'tense', 'uneasy',
                '😰', '😟'
            ],
            EmotionType.EXCITED: [
                'excited', 'thrilled', 'pumped', 'enthusiastic', 'eager',
                "can't wait", 'looking forward', 'stoked',
                '🎊', '🚀'
            ],
            EmotionType.ANGRY: [
                'angry', 'mad', 'furious', 'frustrated', 'annoyed',
                'irritated', 'rage', 'pissed', 'upset',
                '😠', '😡', '🤬'
            ],
            EmotionType.GRATEFUL: [
                'grateful', 'thankful', 'appreciate', 'thanks', 'thank you',
                'blessed', 'fortunate',
                '🙏', '💝'
            ],
            EmotionType.CONFUSED: [
                'confused', 'puzzled', 'lost', "don't understand", 'unclear',
                'bewildered',
                '🤔', '😕'
            ]
        }
    
    async def detect_emotion(
        self, 
        text: str, 
        audio_path: Optional[Path] = None
    ) -> Dict[str, Any]:
        """
        Detect emotion in text using both quick and LLM-based detection,
        optionally enhanced with audio emotion detection
        
        Args:
            text: Text to analyze
            audio_path: Optional path to audio file for voice emotion detection
            
        Returns:
            Dictionary with emotion, sentiment, confidence, intensity, and details
        """
        try:
            quick_emotion = self.quick_emotion_detection(text)
            
            llm_emotion = await self.llm_emotion_detection(text)
            
            # Get audio emotion if available
            audio_emotion = None
            if audio_path and self.audio_emotion_service:
                audio_emotion = await self.audio_emotion_service.detect_emotion_from_audio(audio_path)
            
            # Combine emotions with priority: audio > LLM > quick
            final_emotion = quick_emotion['emotion']
            final_confidence = quick_emotion['confidence']
            emotion_source = 'keyword'
            
            if llm_emotion.get('emotion'):
                final_emotion = llm_emotion['emotion']
                final_confidence = llm_emotion.get('confidence', 0.7)
                emotion_source = 'llm'
            
            if audio_emotion and audio_emotion.get('audio_emotion_detected'):
                # Audio emotion takes priority if confidence is high
                if audio_emotion.get('confidence', 0) > 0.5:
                    final_emotion = audio_emotion['emotion']
                    final_confidence = audio_emotion['confidence']
                    emotion_source = 'audio'
                    logger.info(f"🎤 Using audio emotion: {final_emotion} (confidence: {final_confidence:.2f})")
            
            final_sentiment = llm_emotion.get('sentiment') or quick_emotion['sentiment']
            
            logger.info(f"Emotion detected: {final_emotion}, Sentiment: {final_sentiment}, Source: {emotion_source}")
            
            result = {
                'emotion': final_emotion,
                'sentiment': final_sentiment,
                'confidence': final_confidence,
                'intensity': llm_emotion.get('intensity') or quick_emotion['intensity'],
                'details': llm_emotion.get('details', {}),
                'emotion_source': emotion_source
            }
            
            # Add audio emotion details if available
            if audio_emotion and audio_emotion.get('audio_emotion_detected'):
                result['audio_emotion'] = {
                    'emotion': audio_emotion['emotion'],
                    'confidence': audio_emotion['confidence'],
                    'raw_emotion': audio_emotion.get('raw_emotion'),
                    'all_scores': audio_emotion.get('all_scores', {})
                }
            
            return result
            
        except Exception as error:
            logger.error(f'Error detecting emotion: {error}')
            return self.quick_emotion_detection(text)
    
    def quick_emotion_detection(self, text: str) -> Dict[str, Any]:
        """
        Quick keyword-based emotion detection
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary with emotion, sentiment, confidence, and intensity
        """
        lower_text = text.lower()
        emotion_scores = {}
        
        for emotion, keywords in self.emotion_keywords.items():
            emotion_scores[emotion] = 0
            for keyword in keywords:
                if keyword.lower() in lower_text:
                    emotion_scores[emotion] += 1
        
        max_score = 0
        detected_emotion = EmotionType.NEUTRAL
        
        for emotion, score in emotion_scores.items():
            if score > max_score:
                max_score = score
                detected_emotion = emotion
        
        sentiment = self.detect_sentiment(detected_emotion)
        
        return {
            'emotion': detected_emotion.value,
            'sentiment': sentiment.value,
            'confidence': min(max_score * 0.3, 0.9) if max_score > 0 else 0.5,
            'intensity': 'high' if max_score > 2 else 'medium' if max_score > 0 else 'low'
        }
    
    async def llm_emotion_detection(self, text: str) -> Dict[str, Any]:
        """
        LLM-based emotion detection for more accurate analysis
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary with emotion analysis results
        """
        try:
            prompt = f"""Analyze the emotional content of the following text. Identify:
1. Primary emotion (happy, sad, anxious, excited, angry, neutral, confused, grateful)
2. Sentiment (positive, negative, neutral)
3. Intensity (low, medium, high)
4. Confidence score (0-1)

Text: "{text}"

Respond in JSON format:
{{
  "emotion": "emotion_name",
  "sentiment": "sentiment_type",
  "intensity": "intensity_level",
  "confidence": 0.0,
  "details": {{
    "reasoning": "brief explanation"
  }}
}}"""

            response = await self.llm_service.generate_completion([
                {'role': 'system', 'content': 'You are an expert emotion analyzer. Respond only with valid JSON.'},
                {'role': 'user', 'content': prompt}
            ], {
                'temperature': 0.3,
                'max_tokens': 200
            })

            logger.debug(f'LLM emotion response: {response}')
            
            # Try to extract JSON if wrapped in markdown code blocks
            response_text = response.strip()
            if response_text.startswith('```'):
                # Extract JSON from code block
                lines = response_text.split('\n')
                json_lines = [line for line in lines if line and not line.startswith('```')]
                response_text = '\n'.join(json_lines)
            
            result = json.loads(response_text)
            return result
        except json.JSONDecodeError as error:
            logger.error(f'LLM emotion detection failed - invalid JSON: {error}')
            logger.debug(f'Response was: {response[:200]}...')
            return {}
        except Exception as error:
            logger.error(f'LLM emotion detection failed: {error}')
            return {}
    
    def detect_sentiment(self, emotion: EmotionType) -> SentimentType:
        """
        Detect sentiment based on emotion
        
        Args:
            emotion: Detected emotion
            
        Returns:
            Sentiment type
        """
        positive_emotions = [
            EmotionType.HAPPY,
            EmotionType.EXCITED,
            EmotionType.GRATEFUL
        ]
        negative_emotions = [
            EmotionType.SAD,
            EmotionType.ANXIOUS,
            EmotionType.ANGRY,
            EmotionType.CONFUSED
        ]
        
        if emotion in positive_emotions:
            return SentimentType.POSITIVE
        elif emotion in negative_emotions:
            return SentimentType.NEGATIVE
        
        return SentimentType.NEUTRAL
    
    def generate_emotional_context(self, emotion_data: Dict[str, Any]) -> str:
        """
        Generate emotional context for LLM system prompt
        
        Args:
            emotion_data: Dictionary with emotion, sentiment, and intensity
            
        Returns:
            Emotional context string
        """
        emotion = emotion_data.get('emotion', 'neutral')
        intensity = emotion_data.get('intensity', 'medium')
        
        contexts = {
            EmotionType.SAD.value: 'The user seems to be feeling down. Respond with empathy and gentle support.',
            EmotionType.ANXIOUS.value: 'The user appears anxious or worried. Provide calm reassurance and practical help.',
            EmotionType.EXCITED.value: 'The user is excited! Match their energy with enthusiasm.',
            EmotionType.ANGRY.value: 'The user seems frustrated or angry. Stay calm and validate their feelings.',
            EmotionType.HAPPY.value: 'The user is in a positive mood. Share in their happiness.',
            EmotionType.GRATEFUL.value: 'The user is expressing gratitude. Acknowledge it warmly.',
            EmotionType.CONFUSED.value: 'The user seems confused. Provide clear, patient explanations.',
            EmotionType.NEUTRAL.value: 'The user has a neutral tone. Respond naturally and helpfully.'
        }
        
        context = contexts.get(emotion, contexts[EmotionType.NEUTRAL.value])
        
        if intensity == 'high':
            context += ' The emotion is quite strong, so be especially mindful in your response.'
        
        return context
    
    def should_save_as_memory(self, emotion_data: Dict[str, Any]) -> bool:
        """
        Determine if emotion is significant enough to save as memory
        
        Args:
            emotion_data: Dictionary with emotion and intensity
            
        Returns:
            True if should be saved as memory
        """
        emotion = emotion_data.get('emotion', 'neutral')
        intensity = emotion_data.get('intensity', 'low')
        
        significant_emotions = [
            EmotionType.SAD.value,
            EmotionType.ANXIOUS.value,
            EmotionType.EXCITED.value,
            EmotionType.ANGRY.value,
            EmotionType.GRATEFUL.value
        ]
        
        return emotion in significant_emotions and intensity != 'low'
