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
import time
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
        self.cache_dir = "./carbon_cache"  # Директория для кеширования фоновых изображений
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)

        # Очистка старых кэшированных файлов при инициализации
        self.clear_old_cache(max_age_days=7)

        self.config = loader.ModuleConfig(
            loader.ConfigValue("theme", "vsc-dark-plus", "Тема оформления", validator=loader.validators.String()),
            loader.ConfigValue("color", "gray", "Цвет фона", validator=loader.validators.String()),
            loader.ConfigValue("language", "python", "Язык программирования", validator=loader.validators.String()),
            loader.ConfigValue("max_code_length_for_document", 1000, "Максимальная длина кода для отправки как документ", validator=loader.validators.Integer()),
            loader.ConfigValue("background_image", "", "URL фона изображения (необязательно).", validator=loader.validators.String()),
            loader.ConfigValue("scale", 3, "Коэффициент масштабирования (по умолчанию 3) (0-5)", validator=loader.validators.Integer())
        )

    def clear_old_cache(self, max_age_days=7, only_background=False):
        """Очистка кэшированных файлов, которые старше max_age_days дней.
        Если only_background=True, очищает только фоновые изображения.
        """
        current_time = time.time()
        for filename in os.listdir(self.cache_dir):
            file_path = os.path.join(self.cache_dir, filename)
            if os.path.isfile(file_path):
                if only_background and not filename.endswith('.jpg'):  # Для фона мы только ищем .jpg
                    continue
                file_age_days = (current_time - os.path.getmtime(file_path)) / (60 * 60 * 24)
                if file_age_days > max_age_days:
                    try:
                        os.remove(file_path)
                        logger.info(f"Удален устаревший файл: {file_path}")
                    except Exception as e:
                        logger.error(f"Ошибка при удалении файла {file_path}: {str(e)}")

    async def carboncmd(self, message: Message):
        """Создание изображения кода"""
        code = await self._get_code_from_sources(message)

        if not code:
            await utils.answer(message, self.strings("args"))
            return

        loading_message = await utils.answer(message, self.strings("loading"))
        try:
            doc = await self._generate_code_image(code)
            
            # Если код слишком длинный, отправляем как файл
            if len(code) > self.config["max_code_length_for_document"]:
                await self.client.send_file(
                    utils.get_chat_id(message),
                    file=doc,
                    force_document=True,
                    reply_to=utils.get_topic(message) or await message.get_reply_message(),
                )
            else:
                # Иначе отправляем изображение
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

            cache_path = os.path.join(self.cache_dir, "carbon_bg_cache.jpg")
            if not os.path.exists(cache_path):
                # Параллельная загрузка фона с проверкой статуса
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(background_url) as resp:
                            resp.raise_for_status()
                            if resp.status == 404:
                                raise Exception("Фоновое изображение не найдено.")
                            with open(cache_path, "wb") as f:
                                f.write(await resp.read())
                            logger.info(f"Фоновое изображение сохранено в кэш: {cache_path}")
                except aiohttp.ClientError as e:
                    logger.error("Ошибка при загрузке фона: %s", str(e))
                    raise Exception("Ошибка загрузки фонового изображения")
                except Exception as e:
                    logger.error("Неизвестная ошибка при загрузке фона: %s", str(e))
                    raise

            # Добавляем фоновое изображение как URL
            url += f"&background-image=file://{cache_path}"

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
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except ValueError:
            return False
