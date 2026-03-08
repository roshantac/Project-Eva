---
name: emotional-context-tracker
description: Detect emotional tone, stress, energy levels, and mood shifts from conversation to adapt how the assistant responds. Runs silently on every turn.
priority: HIGH
---

## What This Skill Does

Detect stress, energy levels, emotional tone, life context, and mood shifts over time. Build an evolving emotional profile that informs *how* the assistant responds, not just *what* it responds with.

---

## Trigger Conditions

- New conversation starts (baseline mood assessment)
- User's tone, vocabulary, or pacing shifts noticeably
- Stress/excitement/fatigue keywords appear (explicit or implicit)
- Repeated tasks suggest anxiety or indecision
- Time-of-day context is relevant

---

## What to Detect

**Emotional Tone**: Enthusiastic language, clipped responses, hedging ("I guess", "I don't know"), humor, profanity, all-caps.

**Stress Indicators**: Volume spike of requests, contradictions/mind-changing, pressure words ("urgent", "ASAP", "deadline", "my boss"), unnecessary apologies.

**Energy & Fatigue**: Long detailed messages = high energy. Short incomplete sentences = low energy or rushing. Late-night messages = likely fatigued.

**Life Context**: Mentions of people (family, boss, colleagues), upcoming events (interview, presentation, trip), recurring frustrations.

**Confidence Level**: Assertive phrasing = user knows what they want. Vague/open-ended = user needs guidance. Over-explaining = user feels unheard.

---

## Response Adaptation Rules

| Detected State | Adapt By |
|---|---|
| High stress | Be calm, concise, ruthlessly prioritize. Don't add noise. |
| Fatigued | Reduce cognitive load. Summarize. Avoid questions. |
| Excited | Match energy. Explore and expand. |
| Frustrated | Acknowledge first. Don't immediately problem-solve. |
| Anxious | Give concrete options. Reduce ambiguity. Reassure. |
| Confident | Be direct and efficient. Skip hand-holding. |
| Sad/grieving | Drop productivity mode. Be human and present. |

---

## Memory Schema

```json
{
  "emotional_profile": {
    "baseline_tone": "calm | upbeat | anxious | reserved",
    "current_mood": "stressed | neutral | excited | fatigued | frustrated",
    "stress_level": "1-10",
    "energy_level": "1-10",
    "confidence_level": "high | medium | low",
    "active_life_events": [],
    "recurring_frustrations": [],
    "preferred_response_style": "direct | nurturing | exploratory | structured",
    "last_updated": "ISO timestamp"
  }
}
```

---

## Critical Operating Rules

- Feed a shared context object that all other skills can read
- Never explicitly mention the emotional read to the user — operate silently
- Never say "I can tell you're stressed" — *act* on it instead
- Recalibrate every 5–10 turns or on significant tone shifts
- If confidence in emotional read is below 50%, default to neutral adaptive tone
