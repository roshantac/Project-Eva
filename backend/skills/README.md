# Skills

Skills extend the agent’s behavior with reusable instructions. They follow the **AgentSkills**-compatible format used by OpenClaw and Claude Code.

## Layout

Each skill is a **directory** with a `SKILL.md` file:

```
skills/
├── README.md           # This file
├── code-review/        # Example skill
│   └── SKILL.md
└── your-skill/
    └── SKILL.md
```

## SKILL.md format

- **YAML frontmatter** (between `---` markers): `name`, `description`, and optional metadata.
- **Markdown body**: Instructions the agent should follow when using the skill.

Minimal example:

```yaml
---
name: my-skill
description: Short description so the agent knows when to use this skill.
---

Your instructions here. Be specific so the agent can follow them.
```

## Where skills are loaded from

1. **Project skills**: `backend/skills/` (this directory) — checked first.
2. **User skills**: `~/.eva/skills/` — available across projects.

The agent uses the **list_skills** and **read_skill** tools to discover and load skills at runtime.
