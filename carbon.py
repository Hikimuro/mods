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
import logging
import os
from PIL import Image
from telethon.tl.types import Message
from .. import loader, utils

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)

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
            loader.ConfigValue("max_code_length_for_document", 1000, "Максимальная длина кода для отправки как документ", validator=loader.validators.Integer()),
            loader.ConfigValue("background_image", "", "URL фона изображения (необязательно).", validator=loader.validators.String()),
            loader.ConfigValue("scale", 3, "Коэффициент масштабирования (по умолчанию 3) (0-5)", validator=loader.validators.Integer())
        )

    async def carboncmd(self, message: Message):
        """Создание изображения кода"""
        code = await self._get_code_from_sources(message)

        if not code:
            await utils.answer(message, self.strings("args"))
            return

        if len(code) > self.config["max_code_length_for_document"]:
            await utils.answer(message, "<b>Код слишком длинный, не может быть отправлен как изображение.</b>")
            return

        loading_message = await utils.answer(message, self.strings("loading"))
        try:
            doc = await self._generate_code_image(code)
            await self.client.send_file(
                utils.get_chat_id(message),
                file=doc,
                force_document=self._should_send_as_document(code),
                reply_to=utils.get_topic(message) or await message.get_reply_message(),
            )
        except Exception as e:
            logger.exception("Ошибка при создании изображения для кода: %s", str(e))
            await utils.answer(message, f"<b>Error: {str(e)}</b>")
        finally:
            await loading_message.delete()

    async def _get_code_from_sources(self, message: Message) -> str:
        args = utils.get_args_raw(message)
        reply = await message.get_reply_message()
        media_code = await self._get_code_from_media(message)
        reply_code = await self._get_code_from_media(reply)
        return next((c for c in [args, media_code, reply_code] if c), None)

    async def _get_code_from_media(self, message: Message) -> str:
        if not message or not getattr(message, "document", None):
            return ""
        if not message.document.mime_type.startswith("text/"):
            return ""
        try:
            return (await self.client.download_file(message.media, bytes)).decode("utf-8")
        except Exception as e:
            logger.warning("Ошибка при получении кода из медиа. ID=%s Ошибка=%s", message.id, str(e))
            return ""

    async def _generate_code_image(self, code: str) -> io.BytesIO:
        url = f'https://code2img.vercel.app/api/to-image?theme={self.config["theme"]}&language={self.config["language"]}&line-numbers=true&background-color={self.config["color"]}&scale={self.config["scale"]}'

        background_url = self.config["background_image"]
        if background_url:
            if not self._is_valid_url(background_url):
                raise ValueError(f"Некорректный URL фона: {background_url}")
            
            cache_path = ".carbon_bg_cache.jpg"
            if not os.path.exists(cache_path):
                async with aiohttp.ClientSession() as session:
                    try:
                        async with session.get(background_url) as resp:
                            resp.raise_for_status()
                            with open(cache_path, "wb") as f:
                                f.write(await resp.read())
                    except Exception as e:
                        logger.error("Не удалось загрузить фон: %s", str(e))
                        raise Exception("Ошибка загрузки фонового изображения")
            url += f"&background-image={background_url}"

        headers = {"content-type": "text/plain"}
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(url, headers=headers, data=code.encode("utf-8")) as resp:
                    resp.raise_for_status()
                    img_data = io.BytesIO(await resp.read())
                    img_data.name = "carbonized.jpg"
                    return img_data
            except aiohttp.ClientError as e:
                logger.error("Ошибка API Code2Img: %s", str(e))
                raise Exception("Ошибка API Code2Img")
            except Exception as e:
                logger.error("Ошибка генерации изображения: %s", str(e))
                raise Exception("Неизвестная ошибка генерации изображения")

    def _should_send_as_document(self, code: str) -> bool:
        return len(code) > self.config["max_code_length_for_document"]

    def _is_valid_url(self, url: str) -> bool:
        """Проверка URL на корректность"""
        import re
        regex = re.compile(
            r'^(?:http|ftp)s?://' # Протокол
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' # Домен
            r'localhost|' # Локальный хост
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|' # IP
            r'?[A-F0-9]*:[A-F0-9:]+?)' # IPv6
            r'(?::\d+)?' # Порт
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        return re.match(regex, url) is not None
