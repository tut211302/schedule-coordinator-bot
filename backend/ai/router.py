import json
import os
from typing import Any, Dict, Optional

from aiohttp import ClientSession


OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_ENDPOINT = "https://api.openai.com/v1/responses"


ROUTER_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["action", "confidence"],
    "properties": {
        "action": {
            "type": "string",
            "enum": [
                "start_poll",
                "add_candidate",
                "vote",
                "tally",
                "confirm",
                "cancel",
                "help",
                "connect_google",
                "find_restaurant",
                "clarify",
            ],
        },
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
        "params": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "topic": {"type": "string"},
                "candidate": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "date": {"type": "string", "description": "YYYY-MM-DD"},
                        "start_time": {"type": "string", "description": "HH:MM"},
                        "end_time": {"type": "string", "description": "HH:MM"},
                    },
                },
                "vote_index": {"type": "integer", "minimum": 1},
                "confirm_index": {"type": "integer", "minimum": 1},
                "date_range": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "start": {"type": "string", "description": "YYYY-MM-DD"},
                        "end": {"type": "string", "description": "YYYY-MM-DD"},
                    },
                },
                "time_window": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "start": {"type": "string", "description": "HH:MM"},
                        "end": {"type": "string", "description": "HH:MM"},
                    },
                },
                "restaurant": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "area": {"type": "string"},
                        "budget_min": {"type": "integer"},
                        "budget_max": {"type": "integer"},
                        "party_size": {"type": "integer"},
                        "genre": {"type": "string"},
                        "date": {"type": "string", "description": "YYYY-MM-DD"},
                        "start_time": {"type": "string", "description": "HH:MM"},
                        "end_time": {"type": "string", "description": "HH:MM"},
                        "time": {"type": "string", "description": "free text like 'night'"},
                    },
                },
                "clarify_question": {"type": "string"},
            },
        },
    },
}


SYSTEM_PROMPT = (
    "You are a routing engine for a LINE scheduling assistant.\n"
    "Given a user message and optional context, return JSON only.\n"
    "Pick the best action and extract parameters when possible.\n"
    "If required info is missing or ambiguous, set action=clarify and ask a question.\n"
    "Never include text outside the JSON output."
)


def build_router_input(
    message: str,
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    payload = {"message": message}
    if context:
        payload["context"] = context
    return payload


async def route_message(
    message: str,
    context: Optional[Dict[str, Any]] = None,
    model: Optional[str] = None,
) -> Dict[str, Any]:
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY is not configured")

    body = {
        "model": model or OPENAI_MODEL,
        "input": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": json.dumps(build_router_input(message, context), ensure_ascii=True),
            },
        ],
        "response_format": {
            "type": "json_schema",
            "json_schema": {
                "name": "line_router_output",
                "strict": True,
                "schema": ROUTER_SCHEMA,
            },
        },
    }
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }

    async with ClientSession() as session:
        async with session.post(OPENAI_ENDPOINT, headers=headers, json=body) as resp:
            if resp.status >= 400:
                error_body = await resp.text()
                raise RuntimeError(f"OpenAI API error {resp.status}: {error_body}")
            data = await resp.json()

    output_text = None
    for item in data.get("output", []):
        if item.get("type") == "message":
            for part in item.get("content", []):
                if part.get("type") == "output_text":
                    output_text = part.get("text")
                    break
    if not output_text:
        raise RuntimeError("OpenAI response missing output_text")

    return json.loads(output_text)
