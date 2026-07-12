import asyncio

from telethon.errors import FloodWaitError


async def send_with_retry(client, entity, text: str):
    while True:
        try:
            await client.send_message(entity, text, link_preview=False)
            return
        except FloodWaitError as e:
            await asyncio.sleep(e.seconds + 1)


def format_match(chat_title: str, link: str, text: str, reasoning: str) -> str:
    snippet = text.strip()
    if len(snippet) > 500:
        snippet = snippet[:500] + "..."
    return (
        f"🔔 Совпадение: {chat_title}\n"
        f"{link}\n\n"
        f"{snippet}\n\n"
        f"AI: {reasoning}"
    )
