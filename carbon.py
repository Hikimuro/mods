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

# Настройка логирования
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
console_handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

@loader.tds
class CarbonMod(loader.Module):
    """Создает симпатичные фотки кода"""

    strings = {
        "name": "Carbon",
        "args": "<b>Не указан код!</b>",
        "loading": "<b>Обработка...</b>",
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue("theme", "vsc-dark-plus", "Тема оформления"),
            loader.ConfigValue("color", "gray", "Цвет фона"),
            loader.ConfigValue("language", "python", "Язык программирования"),
            loader.ConfigValue("background_image", "", "Фоновое изображение"),
            loader.ConfigValue("scale", 2, "Масштаб изображения"),
        )

    async def carboncmd(self, message: Message):
        """Создание изображения кода"""
        code = await self._get_code_from_sources(message)

        if not code:
            await utils.answer(message, self.strings["args"])
            return

        loading_message = await utils.answer(message, self.strings["loading"])
        try:
            doc = await self._generate_code_image(code)
            doc = await self._apply_background(doc)

            await self.client.send_file(
                utils.get_chat_id(message),
                file=doc,
                force_document=False,
                reply_to=utils.get_topic(message) or await message.get_reply_message(),
            )
        except Exception as e:
            logger.error(f"Ошибка при создании изображения: {str(e)}")
            await utils.answer(message, f"<b>Error: {str(e)}</b>")
        finally:
            await loading_message.delete()

    async def _generate_code_image(self, code: str) -> io.BytesIO:
        """Генерация изображения с кодом"""
        url = (
            f'https://code2img.vercel.app/api/to-image?theme={self.config["theme"]}'
            f'&language={self.config["language"]}&line-numbers=true'
            f'&background-color={self.config["color"]}&scale={self.config["scale"]}'
        )

        headers = {"content-type": "text/plain"}

        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, data=code.encode("utf-8")) as response:
                response.raise_for_status()
                img_data = io.BytesIO(await response.read())
                img_data.name = "carbonized.png"
                return img_data

    async def _apply_background(self, img_data: io.BytesIO) -> io.BytesIO:
        """Применение фонового изображения с полным вмещением"""
        background_url = self.config["background_image"]
        if not background_url:
            return img_data

        async with aiohttp.ClientSession() as session:
            async with session.get(background_url) as resp:
                background_data = io.BytesIO(await resp.read())
                background = Image.open(background_data).convert("RGBA")

        img_data.seek(0)
        img = Image.open(img_data).convert("RGBA")

        img_width, img_height = img.size
        bg_width, bg_height = background.size

        # Масштабируем фон так, чтобы он полностью умещался
        scale_factor = min(img_width / bg_width, img_height / bg_height)
        new_size = (int(bg_width * scale_factor), int(bg_height * scale_factor))

        background = background.resize(new_size, Image.Resampling.LANCZOS)
        final_image = Image.new("RGBA", (img_width, img_height), (0, 0, 0, 0))

        # Центрируем фон
        left = (img_width - new_size[0]) // 2
        top = (img_height - new_size[1]) // 2
        final_image.paste(background, (left, top))

        # Накладываем код поверх фона
        final_image.paste(img, (0, 0), img)

        output = io.BytesIO()
        final_image.save(output, format="PNG")
        output.seek(0)
        return output
