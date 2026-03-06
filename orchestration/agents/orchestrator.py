"""
Agent Orchestrator
Coordinates all agents and manages the conversation flow
"""

from typing import Dict, Any, Optional
from agents.audio_correction_agent import AudioCorrectionAgent
from agents.intent_classifier_agent import IntentClassifierAgent
from agents.emotional_detector_agent import EmotionalDetectorAgent
from agents.memory_classifier_agent import MemoryClassifierAgent
from agents.conversation_manager_agent import ConversationManagerAgent
from agents.health_wellness_agent import HealthWellnessAgent
from utils.state_manager import ConversationState, Role, EmotionalState
from utils.logger import get_logger
from utils.config_manager import get_config
from utils.ollama_client import OllamaClient
from utils.time_utils import TimeContext

logger = get_logger()


class AgentOrchestrator:
    """Orchestrates all agents and manages conversation flow"""
    
    def __init__(self):
        # Initialize all agents
        self.audio_correction = AudioCorrectionAgent()
        self.intent_classifier = IntentClassifierAgent()
        self.emotional_detector = EmotionalDetectorAgent()
        self.memory_classifier = MemoryClassifierAgent()
        self.conversation_manager = ConversationManagerAgent()
        self.health_wellness = HealthWellnessAgent()
        
        # Configuration
        self.config = get_config()
        
        # LLM client for summarization
        model_config = self.config.get_model_config()
        self.llm_client = OllamaClient(
            base_url=model_config.get('base_url', 'http://localhost:11434'),
            model=model_config.get('name', 'gemma:7b')
        )
        
        logger.info("Agent Orchestrator initialized with all agents including Health & Wellness")
    
    def process_message(
        self,
        raw_text: str,
        conversation_state: ConversationState
    ) -> Dict[str, Any]:
        """
        Process a user message through the agent pipeline
        
        Args:
            raw_text: Raw transcribed text from audio service
            conversation_state: Current conversation state
        
        Returns:
            Dict with response and updated state information
        """
        try:
            logger.info("=" * 60)
            logger.info("Processing new message")
            logger.info("=" * 60)
            
            # Check if summarization is needed
            context_config = self.config.get_context_config()
            summary_threshold = context_config.get('summary_threshold', 20)
            
            if conversation_state.needs_summarization(summary_threshold):
                logger.info("Conversation threshold reached - generating summary")
                self._summarize_conversation(conversation_state)
            
            # Step 1: Audio Correction
            logger.info("Step 1: Audio Correction")
            correction_result = self.audio_correction.process({
                "raw_text": raw_text
            })
            
            if not correction_result.get("success"):
                return self._error_response("Audio correction failed", correction_result)
            
            corrected_text = correction_result.get("corrected_text", raw_text)
            logger.info(f"Corrected text: {corrected_text}")
            
            # Quick check for conversation reset keywords (fallback)
            reset_keywords = ["start new conversation", "fresh start", "clear history",
                            "reset conversation", "start over", "new conversation",
                            "start fresh", "clear chat", "begin again"]
            message_lower = corrected_text.lower()
            if any(keyword in message_lower for keyword in reset_keywords):
                logger.info("Conversation reset detected via keyword matching")
                return self._handle_conversation_reset(conversation_state)
            
            # Quick check for information query keywords (fallback for web search)
            # This ensures web search is triggered even if LLM intent classification fails
            info_keywords = ["latest", "news", "today", "current", "recent", "update",
                           "what's happening", "what is happening", "tell me about",
                           "information about", "search for", "look up", "find out"]
            needs_web_search = any(keyword in message_lower for keyword in info_keywords)
            
            # Step 2: Intent Classification
            logger.info("Step 2: Intent Classification")
            context = conversation_state.get_conversation_context(max_messages=5)
            intent_result = self.intent_classifier.process({
                "message": corrected_text,
                "context": context
            })
            
            if not intent_result.get("success"):
                return self._error_response("Intent classification failed", intent_result)
            
            primary_intent = intent_result.get("primary_intent", "CASUAL_CHAT")
            logger.info(f"Primary intent: {primary_intent}")
            
            # Step 3: Emotional Detection
            logger.info("Step 3: Emotional Detection")
            emotional_result = self.emotional_detector.process({
                "message": corrected_text,
                "context": context
            })
            
            if not emotional_result.get("success"):
                emotional_result = {
                    "emotion": "neutral",
                    "intensity": 5
                }
            
            # Update conversation state with emotional data
            try:
                emotion_enum = EmotionalState[emotional_result["emotion"].upper()]
                conversation_state.update_emotional_state(
                    emotion_enum,
                    emotional_result.get("intensity", 5)
                )
            except (KeyError, AttributeError):
                pass
            
            logger.info(f"Emotion: {emotional_result.get('emotion')} (intensity: {emotional_result.get('intensity')})")
            
            # Step 4: Handle Conversation Reset if requested
            if primary_intent == "CONVERSATION_RESET":
                logger.info("Step 4: Conversation Reset Requested")
                return self._handle_conversation_reset(conversation_state)
            
            # Step 4.5: Handle Role Change if requested
            if primary_intent == "ROLE_CHANGE":
                self._handle_role_change(corrected_text, conversation_state)
            
            # Step 4.5: Check for health-related information
            if self.health_wellness.check_if_health_related(corrected_text):
                logger.info("Step 4.5: Health Information Detection")
                health_info = self.health_wellness.extract_health_info(corrected_text, context)
                
                if health_info.get("has_health_info"):
                    # Store health information in long-term memory
                    health_data = health_info.get("health_data", {})
                    for key, value in health_data.items():
                        if value:
                            content = f"{key}: {value if isinstance(value, str) else ', '.join(value)}"
                            conversation_state.add_session_memory(
                                "health_profile",
                                content,
                                importance=health_info.get("importance", 9)
                            )
                    logger.info(f"Health information stored in long-term memory")
            
            # Step 5: Handle Memory Storage if needed
            memory_result = None
            if intent_result.get("memory_type") != "none":
                logger.info("Step 5: Memory Classification and Storage")
                memory_result = self.memory_classifier.process({
                    "message": corrected_text,
                    "context": context
                })
                
                if memory_result.get("should_store"):
                    logger.info(f"Memory stored: {memory_result.get('memory_type')}")
            
            # Step 6: Handle Web Search if needed
            web_search_results = None
            original_role = None
            # Trigger web search if LLM detected it OR if keywords suggest it
            if intent_result.get("requires_web_search") or needs_web_search:
                if needs_web_search and not intent_result.get("requires_web_search"):
                    logger.info("Step 6: Web Search (triggered by keyword detection)")
                else:
                    logger.info("Step 6: Web Search")
                
                # Temporarily switch to ASSISTANT mode for information queries
                original_role = conversation_state.get_role()
                if original_role != Role.ASSISTANT:
                    logger.info(f"Temporarily switching from {original_role.value} to ASSISTANT mode for web search")
                    conversation_state.set_role(Role.ASSISTANT)
                
                # Build and optimize search query
                search_query = self._optimize_search_query(corrected_text, intent_result)
                
                logger.info(f"Performing web search for: {search_query}")
                web_search_results = self.conversation_manager.handle_web_search(
                    search_query,
                    context
                )
                logger.info(f"Web search completed: {web_search_results.get('count', 0)} results")
            
            # Step 7: Handle Action Requests
            action_result = None
            action_type = intent_result.get("action_type", "none")
            if action_type != "none":
                logger.info(f"Step 7: Action Request - {action_type}")
                action_params = self._extract_action_parameters(
                    action_type,
                    corrected_text,
                    intent_result.get("entities", {})
                )
                action_result = self.conversation_manager.handle_action_request(
                    action_type,
                    action_params
                )
                
                if action_result.get("success"):
                    conversation_state.add_pending_action(action_type, action_params)
                    logger.info(f"Action {action_type} scheduled")
            
            # Step 8: Check if health/wellness suggestion is needed
            # Only suggest if it's actually about personal health/meals, not research questions
            health_suggestion = None
            is_information_query = primary_intent == "INFORMATION_QUERY"
            is_research_question = any(word in corrected_text.lower() for word in
                                      ["theory", "research", "study", "treating", "treatment", "cure", "disease"])
            
            # Don't mix health suggestions with research/information queries
            if self._needs_health_suggestion(corrected_text, primary_intent) and not (is_information_query and is_research_question):
                logger.info("Step 8a: Generating Health/Wellness Suggestion")
                health_suggestion = self._generate_health_suggestion(
                    corrected_text,
                    conversation_state
                )
            elif is_information_query and is_research_question:
                logger.info("Step 8a: Skipping health suggestion - this is a research/information query")
            
            # Step 9: Generate Conversational Response
            logger.info("Step 9: Generate Response")
            response_result = self.conversation_manager.process({
                "message": corrected_text,
                "conversation_state": conversation_state,
                "intent_data": intent_result,
                "emotional_data": emotional_result,
                "web_search_results": web_search_results,
                "health_suggestion": health_suggestion
            })
            
            if not response_result.get("success"):
                return self._error_response("Response generation failed", response_result)
            
            response_text = response_result.get("response", "")
            
            # If health suggestion was generated, append it
            if health_suggestion and health_suggestion.get("success"):
                suggestion_text = health_suggestion.get("suggestion", "")
                if suggestion_text:
                    response_text += f"\n\n{suggestion_text}"
            
            # If action was taken, append confirmation to response
            if action_result and action_result.get("success"):
                action_message = action_result.get("message", "")
                if action_message:
                    response_text += f"\n\n{action_message}"
            
            # Update conversation history
            conversation_state.add_message("user", corrected_text, {
                "intent": primary_intent,
                "emotion": emotional_result.get("emotion"),
                "corrected": correction_result.get("changes_made", False)
            })
            
            conversation_state.add_message("assistant", response_text, {
                "role": conversation_state.get_role().value,
                "had_web_search": web_search_results is not None,
                "had_action": action_result is not None
            })
            
            # Restore original role if it was temporarily changed for web search
            if original_role and original_role != conversation_state.get_role():
                conversation_state.set_role(original_role)
                logger.info(f"Restored role to {original_role.value}")
            
            logger.info("Message processing complete")
            logger.info("=" * 60)
            
            # Return comprehensive result
            return {
                "success": True,
                "response": response_text,
                "metadata": {
                    "corrected_text": corrected_text,
                    "changes_made": correction_result.get("changes_made", False),
                    "intent": primary_intent,
                    "emotion": emotional_result.get("emotion"),
                    "emotion_intensity": emotional_result.get("intensity"),
                    "role": conversation_state.get_role().value,
                    "memory_stored": memory_result.get("should_store", False) if memory_result else False,
                    "web_search_performed": web_search_results is not None,
                    "action_taken": action_result is not None,
                    "conversation_id": conversation_state.conversation_id
                }
            }
        
        except Exception as e:
            logger.error(f"Orchestrator error: {str(e)}")
            return self._error_response("Orchestration failed", {"error": str(e)})
    
    def _handle_role_change(self, message: str, state: ConversationState) -> None:
        """Detect and handle role change requests"""
        message_lower = message.lower()
        
        if "friend" in message_lower:
            state.set_role(Role.FRIEND)
            logger.info("Role changed to FRIEND")
        elif "advisor" in message_lower or "adviser" in message_lower:
            state.set_role(Role.ADVISOR)
            logger.info("Role changed to ADVISOR")
        elif "assistant" in message_lower:
            state.set_role(Role.ASSISTANT)
            logger.info("Role changed to ASSISTANT")
    
    def _handle_conversation_reset(self, state: ConversationState) -> Dict[str, Any]:
        """
        Handle conversation reset request
        Clears conversation history and summary while preserving user profile
        """
        try:
            # Store user profile before reset
            user_profile = state.get_user_profile()
            onboarding_status = state.is_onboarding_completed()
            current_role = state.get_role()
            
            # Clear conversation history and summary
            state.conversation_history = []
            state.conversation_summary = ""
            state.last_summarized_index = 0
            state.session_memories = []
            state.pending_actions = []
            state.active_context = {}
            
            # Reset emotional state to neutral
            state.update_emotional_state(EmotionalState.NEUTRAL, 5)
            
            # Restore user profile and onboarding status
            state.user_profile = user_profile
            state.onboarding_completed = onboarding_status
            
            logger.info("Conversation reset - history cleared, profile preserved")
            
            # Generate a friendly confirmation response
            response_text = "Sure! Let's start fresh. What's on your mind?"
            
            # Add the reset confirmation to history
            state.add_message("assistant", response_text, {
                "role": current_role.value,
                "conversation_reset": True
            })
            
            return {
                "success": True,
                "response": response_text,
                "metadata": {
                    "conversation_reset": True,
                    "role": current_role.value,
                    "profile_preserved": True
                }
            }
        
        except Exception as e:
            logger.error(f"Error handling conversation reset: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "response": "I had trouble resetting the conversation. Let's just continue chatting!"
            }
    
    def _optimize_search_query(self, user_message: str, intent_data: Dict[str, Any]) -> str:
        """
        Optimize search query for better results
        
        Args:
            user_message: Original user message
            intent_data: Intent classification result with entities
        
        Returns:
            Optimized search query
        """
        try:
            # Extract entities
            entities = intent_data.get("entities", {})
            topics = entities.get("topics", [])
            dates = entities.get("dates", [])
            
            # Start with the user message
            query_parts = []
            
            # If we have specific topics, use them
            if topics:
                query_parts.extend(topics)
            else:
                # Use the full message but clean it up
                query_parts.append(user_message)
            
            # Add date context if present
            if dates:
                # Check if date is already in the query
                query_str = " ".join(query_parts).lower()
                for date in dates:
                    if date.lower() not in query_str:
                        query_parts.append(date)
            
            # Build the query
            optimized_query = " ".join(query_parts)
            
            # Remove common filler words that don't help search
            filler_words = ["i want to know", "tell me", "can you", "please",
                          "i wanted to know", "i'd like to know", "could you"]
            
            query_lower = optimized_query.lower()
            for filler in filler_words:
                if query_lower.startswith(filler):
                    optimized_query = optimized_query[len(filler):].strip()
                    break
            
            # Ensure query is not empty
            if not optimized_query or len(optimized_query.strip()) < 3:
                optimized_query = user_message
            
            logger.info(f"Query optimization: '{user_message}' -> '{optimized_query}'")
            return optimized_query
            
        except Exception as e:
            logger.error(f"Error optimizing search query: {str(e)}")
            return user_message
    
    def _extract_action_parameters(
        self,
        action_type: str,
        message: str,
        entities: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Extract parameters for action requests"""
        # This is a simplified extraction
        # In production, you'd use more sophisticated NLP
        
        params = {}
        
        if action_type == "schedule":
            params = {
                "title": entities.get("topics", ["Meeting"])[0] if entities.get("topics") else "Meeting",
                "datetime_str": entities.get("dates", ["tomorrow"])[0] if entities.get("dates") else "tomorrow",
                "participants": entities.get("names", []),
                "notes": message
            }
        elif action_type == "reminder":
            params = {
                "content": message,
                "datetime_str": entities.get("dates", ["tomorrow"])[0] if entities.get("dates") else "tomorrow",
                "priority": "medium"
            }
        elif action_type == "call":
            params = {
                "contact": entities.get("names", ["Unknown"])[0] if entities.get("names") else "Unknown",
                "purpose": message
            }
        elif action_type == "task":
            params = {
                "description": message,
                "deadline": entities.get("dates", [None])[0] if entities.get("dates") else None,
                "priority": "medium"
            }
        
        return params
    
    def _needs_health_suggestion(self, message: str, intent: str) -> bool:
        """Check if message needs health/wellness suggestion"""
        meal_keywords = ["dinner", "lunch", "breakfast", "eat", "meal", "food", "hungry"]
        exercise_keywords = ["workout", "exercise", "gym", "run", "walk", "fitness"]
        
        message_lower = message.lower()
        
        # Check for meal-related queries
        if any(keyword in message_lower for keyword in meal_keywords):
            return True
        
        # Check for exercise-related queries
        if any(keyword in message_lower for keyword in exercise_keywords):
            return True
        
        return False
    
    def _generate_health_suggestion(
        self,
        message: str,
        state: ConversationState
    ) -> Optional[Dict[str, Any]]:
        """Generate health/wellness suggestion based on message"""
        try:
            # Get health profile from memories
            health_memories = [
                m for m in state.get_session_memories(min_importance=7)
                if m.get("type") == "health_profile"
            ]
            
            health_profile = {}
            for memory in health_memories:
                content = memory.get("content", "")
                if ":" in content:
                    key, value = content.split(":", 1)
                    health_profile[key.strip()] = value.strip()
            
            message_lower = message.lower()
            
            # Determine what type of suggestion is needed
            if any(word in message_lower for word in ["dinner", "lunch", "breakfast", "meal", "eat"]):
                # Meal suggestion
                meal_type = "dinner"
                if "breakfast" in message_lower:
                    meal_type = "breakfast"
                elif "lunch" in message_lower:
                    meal_type = "lunch"
                
                return self.health_wellness.suggest_meal(meal_type, health_profile)
            
            elif any(word in message_lower for word in ["workout", "exercise", "gym"]):
                # Exercise suggestion
                return self.health_wellness.suggest_exercise(health_profile, time_available=30)
            
            return None
        
        except Exception as e:
            logger.error(f"Error generating health suggestion: {str(e)}")
            return None
    
    def _summarize_conversation(self, state: ConversationState) -> None:
        """
        Generate summary of older conversation messages
        Keeps last 10 messages unsummarized
        Also extracts important information for long-term memory
        """
        try:
            # Get messages to summarize (excluding last 10)
            messages_to_summarize = state.get_messages_for_summarization(keep_recent=10)
            
            if not messages_to_summarize:
                logger.info("No messages to summarize")
                return
            
            # Format messages for summarization
            message_text = []
            for msg in messages_to_summarize:
                role_label = "User" if msg["role"] == "user" else "EVA"
                message_text.append(f"{role_label}: {msg['content']}")
            
            conversation_text = "\n".join(message_text)
            
            # Create summarization prompt
            prompt = f"""Summarize the following conversation concisely, preserving key information, topics discussed, decisions made, and important context. Keep it under 200 words.

Conversation:
{conversation_text}

Summary:"""
            
            # Generate summary
            result = self.llm_client.generate(
                prompt=prompt,
                system="You are a helpful assistant that creates concise, informative summaries of conversations.",
                temperature=0.3,
                max_tokens=300
            )
            
            if result.get("success"):
                summary = result.get("response", "").strip()
                
                # Combine with existing summary if any
                if state.conversation_summary:
                    combined_prompt = f"""Combine these two conversation summaries into one coherent summary. Keep it under 250 words.

Previous Summary:
{state.conversation_summary}

New Summary:
{summary}

Combined Summary:"""
                    
                    combined_result = self.llm_client.generate(
                        prompt=combined_prompt,
                        system="You are a helpful assistant that creates concise summaries.",
                        temperature=0.3,
                        max_tokens=400
                    )
                    
                    if combined_result.get("success"):
                        summary = combined_result.get("response", "").strip()
                
                # Extract important information for long-term memory
                self._extract_long_term_memories(conversation_text, state)
                
                # Update state with summary
                state.set_conversation_summary(summary)
                logger.info(f"Conversation summarized: {len(messages_to_summarize)} messages -> {len(summary)} chars")
                
                # Clean up old messages from memory to save space
                context_config = self.config.get_context_config()
                keep_recent = context_config.get('max_history_messages', 10)
                removed_count = state.cleanup_old_messages(keep_recent=keep_recent)
                
                if removed_count > 0:
                    logger.info(f"Cleaned up {removed_count} old messages from memory")
            else:
                logger.error(f"Failed to generate summary: {result.get('error')}")
        
        except Exception as e:
            logger.error(f"Error during summarization: {str(e)}")
    
    def _extract_long_term_memories(self, conversation_text: str, state: ConversationState) -> None:
        """
        Extract important information from conversation for long-term memory
        
        Args:
            conversation_text: Formatted conversation text
            state: Conversation state to store memories
        """
        try:
            # Create extraction prompt
            extraction_prompt = f"""Analyze this conversation and extract important information that should be remembered long-term.
Focus on:
- User preferences and likes/dislikes
- Important facts about the user (name, job, family, etc.)
- Significant events or decisions
- Goals or plans mentioned
- Recurring topics or concerns

Format each memory as: TYPE: content (where TYPE is: PREFERENCE, FACT, EVENT, GOAL, or TOPIC)

Conversation:
{conversation_text}

Important memories to store:"""
            
            result = self.llm_client.generate(
                prompt=extraction_prompt,
                system="You are a memory extraction assistant. Extract only truly important, long-term relevant information.",
                temperature=0.2,
                max_tokens=400
            )
            
            if result.get("success"):
                memories_text = result.get("response", "").strip()
                
                # Parse and store memories
                for line in memories_text.split('\n'):
                    line = line.strip()
                    if ':' in line and line:
                        try:
                            memory_type, content = line.split(':', 1)
                            memory_type = memory_type.strip().lower()
                            content = content.strip()
                            
                            if content and len(content) > 10:  # Only store meaningful memories
                                # Determine importance based on type
                                importance = 7  # Default high importance
                                if memory_type == 'preference':
                                    importance = 8
                                elif memory_type == 'fact':
                                    importance = 9
                                elif memory_type == 'goal':
                                    importance = 8
                                elif memory_type == 'event':
                                    importance = 7
                                elif memory_type == 'topic':
                                    importance = 6
                                
                                state.add_session_memory(memory_type, content, importance)
                                logger.info(f"Stored long-term memory: {memory_type} - {content[:50]}...")
                        except ValueError:
                            continue
                
                logger.info(f"Extracted {len(state.session_memories)} long-term memories")
            else:
                logger.warning("Failed to extract long-term memories")
        
        except Exception as e:
            logger.error(f"Error extracting long-term memories: {str(e)}")
    
    def _error_response(self, error_type: str, details: Dict[str, Any]) -> Dict[str, Any]:
        """Generate error response"""
        logger.error(f"{error_type}: {details}")
        return {
            "success": False,
            "error": error_type,
            "details": details,
            "response": "I'm having trouble processing that right now. Could you try rephrasing?"
        }

# Made with Bob
