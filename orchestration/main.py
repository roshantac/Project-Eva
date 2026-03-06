"""
EVA - Emotional Virtual Assistant
Main entry point for the application
"""

import json
import sys
from typing import Dict, Any, Optional
from agents.orchestrator import AgentOrchestrator
from agents.onboarding_agent import OnboardingAgent
from utils.state_manager import ConversationState
from utils.logger import get_logger
from utils.config_manager import get_config
from utils.ollama_client import OllamaClient
from utils.user_profile_manager import UserProfileManager

logger = get_logger()


class EVA:
    """Main EVA application class"""
    
    def __init__(self, model_name: Optional[str] = None, skip_onboarding: bool = False, user_id: str = "default_user"):
        """
        Initialize EVA
        
        Args:
            model_name: Optional model name to use. If not provided, uses config default.
            skip_onboarding: Skip onboarding even for new users
            user_id: User identifier for profile management
        """
        self.config = get_config()
        self.user_id = user_id
        
        # If model name is provided, update the config
        if model_name:
            self.config.set('model.name', model_name)
            logger.info(f"Using model: {model_name}")
        
        self.orchestrator = AgentOrchestrator()
        self.onboarding_agent = OnboardingAgent()
        self.conversation_state = ConversationState(user_id=user_id)
        self.profile_manager = UserProfileManager(user_id=user_id)
        self.skip_onboarding = skip_onboarding
        self.onboarding_in_progress = False
        self.current_onboarding_index = 0
        
        # Load existing profile if available
        self._load_user_profile()
        
        logger.info("=" * 60)
        logger.info("EVA - Emotional Virtual Assistant Initialized")
        logger.info(f"Model: {self.config.get('model.name')}")
        logger.info(f"User: {user_id}")
        logger.info(f"Onboarding completed: {self.conversation_state.is_onboarding_completed()}")
        logger.info("=" * 60)
    
    def _load_user_profile(self) -> None:
        """Load user profile from disk if it exists"""
        profile_data = self.profile_manager.load_profile()
        if profile_data:
            # Restore profile and onboarding status
            self.conversation_state.set_user_profile(profile_data.get('profile', {}))
            # The set_user_profile method automatically sets onboarding_completed to True
            logger.info("User profile loaded from disk")
        else:
            logger.info("No existing user profile found - new user")
    
    def process_audio_input(self, audio_json: str) -> str:
        """
        Process audio input from audio service
        
        Args:
            audio_json: JSON string with transcribed text
                Expected format: {"transcribed_text": "user message"}
        
        Returns:
            JSON string with response
        """
        try:
            # Parse input JSON
            input_data = json.loads(audio_json)
            raw_text = input_data.get("transcribed_text", "")
            
            if not raw_text:
                return json.dumps({
                    "success": False,
                    "error": "No transcribed text provided",
                    "response": "I didn't catch that. Could you say that again?"
                })
            
            logger.info(f"Received audio input: {raw_text}")
            
            # Process through orchestrator
            result = self.orchestrator.process_message(
                raw_text,
                self.conversation_state
            )
            
            # Format response
            response = {
                "success": result.get("success", False),
                "response": result.get("response", ""),
                "metadata": result.get("metadata", {}),
                "conversation_id": self.conversation_state.conversation_id,
                "current_role": self.conversation_state.get_role().value,
                "emotional_state": self.conversation_state.get_emotional_state()
            }
            
            return json.dumps(response, indent=2)
        
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON input: {str(e)}")
            return json.dumps({
                "success": False,
                "error": "Invalid JSON format",
                "response": "I'm having trouble understanding the input format."
            })
        
        except Exception as e:
            logger.error(f"Error processing audio input: {str(e)}")
            return json.dumps({
                "success": False,
                "error": str(e),
                "response": "I encountered an error. Please try again."
            })
    
    def process_text_input(self, text: str) -> Dict[str, Any]:
        """
        Process direct text input (for testing without audio service)
        
        Args:
            text: User message text
        
        Returns:
            Dict with response
        """
        try:
            logger.info(f"Received text input: {text}")
            
            # Check if onboarding is needed
            if not self.skip_onboarding and not self.conversation_state.is_onboarding_completed() and not self.onboarding_in_progress:
                # Start onboarding
                self.onboarding_in_progress = True
                onboarding_start = self.onboarding_agent.start_onboarding()
                
                # Get first question
                first_question = self.onboarding_agent.get_next_question(0)
                
                response = f"{onboarding_start['message']}\n\n{first_question['question']}"
                
                return {
                    "success": True,
                    "response": response,
                    "is_onboarding": True,
                    "onboarding_progress": first_question.get('progress', '1/10')
                }
            
            # Handle onboarding responses
            if self.onboarding_in_progress:
                return self._handle_onboarding_response(text)
            
            # Normal message processing
            result = self.orchestrator.process_message(
                text,
                self.conversation_state
            )
            
            return {
                "success": result.get("success", False),
                "response": result.get("response", ""),
                "metadata": result.get("metadata", {}),
                "conversation_id": self.conversation_state.conversation_id,
                "current_role": self.conversation_state.get_role().value,
                "emotional_state": self.conversation_state.get_emotional_state()
            }
        
        except Exception as e:
            logger.error(f"Error processing text input: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "response": "I encountered an error. Please try again."
            }
    
    def _handle_onboarding_response(self, text: str) -> Dict[str, Any]:
        """Handle user response during onboarding"""
        try:
            # Get current question
            current_question = self.onboarding_agent.get_next_question(self.current_onboarding_index)
            question_id = current_question.get('question_id', '')
            
            if not question_id:
                return {
                    "success": False,
                    "error": "Invalid onboarding state"
                }
            
            # Process the answer
            answer_result = self.onboarding_agent.process_answer(question_id, text)
            
            if answer_result.get("success") and not answer_result.get("skipped"):
                # Store in profile
                profile_data = answer_result.get("profile_data", {})
                self.conversation_state.add_session_memory(
                    f"profile_{profile_data['category']}",
                    f"{question_id}: {profile_data['answer']}",
                    importance=profile_data['importance']
                )
            
            # Move to next question
            self.current_onboarding_index += 1
            next_question = self.onboarding_agent.get_next_question(self.current_onboarding_index)
            
            if next_question.get("completed"):
                # Onboarding complete
                self.onboarding_in_progress = False
                profile = self._build_profile_from_memories()
                self.conversation_state.set_user_profile(profile)
                
                # Save profile to disk
                self._save_user_profile(profile)
                
                completion = self.onboarding_agent.complete_onboarding(
                    self.conversation_state.get_user_profile()
                )
                
                return {
                    "success": True,
                    "response": f"{answer_result.get('acknowledgment')}\n\n{completion['message']}",
                    "is_onboarding": False,
                    "onboarding_completed": True
                }
            else:
                # Continue onboarding
                response = f"{answer_result.get('acknowledgment')}\n\n{next_question['question']}"
                
                return {
                    "success": True,
                    "response": response,
                    "is_onboarding": True,
                    "onboarding_progress": next_question.get('progress', '')
                }
        
        except Exception as e:
            logger.error(f"Error handling onboarding response: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "response": "Sorry, something went wrong. Let's continue."
            }
    
    def _build_profile_from_memories(self) -> Dict[str, Any]:
        """Build user profile from onboarding memories"""
        profile = {}
        memories = self.conversation_state.get_session_memories(min_importance=7)
        
        for memory in memories:
            if memory.get("type", "").startswith("profile_"):
                content = memory.get("content", "")
                if ":" in content:
                    key, value = content.split(":", 1)
                    profile[key.strip()] = value.strip()
        
        return profile
    
    def _save_user_profile(self, profile: Dict[str, Any]) -> None:
        """Save user profile to disk"""
        try:
            profile_data = {
                'profile': profile,
                'onboarding_completed': True,
                'user_id': self.user_id
            }
            success = self.profile_manager.save_profile(profile_data)
            if success:
                logger.info("User profile saved successfully")
            else:
                logger.error("Failed to save user profile")
        except Exception as e:
            logger.error(f"Error saving user profile: {str(e)}")
    
    def get_conversation_state(self) -> Dict[str, Any]:
        """Get current conversation state"""
        return self.conversation_state.to_dict()
    
    def reset_conversation(self) -> None:
        """Reset conversation state"""
        self.conversation_state = ConversationState()
        logger.info("Conversation state reset")


