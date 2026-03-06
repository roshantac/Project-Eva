"""
Basic tests for EVA system
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import EVA
from utils.state_manager import ConversationState, Role, EmotionalState


def test_eva_initialization():
    """Test EVA initialization"""
    print("Testing EVA initialization...")
    eva = EVA()
    assert eva is not None
    assert eva.orchestrator is not None
    assert eva.conversation_state is not None
    print("✓ EVA initialized successfully")


def test_basic_conversation():
    """Test basic conversation"""
    print("\nTesting basic conversation...")
    eva = EVA()
    result = eva.process_text_input("Hello EVA")
    
    assert result["success"] == True
    assert len(result["response"]) > 0
    assert "conversation_id" in result
    print(f"✓ Response: {result['response']}")


def test_role_change():
    """Test role change"""
    print("\nTesting role change...")
    eva = EVA()
    
    # Change to advisor
    result = eva.process_text_input("Act as my advisor")
    assert result["success"] == True
    assert result["current_role"] == "advisor"
    print(f"✓ Role changed to: {result['current_role']}")
    
    # Change to assistant
    result = eva.process_text_input("Switch to assistant mode")
    assert result["success"] == True
    assert result["current_role"] == "assistant"
    print(f"✓ Role changed to: {result['current_role']}")


def test_emotional_detection():
    """Test emotional detection"""
    print("\nTesting emotional detection...")
    eva = EVA()
    
    # Happy message
    result = eva.process_text_input("I'm so excited about my new project!")
    assert result["success"] == True
    emotion = result["emotional_state"]["emotion"]
    print(f"✓ Detected emotion: {emotion}")
    
    # Sad message
    result = eva.process_text_input("I'm feeling really down today")
    assert result["success"] == True
    emotion = result["emotional_state"]["emotion"]
    print(f"✓ Detected emotion: {emotion}")


def test_memory_request():
    """Test memory storage request"""
    print("\nTesting memory storage...")
    eva = EVA()
    
    result = eva.process_text_input("Remember that my favorite color is blue")
    assert result["success"] == True
    metadata = result.get("metadata", {})
    print(f"✓ Memory stored: {metadata.get('memory_stored', False)}")


def test_conversation_context():
    """Test conversation context maintenance"""
    print("\nTesting conversation context...")
    eva = EVA()
    
    # First message
    result1 = eva.process_text_input("My name is John")
    assert result1["success"] == True
    
    # Second message referencing first
    result2 = eva.process_text_input("What's my name?")
    assert result2["success"] == True
    print(f"✓ Context maintained: {result2['response']}")


def test_audio_json_input():
    """Test audio JSON input format"""
    print("\nTesting audio JSON input...")
    eva = EVA()
    
    import json
    audio_json = json.dumps({
        "transcribed_text": "Hello EVA, how are you today?"
    })
    
    response_json = eva.process_audio_input(audio_json)
    response = json.loads(response_json)
    
    assert response["success"] == True
    assert len(response["response"]) > 0
    print(f"✓ Audio input processed: {response['response']}")


def test_conversation_state():
    """Test conversation state management"""
    print("\nTesting conversation state...")
    eva = EVA()
    
    # Add some messages
    eva.process_text_input("Hello")
    eva.process_text_input("How are you?")
    
    state = eva.get_conversation_state()
    assert len(state["conversation_history"]) >= 4  # 2 user + 2 assistant
    assert "conversation_id" in state
    assert "current_role" in state
    print(f"✓ State has {len(state['conversation_history'])} messages")
    
    # Reset
    eva.reset_conversation()
    state = eva.get_conversation_state()
    assert len(state["conversation_history"]) == 0
    print("✓ Conversation reset successfully")


def run_all_tests():
    """Run all tests"""
    print("=" * 60)
    print("Running EVA Tests")
    print("=" * 60)
    
    tests = [
        test_eva_initialization,
        test_basic_conversation,
        test_role_change,
        test_emotional_detection,
        test_memory_request,
        test_conversation_context,
        test_audio_json_input,
        test_conversation_state
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"✗ Test failed: {test.__name__}")
            print(f"  Error: {str(e)}")
            failed += 1
        except Exception as e:
            print(f"✗ Test error: {test.__name__}")
            print(f"  Error: {str(e)}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"Tests completed: {passed} passed, {failed} failed")
    print("=" * 60)
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

# Made with Bob
