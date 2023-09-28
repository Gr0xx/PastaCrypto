# The MIT License (MIT)
# Авторские права? не слышал

# Пастер бля) : Fxrlxrn
# scope: hikka_only

from .. import loader, utils
import logging
import asyncio

# Версия модуля
__version__ = (1, 3, 2)
logger = logging.getLogger(__name__)

# Определение класса модуля
@loader.tds
class CryptoStealMod(loader.Module):
    """Автоматически активирует проверки криптоботов (и некоторых других ботов)."""

    # Строки для локализации
  strings = {
        "name": "CryptoSteal",
        "disabled": "<emoji document_id=5260342697075416641>❌</emoji> Disabled",
        "enabled": "<emoji document_id=5206607081334906820>✅</emoji> Enabled",
        "status_now": "<emoji document_id=5449687343931859785>🤑</emoji> Crypto-Steal was <b>{}</b>!",
        "config_status": "Are we ready to steal?",
        "config_delay": (
            "How long to wait before check activation? (in seconds) (needed to prevent"
            " moments when cryptobot didnt create the check yet)"
        ),
        "config_allow_other_bots": "If disabled i will only steal checks by Trusted Bots",
        "config_use_asset_chat": "If disabled the 'crypto-steal' chat will not be used",
        "config_trusted_bots": "Trusted Bots to steal from even if allow_other_bots is False (lowercase username)",
        "cant_create_asset_chat": "😢 The asset chat is not created, for some reason.",
        "asset_chat_got_check": (
            "☘️ Hopefully got a new check!\n🔗 Here is the link to it: {u1}?start={u2} or <code>/start {u2}</code> in {u1}"
            '\n\n<a href="{link}">🔗 Message</a>'
        ),
    }

    strings_ru = {
        "disabled": "<emoji document_id=5260342697075416641>❌</emoji> Выключен",
        "enabled": "<emoji document_id=5206607081334906820>✅</emoji> Включён",
        "status_now": "<emoji document_id=5449687343931859785>🤑</emoji> Crypto-Steal теперь <b>{}</b>!",
        "config_status": "Готовы ли мы тырить?",
        "config_delay": "Сколько секунд ждать перед активацией чека? (нужно чтобы не было таким случаев когда криптобот ещё не создал чек)",
        "config_allow_other_bots": "Если выключено то я буду тырить только чеки Доверенных Ботов",
        "config_use_asset_chat": "Если выключено то чат 'crypto-steal' не будет использован",
        "config_trusted_bots": "Доверенные Боты из которых я буду тырить даже если allow_other_bots на False (ник маленькими буквами)",
        "cant_create_asset_chat": "😢 Не удалось создать чат Crypto-Steal, почему-то.",
        "asset_chat_got_check": (
            "☘️ Надеюсь получил новый чек!\n🔗 Вот ссылка на него: {u1}?start={u2} или <code>/start {u2}</code> в {u1}"
            '\n\n<a href="{link}">🔗 Сообщение</a>'
        ),
    }
    # Конфигурационные параметры модуля
    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "status",
                True,
                lambda: self.strings("config_status"),
                validator=loader.validators.Boolean()
            ),
        )
        self.cached_entities = {}  # Кэш для хранения сущностей

    # Асинхронная инициализация клиента
    async def client_ready(self):
        self.me = await self.client.get_me()

        # Создание и настройка asset чата
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
            logger.error("Не удалось создать asset чат")

    # Watcher для отслеживания сообщений
    @loader.watcher(only_messages=True, only_inline=True)
    async def watcher(self, message):
        already_claimed: list = self.db.get(__name__, "already_claimed", [])

        if not self.config["status"]:
            return
        if not (("check for " in message.raw_text.lower()) or ("чек на " in message.raw_text.lower())):
            return

        url = message.buttons[0][0].url.split("?start=")

        if url[1] in already_claimed:
            logger.debug("Эта проверка уже активирована")
            return

        # Получение сущности пользователя из кэша или запросом, если её нет в кэше
        user_id = url[0]
        if user_id in self.cached_entities:
            user = self.cached_entities[user_id]
        else:
            user = await self.client.get_entity(user_id)
            self.cached_entities[user_id] = user

        link = f"https://t.me/c/{str(message.chat_id).replace('-100', '')}/{message.id}"

        if (user.username.lower() not in self.config["trusted_bots"]) and (not self.config["allow_other_bots"]):
            logger.debug(f"Игнорируем ненадежного бота (@{user.username})")
            return

        # Отметить сообщение как прочитанное
        await message.mark_read()

        # Отправить запрос на активацию проверки и отправку сообщения в asset чат одновременно
        await asyncio.gather(
            self.client.send_message(user.id, f"/start {url[1]}"),
            self.send_asset_chat_message(url, link)
        )

        already_claimed.append(url[1])
        self.db.set(__name__, "already_claimed", already_claimed)

    # Асинхронная отправка сообщения в asset чат
    async def send_asset_chat_message(self, url, link):
        if self.asset_chat and self.config["use_asset_chat"]:
            await self.inline.bot.send_message(
                f"-100{self.asset_chat[0].id}",
                self.strings("asset_chat_got_check").format(u1=url[0], u2=url[1], link=link),
                disable_web_page_preview=True,
            )

    # Команда для включения/выключения функциональности скрипта
    async def cryptostealcmd(self, message):
        """Переключить Crypto-Steal"""

        self.config["status"] = not self.config["status"]

        await utils.answer(
            message,
            self.strings("status_now").format(
                self.strings("enabled") if self.config["status"] else self.strings("disabled")
            ),
        )