def list_available_models() -> None:
    """List all available Ollama models"""
    config = get_config()
    client = OllamaClient(
        base_url=config.get('model.base_url'),
        model=config.get('model.name')
    )
    
    print("\n" + "=" * 60)
    print("Available Ollama Models")
    print("=" * 60)
    
    if not client.check_connection():
        print("\n❌ Cannot connect to Ollama. Please ensure Ollama is running.")
        print("   Start Ollama with: ollama serve")
        return
    
    models = client.list_models()
    
    if not models:
        print("\n❌ No models found. Please pull a model first.")
        print("   Example: ollama pull gemma:2b")
        return
    
    print(f"\nFound {len(models)} model(s):\n")
    
    for i, model in enumerate(models, 1):
        name = model.get("name", "Unknown")
        size = model.get("size", 0)
        size_gb = size / (1024**3) if size > 0 else 0
        modified = model.get("modified_at", "Unknown")
        
        print(f"{i}. {name}")
        print(f"   Size: {size_gb:.2f} GB")
        print(f"   Modified: {modified[:10] if len(modified) > 10 else modified}")
        print()
    
    print("=" * 60)


def select_model_interactive() -> Optional[str]:
    """
    Interactive model selection
    
    Returns:
        Selected model name or None to use default
    """
    config = get_config()
    client = OllamaClient(
        base_url=config.get('model.base_url'),
        model=config.get('model.name')
    )
    
    if not client.check_connection():
        print("\n❌ Cannot connect to Ollama. Using default model from config.")
        return None
    
    models = client.list_models()
    
    if not models:
        print("\n❌ No models found. Using default model from config.")
        return None
    
    print("\n" + "=" * 60)
    print("Select a Model")
    print("=" * 60)
    print(f"\nAvailable models:\n")
    
    for i, model in enumerate(models, 1):
        name = model.get("name", "Unknown")
        size = model.get("size", 0)
        size_gb = size / (1024**3) if size > 0 else 0
        
        # Highlight default model
        default_marker = " (default)" if name == config.get('model.name') else ""
        print(f"{i}. {name}{default_marker} - {size_gb:.2f} GB")
    
    print(f"\n0. Use default ({config.get('model.name')})")
    print("\n" + "=" * 60)
    
    while True:
        try:
            choice = input("\nEnter model number (or 0 for default): ").strip()
            
            if choice == "0" or choice == "":
                return None
            
            idx = int(choice) - 1
            if 0 <= idx < len(models):
                selected_model = models[idx].get("name", "")
                print(f"\n✓ Selected model: {selected_model}")
                return selected_model
            else:
                print(f"❌ Invalid choice. Please enter a number between 0 and {len(models)}")
        
        except ValueError:
            print("❌ Invalid input. Please enter a number.")
        except KeyboardInterrupt:
            print("\n\nUsing default model.")
            return None


