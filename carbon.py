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
from PIL import Image
from telethon.tl.types import Message
from .. import loader, utils

# Настройка логирования с фильтрацией повторений и уровнями
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)  # Уровень для продакшн-системы
console_handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

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
            loader.ConfigValue("background_image", "", "URL фона изображения (необязательно). faq: размер 1920х1080 загрузить изображение на imgur, далее открыть изображение в новом окне и скопировать ссылку(Телефон), нажать пкм на загруженное изображение и скопировать URL(Пк)", validator=loader.validators.String()),
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
            await loading_message.delete()

    async def _get_code_from_sources(self, message: Message) -> str:
        """Получение кода из различных источников"""
        code_sources = [
            utils.get_args_raw(message),
            await self._get_code_from_media(message),
            await self._get_code_from_media(await message.get_reply_message())
        ]
        return next((c for c in code_sources if c), None)

    async def _get_code_from_media(self, message: Message) -> str:
        """Получение кода из медиа-сообщения"""
        if not message or not getattr(message, "document", None):
            return ""

        if not message.document.mime_type.startswith("text/"):
            return ""

        try:
            return (await self.client.download_file(message.media, bytes)).decode("utf-8")
        except Exception as e:
            logger.warning(f"Ошибка при получении кода из медиа-сообщения. Сообщение: {message.id}, Ошибка: {str(e)}")
            return ""

    async def _generate_code_image(self, code: str) -> io.BytesIO:
        """Генерация изображения с кодом (асинхронная версия)"""
        url = f'https://code2img.vercel.app/api/to-image?theme={self.config["theme"]}&language={self.config["language"]}&line-numbers=true&background-color={self.config["color"]}'

        # Изменяем размер итогового изображения в зависимости от масштаба
        scale = self.config['scale']
        code_width, code_height = 1200 * scale, 536 * scale  # Применяем масштабирование

        # Если задан URL фона, скачиваем и масштабируем фон
        if self.config["background_image"]:
            background_image_url = self.config["background_image"]

            # Скачиваем изображение фона
            async with aiohttp.ClientSession() as session:
                try:
                    async with session.get(background_image_url) as response:
                        response.raise_for_status()  # Проверка на успешный ответ
                        img_data = io.BytesIO(await response.read())
                        background = Image.open(img_data)

                        # Масштабируем фон под размер итогового изображения
                        background = background.resize((code_width, code_height), Image.ANTIALIAS)

                        # Сохраняем результат в новый объект BytesIO
                        img_output = io.BytesIO()
                        background.save(img_output, format="JPEG")
                        img_output.seek(0)

                        # Преобразуем фон в байты для передачи в API
                        background_image_bytes = img_output.read()

                        # Сохраняем фон как временный файл
                        with open("temp_background.jpg", "wb") as f:
                            f.write(background_image_bytes)

                except Exception as e:
                    logger.error(f"Ошибка при загрузке или обработке фона: {str(e)}")
                    raise Exception(f"Ошибка при загрузке или обработке фона: {str(e)}")

            url += f"&background-image={background_image_url}"

        # Добавляем параметр scale
        url += f"&scale={self.config['scale']}"

        headers = {"content-type": "text/plain"}

        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(url, headers=headers, data=code.encode("utf-8")) as response:
                    response.raise_for_status()  # Автоматически выбросит исключение, если статус != 200
                    img_data = io.BytesIO(await response.read())
                    img_data.name = "carbonized.jpg"
                    return img_data
            except aiohttp.ClientError as e:
                logger.error("Ошибка запроса к API Code2Img: URL=%s, Ошибка: %s", url, str(e))
                raise Exception(f"Ошибка запроса к API Code2Img: {str(e)}")
            except Exception as e:
                logger.error(f"Неизвестная ошибка при генерации изображения: {str(e)}")
                raise Exception(f"Неизвестная ошибка при генерации изображения: {str(e)}")

    def _should_send_as_document(self, code: str) -> bool:
        """Определяет, нужно ли отправить код как документ"""
        return len(code) > self.config["max_code_length_for_document"]
