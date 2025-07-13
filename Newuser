# meta developer: @Hikimuro
# ver 1.0.0
# scope: hikka_only

from .. import loader, utils
from telethon.events import ChatAction

@loader.tds
class WelcomeModule(loader.Module):
    """Приветственное сообщение новым участникам"""

    strings = {
        "name": "WelcomeMessage"
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "welcome_chat",
                None,
                "ID чата для отправки сообщения"
            ),
            loader.ConfigValue(
                "welcome_text",
                "Добро пожаловать!",
                "Текст приветствия"
            )
        )

    async def client_ready(self, client, db):
        self._client = client
        self._db = db

        @client.on(ChatAction)
        async def handler(event):
            if event.user_joined or event.user_added:
                chat_id = self.config["welcome_chat"]
                if chat_id is None or str(event.chat_id) != str(chat_id):
                    return

                try:
                    await self._client.send_message(
                        chat_id,
                        self.config["welcome_text"]
                    )
                except Exception:
                    pass
