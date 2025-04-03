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
from PIL import Image
from telethon.tl.types import Message
from .. import loader, utils

# Принудительная замена ANTIALIAS на LANCZOS, независимо от наличия ANTIALIAS
Image.ANTIALIAS = Image.LANCZOS

@loader.tds
class CarbonMod(loader.Module):
    """Создает симпатичные фотки кода. Отредактировано @Hikimuro"""

    strings = {
        "name": "Carbon",
        "args": "<emoji document_id=5312526098750252863>🚫</emoji> <b>No code specified!</b>",
        "loading": "<emoji document_id=5213452215527677338>⏳</emoji> <b>Loading...</b>",
    }

    strings_ru = {
        "_cls_doc": "Создает симпатичные фотки кода. Отредактировано @Hikimuro",
        "args": "<emoji document_id=5312526098750252863>🚫</emoji> <b>Не указан код!</b>",
        "loading": "<emoji document_id=5213452215527677338>⏳</emoji> <b>Обработка...</b>",
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue("theme", "vsc-dark-plus", "Тема оформления", validator=loader.validators.String()),
            loader.ConfigValue("color", "gray", "Цвет фона", validator=loader.validators.String()),
            loader.ConfigValue("language", "python", "Язык программирования", validator=loader.validators.String()),
            loader.ConfigValue("max_code_length_for_document", 1000, "Максимальная длина кода для отправки как документ", validator=loader.validators.Integer())
        )

    async def carboncmd(self, message: Message):
        """Создание изображения кода"""
        args = utils.get_args_raw(message)

        # Попытка получить код из вложений сообщения или ответа
        code_from_message = await self._get_code_from_media(message)
        code_from_reply = await self._get_code_from_media(await message.get_reply_message())

        # Если код не передан через аргументы, используем код из вложений
        args = args or code_from_message or code_from_reply

        if not args:
            await utils.answer(message, self.strings("args"))
            return

        # Отправляем сообщение "Loading..." во время обработки
        message = await utils.answer(message, self.strings("loading"))

        # Запрашиваем изображение с сайта
        doc = await self._generate_code_image(args)

        # Получаем информацию о том, нужно ли отправить как документ
        force_document = len(args) > self.config["max_code_length_for_document"]
        reply = utils.get_topic(message) or await message.get_reply_message()

        # Отправляем изображение как файл
        await self.client.send_file(
            utils.get_chat_id(message),
            file=doc,
            force_document=force_document,
            reply_to=reply,
        )

        # Удаляем сообщение с текстом "Loading..."
        await message.delete()

    async def _get_code_from_media(self, message: Message) -> str:
        """Получение кода из медиа-сообщения"""
        try:
            return (await self._client.download_file(message.media, bytes)).decode("utf-8")
        except Exception:
            return ""

    async def _generate_code_image(self, code: str) -> io.BytesIO:
        """Генерация изображения с кодом"""
        response = await utils.run_sync(
            requests.post,
            f'https://code2img.vercel.app/api/to-image?theme={self.config["theme"]}&language={self.config["language"]}&line-numbers=true&background-color={self.config["color"]}',
            headers={"content-type": "text/plain"},
            data=bytes(code, "utf-8")
        )
        img_data = io.BytesIO(response.content)
        img_data.name = "carbonized.jpg"
        return img_data
