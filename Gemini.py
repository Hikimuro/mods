__version__ = (1, 0, 0)

# This file is a part of Hikka Userbot
# Code is NOT licensed under CC-BY-NC-ND 4.0 unless otherwise specified.
# 🌐 https://github.com/hikariatama/Hikka

# You CAN edit this file without direct permission from the author.
# You can redistribute this file with any modifications.

# edit by @Hikimuro

# meta developer: @yg_modules
# scope: hikka_only
# scope: hikka_min 1.6.3

# requires: google-generativeai pillow

import google.generativeai as genai
import os
from PIL import Image
import asyncio

from .. import loader, utils

@loader.tds
class gemini(loader.Module):
    """Модуль для общения с Gemini AI (асинхронно)"""

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
                "gemini-1.5-flash",
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
        """<reply to photo / text> — отправить запрос к Gemini.
Отредактировано @Hikimuro"""
        if not self.config["api_key"]:
            await message.edit(
                "<emoji document_id=5274099962655816924>❗️</emoji> <b>API ключ не указан. Получи его на aistudio.google.com/apikey и укажи в конфиге</b>"
            )
            return

        prompt = utils.get_args_raw(message)
        media_path = None
        img = None

        # Проверяем, если это ответ на сообщение с изображением
        if message.is_reply:
            reply = await message.get_reply_message()
            try:
                if hasattr(reply, "media") and reply.media and reply.photo:
                    await message.edit("<b><emoji document_id=5386367538735104399>⌛️</emoji> Загрузка фото...</b>")
                    media_path = await reply.download_media()
            except Exception:
                pass

        # Если есть изображение, загружаем и обрабатываем его
        if media_path:
            try:
                img = Image.open(media_path)
                img = img.convert("RGB")
                img.thumbnail((1024, 1024))  # Уменьшаем изображение до разумного размера
            except Exception as e:
                await message.edit(f"<emoji document_id=5274099962655816924>❗️</emoji> <b>Ошибка открытия изображения:</b> {e}")
                if os.path.exists(media_path):
                    os.remove(media_path)
                return

        # Если нет текста и нет изображения, просим пользователя предоставить информацию
        if not prompt and not img:
            await message.edit(
                "<emoji document_id=5274099962655816924>❗️</emoji> <i>Введи запрос или ответь на изображение</i>"
            )
            return

        # Формируем сообщение
        edit_message = (
            f"<emoji document_id=5443038326535759644>💬</emoji> <b>Вопрос:</b> {prompt}\n\n"
            if prompt else
            "<emoji document_id=5443038326535759644>💬</emoji> <b>Ответ от Gemini (по изображению):</b> <emoji document_id=4988080790286894217>🫥</emoji>"
        )
        await message.edit(edit_message)

        try:
            # Конфигурируем и создаем модель для генерации ответа
            genai.configure(api_key=self.config["api_key"])
            system_instruction = self.config["system_instruction"] or None
            model = genai.GenerativeModel(
                model_name=self.config["model_name"],
                system_instruction=system_instruction,
                safety_settings=self.safety_settings,
            )

            # Генерируем ответ с использованием изображения и/или текста
            if img:
                response = await asyncio.to_thread(model.generate_content, [prompt, img] if prompt else ["", img])
            else:
                response = await asyncio.to_thread(model.generate_content, [prompt])

            reply_text = response.text.strip()

            # Отправляем ответ
            await message.edit(
                f"<emoji document_id=5325547803936572038>✨</emoji> <b>Ответ от Gemini:</b> {reply_text}"
            )

        except Exception as e:
            await message.edit(f"<emoji document_id=5274099962655816924>❗️</emoji> <b>Ошибка:</b> {e}")

        finally:
            # Удаляем временный файл изображения, если он был загружен
            if media_path and os.path.exists(media_path):
                try:
                    os.remove(media_path)
                except Exception as e:
                    print(f"Ошибка при удалении изображения: {e}")
