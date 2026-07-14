import asyncio

from telethon import events, functions

from .notifier import format_post, send_with_retry, split_title_body


def build_link(chat, message_id: int) -> str:
    username = getattr(chat, "username", None)
    if username:
        return f"https://t.me/{username}/{message_id}"
    chat_id = str(chat.id)
    if chat_id.startswith("-100"):
        chat_id = chat_id[4:]
    elif chat_id.startswith("-"):
        chat_id = chat_id[1:]
    return f"https://t.me/c/{chat_id}/{message_id}"


async def resolve_chats(client, channels, folder_names):
    entities = {}

    for ref in channels:
        entity = await client.get_entity(ref)
        entities[entity.id] = entity

    if folder_names:
        result = await client(functions.messages.GetDialogFiltersRequest())
        filters = getattr(result, "filters", result)
        for dialog_filter in filters:
            title = getattr(dialog_filter, "title", None)
            title_text = getattr(title, "text", title)
            if title_text not in folder_names:
                continue
            for peer in getattr(dialog_filter, "include_peers", []):
                try:
                    entity = await client.get_entity(peer)
                    entities[entity.id] = entity
                except Exception:
                    continue

    return list(entities.values())


class Monitor:
    def __init__(self, client, config, storage, ai_filter):
        self.client = client
        self.config = config
        self.storage = storage
        self.ai_filter = ai_filter
        self._queue: asyncio.Queue = asyncio.Queue()
        self._notify_entity = None
        self._worker_task = None

    async def setup(self):
        chats = await resolve_chats(self.client, self.config.channels, self.config.folders)
        if not chats:
            raise RuntimeError(
                "No channels/folders resolved - check the 'channels' and 'folders' "
                "entries in config.yaml"
            )

        self._notify_entity = await self.client.get_entity(self.config.notify_channel)
        self._worker_task = asyncio.create_task(self._worker())
        self.client.add_event_handler(self._enqueue, events.NewMessage(chats=chats))
        return chats

    async def _enqueue(self, event):
        await self._queue.put(event)

    async def _worker(self):
        while True:
            event = await self._queue.get()
            try:
                await self._process(event)
            except Exception as exc:
                print(f"[monitor] error processing message: {exc}")
            await asyncio.sleep(self.config.ai_rate_limit_seconds)

    async def _process(self, event):
        message = event.message
        chat = await event.get_chat()
        chat_title = getattr(chat, "title", None) or getattr(chat, "username", None) or str(chat.id)
        link = build_link(chat, message.id)
        text = message.message or ""

        self.storage.save_message(event.chat_id, message.id, chat_title, message.date, text, link)

        result = await self.ai_filter.evaluate(self.config.instruction, self.config.hashtags, text)
        if not result["match"]:
            return

        self.storage.save_match(event.chat_id, message.id, result["hashtag"], result["reasoning"])
        title, body = split_title_body(text)
        notification = format_post(result["hashtag"], title, body, message.date, link)
        await send_with_retry(self.client, self._notify_entity, notification)
