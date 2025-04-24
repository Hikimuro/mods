__version__ = (1, 0, 2)

# This file is a part of Hikka Userbot
# edit by @Hikimuro

# meta developer: @yg_modules
# scope: hikka_only
# scope: hikka_min 1.6.3

# requires: google-generativeai pillow

import google.generativeai as genai
import os
from PIL import Image, ImageOps
import asyncio

from .. import loader, utils

@loader.tds
class gemini(loader.Module):
    """Модуль для общения с Gemini AI"""

    strings = {"name": "gemini"}

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "api_key",
                "",
                "API ключ для Gemini AI (aistudio.google.com/apikey)",
                validator=loader.validators.Hidden(loader.validators.String()),
            ),
            loader.ConfigValue(
                "model_name",
                "gemini-2.0-flash",
                "Модель для Gemini AI.",
                validator=loader.validators.String(),
            ),
            loader.ConfigValue(
                "system_instruction",
                "",
                "Инструкция для Gemini AI.",
                validator=loader.validators.String(),
            ),
            loader.ConfigValue(
                "proxy",
                "",
                "Прокси (http://<user>:<pass>@<proxy>:<port> или http://<proxy>:<port>)",
                validator=loader.validators.String(),
            ),
            loader.ConfigValue(
                "temperature",
                0.7,
                "Температура (от 0 до 1, влияет на креативность)",
                validator=loader.validators.Float(min=0.0, max=1.0),
            ),
            loader.ConfigValue(
                "top_p",
                0.95,
                "Top-p (от 0 до 1, контролирует случайность)",
                validator=loader.validators.Float(min=0.0, max=1.0),
            ),
            loader.ConfigValue(
                "top_k",
                40,
                "Top-k (целое число, контроль разнообразия)",
                validator=loader.validators.Integer(),
            ),
            loader.ConfigValue(
                "max_output_tokens",
                1024,
                "Максимум токенов в ответе",
                validator=loader.validators.Integer(),
            ),
        )

    async def client_ready(self, client, db):
        self.client = client
        self.safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
        ]

        proxy = self.config["proxy"]
        if proxy:
            os.environ["http_proxy"] = proxy
            os.environ["HTTP_PROXY"] = proxy
            os.environ["https_proxy"] = proxy
            os.environ["HTTPS_PROXY"] = proxy

    async def geminicmd(self, message):
        """<reply to photo / text> — отправить запрос к Gemini."""
        if not self.config["api_key"]:
            await message.edit(
                "<emoji document_id=5274099962655816924>❗️</emoji> <b>API ключ не указан. Получи его на aistudio.google.com/apikey и укажи в конфиге</b>"
            )
            return

        prompt = utils.get_args_raw(message)
        media_path = None
        img = None

        if message.is_reply:
            reply = await message.get_reply_message()
            try:
                if hasattr(reply, "media") and reply.media and reply.photo:
                    await message.edit("<b><emoji document_id=5386367538735104399>⌛️</emoji> Загрузка фото...</b>")
                    media_path = await reply.download_media()
            except Exception as e:
                await message.edit(f"<emoji document_id=5274099962655816924>❗️</emoji> <b>Ошибка загрузки изображения:</b> {e}")
                return

        if media_path:
            try:
                img = await asyncio.to_thread(Image.open, media_path)
                img = ImageOps.exif_transpose(img)
                img = img.convert("RGB")
                await asyncio.to_thread(img.thumbnail, (512, 512))
            except Exception as e:
                await message.edit(f"<emoji document_id=5274099962655816924>❗️</emoji> <b>Ошибка открытия изображения:</b> {e}")
                if os.path.exists(media_path):
                    os.remove(media_path)
                return

        if not prompt and not img:
            await message.edit(
                "<emoji document_id=5274099962655816924>❗️</emoji> <i>Введи запрос или ответь на изображение</i>"
            )
            return

        edit_message = (
            f"<emoji document_id=5443038326535759644>💬</emoji> <b>Вопрос:</b> {prompt}\n\n"
            if prompt else
            "<emoji document_id=5443038326535759644>💬</emoji> <b>Ответ от Gemini (по изображению):</b> <emoji document_id=4988080790286894217>🫥</emoji>"
        )
        await message.edit(edit_message)

        try:
            genai.configure(api_key=self.config["api_key"])
            system_instruction = self.config["system_instruction"] or None

            model = genai.GenerativeModel(
                model_name=self.config["model_name"],
                system_instruction=system_instruction,
                safety_settings=self.safety_settings,
                generation_config={
                    "temperature": self.config["temperature"],
                    "top_p": self.config["top_p"],
                    "top_k": self.config["top_k"],
                    "max_output_tokens": self.config["max_output_tokens"],
                },
            )

            if img:
                response = await asyncio.to_thread(model.generate_content, [prompt, img] if prompt else ["", img])
            else:
                response = await asyncio.to_thread(model.generate_content, [prompt])

            reply_text = response.text.strip()

            # Разбиваем длинный ответ на части
            max_length = 4096
            header = "<emoji document_id=5325547803936572038>✨</emoji> <b>Ответ от Gemini:</b>\n\n"
            parts = [reply_text[i:i + max_length - len(header)] for i in range(0, len(reply_text), max_length - len(header))]

            await message.edit(header + parts[0])
            for part in parts[1:]:
                await message.respond(part)

        except Exception as e:
            await message.edit(f"<emoji document_id=5274099962655816924>❗️</emoji> <b>Ошибка:</b> {e}")

        finally:
            if media_path and os.path.exists(media_path):
                try:
                    os.remove(media_path)
                except Exception as e:
                    print(f"Ошибка при удалении изображения: {e}")
