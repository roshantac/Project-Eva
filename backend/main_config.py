import os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_DIR = os.path.join(BASE_DIR, "db")
MEMORY_DIR = os.path.join(DB_DIR, "memory")
USER_DIR = os.path.join(DB_DIR, "user")
SESSIONS_DIR = os.path.join(MEMORY_DIR, "sessions")
HISTORY_DB_PATH = os.path.join(USER_DIR, "history.db")
USERS_DB_PATH = os.path.join(USER_DIR, "users.db")

PROMPTS_DIR = os.path.join(BASE_DIR, "prompts")
DEFAULT_SYSTEM_PROMPT_PATH = os.path.join(PROMPTS_DIR, "personal_assistant_system_prompt.md")