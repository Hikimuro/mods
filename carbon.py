import io import requests from telethon.tl.types import Message from .. import loader, utils

@loader.tds class CarbonMod(loader.Module): """Create beautiful code images. Edited by @Penggrin"""

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
    """Extract code from message or reply."""
    try:
        if message.media:
            return (await self._client.download_file(message.media, bytes)).decode("utf-8")
        
        reply = await message.get_reply_message()
        if reply and reply.media:
            return (await self._client.download_file(reply.media, bytes)).decode("utf-8")
    except Exception:
        pass
    
    return ""

async def _generate_image(self, code: str) -> io.BytesIO:
    """Generate image from code using external API."""
    try:
        url = (
            f'https://code2img.vercel.app/api/to-image?'
            f'theme={self.config["theme"]}&'
            f'language={self.config["language"]}&'
            f'line-numbers=true&'
            f'background-color={self.config["color"]}'
        )
        
        response = await utils.run_sync(requests.post, url, headers={"Content-Type": "text/plain"}, data=code.encode("utf-8"))
        response.raise_for_status()
        
        image = io.BytesIO(response.content)
        image.name = "carbonized.jpg"
        return image
    except requests.RequestException:
        return None

