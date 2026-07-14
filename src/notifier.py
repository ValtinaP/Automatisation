import asyncio

from telethon.errors import FloodWaitError


async def send_with_retry(client, entity, text: str):
    while True:
        try:
            await client.send_message(entity, text, link_preview=False)
            return
        except FloodWaitError as e:
            await asyncio.sleep(e.seconds + 1)


def split_title_body(text: str) -> tuple[str, str]:
    stripped = text.strip()
    if "\n" in stripped:
        title, rest = stripped.split("\n", 1)
        return title.strip(), rest.strip()
    return stripped, ""


def format_post(hashtag: str, title: str, body: str, posted_at, link: str) -> str:
    parts = []
    if hashtag:
        parts.append(hashtag)
    parts.append(title)
    if body:
        parts.append(body)
    parts.append(f"📅 {posted_at.strftime('%d.%m.%Y, %H:%M')}")
    parts.append(f"🔗 {link}")
    return "\n\n".join(parts)
