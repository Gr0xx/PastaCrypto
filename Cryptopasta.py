# The MIT License (MIT)
# Авторские права? не слышал

# Пастер бля) : Fxrlxrn
# scope: hikka_only

from .. import loader, utils
import logging
import asyncio

version = (1, 3, 2)
logger = logging.getLogger(name)

@loader.tds
class CryptoStealMod(loader.Module):
    """Автоматически активирует проверки криптоботов (и некоторых других ботов)."""

    # Строки для локализации
    strings = {
        "name": "CryptoSteal",
        "disabled": "❌ Отключено",
        "enabled": "✅ Включено",
        "status_now": "🤑 Crypto-Steal был <b>{}</b>!",
        "config_status": "Готовы ли мы тырить?",
        "config_delay": (
            "Сколько ждать перед активацией чека? (в секундах) (нужно, чтобы предотвратить моменты, когда криптобот еще не создал чек)"
        ),
        "config_allow_other_bots": "Если отключено, я буду получать чеки только от Доверенных Ботов",
        "config_use_asset_chat": "Если отключено, чат 'crypto-steal' не будет использоваться",
        "config_trusted_bots": "Доверенные Боты, от которых я буду получать чеки, даже если allow_other_bots равен False (имя пользователя в нижнем регистре)",
        "cant_create_asset_chat": "😢 Чат Crypto-Steal не создан, по какой-то причине.",
        "asset_chat_got_check": (
            "☘️ Надеюсь, получен новый чек!\n🔗 Вот ссылка на него: {u1}?start={u2} или <code>/start {u2}</code> в {u1}"
            '\n\n<a href="{link}">🔗 Сообщение</a>'
        ),
    }

    def __init__(self):
        # fmt: off
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "status",
                True,
                lambda: self.strings("config_status"),
                validator=loader.validators.Boolean()
            ),
            loader.ConfigValue(
                "delay",
                0.08,
                lambda: self.strings("config_delay"),
                validator=loader.validators.Float()
            ),
            loader.ConfigValue(
                "allow_other_bots",
                False,
                lambda: self.strings("config_allow_other_bots"),
                validator=loader.validators.Boolean(),
            ),
            loader.ConfigValue(
                "use_asset_chat",
                True,
                lambda: self.strings("config_use_asset_chat"),
                validator=loader.validators.Boolean(),
            ),
            loader.ConfigValue(
                "trusted_bots",
                ["cryptobot", "tonrocketbot", "xjetswapbot"],
                lambda: self.strings("trusted_bots"),
                validator=loader.validators.Series(
                    loader.validators.Union(loader.validators.String(), loader.validators.Integer())
                ),
            ),
        )
        # fmt: on

    async def client_ready(self):
        self.me = await self.client.get_me()

        self.asset_chat = await utils.asset_channel(
            self.client,
            "crypto-steal",
            "",
            avatar=r"https://img2.joyreactor.cc/pics/post/full/Zettai-Ryouiki-%D1%80%D0%B0%D0%B7%D0%BD%D0%BE%D0%B5-3527844.jpeg",
            silent=True,
            invite_bot=True,
        )

        if not self.asset_chat:
            await self.inline.bot.send_message(self._client.tg_id, self.strings("cant_create_asset_chat"))
            logger.error("Не удалось создать чат Crypto-Steal")

    @loader.watcher(only_messages=True, only_inline=True)
    async def watcher(self, message):
        already_claimed: list = self.db.get(__name__, "already_claimed", [])

        if not self.config["status"]:
            return
        if not (("check for " in message.raw_text.lower()) or ("чек на " in message.raw_text.lower())):
            return

        url = message.buttons[0][0].url.split("?start=")

        if url[1] in already_claimed:
            logging.debug("Этот чек уже активирован")
            return

        user = await self.client.get_entity(url[0])

        link = f"https://t.me/c/{str(message.chat_id).replace('-100', '')}/{message.id}"

        if (user.username.lower() not in self.config["trusted_bots"]) and (not self.config["allow_other_bots"]):
            return logger.debug(f"Игнорируется недоверенный бот (@{user.username})")

        # https://t.me/c/1955174868/656
        await message.mark_read()

        await asyncio.sleep(self.config["delay"])

        await self.client.send_message(user.id, f"/start {url[1]}")
        logger.debug("Отправлен запрос на получение чека, надеюсь, мы его получили")

        already_claimed.append(url[1])
        self.db.set(__name__, "already_claimed", already_claimed)

        if self.asset_chat and self.config["use_asset_chat"]:
            await self.inline.bot.send_message(
                f"-100{self.asset_chat[0].id}",
                self.strings("asset_chat_got_check").format(u1=url[0], u2=url[1], link=link),
                disable_web_page_preview=True,
            )

    async def cryptostealcmd(self, message):
        """Переключить Crypto-Steal"""

        self.config["status"] = not self.config["status"]

        await utils.answer(
            message,
            self.strings("status_now").format(
                self.strings("enabled") if self.config["status"] else self.strings("disabled")
            ),
        )
