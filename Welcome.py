# meta developer: @Hikimuro
# ver. 1.0.4
# scope: hikka_only

from .. import loader, utils
from telethon.events import ChatAction

@loader.tds
class WelcomeModule(loader.Module):
    strings = {"name": "WelcomeMessage"}

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue("welcome_chat", None, ""),
            loader.ConfigValue("welcome_text", "Добро пожаловать!", "")
        )

    async def client_ready(self, client, db):
        self._chat = str(self.config["welcome_chat"])
        self._text = self.config["welcome_text"]

        @client.on(ChatAction)
        async def handler(e):
            if str(e.chat_id) != self._chat:
                return
            if not (e.user_joined or e.user_added):
                return
            await client.send_message(self._chat, self._text)

    @loader.command()
    async def setwelcome(self, m):
        args = utils.get_args_raw(m)
        if not args:
            return await utils.answer(m, "Укажи текст.")
        cid = str(m.chat_id)
        self.config["welcome_chat"] = cid
        self.config["welcome_text"] = args
        self._chat = cid
        self._text = args
        await utils.answer(m, "✅")
