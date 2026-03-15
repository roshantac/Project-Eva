"""
Test script for LLM Service
Run with: python test_llm_service.py
"""
import asyncio
import os
from dotenv import load_dotenv
from app.services.llm_service import LLMService

load_dotenv()


async def test_basic_completion():
    print("\n=== Testing Basic Completion ===")
    llm_service = LLMService()
    
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Say hello in one sentence."}
    ]
    
    response = await llm_service.generate_completion(messages)
    print(f"Response: {response}")


async def test_streaming_completion():
    print("\n=== Testing Streaming Completion ===")
    llm_service = LLMService()
    
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Count from 1 to 5."}
    ]
    
    def on_chunk(chunk):
        print(chunk, end='', flush=True)
    
    await llm_service.generate_streaming_completion(messages, on_chunk=on_chunk)
    print()


async def test_generate_response():
    print("\n=== Testing Generate Response ===")
    llm_service = LLMService()
    
    response = await llm_service.generate_response(
        system_prompt="You are a helpful assistant.",
        user_message="What is 2+2?",
        conversation_history=[]
    )
    print(f"Response: {response}")


async def test_provider_info():
    print("\n=== Testing Provider Info ===")
    llm_service = LLMService()
    
    info = llm_service.get_provider_info()
    print(f"Provider Info: {info}")
    
    is_valid = llm_service.validate_api_key()
    print(f"Config Valid: {is_valid}")


async def main():
    print("Starting LLM Service Tests...")
    print(f"Using provider: {os.getenv('LLM_PROVIDER', 'ollama')}")
    
    try:
        await test_provider_info()
        await test_basic_completion()
        # await test_streaming_completion()
        # await test_generate_response()
        
        print("\n✓ All tests completed successfully!")
    except Exception as e:
        print(f"\n✗ Test failed: {e}")


if __name__ == "__main__":
    asyncio.run(main())
