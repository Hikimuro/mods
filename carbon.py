#             █ █ ▀ █▄▀ ▄▀█ █▀█ ▀
#             █▀█ █ █ █ █▀█ █▀▄ █
#              © Copyright 2022
#           https://t.me/hikariatama
#
# 🔒      Licensed under the GNU AGPLv3
# 🌐 https://www.gnu.org/licenses/agpl-3.0.html

# edited by @Hikimuro

# meta pic: https://img.icons8.com/stickers/500/000000/code.png
# meta banner: https://mods.hikariatama.ru/badges/carbon.jpg
# meta developer: @hikarimods
# scope: hikka_only
# scope: hikka_min 1.2.10
# requires: urllib requests

import io
import requests
from telethon.tl.types import Message
from .. import loader, utils
from PIL import Image

# Принудительная замена ANTIALIAS на LANCZOS, независимо от наличия ANTIALIAS
Image.ANTIALIAS = Image.LANCZOS


@loader.tds
class CarbonMod(loader.Module):
    """Create beautiful code images. Edited by @Penggrin"""

    strings = {
        "name": "Carbon",
        "args": "<emoji document_id=5312526098750252863>🚫</emoji> <b>No code specified!</b>",
        "loading": "<emoji document_id=5213452215527677338>⏳</emoji> <b>Loading...</b>",
    }

    strings_ru = {
        "_cls_doc": "Создает симпатичные фотки кода. Отредактировано @Penggrin",
        "args": "<emoji document_id=5312526098750252863>🚫</emoji> <b>Не указан код!</b>",
        "loading": "<emoji document_id=5213452215527677338>⏳</emoji> <b>Обработка...</b>",
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "theme",
                "vsc-dark-plus",
                "Theme from clck.ru/33HUNM",
                validator=loader.validators.String()
            ),
            loader.ConfigValue(
                "color",
                "gray",
                "Background color",
                validator=loader.validators.String()
            ),
            loader.ConfigValue(
                "language",
                "python",
                "Programming language",
                validator=loader.validators.String()
            ),
        )

    @loader.command(ru_doc="<код> - Сделать красивую фотку кода")
    async def carboncmd(self, message: Message):
        """<code> - Create beautiful code image"""
        args = utils.get_args_raw(message)

        # Попытка получить код из вложенного сообщения или из ответа
        try:
            code_from_message = (
                await self._client.download_file(message.media, bytes)
            ).decode("utf-8")
        except Exception:
            code_from_message = ""

        try:
            reply = await message.get_reply_message()
            code_from_reply = (
                await self._client.download_file(reply.media, bytes)
            ).decode("utf-8")
        except Exception:
            code_from_reply = ""

        # Если аргументы не были найдены, используем сообщение или ответ
        args = args or code_from_message or code_from_reply

        if not args:
            await utils.answer(message, self.strings("args"))
            return

        # Ответ с текстом "Loading..." во время обработки
        message = await utils.answer(message, self.strings("loading"))

        # Получение изображения с сайта
        doc = io.BytesIO(
            (
                await utils.run_sync(
                    requests.post,
                    f'https://code2img.vercel.app/api/to-image?theme={self.config["theme"]}&language={self.config["language"]}&line-numbers=true&background-color={self.config["color"]}',
                    headers={"content-type": "text/plain"},
                    data=bytes(args, "utf-8"),
                )
            ).content
        )
        doc.name = "carbonized.jpg"

        reply = utils.get_topic(message) or await message.get_reply_message()

        # Если длина сообщения больше 150 символов, отправляем как файл
        if len(args) > 150:
            await self.client.send_file(
                utils.get_chat_id(message),
                file=doc,
                force_document=True,
                reply_to=reply,
            )
        else:
            # Иначе отправляем изображение как фото
            await self.client.send_file(
                utils.get_chat_id(message),
                file=doc,
                reply_to=reply,
            )

        # Удаляем сообщение о загрузке
        await message.delete()
