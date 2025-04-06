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
from urllib.parse import urlparse
import asyncio

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

        loading_message = await utils.answer(message, self.strings("loading"))
        try:
            doc = await self._generate_code_image(code)
            
            if len(code) > self.config["max_code_length_for_document"]:
                await self.client.send_file(
                    utils.get_chat_id(message),
                    file=doc,
                    force_document=True,
                    reply_to=utils.get_topic(message) or await message.get_reply_message(),
                )
            else:
                await self.client.send_file(
                    utils.get_chat_id(message),
                    file=doc,
                    force_document=self._should_send_as_document(code),
                    reply_to=utils.get_topic(message) or await message.get_reply_message(),
                )
        except Exception as e:
            logger.error(f"Ошибка при создании изображения для кода: {str(e)}")
            await utils.answer(message, f"<b>Error: {str(e)}</b>")
        finally:
            if loading_message:
                await loading_message.delete()

    async def _get_code_from_sources(self, message: Message) -> str:
        args = utils.get_args_raw(message)
        reply = await message.get_reply_message()
        code_from_message = args if args else (reply.text if reply else "")
        
        if not code_from_message and reply:
            code_from_message = reply.text

        return code_from_message

    async def _generate_code_image(self, code: str) -> io.BytesIO:
        url = f'https://code2img.vercel.app/api/to-image?theme={self.config["theme"]}&language={self.config["language"]}&line-numbers=true&background-color={self.config["color"]}&scale={self.config["scale"]}'

        background_url = self.config["background_image"]
        if background_url:
            if not self._is_valid_url(background_url):
                raise ValueError(f"Некорректный URL фона: {background_url}")
            background_image = await self._download_and_resize_background(background_url, code)
            # Вставляем фоновое изображение
            url += f"&background-image={background_image}"

        headers = {"content-type": "text/plain"}
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(url, headers=headers, data=code.encode("utf-8")) as resp:
                    resp.raise_for_status()
                    img_data = io.BytesIO(await resp.read())
                    img_data.name = "carbonized.jpg"
                    return img_data
            except aiohttp.ClientError as e:
                logger.error(f"Ошибка API Code2Img: {str(e)}")
                raise Exception("Ошибка API Code2Img")
            except Exception as e:
                logger.error(f"Ошибка генерации изображения: {str(e)}")
                raise Exception("Неизвестная ошибка генерации изображения")

    async def _download_and_resize_background(self, url: str, code: str) -> str:
        """Загрузка и изменение размера фонового изображения, если необходимо"""
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                resp.raise_for_status()
                img_data = io.BytesIO(await resp.read())
                img_data.seek(0)

                # Загружаем фоновое изображение с помощью PIL
                background = Image.open(img_data)
                width, height = background.size

                # Расчитаем необходимую высоту фона на основе количества строк
                lines = code.split("\n")
                max_height = 1080  # Максимальная высота
                required_height = len(lines) * 15  # Высота строки (например, 15px на строку)

                # Если размер фона меньше требуемого, увеличиваем его
                if required_height > max_height:
                    scale_factor = required_height / height
                    new_width = int(width * scale_factor)
                    new_height = int(height * scale_factor)

                    # Растягиваем фон
                    background = background.resize((new_width, new_height), Image.ANTIALIAS)
                
                # Сохраняем измененное фоновое изображение в буфер
                buffer = io.BytesIO()
                background.save(buffer, format="JPEG")
                buffer.seek(0)
                return buffer

    def _should_send_as_document(self, code: str) -> bool:
        return len(code) > self.config["max_code_length_for_document"]

    def _is_valid_url(self, url: str) -> bool:
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except ValueError:
            return False
