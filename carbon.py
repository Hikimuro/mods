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
import aiohttp
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
        code_sources = [
            utils.get_args_raw(message),
            await self._get_code_from_media(message),
            await self._get_code_from_media(await message.get_reply_message())
        ]
        code = next((c for c in code_sources if c), None)

        if not code:
            await utils.answer(message, self.strings("args"))
            return

        loading_message = await utils.answer(message, self.strings("loading"))
        doc = await self._generate_code_image(code)
        
        await self.client.send_file(
            utils.get_chat_id(message),
            file=doc,
            force_document=self._should_send_as_document(code),
            reply_to=utils.get_topic(message) or await message.get_reply_message(),
        )
        
        await loading_message.delete()

    async def _get_code_from_media(self, message: Message) -> str:
        """Получение кода из медиа-сообщения"""
        if not message or not getattr(message, "document", None):
            return ""
        
        if not message.document.mime_type.startswith("text/"):
            return ""
        
        try:
            return (await self._client.download_file(message.media, bytes)).decode("utf-8")
        except Exception:
            return ""

    async def _generate_code_image(self, code: str) -> io.BytesIO:
        """Генерация изображения с кодом (асинхронная версия)"""
        url = f'https://code2img.vercel.app/api/to-image?theme={self.config["theme"]}&language={self.config["language"]}&line-numbers=true&background-color={self.config["color"]}'
        headers = {"content-type": "text/plain"}

        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, data=code.encode("utf-8")) as response:
                if response.status != 200:
                    raise Exception("Ошибка запроса к API Code2Img")
                
                img_data = io.BytesIO(await response.read())
                img_data.name = "carbonized.jpg"
                return img_data

    def _should_send_as_document(self, code: str) -> bool:
        """Определяет, нужно ли отправить код как документ"""
        return len(code) > self.config["max_code_length_for_document"]
