# -*- coding: utf-8 -*-

# Module: ForwardHidden  
# Description: Модуль для пересылки/копирования сообщений из каналов
# Author: @your_username

import logging
import os
import asyncio
import tempfile
from telethon import errors
from telethon.tl.types import Message, MessageMediaPhoto, MessageMediaDocument
from telethon.tl.types import DocumentAttributeFilename

from .. import loader, utils

logger = logging.getLogger(__name__)

@loader.tds
class ForwardHiddenMod(loader.Module):
    """Модуль для пересылки сообщений из каналов с обходом защиты"""
    
    strings = {
        "name": "ForwardHidden",
        "help": "❓ <b>Использование:</b> <code>.fh {chat_id} {количество}</code>\n❓ <b>Чтобы узнать chat_id:</b> используй <code>.listch</code> или <code>.getid</code>",
        "invalid_args": "❌ <b>Неверные аргументы!</b>\n\n{help}",
        "invalid_count": "❌ <b>Количество должно быть от 1 до 50</b>",
        "chat_not_found": "❌ <b>Не удалось найти чат</b>",
        "no_messages": "❌ <b>Не найдено сообщений для пересылки</b>",
        "processing": "⏳ <b>Обрабатываю сообщения...</b>",
        "success": "✅ <b>Готово!</b> Обработано: <code>{}</code> сообщений",
        "error": "❌ <b>Ошибка:</b> <code>{}</code>"
    }

    def __init__(self):
        self.temp_dir = None

    async def client_ready(self, client, db):
        """Инициализация модуля"""
        self.client = client
        self.db = db
        # Создаем временную директорию для файлов
        self.temp_dir = tempfile.mkdtemp(prefix="fh_temp_")
        logger.info(f"Временная папка создана: {self.temp_dir}")

    async def download_and_save(self, message, index):
        """Скачивает и сохраняет медиа на сервер"""
        try:
            saved_items = []
            
            if message.media:
                if isinstance(message.media, MessageMediaPhoto):
                    # Фотография
                    filename = f"photo_{index}.jpg"
                    filepath = os.path.join(self.temp_dir, filename)
                    await self.client.download_media(message, file=filepath)
                    saved_items.append({
                        'type': 'photo',
                        'path': filepath,
                        'caption': message.text or ""
                    })
                
                elif isinstance(message.media, MessageMediaDocument):
                    # Документ/видео/файл
                    doc = message.media.document
                    
                    # Получаем оригинальное имя файла
                    original_name = f"file_{index}"
                    for attr in doc.attributes:
                        if isinstance(attr, DocumentAttributeFilename):
                            name, ext = os.path.splitext(attr.file_name)
                            original_name = f"{name}_{index}{ext}"
                            break
                    else:
                        # Определяем расширение по MIME типу
                        if doc.mime_type:
                            if "video" in doc.mime_type:
                                original_name = f"video_{index}.mp4"
                            elif "audio" in doc.mime_type:
                                original_name = f"audio_{index}.mp3"
                            elif "image" in doc.mime_type:
                                original_name = f"image_{index}.jpg"
                            else:
                                original_name = f"file_{index}.bin"
                    
                    filepath = os.path.join(self.temp_dir, original_name)
                    await self.client.download_media(message, file=filepath)
                    saved_items.append({
                        'type': 'document', 
                        'path': filepath,
                        'caption': message.text or ""
                    })
            
            elif message.text:
                # Только текст
                saved_items.append({
                    'type': 'text',
                    'text': message.text
                })
            
            return saved_items
            
        except Exception as e:
            logger.error(f"Ошибка скачивания сообщения {index}: {e}")
            # В крайнем случае сохраняем текст
            if message.text:
                return [{'type': 'text', 'text': message.text}]
            return []

    async def send_saved_content(self, saved_items, target_chat):
        """Отправляет сохраненный контент"""
        sent_count = 0
        
        for item in saved_items:
            try:
                if item['type'] == 'text':
                    await self.client.send_message(target_chat, item['text'])
                    sent_count += 1
                
                elif item['type'] in ['photo', 'document']:
                    if os.path.exists(item['path']):
                        await self.client.send_file(
                            target_chat,
                            item['path'],
                            caption=item['caption'] if item['caption'] else ""
                        )
                        sent_count += 1
                        
                        # Удаляем файл после отправки
                        try:
                            os.remove(item['path'])
                        except:
                            pass
                
                # Пауза между отправками
                await asyncio.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Ошибка отправки: {e}")
                continue
        
        return sent_count

    @loader.command()
    async def fh(self, message: Message):
        """<chat_id> <количество> — пересылка последних N сообщений из канала"""
        args = utils.get_args_raw(message)
        
        if not args:
            await utils.answer(message, self.strings["invalid_args"].format(help=self.strings["help"]))
            return
        
        try:
            parts = args.split()
            if len(parts) != 2:
                await utils.answer(message, self.strings["invalid_args"].format(help=self.strings["help"]))
                return
            
            chat_id = parts[0]
            
            try:
                count = int(parts[1])
            except ValueError:
                await utils.answer(message, self.strings["invalid_args"].format(help=self.strings["help"]))
                return
            
            if count <= 0 or count > 50:
                await utils.answer(message, self.strings["invalid_count"])
                return
            
            # Показываем статус
            status_msg = await utils.answer(message, self.strings["processing"])
            
            # Получаем исходный чат
            try:
                if chat_id.isdigit() or chat_id.startswith('-'):
                    source_chat = await self.client.get_entity(int(chat_id))
                else:
                    source_chat = await self.client.get_entity(chat_id)
            except Exception as e:
                await utils.answer(status_msg, self.strings["chat_not_found"])
                logger.error(f"Чат не найден: {e}")
                return
            
            # Собираем сообщения
            messages = []
            async for msg in self.client.iter_messages(source_chat, limit=count):
                if msg and (msg.text or msg.media):
                    messages.append(msg)
            
            if not messages:
                await utils.answer(status_msg, self.strings["no_messages"])
                return
            
            # Обращаем порядок для хронологии
            messages.reverse()
            
            # Скачиваем и сохраняем все файлы
            all_saved_items = []
            for i, msg in enumerate(messages, 1):
                saved_items = await self.download_and_save(msg, i)
                all_saved_items.extend(saved_items)
                await asyncio.sleep(0.1)
            
            # Отправляем сохраненные файлы
            sent_count = await self.send_saved_content(all_saved_items, message.chat_id)
            
            # Результат
            await utils.answer(status_msg, self.strings["success"].format(sent_count))
            
        except Exception as e:
            logger.error(f"Общая ошибка fh: {e}")
            await utils.answer(message, self.strings["error"].format(str(e)))

    @loader.command()
    async def listch(self, message: Message):
        """— показать список всех каналов и супергрупп, включая закрытые"""
        try:
            dialogs = await self.client.get_dialogs(limit=50)
            
            result = "<b>📋 Список доступных чатов:</b>\n\n"
            
            channels = []
            groups = []
            
            for dialog in dialogs:
                entity = dialog.entity
                chat_id = entity.id
                
                if hasattr(entity, 'broadcast') and entity.broadcast:
                    # Канал
                    protected = "🔒" if getattr(entity, 'noforwards', False) else ""
                    channels.append(f"📢 <code>{chat_id}</code> - {entity.title} {protected}")
                elif hasattr(entity, 'megagroup') or hasattr(entity, 'title'):
                    # Группа/супергруппа
                    protected = "🔒" if getattr(entity, 'noforwards', False) else ""
                    title = getattr(entity, 'title', 'Без названия')
                    groups.append(f"👥 <code>{chat_id}</code> - {title} {protected}")
            
            if channels:
                result += "<b>📢 Каналы:</b>\n" + "\n".join(channels[:20]) + "\n\n"
            
            if groups:  
                result += "<b>👥 Группы:</b>\n" + "\n".join(groups[:15]) + "\n\n"
            
            result += f"<b>💡 Пример использования:</b>\n<code>.fh {chat_id} 5</code>\n\n"
            result += "<i>🔒 - защищенный от пересылки</i>"
            
            if result.strip() == "<b>📋 Список доступных чатов:</b>\n\n":
                result = "❌ <b>Чаты не найдены</b>"
            
            await utils.answer(message, result)
            
        except Exception as e:
            logger.error(f"Ошибка listch: {e}")
            await utils.answer(message, f"❌ <b>Не удалось получить chat_id:</b> <code>{e}</code>")

    @loader.command()
    async def getid(self, message: Message):
        """— получить ID текущего чата"""
        chat_id = message.chat_id
        
        try:
            chat = await self.client.get_entity(chat_id)
            chat_name = getattr(chat, 'title', None) or getattr(chat, 'first_name', 'Неизвестно')
            
            result = f"🆔 <b>ID этого чата:</b> <code>{chat_id}</code>\n"
            result += f"📝 <b>Название:</b> {chat_name}\n\n"
            result += f"<b>💡 Для копирования используй:</b>\n<code>.fh {chat_id} 10</code>"
            
            await utils.answer(message, result)
            
        except Exception as e:
            await utils.answer(message, f"🆔 <b>ID чата:</b> <code>{chat_id}</code>")