def interactive_mode(model_name: Optional[str] = None):
    """
    Run EVA in interactive mode for testing
    
    Args:
        model_name: Optional model name to use
    """
    print("\n" + "=" * 60)
    print("EVA - Emotional Virtual Assistant")
    print("Interactive Mode")
    print("=" * 60)
    print("\nCommands:")
    print("  - Type your message to chat with EVA")
    print("  - 'models' to list available models")
    print("  - 'switch <model>' to switch to a different model")
    print("  - 'role friend/advisor/assistant' to change EVA's role")
    print("  - 'state' to see conversation state")
    print("  - 'reset' to reset conversation")
    print("  - 'quit' or 'exit' to quit")
    print("\nNatural Commands:")
    print("  - Say 'start new conversation' or 'fresh start' to clear history")
    print("  - EVA will remember your profile even after reset")
    print("\n" + "=" * 60 + "\n")
    
    eva = EVA(model_name=model_name)
    
    while True:
        try:
            user_input = input("\nYou: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ['quit', 'exit']:
                print("\nGoodbye! 👋")
                break
            
            if user_input.lower() == 'reset':
                eva.reset_conversation()
                print("\n✓ Conversation reset")
                continue
            
            if user_input.lower() == 'state':
                state = eva.get_conversation_state()
                print(f"\nConversation ID: {state['conversation_id']}")
                print(f"Current Role: {state['current_role']}")
                print(f"Current Model: {eva.config.get('model.name')}")
                print(f"Emotional State: {state['emotional_state']['current']} (Intensity: {state['emotional_state']['intensity']})")
                print(f"Messages: {len(state['conversation_history'])}")
                continue
            
            if user_input.lower() == 'models':
                list_available_models()
                continue
            
            if user_input.lower().startswith('switch '):
                new_model = user_input[7:].strip()
                if new_model:
                    eva.config.set('model.name', new_model)
                    # Reinitialize orchestrator with new model
                    eva.orchestrator = AgentOrchestrator()
                    print(f"\n✓ Switched to model: {new_model}")
                else:
                    print("\n❌ Please specify a model name. Example: switch gemma:2b")
                continue
            
            # Process message
            result = eva.process_text_input(user_input)
            
            if result.get("success"):
                # Get role for display (may not be present during onboarding)
                role = result.get('current_role', 'EVA')
                print(f"\nEVA ({role}): {result['response']}")
                
                # Show onboarding progress if applicable
                if result.get("is_onboarding"):
                    progress = result.get("onboarding_progress", "")
                    if progress:
                        print(f"  [Onboarding Progress: {progress}]")
                
                # Show metadata if available
                metadata = result.get("metadata", {})
                if metadata.get("changes_made"):
                    print(f"  [Corrected from: {metadata.get('corrected_text')}]")
                if metadata.get("emotion"):
                    print(f"  [Detected emotion: {metadata['emotion']} (intensity: {metadata.get('emotion_intensity', 5)})]")
            else:
                print(f"\nError: {result.get('error', 'Unknown error')}")
        
        except KeyboardInterrupt:
            print("\n\nGoodbye! 👋")
            break
        except Exception as e:
            print(f"\nError: {str(e)}")


def main():
    """Main entry point"""
    if len(sys.argv) > 1:
        if sys.argv[1] == "--interactive" or sys.argv[1] == "-i":
            # Check if model selection flag is present
            if "--select-model" in sys.argv or "-s" in sys.argv:
                model_name = select_model_interactive()
                interactive_mode(model_name=model_name)
            elif "--model" in sys.argv or "-m" in sys.argv:
                # Direct model specification
                try:
                    model_idx = sys.argv.index("--model") if "--model" in sys.argv else sys.argv.index("-m")
                    if model_idx + 1 < len(sys.argv):
                        model_name = sys.argv[model_idx + 1]
                        interactive_mode(model_name=model_name)
                    else:
                        print("❌ Please specify a model name after --model/-m")
                        sys.exit(1)
                except (ValueError, IndexError):
                    print("❌ Error parsing model argument")
                    sys.exit(1)
            else:
                interactive_mode()
        elif sys.argv[1] == "--list-models" or sys.argv[1] == "-l":
            list_available_models()
        elif sys.argv[1] == "--help" or sys.argv[1] == "-h":
            print("EVA - Emotional Virtual Assistant")
            print("\nUsage:")
            print("  python main.py --interactive              Run in interactive mode")
            print("  python main.py -i --select-model          Run with model selection")
            print("  python main.py -i --model <name>          Run with specific model")
            print("  python main.py --list-models              List available models")
            print("  python main.py --help                     Show this help message")
            print("\nExamples:")
            print("  python main.py -i                         # Use default model")
            print("  python main.py -i -s                      # Select model interactively")
            print("  python main.py -i -m gemma:2b             # Use gemma:2b model")
            print("  python main.py -l                         # List all models")
            print("\nFor integration with audio service:")
            print("  from main import EVA")
            print("  eva = EVA(model_name='gemma:2b')  # Optional model parameter")
            print("  response_json = eva.process_audio_input(audio_json)")
        else:
            print(f"Unknown argument: {sys.argv[1]}")
            print("Use --help for usage information")
    else:
        print("EVA - Emotional Virtual Assistant")
        print("\nUse --interactive to run in interactive mode")
        print("Use --list-models to see available models")
        print("Use --help for more information")


if __name__ == "__main__":
    main()

# Made with Bob
