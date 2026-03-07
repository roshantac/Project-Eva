"""
Test script for Audio Services (STT and TTS)
Run with: python test_audio_services.py
"""
import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv
from app.services.stt_service import STTService
from app.services.tts_service import TTSService

load_dotenv()


async def test_stt_provider_info():
    print("\n=== Testing STT Provider Info ===")
    stt_service = STTService()
    
    info = stt_service.get_provider_info()
    print(f"Provider Info: {info}")
    
    is_valid = stt_service.validate_config()
    print(f"Config Valid: {is_valid}")


async def test_tts_provider_info():
    print("\n=== Testing TTS Provider Info ===")
    tts_service = TTSService()
    
    info = tts_service.get_provider_info()
    print(f"Provider Info: {info}")
    
    is_valid = tts_service.validate_config()
    print(f"Config Valid: {is_valid}")


async def test_tts_basic():
    print("\n=== Testing Basic TTS ===")
    tts_service = TTSService()
    
    text = "Hello, this is a test of the text to speech system."
    print(f"Generating speech for: {text}")
    
    audio_buffer = await tts_service.generate_speech(text)
    print(f"Generated audio: {len(audio_buffer)} bytes")
    
    # Save to temp directory for verification
    output_path = Path('temp') / 'test_tts_output.wav'
    output_path.parent.mkdir(exist_ok=True)
    
    with open(output_path, 'wb') as f:
        f.write(audio_buffer)
    
    print(f"Audio saved to: {output_path}")


async def test_tts_emotional():
    print("\n=== Testing Emotional TTS ===")
    tts_service = TTSService()
    
    emotions = ['happy', 'sad', 'excited', 'neutral']
    text = "This is a test of emotional speech."
    
    for emotion in emotions:
        print(f"\nGenerating {emotion} speech...")
        audio_buffer = await tts_service.generate_emotional_speech(text, emotion)
        print(f"Generated {emotion} audio: {len(audio_buffer)} bytes")
        
        # Save to temp directory
        output_path = Path('temp') / f'test_tts_{emotion}.wav'
        with open(output_path, 'wb') as f:
            f.write(audio_buffer)
        print(f"Saved to: {output_path}")


async def test_tts_text_splitting():
    print("\n=== Testing Text Splitting ===")
    tts_service = TTSService()
    
    long_text = "This is a sentence. This is another sentence! And here's a question? " * 100
    chunks = tts_service.split_text_for_tts(long_text, max_length=200)
    
    print(f"Split {len(long_text)} characters into {len(chunks)} chunks:")
    for i, chunk in enumerate(chunks[:3]):
        print(f"Chunk {i+1}: {chunk[:50]}... ({len(chunk)} chars)")


async def test_tts_available_voices():
    print("\n=== Testing Available Voices ===")
    tts_service = TTSService()
    
    voices = tts_service.get_available_voices()
    print(f"Available voices: {voices}")
    
    emotional_mapping = tts_service.get_emotional_voice_mapping()
    print(f"Emotional voice mapping: {emotional_mapping}")


async def test_stt_with_sample():
    print("\n=== Testing STT with Sample Audio ===")
    
    # Check if there's a sample audio file in temp
    sample_path = Path('temp') / 'test_audio_sample.webm'
    
    if not sample_path.exists():
        print(f"No sample audio found at {sample_path}")
        print("Skipping STT test. To test STT, place a sample audio file at the path above.")
        return
    
    stt_service = STTService()
    
    with open(sample_path, 'rb') as f:
        audio_buffer = f.read()
    
    print(f"Transcribing audio ({len(audio_buffer)} bytes)...")
    result = await stt_service.transcribe_audio(audio_buffer)
    
    print(f"Transcription: {result['text']}")
    print(f"Language: {result['language']}")


async def test_tts_chunks():
    print("\n=== Testing TTS Chunks ===")
    tts_service = TTSService()
    
    text_chunks = [
        "This is the first chunk.",
        "Here is the second chunk.",
        "And finally, the third chunk."
    ]
    
    print(f"Generating speech for {len(text_chunks)} chunks...")
    audio_chunks = await tts_service.generate_speech_chunks(text_chunks)
    
    print(f"Generated {len(audio_chunks)} audio chunks")
    for i, chunk in enumerate(audio_chunks):
        print(f"Chunk {i+1}: {len(chunk)} bytes")


async def main():
    print("Starting Audio Services Tests...")
    print(f"Using audio provider: {os.getenv('AUDIO_PROVIDER', 'local')}")
    
    try:
        # Provider info tests
        await test_stt_provider_info()
        await test_tts_provider_info()
        
        # TTS tests
        await test_tts_available_voices()
        await test_tts_text_splitting()
        await test_tts_basic()
        await test_tts_emotional()
        await test_tts_chunks()
        
        # STT tests (requires sample audio)
        await test_stt_with_sample()
        
        print("\n✓ All tests completed successfully!")
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
