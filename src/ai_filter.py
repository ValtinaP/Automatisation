import json

import httpx

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

SYSTEM_PROMPT = (
    "You classify Telegram posts against a user's stated interest, and if the "
    "post matches, you assign exactly one hashtag from the allowed list below. "
    "Reply with ONLY a JSON object of the form "
    '{{"match": true|false, "hashtag": "<one tag from the list, or empty string '
    'if match is false>", "reasoning": "<one short sentence>"}}. '
    "No markdown, no extra text.\n\n"
    "User's interest:\n{instruction}\n\n"
    "Allowed hashtags:\n{hashtags}"
)


class AIFilter:
    def __init__(self, api_key: str, model: str):
        self._model = model
        self._client = httpx.AsyncClient(
            base_url="https://openrouter.ai/api/v1",
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=30.0,
        )

    async def evaluate(self, instruction: str, hashtags: list, message_text: str) -> dict:
        if not message_text or not message_text.strip():
            return {"match": False, "hashtag": "", "reasoning": "empty message"}

        system_prompt = SYSTEM_PROMPT.format(
            instruction=instruction,
            hashtags="\n".join(hashtags) if hashtags else "(none configured)",
        )
        response = await self._client.post(
            "/chat/completions",
            json={
                "model": self._model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message_text},
                ],
                "temperature": 0,
            },
        )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"].strip()

        try:
            parsed = json.loads(content)
            return {
                "match": bool(parsed.get("match")),
                "hashtag": str(parsed.get("hashtag", "")),
                "reasoning": str(parsed.get("reasoning", "")),
            }
        except (json.JSONDecodeError, KeyError):
            return {
                "match": False,
                "hashtag": "",
                "reasoning": f"unparsable model output: {content[:200]}",
            }

    async def close(self):
        await self._client.aclose()
