from __future__ import annotations

from typing import Dict


# Top-level categories for user-facing long-term memory.
PERSONAL_MEMORY_CATEGORIES: Dict[str, str] = {
    "identity_profile": "Identity, demographics, languages, and where the user lives.",
    "preferences_general": "General likes and dislikes for food, music, brands, products, media, and style.",
    "preferences_workstyle": "How the user prefers to work, communicate, and schedule meetings.",
    "work_career": "Jobs, roles, employers, teams, and important work projects.",
    "education_skills": "Education history, courses, certifications, and skills the user has or is learning.",
    "relationships_family": "Family members and important facts about them.",
    "relationships_social": "Friends, colleagues, and other social relationships.",
    "hobbies_interests": "Hobbies, sports, games, creative pursuits, and other interests.",
    "health_wellness": "High-level health constraints, allergies, routines, and fitness or wellness goals.",
    "finance_life_admin": "Budgets, recurring bills, subscriptions, and other life administration details.",
    "logistics_routines": "Daily and weekly routines, schedules, time zones, and commute or travel patterns.",
    "digital_life_tools": "Devices, apps, and services the user uses and how they are configured.",
    "goals_plans": "Short-term and long-term goals, projects, and milestones.",
    "constraints_boundaries": "Hard limits, constraints, and things the assistant should avoid.",
    "assistant_preferences": "How the user wants the assistant to respond, behave, and take initiative.",
}

CATEGORY_LIST = list(PERSONAL_MEMORY_CATEGORIES.keys())


def normalize_category(raw: str | None) -> str | None:
    if not raw:
        return None
    key = str(raw).strip().lower()
    if key in PERSONAL_MEMORY_CATEGORIES:
        return key
    # Allow minor variations like dashes vs underscores.
    key = key.replace("-", "_")
    return key if key in PERSONAL_MEMORY_CATEGORIES else None


__all__ = ["PERSONAL_MEMORY_CATEGORIES", "CATEGORY_LIST", "normalize_category"]

