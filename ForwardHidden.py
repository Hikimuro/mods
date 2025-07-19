# 🔧 Module: ForwardHidden
# 👤 Developer: @Hikimuro
# 🧩 Version: 1.0.0

from telethon.tl.types import Message
from .. import loader, utils

@loader.tds
class ForwardHiddenMod(loader.Module):
    """
▫️ -fh <chat_id> <кол-во> — копировать сообщения в текущий чат
▫️ -getid [username или пусто] — получить chat_id канала, группы или чата
▫️ -listch — показать список каналов и супергрупп, где ты подписан
    """

    strings = {"name": "ForwardHidden"}

    @loader.command()
    async def getid(self, message: Message):
        """[username] — получить chat_id канала, группы или чата"""
        args = utils.get_args_raw(message)
        if args:
            try:
                entity = await message.client.get_entity(args)
            except Exception as e:
                return await utils.answer(message, f"❌ Не найдено: {e}")
        else:
            entity = await message.get_chat()

        chat_id = entity.id
        title = getattr(entity, "title", "—")
        await utils.answer(message, f"<b>🆔 chat_id:</b> <code>{chat_id}</code>\n<b>📛 Название:</b> {title}")

    @loader.command()
    async def listch(self, message: Message):
        """Показать список каналов и супергрупп, где ты подписан"""
        dialogs = await message.client.get_dialogs()
        lines = []
        for d in dialogs:
            entity = d.entity
            if getattr(entity, 'megagroup', False) or getattr(entity, 'broadcast', False):
                chat_id = entity.id
                title = entity.title or "—"
                lines.append(f"{title}\n🆔 <code>{chat_id}</code>\n")

        if not lines:
            await utils.answer(message, "❌ Не найдено каналов/супергрупп.")
            return

        text = "<b>📋 Каналы и супергруппы, где ты подписан:</b>\n\n" + "\n".join(lines)
        await utils.answer(message, text)

    @loader.command()
    async def fh(self, message: Message):
        """<chat_id> <кол-во> — копировать сообщения в текущий чат"""
        args = utils.get_args_raw(message)
        if not args or len(args.split()) < 2:
            return await utils.answer(
                message,
                "<b>Использование:</b> <code>.fh -1001234567890 20</code>\n"
                "❓ Чтобы узнать chat_id: используй .listch или .getid"
            )

        chat_id, count = args.split()
        try:
            count = int(count)
        except ValueError:
            return await utils.answer(message, "⚠️ Укажи число сообщений.")

        msgs = []
        async for msg in message.client.iter_messages(chat_id, limit=count):
            if msg.text or msg.media:
                msgs.append(msg)

        if not msgs:
            return await utils.answer(message, "❌ Нет сообщений.")

        await utils.answer(message, f"📤 Отправка {len(msgs)} сообщений...")

        for msg in reversed(msgs):
            text = msg.text or ""
            markup = msg.reply_markup
            sender = await msg.get_sender()
            author = f"\n\n👤 <b>От:</b> {getattr(sender, 'first_name', 'неизвестно')}"

            if msg.media:
                await message.client.send_file(
                    message.chat_id,
                    msg.media,
                    caption=text + author,
                    reply_markup=markup
                )
            else:
                await message.client.send_message(
                    message.chat_id,
                    text + author,
                    reply_markup=markup
                )

        await utils.answer(message, "✅ Готово.")
