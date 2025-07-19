# 🔧 Module: ForwardHidden
# 👤 Developer: @Hikimuro
# 🧩 Version: 1.0.0

from telethon.tl.types import Message
from .. import loader, utils

@loader.tds
class ForwardHiddenMod(loader.Module):
    """Копирует сообщения из чатов с запретом пересылки (включая кнопки и медиа)

    📌 Команды:
    .fh <chat_id> <кол-во> — копировать <кол-во> сообщений из <chat_id> в текущий чат
    """

    strings = {"name": "ForwardHidden"}

    @loader.command()
    async def fh(self, message: Message):
        """<chat_id> <кол-во> — копировать сообщения в текущий чат"""
        args = utils.get_args_raw(message)
        if not args or len(args.split()) < 2:
            return await utils.answer(
                message,
                "<b>Пример:</b> <code>.fh -1001234567890 20</code>\n"
                "Скопирует 20 сообщений из указанного чата."
            )

        chat_id, count = args.split()
        try:
            count = int(count)
        except ValueError:
            return await utils.answer(message, "⚠️ Укажи число сообщений.")

        msgs = []
        async for msg in message.client.iter_messages(int(chat_id), limit=count):
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
