# Personal AI Conversation Bot — Full Implementation Plan

> **Stack:** OpenClaw / ZeroClaw · Telegram · Neo4j Graph Memory (Mem0-style) · Node.js / TypeScript  
> **Document version:** 2026-02-17

---

## Table of Contents

1. [Executive Overview](#1-executive-overview)
2. [Architecture Philosophy: OpenClaw vs ZeroClaw](#2-architecture-philosophy-openclaw-vs-zeroclaw)
3. [High-Level System Architecture](#3-high-level-system-architecture)
4. [Component Deep-Dive](#4-component-deep-dive)
   - 4.1 [Gateway (Control Plane)](#41-gateway-control-plane)
   - 4.2 [Heartbeat Engine](#42-heartbeat-engine)
   - 4.3 [Cron Job Scheduler](#43-cron-job-scheduler)
   - 4.4 [Webhook Invoke Surface](#44-webhook-invoke-surface)
   - 4.5 [Telegram Channel Adapter](#45-telegram-channel-adapter)
5. [Memory System — Mem0 + Neo4j Graph](#5-memory-system--mem0--neo4j-graph)
   - 5.1 [Memory Architecture](#51-memory-architecture)
   - 5.2 [Graph Schema (Neo4j)](#52-graph-schema-neo4j)
   - 5.3 [Memory Tools for the Agent](#53-memory-tools-for-the-agent)
6. [Skills System](#6-skills-system)
   - 6.1 [Skill Structure (SKILL.md Standard)](#61-skill-structure-skillmd-standard)
   - 6.2 [Core Built-in Skills](#62-core-built-in-skills)
7. [Templates](#7-templates)
   - 7.1 [Onboarding Template](#71-onboarding-template)
   - 7.2 [Daily Check-in Template](#72-daily-check-in-template)
   - 7.3 [HEARTBEAT.md Template](#73-heartbeatmd-template)
8. [Agent Tool Catalogue](#8-agent-tool-catalogue)
9. [Proactive Intelligence Loop](#9-proactive-intelligence-loop)
10. [User Behaviour Pattern Engine](#10-user-behaviour-pattern-engine)
11. [Internet Search Integration](#11-internet-search-integration)
12. [Data Flow Diagrams](#12-data-flow-diagrams)
13. [Project File Structure](#13-project-file-structure)
14. [Configuration Reference](#14-configuration-reference)
15. [Implementation Roadmap (Phases)](#15-implementation-roadmap-phases)
16. [Security & Privacy Considerations](#16-security--privacy-considerations)
17. [Deployment Guide](#17-deployment-guide)

---

## 1. Executive Overview

This document describes a production-grade **personal AI conversation bot** built on the OpenClaw / ZeroClaw agentic framework. The bot runs persistently, connects to users over **Telegram**, and evolves as a proactive life assistant that:

- **Onboards** new users via a structured question template covering life context, goals, routines, preferences, and relationships.
- **Remembers** everything across sessions using a **Mem0-inspired hybrid memory store** backed by Neo4j for graph relationships, a vector database for semantic recall, and a key-value store for fast fact lookup.
- **Acts autonomously** via a 30-minute heartbeat cycle that lets the agent check in, surface relevant reminders, notice patterns, and proactively message users when warranted.
- **Schedules itself** by writing its own cron jobs once it identifies the user's behavioural patterns — for example, scheduling a morning briefing at the exact time the user typically wakes up.
- **Searches the internet** daily and blends external news/information with the user's personal context to deliver curated, relevant updates.
- **Extracts structured knowledge** from every conversation and stores it as nodes and relationships in a Neo4j graph — mapping the user's world: relationships, habits, goals, routines, emotions, and events.

---

## 2. Architecture Philosophy: OpenClaw vs ZeroClaw

### OpenClaw
OpenClaw (formerly Clawdbot / Moltbot) is an open-source TypeScript/Node.js CLI process and Gateway server. It uses a **Lane Queue** system that defaults to serial execution within each session lane, preventing race conditions while allowing explicit parallelism for idempotent tasks (e.g., heartbeats). Its key capabilities relevant here:

- A **Gateway** WebSocket control plane (default `127.0.0.1:18789`) that is the single source of truth for sessions, presence, routing, cron, and webhooks.
- A **heartbeat** loop that fires on a configurable interval (default 30 minutes), reads `HEARTBEAT.md` from the workspace, and runs a full agent turn in an isolated session so it never pollutes main conversation history.
- **Cron jobs** stored at `~/.openclaw/cron/jobs.json`, supporting both one-shot `at:` triggers and recurring `cron:` expressions (standard 5-field POSIX). The agent itself can write new cron jobs via tool calls.
- **Webhooks** as external trigger endpoints — any HTTP POST to the webhook surface fires an agent turn in the configured session.
- A **Skills** system using the `AgentSkills` / `SKILL.md` standard: each skill is a folder with a `SKILL.md` config file plus any supporting scripts.
- **Dual memory**: JSONL audit transcripts (immutable) + Markdown memory files (writable knowledge).
- **Hybrid search**: vector similarity (semantic) + SQLite FTS5 keyword matching for precision recall.

### ZeroClaw
ZeroClaw is a Rust fork of OpenClaw, built for production deployments on constrained infrastructure. It uses the same conceptual architecture but with:

- A **trait-driven** pluggable architecture: provider, channel, memory, tool, and tunnel are all swappable Rust traits with no vendor lock-in.
- A **Gateway on port 8080** (configurable) with the same WebSocket control plane concept.
- Faster startup and lower memory footprint ideal for long-running server deployments (VPS/cloud).
- `config.toml` format instead of JSON.
- Security-first defaults: filesystem scoping, allowlists, encrypted secrets, sandbox controls, and gateway-style access patterns.

### Our Choice for This Implementation
We use **OpenClaw as the runtime** (TypeScript/Node.js ecosystem, richest community skills library, native Telegram grammY adapter) with **ZeroClaw-inspired configuration discipline** (immutable audit logs, trait-like abstraction for memory providers, strict sandbox controls). The memory layer is implemented as a **custom OpenClaw plugin** wrapping `mem0` with Neo4j graph storage.

---

## 3. High-Level System Architecture

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                           TELEGRAM (User-Facing)                             │
│              Messages ↕  |  Photos ↕  |  Voice ↕  |  Commands ↕            │
└────────────────────────────────┬─────────────────────────────────────────────┘
                                 │ grammY WebSocket / Polling
                                 ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                        OPENCLAW GATEWAY (Control Plane)                      │
│   ws://127.0.0.1:18789                                                       │
│                                                                              │
│   ┌──────────┐  ┌──────────┐  ┌──────────────┐  ┌────────────────────────┐ │
│   │ Sessions │  │ Presence │  │  Cron Sched. │  │  Webhook Surface       │ │
│   │ Manager  │  │ Tracker  │  │  (jobs.json) │  │  POST /webhook/:key    │ │
│   └──────────┘  └──────────┘  └──────────────┘  └────────────────────────┘ │
│                                                                              │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                    HEARTBEAT ENGINE (every 30m)                     │   │
│   │   Reads HEARTBEAT.md → Runs agent turn in isolated cron: session   │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────┬────────────────────────────────────────────────┘
                              │ RPC / WebSocket events
                              ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                           AGENT RUNNER (Lane Queue)                          │
│                                                                              │
│   ┌──────────────────────────────────────────────────────────────────────┐  │
│   │  SOUL (System Prompt) + Context Assembly                             │  │
│   │  ┌─────────────┐  ┌──────────────────┐  ┌────────────────────────┐  │  │
│   │  │ User Profile│  │ Memory Recall     │  │ Skill Instructions     │  │  │
│   │  │ (from Neo4j)│  │ (vector + graph)  │  │ (active SKILL.md files)│  │  │
│   │  └─────────────┘  └──────────────────┘  └────────────────────────┘  │  │
│   └──────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│   ┌──────────────────────────────────────────────────────────────────────┐  │
│   │  MODEL RESOLVER  (primary: claude-sonnet-4 | fallback: haiku)       │  │
│   └──────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│   ┌──────────────────────────────────────────────────────────────────────┐  │
│   │  TOOL EXECUTION SANDBOX                                              │  │
│   │  memory_recall | memory_write | web_search | cron_write | cron_list │  │
│   │  send_telegram | graph_query | extract_entities | pattern_analyze   │  │
│   └──────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────┬────────────────────────────────────────────────┘
                              │
          ┌───────────────────┼──────────────────────┐
          ▼                   ▼                       ▼
┌──────────────────┐  ┌──────────────────┐  ┌─────────────────────┐
│  NEO4J GRAPH DB  │  │  VECTOR DB       │  │  SQLITE (FTS5)      │
│  (Relationships, │  │  (Qdrant/Chroma) │  │  (Keyword search,   │
│  Entities, Life  │  │  (Semantic mem.) │  │   audit log, cron)  │
│  Events, Habits) │  │                  │  │                     │
└──────────────────┘  └──────────────────┘  └─────────────────────┘
```

---

## 4. Component Deep-Dive

### 4.1 Gateway (Control Plane)

The Gateway is the single brain of the system. It owns session state, routes inbound messages, fires heartbeats, manages cron schedules, and exposes the webhook surface. It runs as a persistent daemon process separate from the agent logic.

**Key responsibilities:**

- **Session isolation:** Each user gets their own session lane (`user:<telegramUserId>`). Heartbeats run in `cron:<jobId>` lanes so they never contaminate conversation history.
- **Access control:** Pairing token verification. All non-loopback bindings require token or password auth.
- **Health monitoring:** Exposes a `/health` endpoint polled by the heartbeat system. Logs all session activity to the audit JSONL.
- **Message routing:** Inbound Telegram messages → access check → session resolve → agent runner dispatch → response back through Telegram adapter.

**Config snippet (`openclaw.json`):**

```json
{
  "gateway": {
    "host": "127.0.0.1",
    "port": 18789,
    "auth": { "mode": "token", "token": "${GATEWAY_TOKEN}" }
  },
  "agents": {
    "defaults": {
      "model": {
        "primary": "anthropic/claude-sonnet-4-5-20250929",
        "fallbacks": ["anthropic/claude-haiku-4-5-20251001"]
      },
      "heartbeat": {
        "every": "30m",
        "model": "anthropic/claude-haiku-4-5-20251001",
        "target": "last",
        "includeReasoning": false
      }
    }
  },
  "cron": {
    "enabled": true,
    "store": "~/.openclaw/cron/jobs.json",
    "maxConcurrentRuns": 1
  },
  "channels": {
    "telegram": {
      "enabled": true,
      "token": "${TELEGRAM_BOT_TOKEN}"
    }
  }
}
```

---

### 4.2 Heartbeat Engine

The heartbeat is the agent's autonomous pulse. Every 30 minutes, the Gateway fires an isolated agent turn using the `HEARTBEAT.md` file as its operational checklist. This is distinct from cron jobs: the heartbeat is **always-on interval sensing**, while cron jobs are **precise scheduled tasks** the agent writes itself.

**Heartbeat mechanics:**
1. Gateway timer fires at the configured interval.
2. A `system-event` is enqueued in the `cron:heartbeat` session lane.
3. The agent runner reads `HEARTBEAT.md` from the workspace, assembles context (recent conversation summary, Neo4j user state, pending reminders), and runs a full LLM turn.
4. If the agent decides nothing warrants user notification, it responds with `HEARTBEAT_OK` — the Gateway strips this and sends nothing to Telegram (silent run).
5. If there is something to surface (a reminder, a pattern observation, a proactive check-in), the agent sends a message directly to the user's last-active Telegram session.

**HEARTBEAT.md (loaded by the agent on every heartbeat):**

```markdown
# HEARTBEAT INSTRUCTIONS

You are running a proactive check on behalf of the user. Do the following silently unless action is required:

## Checks (run in order)
1. **Pending Reminders** — Query memory for any reminders due within the next 2 hours. If found, draft and send a message.
2. **Unfinished Threads** — Check if there's an open conversation topic from the last session that deserves a follow-up.
3. **Daily Briefing Trigger** — If it is between 06:00–08:00 in the user's local timezone AND no briefing has been sent today, compose and send the morning brief.
4. **Emotional Check-in** — If the user has not messaged in > 48 hours, send a gentle, contextual check-in message (not generic).
5. **Pattern Alert** — If the user behaviour pattern engine has detected a new significant pattern (confidence > 0.85), surface it as an insight.
6. **Internet Freshness** — If a tracked topic has new significant developments (checked via web_search), compose a brief update.

## Response Rules
- If nothing requires user attention: respond only with `HEARTBEAT_OK`
- If something requires attention: send only what is needed — be brief, warm, and contextual
- Never send more than 2 unprompted messages per heartbeat cycle
- Log all decisions (act or skip) to the heartbeat audit log
```

---

### 4.3 Cron Job Scheduler

Cron jobs are distinct from the heartbeat. They are **agent-authored, precisely-timed tasks** created using the `cron_write` tool once the agent understands the user's behavioural patterns. For example:

- The agent observes the user always messages between 07:15–07:45 each weekday morning.
- It writes a cron job: `0 7 * * 1-5` → "Send morning brief with weather, agenda digest, and a relevant article."
- That cron job then fires independently of the heartbeat, in its own isolated session.

**Cron job structure (stored in `~/.openclaw/cron/jobs.json`):**

```json
{
  "jobs": [
    {
      "jobId": "morning-brief-weekday",
      "name": "Weekday Morning Brief",
      "description": "Auto-created after observing user's 7am wake pattern (confidence: 0.91)",
      "schedule": {
        "kind": "cron",
        "expr": "0 7 * * 1-5",
        "tz": "Europe/London"
      },
      "sessionTarget": "isolated",
      "wakeMode": "now",
      "payload": {
        "kind": "agentTurn",
        "message": "Morning brief time. Query user graph for today's context, search for relevant news on their tracked topics, compose a brief warm message."
      },
      "delivery": {
        "mode": "announce",
        "channel": "telegram",
        "to": "${USER_TELEGRAM_ID}"
      },
      "agentId": "personal-bot",
      "createdBy": "agent",
      "createdAt": "2026-02-10T08:34:00Z"
    }
  ]
}
```

**Agent-writable cron fields** (accessible via `cron_write` tool):
- `name`, `description`, `schedule.expr`, `schedule.tz`, `payload.message`, `delivery`, `enabled`, `deleteAfterRun`

The agent **cannot** modify `jobId`, `createdBy`, `agentId`, or security-sensitive fields — these are owner-locked.

---

### 4.4 Webhook Invoke Surface

Webhooks allow external systems to trigger agent turns. This enables:

- **Email-to-agent**: A Gmail Pub/Sub push notifies the agent of important emails.
- **Calendar events**: A Google Calendar webhook fires 15 minutes before any event the user has.
- **Third-party alerts**: Any system that can POST to an HTTPS endpoint can trigger the agent.

**Webhook endpoint:** `POST https://<your-domain>/webhook/invoke/:key`

**Payload structure:**
```json
{
  "event": "calendar_reminder",
  "data": {
    "eventTitle": "Weekly team standup",
    "startsAt": "2026-02-17T10:00:00Z",
    "location": "Zoom"
  },
  "sessionHint": "user:123456789"
}
```

The Gateway validates the bearer token, resolves the session from `sessionHint`, and enqueues a system event with the payload stringified. The agent tool `webhook_register` can register new webhook keys and their associated prompt templates.

---

### 4.5 Telegram Channel Adapter

The bot connects to Telegram using the **grammY** library (OpenClaw's built-in Telegram adapter). Messages flow through the Gateway.

**Supported interaction types:**
- Text messages (primary conversation channel)
- Voice messages (transcribed via Whisper before routing to the agent)
- Photos (described via vision model before routing)
- Inline commands: `/status`, `/memory`, `/remind`, `/skip`, `/reset-onboarding`
- Reactions (tracked as emotional sentiment signals)

**Message pre-processing pipeline:**
```
Raw Telegram Event
  → Media handler (transcribe voice / describe image)
  → Language detection
  → Toxicity / safety filter
  → Timestamp + timezone tagging
  → Route to session lane
  → Agent runner
```

---

## 5. Memory System — Mem0 + Neo4j Graph

The memory system is the heart of what makes this bot feel like a genuine personal assistant. It is modelled on the **Mem0 / Mem0g architecture** — a two-phase pipeline (extraction → update) combined with a graph-based representation for complex relational reasoning.

### 5.1 Memory Architecture

Memory is stored across three complementary stores:

| Store | Technology | Role |
|---|---|---|
| **Graph DB** | Neo4j Aura | Entities, relationships, life events, habits, people, goals |
| **Vector DB** | Qdrant (self-hosted) or Chroma | Semantic recall for open-ended queries |
| **Key-Value / FTS** | SQLite with FTS5 | Fast keyword search, exact fact lookup, audit logs |

**Two-Phase Memory Pipeline** (fired after every conversation turn):

**Phase 1 — Extraction:**
The agent (or a lightweight background worker using a cheaper model) processes the most recent message pair(s) and extracts:
- Named entities (people, places, organisations, products)
- Stated facts about the user ("I work at Acme Corp", "my partner is Sarah")
- Emotional signals and sentiment
- Time anchors ("this weekend", "next Tuesday")
- Preferences and opinions
- Goals and intentions ("I want to learn Spanish")
- Habitual patterns ("I usually run in the mornings")

**Phase 2 — Update:**
Extracted candidates are compared against the existing graph. The update resolver applies one of: `CREATE` (new node/edge), `UPDATE` (merge into existing), `DEPRECATE` (old fact replaced), or `SKIP` (duplicate or low confidence).

### 5.2 Graph Schema (Neo4j)

**Node Types:**

```cypher
// Core user node
(:User {
  telegramId: String,
  name: String,
  timezone: String,
  language: String,
  onboardingComplete: Boolean,
  createdAt: DateTime,
  lastActive: DateTime
})

// People in the user's life
(:Person {
  name: String,
  relationship: String,  // "partner", "friend", "colleague", "parent"
  notes: String,
  sentiment: Float       // -1.0 to 1.0
})

// Places
(:Place {
  name: String,
  type: String,          // "home", "work", "gym", "favourite_restaurant"
  address: String,
  coordinates: Point
})

// Goals the user has
(:Goal {
  title: String,
  category: String,      // "health", "career", "relationship", "learning"
  status: String,        // "active", "achieved", "abandoned"
  deadline: Date,
  progress: Float,
  createdAt: DateTime
})

// Habits and routines
(:Habit {
  name: String,
  frequency: String,     // "daily", "weekly", "morning", etc.
  timeOfDay: String,
  confidence: Float,     // how consistent this habit is (0–1)
  streak: Integer,
  lastObservedAt: DateTime
})

// Life events and memories
(:Event {
  title: String,
  description: String,
  date: DateTime,
  sentiment: Float,
  tags: [String],
  importance: Integer    // 1-5
})

// Topics the user follows or cares about
(:Topic {
  name: String,
  category: String,
  interest_level: Integer,  // 1-5
  lastSearchedAt: DateTime
})

// Reminders
(:Reminder {
  text: String,
  dueAt: DateTime,
  recurrence: String,
  status: String,        // "pending", "delivered", "dismissed"
  cronJobId: String      // link to cron job if recurring
})
```

**Relationship Types:**

```cypher
(User)-[:KNOWS {since: Date, context: String}]->(Person)
(User)-[:LIVES_AT]->(Place)
(User)-[:WORKS_AT]->(Place)
(User)-[:HAS_GOAL]->(Goal)
(User)-[:HAS_HABIT]->(Habit)
(User)-[:EXPERIENCED]->(Event)
(User)-[:FOLLOWS_TOPIC]->(Topic)
(User)-[:HAS_REMINDER]->(Reminder)
(Person)-[:RELATED_TO {type: String}]->(Person)
(Event)-[:INVOLVES]->(Person)
(Event)-[:HAPPENED_AT]->(Place)
(Goal)-[:RELATED_TO]->(Habit)
(Goal)-[:INSPIRED_BY]->(Event)
```

**Example graph query — morning brief context assembly:**
```cypher
MATCH (u:User {telegramId: $userId})
OPTIONAL MATCH (u)-[:HAS_REMINDER]->(r:Reminder {status: "pending"})
  WHERE r.dueAt <= datetime() + duration("PT8H")
OPTIONAL MATCH (u)-[:HAS_GOAL {status: "active"}]->(g:Goal)
OPTIONAL MATCH (u)-[:FOLLOWS_TOPIC]->(t:Topic)
OPTIONAL MATCH (u)-[:HAS_HABIT]->(h:Habit)
  WHERE h.timeOfDay = "morning"
RETURN u, collect(r) as reminders, collect(g) as goals,
       collect(t) as topics, collect(h) as morningHabits
```

### 5.3 Memory Tools for the Agent

The agent can invoke these tools during any turn (reactive or heartbeat/cron):

```typescript
// Tool definitions exposed to the LLM
const memoryTools = [
  {
    name: "memory_recall",
    description: "Search the user's memory graph using a natural-language query. Returns relevant facts, relationships, and recent context.",
    parameters: {
      query: { type: "string", description: "What to look for in memory" },
      limit: { type: "number", default: 5 },
      include_graph: { type: "boolean", default: true }
    }
  },
  {
    name: "memory_write",
    description: "Store a new fact, preference, event, or relationship into the user's memory graph. Use after learning something new about the user.",
    parameters: {
      content: { type: "string", description: "The fact or information to store" },
      type: { 
        type: "string", 
        enum: ["fact", "event", "goal", "habit", "preference", "person", "reminder", "topic"]
      },
      metadata: { type: "object", description: "Optional structured metadata (e.g. {dueAt, person_name, place})" }
    }
  },
  {
    name: "memory_update",
    description: "Update or correct an existing memory. Use when the user provides new information that supersedes old facts.",
    parameters: {
      memory_id: { type: "string" },
      updated_content: { type: "string" },
      reason: { type: "string" }
    }
  },
  {
    name: "memory_delete",
    description: "Mark a memory as deprecated. Use when the user explicitly says something is no longer true.",
    parameters: {
      memory_id: { type: "string" },
      reason: { type: "string" }
    }
  },
  {
    name: "graph_query",
    description: "Run a direct Cypher query against the user's Neo4j graph for complex relational lookups. Returns raw graph results.",
    parameters: {
      cypher: { type: "string", description: "The Cypher query to execute" },
      params: { type: "object" }
    }
  }
]
```

---

## 6. Skills System

Skills extend what the agent can do. Each skill is a folder containing a `SKILL.md` file (using the `AgentSkills` standard) and any supporting scripts.

### 6.1 Skill Structure (SKILL.md Standard)

```
skills/
├── memory-manager/
│   ├── SKILL.md
│   └── neo4j-helpers.ts
├── daily-briefing/
│   ├── SKILL.md
│   └── templates/
├── onboarding/
│   ├── SKILL.md
│   └── questions.json
├── web-researcher/
│   ├── SKILL.md
│   └── search-wrapper.ts
├── pattern-analyzer/
│   ├── SKILL.md
│   └── behaviour-model.ts
├── reminder-manager/
│   ├── SKILL.md
│   └── reminder-engine.ts
└── cron-author/
    ├── SKILL.md
    └── cron-templates.json
```

**SKILL.md format:**
```yaml
---
name: memory-manager
version: 1.0.0
description: Manages the user's Neo4j memory graph — reading, writing, and reasoning over personal knowledge.
dependencies:
  - neo4j-driver
  - mem0ai
tools:
  - memory_recall
  - memory_write
  - memory_update
  - memory_delete
  - graph_query
triggers:
  - always  # loaded into context on every turn
---

# Memory Manager Skill

You have access to a persistent Neo4j graph database that stores everything known about this user.
Use `memory_recall` before answering questions about the user's life, preferences, or history.
Use `memory_write` whenever the user reveals new information about themselves.
...
```

### 6.2 Core Built-in Skills

| Skill | Trigger | Purpose |
|---|---|---|
| `memory-manager` | always | Read/write/query the Neo4j memory graph |
| `onboarding` | first session + `onboardingComplete: false` | Run structured life-context interview |
| `daily-briefing` | morning cron / heartbeat | Compose personalised morning summary |
| `web-researcher` | on demand + daily topic scan | Search internet; blend with personal context |
| `pattern-analyzer` | heartbeat (background) | Identify behavioural patterns from conversation history |
| `reminder-manager` | on demand + heartbeat | Create, query, deliver, and dismiss reminders |
| `cron-author` | agent decision | Write new cron jobs based on identified patterns |
| `emotion-tracker` | always | Detect and store emotional signals from messages |
| `topic-watcher` | daily cron | Monitor tracked topics; surface relevant news |

---

## 7. Templates

### 7.1 Onboarding Template

The onboarding template is a structured interview the agent runs during the user's first sessions. It is conversational, not a form — the agent asks questions naturally and extracts structured data into the graph.

The onboarding skill tracks which questions have been asked and stores partial state in the user's memory so it can resume across sessions. A typical onboarding flows across 2–3 early conversations rather than a single long session.

**Onboarding question categories and example prompts:**

```json
{
  "onboarding": {
    "sections": [
      {
        "id": "identity",
        "label": "Who are you?",
        "questions": [
          "What should I call you?",
          "Where are you based? (City / Country helps me tailor timing and context)",
          "What do you do for work, roughly? No need to be specific if you'd prefer not."
        ]
      },
      {
        "id": "relationships",
        "label": "The people in your life",
        "questions": [
          "Tell me about the people who matter most to you — partner, close friends, family?",
          "Anyone I should know about at work — a manager, teammates you mention a lot?",
          "Any pets? 😄"
        ]
      },
      {
        "id": "daily_life",
        "label": "Your daily rhythm",
        "questions": [
          "What does a typical weekday look like for you?",
          "When do you usually wake up? When do you wind down?",
          "Do you have regular habits — gym, meditation, journaling, walks?"
        ]
      },
      {
        "id": "goals_and_focus",
        "label": "What you're working toward",
        "questions": [
          "What's something you're trying to improve or achieve right now?",
          "Is there a skill you're trying to learn?",
          "Any big life goals — things you're building toward over months or years?"
        ]
      },
      {
        "id": "interests_and_topics",
        "label": "What you care about",
        "questions": [
          "What topics do you follow closely — tech, health, finance, sports, something else?",
          "Any shows, books, games, or hobbies I should know about?",
          "Is there anything you'd love me to keep you updated on — news, trends, prices?"
        ]
      },
      {
        "id": "communication_style",
        "label": "How to work well together",
        "questions": [
          "Do you prefer I check in proactively, or wait for you to reach out?",
          "Short and punchy, or more detail when relevant?",
          "Anything that would make me more useful — or anything that would be annoying?"
        ]
      }
    ],
    "completion": {
      "message": "That's everything I need to get started. I'll keep learning as we talk — and I'll ask before I assume anything important. You can always tell me to update, correct, or forget anything I know about you. 🦞",
      "action": "set_onboarding_complete"
    }
  }
}
```

**Onboarding system prompt segment (injected when `onboardingComplete: false`):**

```
You are in ONBOARDING MODE. Your job is to learn about this new user through warm, natural conversation.

Rules:
- Ask ONE question at a time. Never list multiple questions in one message.
- Follow the user's lead — if they volunteer info beyond the question, capture it but don't interrogate further.
- Be warm, curious, and personal — not clinical or form-like.
- After each response, use memory_write to store what you learned before asking the next question.
- Track which onboarding sections are complete using memory_write {type: "fact", content: "onboarding:identity:complete"}.
- The full interview should feel natural across 2–3 conversations, not like a single long form.
- Once all sections are complete, call the action set_onboarding_complete.
```

---

### 7.2 Daily Check-in Template

This template is used by the `daily-briefing` skill, fired by the user's morning cron job:

```markdown
# Daily Brief Template

## Context Assembly (agent does this before composing the message)
1. `memory_recall("today's agenda, upcoming events, reminders")` 
2. `graph_query("MATCH (u:User)-[:HAS_REMINDER]->(r) WHERE r.status='pending' AND r.dueAt < datetime()+duration('PT24H') RETURN r")`
3. `web_search("${user.trackedTopics} latest news")` — search each tracked topic
4. Check `current time` against user's `wake_pattern` and `timezone`

## Message Structure
- Opening: Personalised greeting referencing something contextually relevant (day of week, known plans, recent conversation thread)
- Reminders: Any pending items due today (max 3)
- Brief: 2–3 curated items from tracked topics (with one-sentence summaries, no links unless requested)
- Focus: One "thought for the day" tied to an active goal
- Closing: Light, optional — could reference weather, a running streak, an upcoming milestone

## Tone
- Warm, like a thoughtful friend who's well-informed
- Never robotic or newsletter-like
- Length: 150–250 words total
```

---

### 7.3 HEARTBEAT.md Template

This file lives in the agent's workspace and is read on every 30-minute heartbeat:

```markdown
# HEARTBEAT

You are running autonomously. Check the following. Be minimal. Only message the user if genuinely warranted.

## Priority Checks

### 1. Overdue Reminders
Query: reminders where dueAt < now AND status = 'pending'
Action if found: Send reminder message immediately. Update status to 'delivered'.

### 2. Scheduled Briefs
Query: Has the morning brief been sent today? (check memory for "brief_sent:YYYY-MM-DD")
Action if within wake window AND brief not sent: Compose and send morning brief.

### 3. Stale Conversation
Query: Last message from user. If > 36h ago AND no recent check-in sent:
Action: Send a contextual, non-generic check-in (reference something real from memory)

### 4. Pattern Engine Output
Query: pattern_analyze tool — any new high-confidence patterns?
Action if confidence > 0.85: Surface insight to user. Optionally use cron_write to schedule a new job.

### 5. Topic Alerts
Query: For each tracked topic, check for breaking news or significant updates
Action if significant update found: Send a one-line alert with a follow-up offer

## Silent Conditions
- If ALL checks return nothing actionable: respond only with HEARTBEAT_OK
- Log all check results to heartbeat_audit.jsonl regardless of outcome
- Never send more than 2 messages per heartbeat cycle
```

---

## 8. Agent Tool Catalogue

The complete set of tools available to the agent in any given turn:

| Tool | Category | Description |
|---|---|---|
| `memory_recall` | Memory | Semantic + keyword search across vector + FTS stores |
| `memory_write` | Memory | Write new fact/event/goal/habit/person to Neo4j + vector |
| `memory_update` | Memory | Update an existing memory node |
| `memory_delete` | Memory | Deprecate an outdated memory |
| `graph_query` | Memory | Raw Cypher query on Neo4j for complex reasoning |
| `cron_write` | Scheduling | Create a new cron job (agent-authored schedule) |
| `cron_list` | Scheduling | List all active cron jobs for this user |
| `cron_delete` | Scheduling | Remove a cron job (must confirm with user first) |
| `reminder_set` | Scheduling | Set a one-time or recurring reminder |
| `reminder_list` | Scheduling | List pending reminders |
| `reminder_dismiss` | Scheduling | Mark a reminder as dismissed |
| `web_search` | Research | Search the internet using a query string |
| `web_fetch` | Research | Fetch and extract text content from a URL |
| `extract_entities` | Intelligence | Extract named entities from a text block |
| `pattern_analyze` | Intelligence | Run behaviour pattern detection on conversation history |
| `send_telegram` | Communication | Send a proactive Telegram message to the user |
| `get_user_profile` | Context | Fetch the complete user profile from Neo4j |
| `get_time_context` | Context | Get current time in user's timezone + day-of-week |
| `log_heartbeat` | Observability | Write an entry to the heartbeat audit log |

**Tool implementation locations:**
- Memory tools: `plugins/memory-plugin/tools/`
- Scheduling tools: `plugins/scheduler-plugin/tools/`
- Research tools: `plugins/research-plugin/tools/`
- Intelligence tools: `plugins/intelligence-plugin/tools/`

---

## 9. Proactive Intelligence Loop

This is the system that turns the bot from a passive chat assistant into a proactive life companion. It operates on three time horizons:

### Immediate (reactive — every message)
- Entity extraction + memory write (background, non-blocking)
- Sentiment detection stored in user graph
- Check for any user-triggered reminder triggers (e.g., "remind me about this")

### Medium-term (heartbeat — every 30 minutes)
- Reminder delivery check
- Morning/evening brief triggers
- Stale conversation check-in
- Topic freshness check (lightweight web search per tracked topic)
- Pattern engine output check

### Long-term (daily cron — configurable time)
- Full daily topic scan with curated summaries
- Goal progress review (nudge if no progress mentioned recently)
- Weekly retrospective (Sundays): summarise the week, celebrate wins, surface patterns
- Monthly profile refresh: ask if any big life changes need updating in memory

---

## 10. User Behaviour Pattern Engine

The pattern analyzer skill runs on each heartbeat and on-demand. It ingests the conversation transcript history and the activity timestamps to build a behavioural model.

**What it detects:**

```typescript
interface BehaviourPattern {
  type: "wake_time" | "sleep_time" | "active_hours" | "message_frequency" 
      | "emotional_cycle" | "topic_interest_shift" | "goal_momentum" | "habit_consistency";
  description: string;
  confidence: number;     // 0–1, only surfaced if > 0.80
  data_points: number;    // how many observations support it
  first_observed: Date;
  recommended_action: "new_cron_job" | "reminder_adjustment" | "check_in" | "insight_surface" | "none";
  cron_suggestion?: {
    expr: string;
    tz: string;
    description: string;
    payload_message: string;
  };
}
```

**Example pattern detection output:**

```json
{
  "type": "wake_time",
  "description": "User consistently sends their first message between 07:12–07:38 on weekdays",
  "confidence": 0.93,
  "data_points": 14,
  "recommended_action": "new_cron_job",
  "cron_suggestion": {
    "expr": "0 7 * * 1-5",
    "tz": "Europe/London",
    "description": "Weekday morning brief — timed to user's observed wake pattern",
    "payload_message": "User is likely just woken up. Send a warm, brief morning message: pending reminders, one topic update, and one goal nudge."
  }
}
```

When the agent surfaces a pattern, it asks the user for permission before creating any new cron job:

> "I've noticed you seem to be most active around 7:15am on weekdays. Want me to set up an automatic morning brief that arrives just before you start your day?"

---

## 11. Internet Search Integration

The `web-researcher` skill wraps the `web_search` and `web_fetch` tools with a topic-aware query builder.

**Daily topic scan (runs via cron job, fires once per day):**

```typescript
async function dailyTopicScan(userId: string) {
  const topics = await graphQuery(
    `MATCH (u:User {telegramId: $userId})-[:FOLLOWS_TOPIC]->(t:Topic) 
     WHERE t.interest_level >= 3 
     RETURN t ORDER BY t.interest_level DESC LIMIT 5`,
    { userId }
  );
  
  const results: TopicUpdate[] = [];
  
  for (const topic of topics) {
    const searchResult = await webSearch(`${topic.name} latest news today`);
    const significant = filterSignificant(searchResult, topic.lastSearchedAt);
    
    if (significant.length > 0) {
      results.push({
        topic: topic.name,
        updates: significant.slice(0, 2),  // max 2 per topic
        importance: scoreImportance(significant)
      });
      
      // Update last searched timestamp
      await memoryWrite({
        type: "fact",
        content: `topic:${topic.name}:last_searched:${new Date().toISOString()}`
      });
    }
  }
  
  // Only send if at least one topic has significant updates
  if (results.length > 0) {
    await composeDailyTopicDigest(userId, results);
  }
}
```

**Search quality rules:**
- Never send more than 3 topic updates per day digest.
- Filter out results older than 24 hours (for daily scan) or 6 hours (for heartbeat checks).
- Score importance based on: source credibility, keyword match density, topic interest level.
- Store search results in vector DB for recall (user can ask "what did you find about X yesterday?").

---

## 12. Data Flow Diagrams

### Inbound Message Flow

```
User sends Telegram message
  │
  ▼
grammY adapter receives update
  │
  ▼
Gateway: access control check → session resolve → enqueue to user lane
  │
  ▼
Agent Runner: context assembly
  ├── Recall recent memory (memory_recall, top-5 relevant facts)
  ├── Load active skill instructions
  └── Attach user profile snapshot from Neo4j
  │
  ▼
LLM call (claude-sonnet-4 primary)
  │
  ├── Tool calls? → Execute in sandbox → Append results → Re-call LLM
  └── Final text response
  │
  ▼
Background (non-blocking, parallel lane):
  ├── Extract entities from message + response
  ├── memory_write new facts discovered
  ├── Sentiment analysis → update user emotion graph
  └── Update conversation timestamp in Neo4j
  │
  ▼
Gateway sends response back via Telegram adapter
```

### Heartbeat Flow

```
Gateway timer fires (30m interval)
  │
  ▼
Enqueue system event to cron:heartbeat lane
  │
  ▼
Agent Runner: isolated session (no main chat history)
  ├── Read HEARTBEAT.md
  ├── Query Neo4j for pending reminders, briefing status
  ├── Run pattern_analyze (background)
  └── Check tracked topics (lightweight search)
  │
  ▼
LLM decision: anything to surface?
  ├── YES → Compose message → send_telegram → log to heartbeat_audit.jsonl
  └── NO  → Respond HEARTBEAT_OK → Gateway suppresses delivery → log
```

### Cron Author Flow

```
Pattern Engine detects high-confidence pattern (> 0.85)
  │
  ▼
Heartbeat: agent surface insight to user
  │
  ▼
User agrees / requests automation
  │
  ▼
Agent calls cron_write tool with:
  { name, expr, tz, payload_message, delivery }
  │
  ▼
Cron written to ~/.openclaw/cron/jobs.json
  │
  ▼
memory_write: "cron_job_created: morning-brief-weekday"
  │
  ▼
Agent confirms to user with a natural explanation of what will happen
```

---

## 13. Project File Structure

```
personal-bot/
├── openclaw.json                  # Gateway + agent + channel config
├── HEARTBEAT.md                   # Heartbeat instructions (loaded each heartbeat)
├── SOUL.md                        # Agent's core system prompt / personality
│
├── plugins/
│   ├── memory-plugin/
│   │   ├── index.ts               # Plugin registration
│   │   ├── neo4j-client.ts        # Neo4j driver wrapper
│   │   ├── vector-client.ts       # Qdrant client wrapper
│   │   ├── mem0-pipeline.ts       # Extract → Update pipeline
│   │   └── tools/
│   │       ├── memory_recall.ts
│   │       ├── memory_write.ts
│   │       ├── memory_update.ts
│   │       ├── memory_delete.ts
│   │       └── graph_query.ts
│   │
│   ├── scheduler-plugin/
│   │   ├── index.ts
│   │   └── tools/
│   │       ├── cron_write.ts
│   │       ├── cron_list.ts
│   │       ├── cron_delete.ts
│   │       ├── reminder_set.ts
│   │       ├── reminder_list.ts
│   │       └── reminder_dismiss.ts
│   │
│   ├── research-plugin/
│   │   ├── index.ts
│   │   ├── search-wrapper.ts
│   │   └── tools/
│   │       ├── web_search.ts
│   │       └── web_fetch.ts
│   │
│   └── intelligence-plugin/
│       ├── index.ts
│       ├── entity-extractor.ts
│       ├── sentiment-analyzer.ts
│       ├── pattern-engine.ts
│       └── tools/
│           ├── extract_entities.ts
│           └── pattern_analyze.ts
│
├── skills/
│   ├── memory-manager/
│   │   └── SKILL.md
│   ├── onboarding/
│   │   ├── SKILL.md
│   │   └── questions.json
│   ├── daily-briefing/
│   │   ├── SKILL.md
│   │   └── templates/
│   ├── web-researcher/
│   │   └── SKILL.md
│   ├── pattern-analyzer/
│   │   └── SKILL.md
│   ├── reminder-manager/
│   │   └── SKILL.md
│   ├── cron-author/
│   │   ├── SKILL.md
│   │   └── cron-templates.json
│   └── emotion-tracker/
│       └── SKILL.md
│
├── templates/
│   ├── onboarding.json
│   ├── morning-brief.md
│   ├── evening-reflection.md
│   ├── weekly-retrospective.md
│   └── reminder-delivery.md
│
├── data/
│   ├── transcripts/               # JSONL audit logs (immutable)
│   ├── memory/                    # Markdown memory snapshots
│   └── heartbeat-audit.jsonl      # Heartbeat decision log
│
├── scripts/
│   ├── setup-neo4j-schema.cypher  # Schema + indexes
│   ├── setup-qdrant.ts            # Vector collection setup
│   └── onboard-user.ts            # Manual onboarding trigger
│
└── docs/
    ├── IMPLEMENTATION.md           # This file
    ├── SECURITY.md
    └── RUNBOOK.md
```

---

## 14. Configuration Reference

### Core `openclaw.json`

```json
{
  "gateway": {
    "host": "127.0.0.1",
    "port": 18789,
    "auth": {
      "mode": "token",
      "token": "${GATEWAY_TOKEN}"
    },
    "logLevel": "info"
  },
  "agents": {
    "personal-bot": {
      "soul": "./SOUL.md",
      "model": {
        "primary": "anthropic/claude-sonnet-4-5-20250929",
        "fallbacks": ["anthropic/claude-haiku-4-5-20251001"]
      },
      "heartbeat": {
        "every": "30m",
        "model": "anthropic/claude-haiku-4-5-20251001",
        "prompt": "Read HEARTBEAT.md and act accordingly.",
        "target": "last",
        "includeReasoning": false,
        "ackMaxChars": 200
      },
      "skills": [
        "./skills/memory-manager",
        "./skills/onboarding",
        "./skills/daily-briefing",
        "./skills/web-researcher",
        "./skills/pattern-analyzer",
        "./skills/reminder-manager",
        "./skills/cron-author",
        "./skills/emotion-tracker"
      ],
      "plugins": [
        "./plugins/memory-plugin",
        "./plugins/scheduler-plugin",
        "./plugins/research-plugin",
        "./plugins/intelligence-plugin"
      ],
      "sandbox": {
        "allowedPaths": ["./data", "./skills", "./templates"],
        "allowedHosts": ["api.anthropic.com", "neo4j.io", "search-api.example.com"],
        "denyShellExec": false
      }
    }
  },
  "channels": {
    "telegram": {
      "enabled": true,
      "token": "${TELEGRAM_BOT_TOKEN}",
      "agent": "personal-bot",
      "webhook": {
        "enabled": true,
        "url": "${TELEGRAM_WEBHOOK_URL}"
      }
    }
  },
  "cron": {
    "enabled": true,
    "store": "~/.openclaw/cron/jobs.json",
    "maxConcurrentRuns": 1,
    "webhookToken": "${CRON_WEBHOOK_TOKEN}"
  },
  "memory": {
    "provider": "custom",
    "plugin": "./plugins/memory-plugin",
    "neo4j": {
      "url": "${NEO4J_URL}",
      "username": "${NEO4J_USERNAME}",
      "password": "${NEO4J_PASSWORD}",
      "database": "neo4j"
    },
    "vector": {
      "provider": "qdrant",
      "url": "${QDRANT_URL}",
      "collection": "personal-bot-memories"
    },
    "fts": {
      "path": "./data/fts.sqlite"
    }
  },
  "webhooks": {
    "surface": {
      "enabled": true,
      "path": "/webhook",
      "token": "${WEBHOOK_SURFACE_TOKEN}"
    }
  }
}
```

### Environment Variables (`.env`)

```bash
# Anthropic
ANTHROPIC_API_KEY=sk-ant-...

# Telegram
TELEGRAM_BOT_TOKEN=12345:ABCDE...
TELEGRAM_WEBHOOK_URL=https://your-domain.com/telegram-webhook

# Gateway
GATEWAY_TOKEN=your-secure-gateway-token

# Neo4j
NEO4J_URL=neo4j+s://your-instance.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your-neo4j-password

# Vector DB
QDRANT_URL=http://localhost:6333

# Webhooks
WEBHOOK_SURFACE_TOKEN=your-webhook-surface-token
CRON_WEBHOOK_TOKEN=your-cron-webhook-token

# Search (choose one)
BRAVE_SEARCH_API_KEY=BSA...
# or
SERP_API_KEY=...
```

---

## 15. Implementation Roadmap (Phases)

### Phase 0 — Foundation (Week 1)

Set up the bare minimum to run the bot and exchange messages.

- [ ] Install OpenClaw (`npx openclaw@latest` or from source)
- [ ] Run `openclaw onboard` to generate base config
- [ ] Configure Telegram channel with bot token
- [ ] Verify `openclaw doctor` passes all checks
- [ ] Test round-trip: message → agent response → Telegram delivery
- [ ] Set up Neo4j Aura (free tier) and run schema setup script
- [ ] Set up Qdrant (Docker: `docker run -p 6333:6333 qdrant/qdrant`)
- [ ] Implement `memory-plugin` (basic `memory_recall` and `memory_write`)
- [ ] Write `SOUL.md` — agent's core personality and instructions
- [ ] Deploy to VPS / cloud host (DigitalOcean, Railway, or Hetzner)

**End of Phase 0 deliverable:** Bot receives messages, responds with Claude, writes basic facts to memory.

---

### Phase 1 — Memory & Onboarding (Weeks 2–3)

- [ ] Implement full `mem0-pipeline.ts` (extract → update two-phase pipeline)
- [ ] Build complete Neo4j schema (all node types, relationships, indexes)
- [ ] Implement all 5 memory tools (`recall`, `write`, `update`, `delete`, `graph_query`)
- [ ] Build `onboarding` skill with full question set and state tracking
- [ ] Test: User completes onboarding; all facts appear as nodes in Neo4j
- [ ] Build `emotion-tracker` skill (sentiment → Neo4j storage)
- [ ] Implement background entity extraction (non-blocking, after each turn)
- [ ] Add FTS5 SQLite layer (keyword indexing of all memory writes)

**End of Phase 1 deliverable:** Bot remembers everything, user profile is rich in Neo4j, onboarding flow is complete.

---

### Phase 2 — Heartbeat & Scheduling (Week 4)

- [ ] Configure and test the heartbeat engine (30m interval, isolated session)
- [ ] Write `HEARTBEAT.md` with all check logic
- [ ] Implement `reminder-manager` skill (set, list, dismiss via tool calls)
- [ ] Test heartbeat reminder delivery end-to-end
- [ ] Implement `cron-author` skill and `cron_write` tool
- [ ] Build `scheduler-plugin` (full cron tool set)
- [ ] Write first user-facing cron job template (morning brief)
- [ ] Test: Agent identifies a pattern → proposes cron → user agrees → cron fires

**End of Phase 2 deliverable:** Bot sends proactive messages, delivers reminders, and can write its own schedules.

---

### Phase 3 — Intelligence & Research (Weeks 5–6)

- [ ] Implement `web-researcher` skill and search tools (Brave Search API or SerpAPI)
- [ ] Build daily topic scan cron job
- [ ] Implement `pattern-engine.ts` with time-of-day analysis and habit detection
- [ ] Build `pattern-analyzer` skill
- [ ] Test: 2 weeks of synthetic conversation data → pattern engine detects wake time with 0.9+ confidence
- [ ] Implement `daily-briefing` skill with full context assembly pipeline
- [ ] Build and test morning brief cron job with real Neo4j data + web search
- [ ] Implement webhook surface integration (test with a simulated calendar event)

**End of Phase 3 deliverable:** Bot delivers curated daily briefs, searches the web, detects and acts on patterns.

---

### Phase 4 — Polish & Production (Weeks 7–8)

- [ ] Add model failover configuration (haiku fallback for heartbeats)
- [ ] Add rate limiting and token budget tracking
- [ ] Implement conversation compaction (summary older sessions to reduce context)
- [ ] Add voice message transcription (Whisper API)
- [ ] Security review: sandbox paths, allowlists, no credential leakage in logs
- [ ] Add `SECURITY.md` and `RUNBOOK.md`
- [ ] Load testing: simulate 100 conversations across 30m heartbeat window
- [ ] Add monitoring (Grafana + Prometheus or simple health endpoint)
- [ ] Write user-facing docs (how to use, privacy, how to delete memory)

**End of Phase 4 deliverable:** Production-ready personal bot running stably, securely, with full autonomy.

---

## 16. Security & Privacy Considerations

### Data Residency
All personal data lives in the operator-controlled Neo4j instance (Aura or self-hosted) and the Qdrant vector store. No personal data is sent to Anthropic beyond what is in the LLM context window for each API call. OpenClaw's JSONL audit transcripts are stored locally.

### Sensitive Data Handling
- Never store raw API keys in Neo4j or memory stores — only in env variables or the encrypted secrets vault.
- Memory writes are scoped by `userId` — the graph queries always filter `WHERE u.telegramId = $userId` to prevent cross-user contamination.
- The Telegram channel adapter validates `chat.id` and `user.id` against the known user set before routing any message to the agent.

### Prompt Injection Defences
- Web search results are wrapped in explicit `<search_result>` tags before being added to context. The system prompt instructs the agent that content within these tags is untrusted external data and should never be executed as instructions.
- Tool output is sanitised before being appended to the message chain.
- The cron author tool requires explicit parameters rather than accepting freeform cron expressions from user messages — the agent must structure a valid JSON payload, which is validated before writing to `jobs.json`.

### Sandbox Controls
- Allowed file paths: `./data`, `./skills`, `./templates` only.
- Allowed outbound hosts: Anthropic API, Neo4j, Qdrant, configured search APIs.
- No shell exec in production (`denyShellExec: true` after Phase 0).

### User Control
- `GET /memory` — user can request a dump of all stored memories.
- `DELETE /memory/:id` — user can delete specific memories via a Telegram command.
- `/reset-onboarding` — wipes onboarding state so user can redo the interview.
- `/forget-me` — full data deletion from Neo4j, Qdrant, and SQLite.

---

## 17. Deployment Guide

### Local Development (macOS / Linux)

```bash
# 1. Install OpenClaw
npx openclaw@latest

# 2. Clone this repo
git clone https://github.com/your-org/personal-bot
cd personal-bot

# 3. Copy and configure environment
cp .env.example .env
# Edit .env with your API keys

# 4. Set up databases
docker compose up -d  # starts Qdrant + Neo4j (local)
npm run setup:neo4j   # runs schema + index setup

# 5. Run onboarding
openclaw onboard --config ./openclaw.json

# 6. Start the gateway
openclaw start --config ./openclaw.json

# 7. Check health
openclaw doctor
openclaw status
```

### Production (VPS — Ubuntu 22.04+)

```bash
# 1. Install Node.js 22+
curl -fsSL https://deb.nodesource.com/setup_22.x | sudo bash
sudo apt install -y nodejs

# 2. Install OpenClaw globally
npm install -g openclaw

# 3. Clone and configure
git clone https://github.com/your-org/personal-bot /opt/personal-bot
cd /opt/personal-bot
cp .env.example .env && nano .env

# 4. Configure Telegram webhook (instead of polling)
# Set your TELEGRAM_WEBHOOK_URL to your HTTPS domain
# OpenClaw will auto-register it on start

# 5. Set up Neo4j Aura (recommended for production)
# Create instance at console.neo4j.io
# Copy credentials to .env

# 6. Systemd service for the gateway
sudo cp scripts/personal-bot.service /etc/systemd/system/
sudo systemctl enable personal-bot
sudo systemctl start personal-bot

# 7. Nginx reverse proxy (for webhook surface + dashboard)
sudo cp scripts/nginx.conf /etc/nginx/sites-available/personal-bot
sudo certbot --nginx -d your-domain.com
sudo systemctl reload nginx

# 8. Verify
curl https://your-domain.com/health
openclaw status
```

### Docker Compose (all-in-one)

```yaml
version: "3.9"
services:
  gateway:
    build: .
    env_file: .env
    ports:
      - "127.0.0.1:18789:18789"
    volumes:
      - ./data:/app/data
      - ./skills:/app/skills
    depends_on:
      - qdrant
    restart: unless-stopped

  qdrant:
    image: qdrant/qdrant:latest
    volumes:
      - qdrant_data:/qdrant/storage
    restart: unless-stopped

volumes:
  qdrant_data:
```

Neo4j is recommended as Aura (cloud) for production. For local development only, add:
```yaml
  neo4j:
    image: neo4j:5
    environment:
      NEO4J_AUTH: "neo4j/your-password"
    volumes:
      - neo4j_data:/data
    restart: unless-stopped
```

---

## Summary

This implementation delivers a **truly personal, autonomous AI companion** grounded in the OpenClaw / ZeroClaw architecture. The key design decisions are:

**Gateway-first:** Every interaction — reactive, proactive, scheduled, or webhook-triggered — flows through the single Gateway control plane. This is the source of truth for sessions, schedules, and state.

**Memory as the product:** The Neo4j graph is what differentiates this bot from a stateless chatbot. The quality of the user's experience is directly proportional to the richness of their memory graph. The onboarding template and the background extraction pipeline are both feeding this graph continuously.

**Proactivity is earned, not assumed:** The heartbeat gives the agent a voice on its own schedule, but it is instructed to be silent (`HEARTBEAT_OK`) unless there is genuine reason to speak. The agent writes its own cron jobs only after it has observed sufficient data and gotten user consent. This respects user attention and builds trust.

**Self-scheduling as the capability ceiling:** The most powerful feature is the agent's ability to write its own cron jobs once it understands the user's patterns. A bot that schedules itself based on your actual behaviour — not a fixed 9am push notification — is categorically more useful than one that asks you to configure everything manually.

**Separation of concerns:** The Lane Queue (serial-within-lane, explicit parallelism) prevents race conditions. Background extraction runs in a parallel lane. Heartbeats run in their own isolated `cron:` session. The main conversation lane is never blocked by any of these background processes.

---

*Built on OpenClaw (MIT) · Memory powered by Mem0 + Neo4j · Channel: Telegram*  
*Implementation plan authored: 2026-02-17*
