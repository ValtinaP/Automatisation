import json

import httpx

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

SYSTEM_PROMPT = (
    "You classify Telegram posts against a user's stated interest. "
    "Reply with ONLY a JSON object of the form "
    '{{"match": true|false, "reasoning": "<one short sentence>"}}. '
    "No markdown, no extra text.\n\n"
    "User's interest:\n{instruction}"
)


class AIFilter:
    def __init__(self, api_key: str, model: str):
        self._model = model
        self._client = httpx.AsyncClient(
            base_url="https://openrouter.ai/api/v1",
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=30.0,
        )

    async def evaluate(self, instruction: str, message_text: str) -> dict:
        if not message_text or not message_text.strip():
            return {"match": False, "reasoning": "empty message"}

        response = await self._client.post(
            "/chat/completions",
            json={
                "model": self._model,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT.format(instruction=instruction)},
                    {"role": "user", "content": message_text},
                ],
                "temperature": 0,
            },
        )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"].strip()

        try:
            parsed = json.loads(content)
            return {"match": bool(parsed.get("match")), "reasoning": str(parsed.get("reasoning", ""))}
        except (json.JSONDecodeError, KeyError):
            return {"match": False, "reasoning": f"unparsable model output: {content[:200]}"}

    async def close(self):
        await self._client.aclose()
