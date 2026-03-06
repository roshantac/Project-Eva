# 🎙 EVA

## Fully Open-Source | Self-Hosted | Free Models Only

**Version:** 1.0  
**Deployment Model:** Local / Self-Hosted / Free Cloud Tier Compatible

---

# 1. Executive Summary

This document describes the architecture and implementation plan for a fully open-source, emotion-aware voice conversational agent that:

- Converts speech to text (offline)
- Detects emotions from audio and text
- Maintains conversational memory
- Switches between conversational modes (therapist, coach, professional, etc.)
- Generates responses using a local LLM
- Responds via emotion-aware text-to-speech
- Runs fully locally or on free infrastructure

No paid APIs. No proprietary services. Fully self-hosted.

---

# 2. System Objectives

## Functional Objectives

1. Real-time voice conversation
2. Emotion detection (audio + text)
3. Multi-mode personality engine
4. Context retention
5. Emotion-adaptive speech output

## Non-Functional Objectives

- Offline capable
- Low latency (< 3 seconds)
- Modular architecture
- Scalable to GPU
- Deployable on consumer hardware

---

# 3. High-Level System Architecture

```
User Voice Input
↓
Voice Activity Detection (VAD)
↓
Speech-to-Text (ASR)
↓
Emotion Detection
├── Audio Emotion Model
└── Text Emotion Model
↓
Emotion Fusion Layer
↓
Conversation Orchestrator
↓
Mode Engine (Personality Layer)
↓
Local LLM (Response Generation)
↓
Memory Manager (FAISS)
↓
Text-to-Speech (TTS)
↓
Voice Response to User
```

---

# 4. Technology Stack (Fully Free & Open Source)

| Layer         | Technology                  | Purpose                  |
| ------------- | --------------------------- | ------------------------ |
| VAD           | Silero VAD                  | Detect speech segments   |
| ASR           | Whisper.cpp                 | Offline speech-to-text   |
| Audio Emotion | wav2vec2 Emotion Model      | Emotion from voice       |
| Text Emotion  | DistilRoBERTa Emotion Model | Emotion from text        |
| LLM           | Mistral 7B / LLaMA 3 (GGUF) | Conversational reasoning |
| Runtime       | Ollama or llama.cpp         | Local LLM execution      |
| Memory        | FAISS                       | Vector similarity search |
| Embeddings    | all-MiniLM-L6-v2            | Memory embeddings        |
| TTS           | Piper                       | Offline text-to-speech   |
| Backend       | FastAPI                     | Orchestration API        |
| UI            | Gradio / React              | User interface           |

---

# 5. Component Design

## 5.1 Voice Activity Detection

**Tool:** Silero VAD
**Purpose:** Detect start/end of speech to reduce processing load.

**Output:**

- Speech segments only
- Reduced ASR latency

---

## 5.2 Speech-to-Text

**Tool:** Whisper.cpp

### Model Options

- `base` – lightweight
- `small` – balanced
- `medium` – higher accuracy

**Characteristics:**

- Fully offline
- CPU compatible
- Real-time capable

---

## 5.3 Emotion Detection

### 5.3.1 Audio Emotion Model

Model: wav2vec2-based classifier

Detects:

- Angry
- Happy
- Sad
- Neutral

---

### 5.3.2 Text Emotion Model

Model: DistilRoBERTa emotion classifier

Detects:

- Joy
- Sadness
- Anger
- Fear
- Surprise
- Neutral

---

### 5.3.3 Emotion Fusion Strategy

```python
if audio_confidence > threshold:
    final_emotion = audio_emotion
else:
    final_emotion = text_emotion
```

**Example Output**

```
Primary Emotion: Sad
Intensity: 0.82
Confidence: 0.91
```

---

# 6. Mode Engine (Personality Layer)

The system supports multiple conversational modes.

| Mode         | Behavior               |
| ------------ | ---------------------- |
| Professional | Structured, concise    |
| Friendly     | Casual, warm           |
| Therapist    | Empathetic, validating |
| Coach        | Motivational           |
| Technical    | Analytical, detailed   |
| Playful      | Light humor            |

---

## Mode Switching Logic

Switch occurs based on:

- Explicit user selection
- Detected emotional state
- Context changes

Example:

```python
if emotion == "sad":
    mode = "therapist"
```

---

# 7. Local LLM Architecture

## Recommended Models

### Mistral 7B Instruct (Quantized GGUF)

- 8GB RAM minimum
- Good dialogue performance

### LLaMA 3 8B (GGUF)

- Stronger personality control

---

## Execution Options

1. Ollama (Simplest)
2. llama.cpp (Advanced control)

---

## Prompt Template Structure

```
You are in {MODE} MODE.
User Emotion: {EMOTION} (Intensity: {VALUE})

Respond accordingly.
```

---

# 8. Memory Architecture

## 8.1 Short-Term Memory

- Last 5–10 exchanges
- Stored in RAM

## 8.2 Long-Term Memory

- Stored using FAISS vector database
- Uses sentence embeddings
- Retrieves semantically relevant past interactions

---

# 9. Text-to-Speech System

## Tool: Piper (Offline TTS)

**Advantages:**

- Lightweight
- CPU-friendly
- Fast inference

---

## Emotion-Adaptive Speech Parameters

| Emotion | Speed   | Pitch           |
| ------- | ------- | --------------- |
| Sad     | Slower  | Lower           |
| Happy   | Normal  | Slightly Higher |
| Angry   | Faster  | Higher          |
| Neutral | Default | Default         |

---

# 10. Backend Architecture

## Framework: FastAPI

### Core Modules

- ASR Service
- Emotion Service
- LLM Service
- Mode Manager
- Memory Manager
- TTS Service

### API Endpoints

```
POST /audio
POST /chat
GET /emotion
GET /mode
```

---

# 11. Hardware Requirements

## Minimum (CPU Only)

- 16GB RAM
- 6-core CPU
- SSD storage

## Recommended (GPU)

- 32GB RAM
- RTX 3060 (12GB VRAM)
- NVMe SSD

---

# 12. Performance Expectations

| Stage             | Latency       |
| ----------------- | ------------- |
| ASR               | 300–700ms     |
| Emotion Detection | 100ms         |
| LLM               | 500–1200ms    |
| TTS               | 300ms         |
| Total             | 1.5–3 seconds |

---

# 13. Deployment Options

## Option A: Fully Local Desktop

- Python backend
- Electron or Web UI
- No internet required

## Option B: Free Cloud Tier

- Smaller 3B LLM
- CPU-only inference
- Limited concurrent users

---

# 14. Security & Safety

- Self-harm keyword detection
- Content moderation layer
- No external data transmission
- Encrypted storage for memory

---

# 15. Implementation Roadmap

## Phase 1 (Weeks 1–2)

- Setup ASR + LLM pipeline
- Basic voice conversation

## Phase 2 (Weeks 3–4)

- Add emotion detection
- Add personality modes
- Add TTS

## Phase 3 (Weeks 5–6)

- Add memory (FAISS)
- Optimize latency
- UI improvements

---

# 16. Future Enhancements

- LoRA fine-tuning
- Personalized emotional modeling
- Voice cloning
- Multi-language support
- Mobile app deployment

---

# 17. Conclusion

This architecture enables development of a:

- Fully offline
- Emotion-aware
- Multi-mode conversational agent
- Zero recurring cost system
- Scalable AI platform

Built entirely with open-source technologies and freely available models.
