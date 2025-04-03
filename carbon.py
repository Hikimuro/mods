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

@loader.tds
class CarbonMod(loader.Module):
    """Create beautiful code images. Edited by @Hikimuro"""

    strings = {
        "name": "Carbon",
        "args": "🚫 <b>No code specified!</b>",
        "loading": "⏳ <b>Loading...</b>",
        "error": "❌ <b>Failed to generate image!</b>",
    }

    strings_ru = {
        "_cls_doc": "Создает красивые изображения кода. Отредактировано @Penggrin",
        "args": "🚫 <b>Не указан код!</b>",
        "loading": "⏳ <b>Обработка...</b>",
        "error": "❌ <b>Ошибка генерации изображения!</b>",
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue("theme", "vsc-dark-plus", "Theme", validator=loader.validators.String()),
            loader.ConfigValue("color", "gray", "Background color", validator=loader.validators.String()),
            loader.ConfigValue("language", "python", "Programming language", validator=loader.validators.String()),
        )

    @loader.command(ru_doc="<код> - Создать красивое изображение кода")
    async def carboncmd(self, message: Message):
        """<code> - Create a beautiful code image"""
        args = utils.get_args_raw(message)

        code = args or await self._extract_code_from_message(message)
        if not code:
            await utils.answer(message, self.strings("args"))
            return

        await utils.answer(message, self.strings("loading"))
        image = await self._generate_image(code)
        if not image:
            await utils.answer(message, self.strings("error"))
            return

        await self.client.send_file(
            utils.get_chat_id(message),
            file=image,
            force_document=(len(code.splitlines()) > 35),
            reply_to=await message.get_reply_message(),
        )
        await message.delete()

    async def _extract_code_from_message(self, message: Message) -> str:
        try:
            return (await self._client.download_file(message.media, bytes)).decode("utf-8")
        except Exception:
            try:
                reply = await message.get_reply_message()
                return (await self._client.download_file(reply.media, bytes)).decode("utf-8")
            except Exception:
                return ""

    async def _generate_image(self, code: str) -> io.BytesIO:
        try:
            response = await utils.run_sync(
                requests.post,
                f'https://code2img.vercel.app/api/to-image?theme={self.config["theme"]}&language={self.config["language"]}&line-numbers=true&background-color={self.config["color"]}',
                headers={"content-type": "text/plain"},
                data=code.encode("utf-8"),
            )
            image = io.BytesIO(response.content)
            image.name = "carbonized.jpg"
            return image
        except Exception:
            return None
