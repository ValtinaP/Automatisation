import asyncio

from telethon import TelegramClient

from src.ai_filter import AIFilter
from src.config import load_config
from src.db import Storage
from src.monitor import Monitor


async def run():
    config = load_config()

    client = TelegramClient(config.session_name, config.api_id, config.api_hash)
    storage = Storage()
    ai_filter = AIFilter(config.openrouter_api_key, config.openrouter_model)

    await client.start()  # prompts for phone/code/2FA on first run, reuses session after

    monitor = Monitor(client, config, storage, ai_filter)
    chats = await monitor.setup()
    print(f"Watching {len(chats)} chat(s). Press Ctrl+C to stop.")

    try:
        await client.run_until_disconnected()
    finally:
        await ai_filter.close()
        storage.close()


if __name__ == "__main__":
    asyncio.run(run())
