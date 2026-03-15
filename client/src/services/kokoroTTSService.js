import { KokoroTTS } from 'kokoro-js';

class KokoroTTSService {
  constructor() {
    this.tts = null;
    this.isInitialized = false;
    this.isInitializing = false;
    this.initPromise = null;
    
    this.emotionalVoices = {
      'happy': 'af_bella',
      'excited': 'af_heart',
      'sad': 'af_sky',
      'anxious': 'af_alloy',
      'angry': 'am_onyx',
      'neutral': 'af_heart',
      'grateful': 'af_bella',
      'confused': 'af_sarah'
    };
  }

  async initialize() {
    if (this.isInitialized) {
      return;
    }

    if (this.isInitializing) {
      return this.initPromise;
    }

    this.isInitializing = true;
    this.initPromise = this._doInitialize();
    
    try {
      await this.initPromise;
    } finally {
      this.isInitializing = false;
    }
  }

  async _doInitialize() {
    try {
      console.log('🎤 Initializing Kokoro TTS...');
      
      const model_id = 'onnx-community/Kokoro-82M-v1.0-ONNX';
      
      this.tts = await KokoroTTS.from_pretrained(model_id, {
        dtype: 'q8',
        device: 'wasm',
        progress_callback: (progress) => {
          if (progress.status === 'downloading') {
            console.log(`📥 Downloading ${progress.file}: ${Math.round(progress.progress)}%`);
          } else if (progress.status === 'loading') {
            console.log(`⚙️ Loading ${progress.file}...`);
          }
        }
      });

      this.isInitialized = true;
      console.log('✅ Kokoro TTS initialized successfully');
      console.log('Available voices:', this.tts.list_voices());
    } catch (error) {
      console.error('❌ Failed to initialize Kokoro TTS:', error);
      throw error;
    }
  }

  async generateSpeech(text, emotion = 'neutral') {
    if (!this.isInitialized) {
      await this.initialize();
    }

    try {
      const voice = this.emotionalVoices[emotion] || 'af_heart';
      console.log(`🎵 Generating speech with voice: ${voice}, emotion: ${emotion}`);
      
      const audio = await this.tts.generate(text, { voice });
      
      const wavBuffer = audio.wav;
      
      const audioBlob = new Blob([wavBuffer], { type: 'audio/wav' });
      console.log(`✅ Generated ${audioBlob.size} bytes of audio`);
      
      return audioBlob;
    } catch (error) {
      console.error('❌ Error generating speech with Kokoro:', error);
      throw error;
    }
  }

  getAvailableVoices() {
    if (!this.isInitialized || !this.tts) {
      return Object.values(this.emotionalVoices);
    }
    return this.tts.list_voices();
  }

  getEmotionalVoiceMapping() {
    return this.emotionalVoices;
  }
}

export default new KokoroTTSService();
