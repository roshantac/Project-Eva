"""
Audio Correction Agent
Corrects transcription errors from speech-to-text conversion
"""

from typing import Dict, Any
from agents.base_agent import BaseAgent
from prompts.system_prompts import SystemPrompts, PromptTemplates


class AudioCorrectionAgent(BaseAgent):
    """Agent for correcting audio transcription errors"""
    
    def __init__(self):
        super().__init__("audio_correction")
        self.system_prompt = SystemPrompts.AUDIO_CORRECTION
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Correct transcription errors in audio-to-text output
        
        Args:
            input_data: Dict with 'raw_text' key containing transcribed text
        
        Returns:
            Dict with 'corrected_text' and metadata
        """
        try:
            raw_text = input_data.get("raw_text", "")
            
            if not raw_text or not raw_text.strip():
                return {
                    "success": True,
                    "corrected_text": "",
                    "changes_made": False,
                    "original_text": raw_text
                }
            
            self.log_decision("Correcting audio transcription", {
                "text_length": len(raw_text)
            })
            
            # Build prompt
            prompt = PromptTemplates.audio_correction_template(raw_text)
            
            # Call LLM
            result = self.call_llm(
                prompt=prompt,
                system_prompt=self.system_prompt
            )
            
            if not result.get("success"):
                # Fallback: return original text if correction fails
                self.log_decision("Correction failed, using original text", {
                    "error": result.get("error")
                })
                return {
                    "success": True,
                    "corrected_text": raw_text,
                    "changes_made": False,
                    "original_text": raw_text,
                    "error": result.get("error")
                }
            
            corrected_text = result.get("response", "").strip()
            
            # Fallback: if corrected text is empty, use original
            if not corrected_text:
                self.log_decision("Correction returned empty, using original text", {
                    "original_length": len(raw_text)
                })
                corrected_text = raw_text
                changes_made = False
            else:
                # Check if any changes were made
                changes_made = corrected_text.lower() != raw_text.lower()
            
            self.log_decision("Transcription corrected", {
                "changes_made": changes_made,
                "original_length": len(raw_text),
                "corrected_length": len(corrected_text)
            })
            
            return {
                "success": True,
                "corrected_text": corrected_text,
                "original_text": raw_text,
                "changes_made": changes_made,
                "metadata": {
                    "agent": self.agent_name,
                    "model": result.get("model"),
                    "processing_time": result.get("total_duration", 0)
                }
            }
        
        except Exception as e:
            return self.handle_error(e, "audio correction")

# Made with Bob
