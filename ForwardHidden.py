# 🔧 Module: ForwardHidden
# 👤 Developer: @Hikimuro
# 🧩 Version: 1.0.1

from telethon.tl.types import Message, Channel
from .. import loader, utils
import os

@loader.tds
class ForwardHiddenMod(loader.Module):
    strings = {"name": "ForwardHidden"}

    @loader.command()
    async def getid(self, message: Message):
        """[username или пусто] — получить chat_id канала, группы или чата"""
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
        ids = set()
        for d in dialogs:
            entity = d.entity
            if isinstance(entity, Channel) and (entity.megagroup or entity.broadcast):
                chat_id = entity.id
                if chat_id in ids:
                    continue
                ids.add(chat_id)

                title = entity.title or "—"
                lines.append(f"{title}\n🆔 <code>{chat_id}</code>\n")

        if not lines:
            await utils.answer(message, "❌ Не найдено каналов/супергрупп.")
            return

        text = "<b>📋 Каналы и супергруппы, где ты подписан:</b>\n\n" + "\n".join(lines)
        await utils.answer(message, text)

    @loader.command()
    async def fh(self, message: Message):
        """<chat_id> <кол-во> — копировать сообщения в текущий чат (обход запрета пересылки)"""
        args = utils.get_args_raw(message)
        if not args or len(args.split()) < 2:
            return await utils.answer(
                message,
                "<b>Использование:</b> <code>.fh 1655808918 20</code>\n"
                "❓ Чтобы узнать chat_id: используй .listch или .getid"
            )

        chat_id_str, count_str = args.split()
        try:
            count = int(count_str)
        except ValueError:
            return await utils.answer(message, "⚠️ Укажи число сообщений.")

        try:
            chat_id = int(chat_id_str)
        except Exception:
            try:
                entity = await message.client.get_entity(chat_id_str)
                chat_id = entity.id
            except Exception as e:
                return await utils.answer(message, f"❌ Не удалось получить chat_id: {e}")

        msgs = []
        try:
            async for msg in message.client.iter_messages(chat_id, limit=count):
                if msg.text or msg.media:
                    msgs.append(msg)
        except Exception as e:
            return await utils.answer(message, f"❌ Ошибка при получении сообщений: {e}")

        if not msgs:
            return await utils.answer(message, "❌ Нет сообщений.")

        await utils.answer(message, f"📤 Отправка {len(msgs)} сообщений...")

        for msg in reversed(msgs):
            text = msg.text or ""
            sender = await msg.get_sender()
            author = f"\n\n👤 <b>От:</b> {getattr(sender, 'first_name', 'неизвестно')}"

            try:
                if msg.media:
                    file_path = await message.client.download_media(msg.media)
                    await message.client.send_file(
                        message.chat_id,
                        file_path,
                        caption=text + author if text else author,
                    )
                    if file_path and os.path.exists(file_path):
                        os.remove(file_path)
                else:
                    await message.client.send_message(
                        message.chat_id,
                        text + author
                    )
            except Exception as e:
                await utils.answer(message, f"⚠️ Не удалось отправить сообщение: {e}")

        await utils.answer(message, "✅ Готово.")
