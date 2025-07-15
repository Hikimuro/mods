# ver. 1.0.1
# meta developer: @Hikimuro

from .. import loader, utils
import requests
import random
import logging
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

@loader.tds
class FapReactorMod(loader.Module):
    """Отправляет случайное изображение с fapreactor.cc по категории"""

    strings = {
        "name": "FapReactor",
        "no_category": "❌ Категория не установлена. Используй .setfapcategory <категория>",
        "not_found": "❌ Не удалось найти изображения.\n\nПричина: {}",
        "downloading": "🔍 Ищу изображение..."
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "category", 
                None, 
                lambda: "Раздел с fapreactor.cc (например: hentai, porn, ero и т.д.)"
            )
        )

    @loader.command()
    async def setfapcategory(self, message):
        """Устанавливает категорию (раздел)"""
        args = utils.get_args_raw(message)
        if not args:
            await message.edit("⚠️ Укажи категорию.")
            return
        self.set("category", args)
        await message.edit(f"✅ Категория установлена на: `{args}`")

    @loader.command()
    async def fap(self, message):
        """Отправляет рандомное изображение с fapreactor.cc"""
        category = self.get("category")
        if not category:
            await message.edit(self.strings("no_category"))
            return

        await message.edit(self.strings("downloading"))

        try:
            page = random.randint(1, 20)
            url = f"https://fapreactor.cc/tag/{category}?page={page}"
            headers = {"User-Agent": "Mozilla/5.0"}
            r = requests.get(url, headers=headers, timeout=10)
            r.raise_for_status()

            soup = BeautifulSoup(r.text, "html.parser")
            posts = soup.select(".content .postContainer .post_content a img")

            if not posts:
                raise ValueError("Список изображений пуст. Возможно, сайт изменил структуру или использует защиту.")

            images = [img["src"] for img in posts if "src" in img.attrs]
            image_url = random.choice(images)

            await message.client.send_file(message.chat_id, image_url)
            await message.delete()

        except Exception as e:
            logger.exception("Ошибка при получении изображения с fapreactor")
            await message.edit(self.strings("not_found").format(str(e)))
