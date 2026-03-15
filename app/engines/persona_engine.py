"""
Persona management engine for different conversation styles
"""

from typing import Dict, Any, Optional, List
from app.config.constants import PersonaType
from app.utils.logger import logger


class PersonaEngine:
    """Engine for managing different conversation personas"""
    
    def __init__(self):
        self.personas = self._initialize_personas()
        self.current_persona = PersonaType.FRIEND
    
    def _initialize_personas(self) -> Dict[PersonaType, Dict[str, Any]]:
        """Initialize persona definitions with system prompts"""
        return {
            PersonaType.MENTOR: {
                'name': 'Mentor',
                'description': 'Encouraging, growth-oriented, and reflective',
                'system_prompt': """You are Eva, an AI mentor focused on personal growth and development.

Your characteristics:
- Encouraging and supportive, helping users reach their potential
- Ask reflective questions that promote self-discovery
- Focus on long-term thinking and sustainable growth
- Share wisdom and insights that inspire action
- Celebrate progress and learning from setbacks
- Use a warm but professional tone
- Guide rather than dictate

Your approach:
- Help users identify their goals and values
- Encourage critical thinking and self-reflection
- Provide constructive feedback with actionable steps
- Share relevant examples and analogies
- Foster independence and self-reliance
- Acknowledge emotions while focusing on growth""",
                'response_style': {
                    'tone': 'encouraging and wise',
                    'language': 'thoughtful and inspiring',
                    'questions': 'reflective and growth-oriented',
                    'examples': 'uses metaphors and life lessons'
                }
            },
            
            PersonaType.FRIEND: {
                'name': 'Friend',
                'description': 'Casual, warm, and supportive',
                'system_prompt': """You are Eva, a friendly and supportive AI companion.

Your characteristics:
- Warm, casual, and approachable
- Genuinely interested in the user's wellbeing
- Use conversational, natural language
- Show empathy and emotional support
- Share in their joys and comfort them in struggles
- Be authentic and relatable
- Use appropriate humor when suitable

Your approach:
- Listen actively and validate feelings
- Offer support without being pushy
- Be present and engaged in the conversation
- Share excitement for their wins
- Provide comfort during difficult times
- Keep things light and enjoyable when appropriate
- Be someone they can trust and confide in""",
                'response_style': {
                    'tone': 'warm and friendly',
                    'language': 'casual and conversational',
                    'questions': 'curious and caring',
                    'examples': 'relatable everyday situations'
                }
            },
            
            PersonaType.ADVISOR: {
                'name': 'Advisor',
                'description': 'Structured, practical, and professional',
                'system_prompt': """You are Eva, a professional AI advisor providing practical guidance.

Your characteristics:
- Clear, structured, and organized
- Focus on practical solutions and actionable steps
- Professional yet approachable tone
- Data-informed and logical
- Efficient and to-the-point
- Provide clear frameworks and methodologies
- Help prioritize and plan

Your approach:
- Break down complex problems into manageable steps
- Provide clear, actionable recommendations
- Use structured formats (lists, steps, frameworks)
- Consider pros and cons objectively
- Help with decision-making processes
- Offer practical tools and resources
- Focus on implementation and results""",
                'response_style': {
                    'tone': 'professional and clear',
                    'language': 'structured and precise',
                    'questions': 'clarifying and strategic',
                    'examples': 'practical case studies and frameworks'
                }
            }
        }
    
    def set_persona(self, persona_type: str) -> bool:
        """
        Set the current persona
        
        Args:
            persona_type: Persona type to set
            
        Returns:
            True if successful, False otherwise
        """
        try:
            persona_enum = PersonaType(persona_type)
            if persona_enum not in self.personas:
                logger.warning(f"Invalid persona type: {persona_type}, defaulting to friend")
                self.current_persona = PersonaType.FRIEND
                return False
            
            self.current_persona = persona_enum
            logger.info(f"Persona changed to: {persona_type}")
            return True
        except ValueError:
            logger.warning(f"Invalid persona type: {persona_type}, defaulting to friend")
            self.current_persona = PersonaType.FRIEND
            return False
    
    def get_persona(self, persona_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Get persona definition
        
        Args:
            persona_type: Optional persona type, defaults to current persona
            
        Returns:
            Persona definition dictionary
        """
        try:
            if persona_type:
                persona_enum = PersonaType(persona_type)
            else:
                persona_enum = self.current_persona
            
            return self.personas.get(persona_enum, self.personas[PersonaType.FRIEND])
        except ValueError:
            return self.personas[PersonaType.FRIEND]
    
    def get_current_persona(self) -> Dict[str, Any]:
        """
        Get current persona definition
        
        Returns:
            Current persona definition dictionary
        """
        return self.get_persona(self.current_persona.value)
    
    def get_system_prompt(
        self,
        persona_type: Optional[str] = None,
        emotional_context: str = ''
    ) -> str:
        """
        Get system prompt for persona with optional emotional context
        
        Args:
            persona_type: Optional persona type, defaults to current persona
            emotional_context: Optional emotional context to append
            
        Returns:
            System prompt string
        """
        persona = self.get_persona(persona_type)
        prompt = persona['system_prompt']
        
        if emotional_context:
            prompt += f"\n\nCurrent emotional context: {emotional_context}"
        
        prompt += f"\n\nRemember to embody the {persona['name']} persona in your responses, using a {persona['response_style']['tone']} tone."
        
        return prompt
    
    def get_all_personas(self) -> List[Dict[str, str]]:
        """
        Get all available personas
        
        Returns:
            List of persona summaries
        """
        return [
            {
                'type': persona_type.value,
                'name': persona_data['name'],
                'description': persona_data['description']
            }
            for persona_type, persona_data in self.personas.items()
        ]
    
    def get_persona_guidance(
        self,
        persona_type: Optional[str] = None,
        situation: str = ''
    ) -> str:
        """
        Get guidance for how to respond based on persona and situation
        
        Args:
            persona_type: Optional persona type, defaults to current persona
            situation: Description of the situation
            
        Returns:
            Guidance string
        """
        persona = self.get_persona(persona_type)
        current_type = persona_type or self.current_persona.value
        
        guidance = f"As a {persona['name']}, "
        
        if 'problem' in situation or 'issue' in situation:
            if current_type == PersonaType.MENTOR.value:
                guidance += 'help them see this as a learning opportunity and guide them to find their own solution.'
            elif current_type == PersonaType.FRIEND.value:
                guidance += 'offer emotional support first, then help them think through it together.'
            elif current_type == PersonaType.ADVISOR.value:
                guidance += 'provide a structured approach to solve the problem with clear steps.'
        elif 'success' in situation or 'achievement' in situation:
            if current_type == PersonaType.MENTOR.value:
                guidance += 'celebrate their growth and help them reflect on what they learned.'
            elif current_type == PersonaType.FRIEND.value:
                guidance += 'share genuine excitement and celebrate with them!'
            elif current_type == PersonaType.ADVISOR.value:
                guidance += 'acknowledge the achievement and discuss next steps or optimization.'
        else:
            guidance += f"respond with a {persona['response_style']['tone']} tone and {persona['response_style']['language']} language."
        
        return guidance
    
    def adapt_response_to_persona(
        self,
        response: str,
        persona_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Adapt response to match persona style
        
        Args:
            response: Response text
            persona_type: Optional persona type, defaults to current persona
            
        Returns:
            Dictionary with adapted response and persona info
        """
        persona = self.get_persona(persona_type)
        return {
            'text': response,
            'persona': persona['name'],
            'style': persona['response_style']
        }
