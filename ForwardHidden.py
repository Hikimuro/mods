# ForwardHidden 
# meta developer: @Hikimuro
# ver. 1.0.1

from .. import loader, utils
import os

@loader.tds
class ForwardHiddenMod(loader.Module):
    """Копирование скрытых сообщений (даже с кнопками и медиа)"""
    strings = {
        "name": "ForwardHidden"
    }

    async def client_ready(self, client, db):
        self.client = client

    @loader.command()
    async def fh(self, message):
        """-fh <chat_id> <кол-во> — копировать сообщения в текущий чат"""
        args = utils.get_args(message)
        if len(args) < 2:
            return await utils.answer(message, "❗ Укажи chat_id и количество сообщений")

        chat_id = args[0]
        try:
            count = int(args[1])
        except ValueError:
            return await utils.answer(message, "❗ Количество должно быть числом")

        try:
            async for msg in self.client.iter_messages(chat_id, limit=count):
                file_path = None
                try:
                    if msg.media:
                        file_path = await self.client.download_media(msg)
                        if file_path:
                            await self.client.send_file(
                                message.chat_id,
                                file_path,
                                caption=msg.text or msg.message or "",
                                buttons=msg.buttons,
                                reply_to=message.reply_to_msg_id,
                            )
                    elif msg.text:
                        await self.client.send_message(
                            message.chat_id,
                            msg.text,
                            buttons=msg.buttons,
                            reply_to=message.reply_to_msg_id,
                        )
                finally:
                    if file_path and os.path.exists(file_path):
                        os.remove(file_path)
        except Exception as e:
            await utils.answer(message, f"❌ Ошибка: {e}")

    @loader.command()
    async def getid(self, message):
        """-getid [username или пусто] — получить chat_id канала, группы или чата"""
        args = utils.get_args(message)
        try:
            if args:
                entity = await self.client.get_entity(args[0])
            elif message.is_reply:
                entity = (await message.get_reply_message()).peer_id
            else:
                entity = await self.client.get_entity(message.chat_id)
            await utils.answer(message, f"🆔 ID: `{entity.id}`\nПолный ID: `{entity.id if str(entity.id).startswith('-100') else '-100' + str(entity.id)}`")
        except Exception as e:
            await utils.answer(message, f"❌ Не удалось получить ID\n{e}")

    @loader.command()
    async def listch(self, message):
        """-listch — показать список каналов и супергрупп, где ты подписан"""
        result = []
        async for dialog in self.client.iter_dialogs():
            if dialog.is_channel and not dialog.entity.broadcast:
                result.append(f"{dialog.name} — `{dialog.id}`")
        if result:
            await utils.answer(message, "\n".join(result))
        else:
            await utils.answer(message, "❗ Каналы не найдены")
