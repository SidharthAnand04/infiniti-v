"""Multi-agent scene generation helpers."""

import os
import itertools
from typing import List, Dict

# Placeholder environment variables for API keys
GROQ_API_KEY = os.getenv('GROQ_API_KEY')
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
LETTA_API_KEY = os.getenv('LETTA_API_KEY')


def interpret_prompt(prompt: str) -> Dict:
    """Parse the user prompt to determine topic, setting and characters."""

    clean = prompt.strip()
    topic = clean
    setting = "unknown"

    # Very light parsing for "<topic> in <setting>" prompts
    if " in " in clean:
        first, setting_part = clean.split(" in ", 1)
        topic = first.rstrip(".")
        setting = setting_part.rstrip(".")
    else:
        topic = clean.rstrip('.')

    characters: List[Dict] = []
    lower = clean.lower()
    if "teacher" in lower:
        characters.append({"name": "Teacher", "role": "teacher", "traits": {}})
    if "student" in lower:
        characters.append({"name": "Student", "role": "student", "traits": {}})
    if not characters:
        characters.append({"name": "Narrator", "role": "narrator", "traits": {}})

    return {
        "scene_topic": topic.capitalize(),
        "setting": setting,
        "scene_type": "conversation",
        "characters": characters,
        "target_length_seconds": 150,
    }


def web_search(scene_topic: str, setting: str) -> Dict:
    """Stub for a web search agent using Letta."""

    # Internet access is blocked so we return dummy references.
    return {
        "references": [
            f"Facts about {scene_topic} gleaned from a web search.",
            f"Information about {setting} for background."
        ],
        "images": [],
    }


def plan_scene(metadata: Dict, references: Dict) -> Dict:
    """Create a lightweight scene plan based on metadata."""

    flow = ["intro", "concept", "reaction", "wrap"]

    # Basic estimate: 8 dialogue turns for a short 2 minute scene
    turns = 8

    return {
        "scene_title": metadata["scene_topic"],
        "background": metadata["setting"],
        "flow": flow,
        "dialogue_turns": turns,
        "camera_plan": ["wide", "close-up", "medium", "wide"],
    }


def generate_dialogue(characters: List[Dict], turns: int, topic: str) -> List[Dict]:
    """Create simple dialogue lines cycling through characters."""

    speakers = itertools.cycle(characters)
    lines: List[Dict] = []

    for i in range(1, turns + 1):
        speaker = next(speakers)
        text = f"This is line {i} about {topic}."
        duration = max(1.5, 0.15 * len(text.split()))

        lines.append(
            {
                "id": str(len(lines) + 1),
                "type": "dialogue",
                "character": speaker["name"],
                "traits": speaker["traits"],
                "emotion": "neutral",
                "text": text,
                "duration": round(duration, 2),
                "voice_url": "",
            }
        )

    return lines


def add_actions(dialogue: List[Dict], characters: List[Dict]) -> List[Dict]:
    """Attach a basic gesture action after each dialogue block."""

    actions: List[Dict] = []
    for idx, line in enumerate(dialogue, 1):
        actions.append(
            {
                "id": str(len(dialogue) + idx),
                "type": "action",
                "description": f"{line['character']} gestures while speaking.",
                "timing": "after",
            }
        )
    return actions


def structure_script(dialogue: List[Dict], actions: List[Dict]) -> List[Dict]:
    """Combine dialogue and action blocks into a single list."""

    return dialogue + actions


def run_pipeline(prompt: str) -> List[Dict]:
    """Execute the pipeline of agents to build a script."""

    meta = interpret_prompt(prompt)
    refs = web_search(meta["scene_topic"], meta["setting"])
    plan = plan_scene(meta, refs)
    dialogue = generate_dialogue(
        meta["characters"], plan["dialogue_turns"], meta["scene_topic"]
    )
    actions = add_actions(dialogue, meta["characters"])
    return structure_script(dialogue, actions)
