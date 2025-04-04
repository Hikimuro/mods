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
import logging
import aiohttp
from PIL import Image, ImageDraw
from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import ImageFormatter
from telethon.tl.types import Message
from .. import loader, utils

logger = logging.getLogger(__name__)

@loader.tds
class CarbonMod(loader.Module):
    """Создает симпатичные фотки кода. Поддержка API и локальной генерации"""

    strings = {
        "name": "Carbon",
        "args": "<emoji document_id=5312526098750252863>🚫</emoji> <b>No code specified!</b>",
        "loading": "<emoji document_id=5213452215527677338>⏳</emoji> <b>Loading...</b>",
        "api_error": "<b>API недоступен, используется локальная генерация.</b>",
    }

    strings_ru = {
        "_cls_doc": "Создает симпатичные фотки кода. С поддержкой локальной генерации",
        "args": "<emoji document_id=5312526098750252863>🚫</emoji> <b>Не указан код!</b>",
        "loading": "<emoji document_id=5213452215527677338>⏳</emoji> <b>Обработка...</b>",
        "api_error": "<b>API недоступен, используется локальная генерация.</b>",
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue("theme", "vsc-dark-plus", "Тема оформления"),
            loader.ConfigValue("color", "#2e3440", "Цвет фона (hex)"),
            loader.ConfigValue("language", "python", "Язык подсветки"),
            loader.ConfigValue("max_code_length_for_document", 1000, "Макс. длина кода для документа"),
            loader.ConfigValue("generation_mode", "auto", "Режим генерации: auto/api/local",
                               validator=loader.validators.Choice(["auto", "api", "local"]))
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

        loading = await utils.answer(message, self.strings("loading"))
        mode = self.config["generation_mode"]

        image = None

        if mode in ("api", "auto"):
            try:
                image = await self._generate_code_image(code)
            except aiohttp.ClientError:
                logger.warning("API недоступен")
                if mode == "auto":
                    await utils.answer(message, self.strings("api_error"))

        if image is None:
            image = self._generate_local_image(code)

        await self.client.send_file(
            utils.get_chat_id(message),
            file=image,
            force_document=self._should_send_as_document(code),
            reply_to=utils.get_topic(message) or await message.get_reply_message(),
        )
        await loading.delete()

    async def _get_code_from_media(self, message: Message) -> str:
        if not message or not getattr(message, "document", None):
            return ""

        if not message.document.mime_type.startswith("text/"):
            return ""

        try:
            return (await self._client.download_file(message.media, bytes)).decode("utf-8")
        except Exception as e:
            logger.exception("Ошибка при чтении файла: %s", e)
            return ""

    async def _generate_code_image(self, code: str) -> io.BytesIO:
        url = f'https://code2img.vercel.app/api/to-image?theme={self.config["theme"]}&language={self.config["language"]}&line-numbers=true&background-color={self.config["color"]}'
        headers = {"content-type": "text/plain"}

        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, data=code.encode("utf-8")) as response:
                if response.status != 200:
                    raise aiohttp.ClientError("Bad response from API")
                img_data = io.BytesIO(await response.read())
                img_data.name = "carbonized.jpg"
                return img_data

    def _generate_local_image(self, code: str) -> io.BytesIO:
        try:
            lexer = get_lexer_by_name(self.config["language"], stripall=True)
        except Exception:
            lexer = get_lexer_by_name("python")

        formatter = ImageFormatter(
            style="default",
            font_name="DejaVu Sans Mono",
            line_numbers=True,
            font_size=16,
            image_pad=10,
            line_pad=2,
            bg=self.config["color"]
        )

        img_data = io.BytesIO()
        try:
            highlight(code, lexer, formatter, img_data)
            img_data.seek(0)
            img_data.name = "local_carbon.png"
            return img_data
        except Exception as e:
            logger.exception("Ошибка локальной генерации: %s", e)
            fallback = Image.new("RGB", (800, 400), self.config["color"])
            draw = ImageDraw.Draw(fallback)
            draw.text((10, 10), "Ошибка генерации изображения", fill="white")
            output = io.BytesIO()
            fallback.save(output, format="PNG")
            output.name = "error.png"
            output.seek(0)
            return output

    def _should_send_as_document(self, code: str) -> bool:
        return len(code) > self.config["max_code_length_for_document"]
