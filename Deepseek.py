__version__ = (1, 0, 0)

# This file is a part of Hikka Userbot
# Code is NOT licensed under CC-BY-NC-ND 4.0 unless otherwise specified.
# 🌐 https://github.com/hikariatama/Hikka

# You CAN edit this file without direct permission from the author.
# You can redistribute this file with any modifications.

# meta developer: @Hikimuro
# scope: hikka_only
# scope: hikka_min 1.6.3

# requires: deepseek pillow

import requests
import os
from PIL import Image
import io
import base64

from .. import loader, utils

@loader.tds
class DeepSeekModule(loader.Module):
    """Модуль для общения с DeepSeek AI через официальный API"""

    strings = {"name": "DeepSeek"}

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "api_key",
                "",
                "API ключ для DeepSeek AI",
                validator=loader.validators.Hidden(loader.validators.String()),
            ),
            loader.ConfigValue(
                "api_url",
                "https://api.deepseek.com/v1/generate",
                "URL эндпоинта DeepSeek AI",
                validator=loader.validators.String(),
            ),
            loader.ConfigValue(
                "system_instruction",
                "",
                "Инструкция для DeepSeek AI.",
                validator=loader.validators.String(),
            ),
            loader.ConfigValue(
                "proxy",
                "",
                "Прокси (http://<user>:<pass>@<proxy>:<port> или http://<proxy>:<port>)",
                validator=loader.validators.String(),
            ),
        )

    async def client_ready(self, client, db):
        self.client = client
        proxy = self.config["proxy"]
        if proxy:
            os.environ["http_proxy"] = proxy
            os.environ["https_proxy"] = proxy

    async def deepseekcmd(self, message):
        """<reply to photo / text> — отправить запрос к DeepSeek AI."""
        if not self.config["api_key"]:
            await message.edit(
                "<emoji document_id=5274099962655816924>❗️</emoji> <b>API ключ не указан. Получите его и укажите в конфиге.</b>"
            )
            return

        prompt = utils.get_args_raw(message)
        image_data = None

        if message.is_reply:
            reply = await message.get_reply_message()
            if reply.photo:
                await message.edit("<b><emoji document_id=5386367538735104399>⌛️</emoji> Загрузка фото...</b>")
                media_path = await reply.download_media()
                with Image.open(media_path) as img:
                    img = img.convert("RGB")
                    buffered = io.BytesIO()
                    img.save(buffered, format="JPEG")
                    image_data = base64.b64encode(buffered.getvalue()).decode()

        if not prompt and not image_data:
            await message.edit(
                "<emoji document_id=5274099962655816924>❗️</emoji> <i>Введите запрос или ответьте на изображение.</i>"
            )
            return

        headers = {
            "Authorization": f"Bearer {self.config['api_key']}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": "deepseek-1.0",
            "prompt": prompt,
            "image": image_data,
            "system_instruction": self.config["system_instruction"],
        }

        await message.edit("<b><emoji document_id=5386367538735104399>⌛️</emoji> Ожидание ответа от DeepSeek...</b>")

        try:
            response = requests.post(self.config["api_url"], json=payload, headers=headers)
            response.raise_for_status()
            result = response.json()
            reply_text = result.get("text", "").strip()

            if reply_text:
                await message.edit(
                    f"<emoji document_id=5325547803936572038>✨</emoji> <b>Ответ от DeepSeek:</b> {reply_text}"
                )
            else:
                await message.edit(
                    "<emoji document_id=5274099962655816924>❗️</emoji> <b>Пустой ответ от DeepSeek.</b>"
                )

        except requests.exceptions.RequestException as e:
            await message.edit(
                f"<emoji document_id=5274099962655816924>❗️</emoji> <b>Ошибка при запросе к DeepSeek API:</b> {e}"
            )
