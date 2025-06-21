"""Multi-agent scene generation helpers."""

import os
import itertools
from typing import List, Dict
import json
import requests
import openai

# Placeholder environment variables for API keys
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
LETTA_API_KEY = os.getenv("LETTA_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

openai.api_key = GROQ_API_KEY or OPENAI_API_KEY
if GROQ_API_KEY:
    openai.api_base = "https://api.groq.com/openai/v1"
elif OPENAI_API_KEY:
    openai.api_base = "https://api.openai.com/v1"


def call_llm(messages: List[Dict], model: str = "gpt-3.5-turbo", max_tokens: int = 256) -> str:
    """Query whichever LLM provider is configured."""

    if GROQ_API_KEY or OPENAI_API_KEY:
        response = openai.ChatCompletion.create(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
        )
        return response.choices[0].message["content"].strip()

    if ANTHROPIC_API_KEY:
        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01",
        }
        payload = {
            "model": model,
            "max_tokens": max_tokens,
            "messages": [
                {"role": m["role"], "content": m["content"]} for m in messages
            ],
        }
        r = requests.post(url, headers=headers, json=payload, timeout=30)
        r.raise_for_status()
        data = r.json()
        if data.get("content"):
            return data["content"][0]["text"].strip()

    raise RuntimeError("No LLM API key configured")


def interpret_prompt(prompt: str) -> Dict:
    """Parse the user prompt to determine topic, setting and characters."""

    if GROQ_API_KEY or OPENAI_API_KEY or ANTHROPIC_API_KEY:
        messages = [
            {
                "role": "system",
                "content": (
                    "Extract scene metadata from the user prompt. "
                    "Respond in JSON with keys: scene_topic, setting, "
                    "scene_type, characters (list of {name, role, traits})."
                ),
            },
            {"role": "user", "content": prompt},
        ]
        try:
            content = call_llm(messages)
            data = json.loads(content)
            return data
        except Exception:
            pass

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
    """Search the web for background information."""

    query = f"{scene_topic} {setting}".strip()
    if LETTA_API_KEY:
        url = "https://api.letta.ai/v1/search"
        headers = {"Authorization": f"Bearer {LETTA_API_KEY}"}
        try:
            resp = requests.get(url, params={"q": query, "n": 3}, headers=headers, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            refs = [r.get("snippet", r.get("title", "")) for r in data.get("results", [])]
            images = [i.get("url") for i in data.get("images", [])]
            return {"references": refs, "images": images}
        except Exception:
            pass

    return {
        "references": [
            f"Facts about {scene_topic} gleaned from a web search.",
            f"Information about {setting} for background."
        ],
        "images": [],
    }


def plan_scene(metadata: Dict, references: Dict) -> Dict:
    """Create a lightweight scene plan based on metadata."""

    if GROQ_API_KEY or OPENAI_API_KEY or ANTHROPIC_API_KEY:
        prompt = (
            "Using the following metadata and references, create a concise JSON\n"
            "with keys: scene_title, background, flow (list), dialogue_turns,\n"
            "camera_plan (list).\n"
            f"Metadata: {json.dumps(metadata)}\n"
            f"References: {json.dumps(references)}"
        )
        messages = [{"role": "user", "content": prompt}]
        try:
            response = call_llm(messages)
            data = json.loads(response)
            return data
        except Exception:
            pass

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

    if GROQ_API_KEY or OPENAI_API_KEY or ANTHROPIC_API_KEY:
        names = ", ".join(c["name"] for c in characters)
        prompt = (
            "Generate {turns} short dialogue lines about '{topic}'. "
            "Cycle through the following characters: {names}. "
            "Return JSON list with fields id, type='dialogue', character, text, duration.".format(
                turns=turns, topic=topic, names=names
            )
        )
        messages = [{"role": "user", "content": prompt}]
        try:
            content = call_llm(messages, max_tokens=turns * 40)
            data = json.loads(content)
            return data
        except Exception:
            pass

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
