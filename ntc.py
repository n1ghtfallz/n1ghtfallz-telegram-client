import asyncio
from telethon import TelegramClient, events
from telethon.tl import types
from telethon.tl.functions.account import UpdateProfileRequest, UpdateUsernameRequest
from telethon.tl.functions.auth import LogOutRequest
from telethon.tl.functions.messages import EditMessageRequest, DeleteMessagesRequest, SendReactionRequest
from telethon.tl.functions.contacts import GetContactsRequest, DeleteContactsRequest, AddContactRequest
from telethon.errors import ChatRestrictedError, ChatWriteForbiddenError, MessageNotModifiedError
from dotenv import load_dotenv
import os
from collections import defaultdict
import time
import random
import sys
import pickle
import unicodedata
import argparse
import re
import json
import importlib.util
from cryptography.fernet import Fernet
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.style import Style
from rich.theme import Theme
from rich.markdown import Markdown
from rich.syntax import Syntax

load_dotenv()

SESSION_NAME = 'telegram_cli_session'
MEDIA_DIR = 'downloads'
CACHE_FILE = 'dialogs_cache.pkl'
CONFIG_FILE = '.ntc_config'
DRAFTS_FILE = 'drafts.json'
MESSAGE_CACHE_FILE = 'message_cache.enc'
KEY_FILE = '.ntc_key'
PLUGINS_DIR = 'plugins'

def get_or_prompt_api_keys():
    """Get API ID and HASH from .env or prompt user"""
    api_id = os.getenv('API_ID')
    api_hash = os.getenv('API_HASH')

    if api_id and api_hash:
        return api_id, api_hash

    print("\n⚠ API_ID and API_HASH not found in .env")
    print("Get them at https://my.telegram.org\n")

    api_id = input("API_ID: ").strip()
    api_hash = input("API_HASH: ").strip()

    if not api_id or not api_hash:
        print("\n✗ API_ID and API_HASH are required!")
        exit(1)

    with open('.env', 'a') as f:
        f.write(f"\nAPI_ID={api_id}\n")
        f.write(f"API_HASH={api_hash}\n")

    print("\n✓ Saved to .env\n")
    return api_id, api_hash

API_ID, API_HASH = get_or_prompt_api_keys()

if not os.path.exists(MEDIA_DIR):
    os.makedirs(MEDIA_DIR)
if not os.path.exists(PLUGINS_DIR):
    os.makedirs(PLUGINS_DIR)

# Rich Themes
THEMES = {
    'dark': {
        'primary': 'bold magenta',
        'secondary': 'white',
        'accent': 'cyan',
        'dim': 'dim',
        'error': 'bold red',
        'success': 'bold green',
        'warning': 'yellow',
    },
    'light': {
        'primary': 'bold blue',
        'secondary': 'black',
        'dim': 'dim green',
        'error': 'bold red',
        'success': 'bold green',
        'warning': 'bold yellow',
    },
    'purple': {
        'primary': 'bold purple',
        'secondary': 'white',
        'accent': 'bold yellow',
        'dim': 'dim',
        'error': 'bold red',
        'success': 'bold green',
        'warning': 'bold yellow',
    },
    'matrix': {
        'primary': 'bold green',
        'secondary': 'green',
        'accent': 'bold white',
        'dim': 'dim green',
        'error': 'bold red',
        'success': 'bold green',
        'warning': 'bold yellow',
    },
}

LANGUAGES = {
    'en': {
        'name': 'English', 'session': 'Session', 'logged_in': 'Logged in', 'chats': 'Chats', 'history': 'History',
        'no_chat': 'No chat selected', 'error': 'Error', 'not_found': 'Not found', 'no_media': 'No media',
        'exit': 'Exit', 'send_text': 'Message', 'cant_write': 'Cannot write', 'help_title': 'Help',
        'about_title': 'About', 'search': 'Search', 'profile': 'Profile', 'saved': 'Saved Messages',
        'downloaded': 'Downloaded to', 'pinned': 'Pinned', 'forwarded': 'Forwarded', 'deleted': 'Deleted',
        'edited': 'Edited', 'reacted': 'Reacted', 'poll': 'Poll', 'sticker': 'Sticker',
        'h_chats': 'Chats', 'h_msgs': 'Messages', 'h_media': 'Media', 'h_prof': 'Profile',
        'h_set': 'Settings', 'h_other': 'Other',
        'cmd_list': 'show chats', 'cmd_sel': 'select chat', 'cmd_msg': 'show messages',
        'cmd_search': 'search messages', 'cmd_send': 'send message', 'cmd_reply': 'reply to message',
        'cmd_fwd': 'forward to saved', 'cmd_edit': 'edit message', 'cmd_del': 'delete message',
        'cmd_react': 'add reaction', 'cmd_dl': 'download media', 'cmd_up': 'upload file',
        'cmd_me': 'my profile', 'cmd_user': 'change username', 'cmd_name': 'change name',
        'cmd_bio': 'change bio', 'cmd_theme': 'change theme', 'cmd_lang': 'change language',
        'cmd_logout': 'logout', 'cmd_saved': 'saved messages', 'cmd_slots': 'slot machine',
        'cmd_about': 'about', 'cmd_help': 'help', 'cmd_exit': 'exit', 'contacts': 'Contacts',
        'cmd_contacts': 'manage contacts', 'plugin_load': 'Plugin loaded'
    },
    'ru': {
        'name': 'Русский', 'session': 'Сессия', 'logged_in': 'Вошли как', 'chats': 'Чаты', 'history': 'История',
        'no_chat': 'Чат не выбран', 'error': 'Ошибка', 'not_found': 'Не найдено', 'no_media': 'Нет медиа',
        'exit': 'Выход', 'send_text': 'Сообщение', 'cant_write': 'Нельзя писать', 'help_title': 'Помощь',
        'about_title': 'О программе', 'search': 'Поиск', 'profile': 'Профиль', 'saved': 'Избранное',
        'downloaded': 'Скачано в', 'pinned': 'Закреплено', 'forwarded': 'Переслано', 'deleted': 'Удалено',
        'edited': 'Изменено', 'reacted': 'Реакция добавлена', 'poll': 'Опрос', 'sticker': 'Стикер',
        'h_chats': 'Чаты', 'h_msgs': 'Сообщения', 'h_media': 'Медиа', 'h_prof': 'Профиль',
        'h_set': 'Настройки', 'h_other': 'Другое',
        'cmd_list': 'список чатов', 'cmd_sel': 'выбрать чат', 'cmd_msg': 'история сообщений',
        'cmd_search': 'поиск', 'cmd_send': 'отправить', 'cmd_reply': 'ответить',
        'cmd_fwd': 'в избранное', 'cmd_edit': 'изменить', 'cmd_del': 'удалить',
        'cmd_react': 'реакция', 'cmd_dl': 'скачать', 'cmd_up': 'отправить файл',
        'cmd_me': 'мой профиль', 'cmd_user': 'сменить юзернейм', 'cmd_name': 'сменить имя',
        'cmd_bio': 'сменить био', 'cmd_theme': 'сменить тему', 'cmd_lang': 'сменить язык',
        'cmd_logout': 'выйти', 'cmd_saved': 'избранное', 'cmd_slots': 'слоты',
        'cmd_about': 'о программе', 'cmd_help': 'помощь', 'cmd_exit': 'выход', 'contacts': 'Контакты',
        'cmd_contacts': 'управление контактами', 'plugin_load': 'Плагин загружен'
    },
    'uk': {
        'name': 'Українська', 'session': 'Сесія', 'logged_in': 'Увійшли як', 'chats': 'Чати', 'history': 'Історія',
        'no_chat': 'Чат не вибрано', 'error': 'Помилка', 'not_found': 'Не знайдено', 'no_media': 'Немає медіа',
        'exit': 'Вихід', 'send_text': 'Повідомлення', 'cant_write': 'Не можна писати', 'help_title': 'Допомога',
        'about_title': 'Про програму', 'search': 'Пошук', 'profile': 'Профіль', 'saved': 'Збережене',
        'downloaded': 'Завантажено в', 'pinned': 'Закріплено', 'forwarded': 'Переслано', 'deleted': 'Видалено',
        'edited': 'Змінено', 'reacted': 'Реакцію додано', 'poll': 'Опитування', 'sticker': 'Стікер',
        'h_chats': 'Чати', 'h_msgs': 'Повідомлення', 'h_media': 'Медіа', 'h_prof': 'Профіль',
        'h_set': 'Налаштування', 'h_other': 'Інше',
        'cmd_list': 'список чатів', 'cmd_sel': 'вибрати чат', 'cmd_msg': 'історія повідомлень',
        'cmd_search': 'пошук', 'cmd_send': 'надіслати', 'cmd_reply': 'відповісти',
        'cmd_fwd': 'в збережене', 'cmd_edit': 'змінити', 'cmd_del': 'видалити',
        'cmd_react': 'реакція', 'cmd_dl': 'завантажити', 'cmd_up': 'надіслати файл',
        'cmd_me': 'мій профіль', 'cmd_user': 'змінити юзернейм', 'cmd_name': 'змінити ім\'я',
        'cmd_bio': 'змінити біо', 'cmd_theme': 'змінити тему', 'cmd_lang': 'змінити мову',
        'cmd_logout': 'вийти', 'cmd_saved': 'збережене', 'cmd_slots': 'слоти',
        'cmd_about': 'про програму', 'cmd_help': 'допомога', 'cmd_exit': 'вихід', 'contacts': 'Контакти',
        'cmd_contacts': 'управління контактами', 'plugin_load': 'Плагін завантажено'
    },
    'kk': {
        'name': 'Қазақша', 'session': 'Сессия', 'logged_in': 'Кірді', 'chats': 'Чаттар', 'history': 'Тарих',
        'no_chat': 'Чат таңдалмаған', 'error': 'Қате', 'not_found': 'Табылмады', 'no_media': 'Медиа жоқ',
        'exit': 'Шығу', 'send_text': 'Хабарлама', 'cant_write': 'Жаза алмаймын', 'help_title': 'Көмек',
        'about_title': 'Бағдарлама туралы', 'search': 'Іздеу', 'profile': 'Профиль', 'saved': 'Сақталғандар',
        'downloaded': 'Жүктелді', 'pinned': 'Бекітілді', 'forwarded': 'Жіберілді', 'deleted': 'Өшірілді',
        'edited': 'Өзгертілді', 'reacted': 'Реакция қосылды', 'poll': 'Сауалнама', 'sticker': 'Стикер',
        'h_chats': 'Чаттар', 'h_msgs': 'Хабарламалар', 'h_media': 'Медиа', 'h_prof': 'Профиль',
        'h_set': 'Баптаулар', 'h_other': 'Басқа',
        'cmd_list': 'чаттар тізімі', 'cmd_sel': 'чатты таңдау', 'cmd_msg': 'хабарламалар тарихы',
        'cmd_search': 'іздеу', 'cmd_send': 'жіберу', 'cmd_reply': 'жауап беру',
        'cmd_fwd': 'сақталғанға', 'cmd_edit': 'өзгерту', 'cmd_del': 'өшіру',
        'cmd_react': 'реакция', 'cmd_dl': 'жүктеу', 'cmd_up': 'файл жіберу',
        'cmd_me': 'менің профилім', 'cmd_user': 'юзернеймді өзгерту', 'cmd_name': 'атын өзгерту',
        'cmd_bio': 'био өзгерту', 'cmd_theme': 'тақырыпты өзгерту', 'cmd_lang': 'тілді өзгерту',
        'cmd_logout': 'шығу', 'cmd_saved': 'сақталғандар', 'cmd_slots': 'слоттар',
        'cmd_about': 'туралы', 'cmd_help': 'көмек', 'cmd_exit': 'шығу', 'contacts': 'Контактілер',
        'cmd_contacts': 'контактілерді басқару', 'plugin_load': 'Плагин жүктелді'
    },
}

CMD_ALIASES = {
    'l': 'list', 's': 'select', 'm': 'msg', 'sr': 'search', 'sd': 'send',
    'r': 'reply', 'f': 'forward', 'i': 'img', 'si': 'send-img', 'n': 'name',
    'b': 'bio', 'cu': 'cu', 'mp': 'mp', 'lo': 'logout', 'sa': 'saved',
    'sl': 'slots', 'a': 'about', 'h': 'help', 'e': 'exit', 'd': 'del',
    't': 'text', 'th': 'theme', 'lang': 'language', 'c': 'contacts'
}

class EncryptionManager:
    def __init__(self):
        self.key = self.load_or_generate_key()
        self.cipher = Fernet(self.key)

    def load_or_generate_key(self):
        if os.path.exists(KEY_FILE):
            with open(KEY_FILE, 'rb') as f:
                return f.read()
        else:
            key = Fernet.generate_key()
            with open(KEY_FILE, 'wb') as f:
                f.write(key)
            return key

    def encrypt(self, data):
        return self.cipher.encrypt(pickle.dumps(data))

    def decrypt(self, data):
        return pickle.loads(self.cipher.decrypt(data))

class PluginManager:
    def __init__(self, cli):
        self.cli = cli
        self.plugins = {}

    def load_plugins(self):
        if not os.path.exists(PLUGINS_DIR):
            return
        for filename in os.listdir(PLUGINS_DIR):
            if filename.endswith('.py'):
                self.load_plugin(os.path.join(PLUGINS_DIR, filename))

    def load_plugin(self, path):
        try:
            name = os.path.basename(path)[:-3]
            spec = importlib.util.spec_from_file_location(name, path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            if hasattr(module, 'register'):
                module.register(self.cli)
                self.plugins[name] = module
                self.cli.console.print(f"[dim]{self.cli.t('plugin_load')}: {name}[/dim]")
        except Exception as e:
            self.cli.console.print(f"[error]Failed to load plugin {path}: {e}[/error]")

class TelegramCLI:
    def __init__(self):
        self.client = TelegramClient(SESSION_NAME, int(API_ID), API_HASH, flood_sleep_threshold=0)
        self.current_chat = None
        self.dialogs = []
        self.message_cache = defaultdict(dict)
        self.message_list = []
        self.media_list = []
        self.image_counter = 0
        self.running = True
        self.message_read_status = {}
        self.display_counter = 0
        self.update_task = None
        self.language = 'en'
        self.theme = 'dark'
        self.drafts = self.load_drafts()
        self.folders = {}
        self.current_folder = None
        self.console = Console()
        self.encryption = EncryptionManager()
        self.load_theme_from_config()
        self.apply_theme()
        self.load_message_cache()
        self.plugins = PluginManager(self)

    def load_theme_from_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    config = json.load(f)
                    self.theme = config.get('theme', 'dark')
                    self.language = config.get('language', 'en')
            except:
                pass

    def save_config(self):
        config = {'theme': self.theme, 'language': self.language}
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f)

    def apply_theme(self):
        theme_data = THEMES.get(self.theme, THEMES['dark'])
        rich_theme = Theme(theme_data)
        self.console = Console(theme=rich_theme)

    def load_drafts(self):
        if os.path.exists(DRAFTS_FILE):
            try:
                with open(DRAFTS_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def save_drafts(self):
        try:
            with open(DRAFTS_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.drafts, f, ensure_ascii=False, indent=2)
        except:
            pass

    def save_draft(self, chat_id, text):
        self.drafts[str(chat_id)] = text
        self.save_drafts()

    def get_draft(self, chat_id):
        return self.drafts.get(str(chat_id), '')

    def clear_draft(self, chat_id):
        if str(chat_id) in self.drafts:
            del self.drafts[str(chat_id)]
            self.save_drafts()

    def load_message_cache(self):
        if os.path.exists(MESSAGE_CACHE_FILE):
            try:
                with open(MESSAGE_CACHE_FILE, 'rb') as f:
                    data = f.read()
                    cache_data = self.encryption.decrypt(data)
                    self.message_cache = cache_data.get('messages', defaultdict(dict))
                    self.console.print(f"[success]✓[/success] Cache loaded")
            except Exception as e:
                self.console.print(f"[dim]Cache load failed: {e}[/dim]")

    def save_message_cache(self):
        try:
            cache_data = {
                'messages': dict(self.message_cache),
                'timestamp': time.time()
            }
            encrypted = self.encryption.encrypt(cache_data)
            with open(MESSAGE_CACHE_FILE, 'wb') as f:
                f.write(encrypted)
        except:
            pass

    def t(self, key):
        return LANGUAGES[self.language].get(key, key)

    def get_chat_type(self, entity):
        if isinstance(entity, types.Channel):
            return 'channel' if entity.broadcast else 'group'
        elif isinstance(entity, types.Chat):
            return 'group'
        elif isinstance(entity, types.User):
            return 'bot' if entity.bot else 'private'
        return 'unknown'

    def get_type_badge(self, entity):
        badges = {
            'bot': '[primary]*[/primary]',
            'private': '[secondary]@[/secondary]',
            'group': '[secondary]#[/secondary]',
            'channel': '[secondary]~[/secondary]',
        }
        return badges.get(self.get_chat_type(entity), '?')

    def get_media_type(self, msg):
        if not msg.media:
            return None
        if isinstance(msg.media, types.MessageMediaPhoto):
            return ('img', '.jpg')
        elif isinstance(msg.media, types.MessageMediaDocument):
            mime = getattr(msg.media.document, 'mime_type', '')
            filename = 'file'
            if msg.media.document.attributes:
                attr = msg.media.document.attributes[0]
                if hasattr(attr, 'file_name'):
                    filename = attr.file_name

            if 'sticker' in mime or filename.endswith(('.webp', '.tgs')):
                emoji = '🗿'
                for attr in msg.media.document.attributes:
                    if isinstance(attr, types.DocumentAttributeSticker):
                        emoji = attr.alt
                return ('sticker', emoji)
            elif 'gif' in mime or filename.endswith('.gif'):
                return ('gif', '.gif')
            elif 'video' in mime or filename.endswith('.mp4'):
                return ('video', '.mp4')
            elif 'voice' in mime or filename.endswith('.ogg'):
                return ('voice', '.ogg')
            elif 'audio' in mime or filename.endswith('.mp3'):
                return ('audio', '.mp3')
            else:
                ext = os.path.splitext(filename)[1] or '.bin'
                return ('document', ext)
        elif isinstance(msg.media, types.MessageMediaPoll):
            return ('poll', '')
        return ('media', '')

    def format_media_label(self, msg):
        media_info = self.get_media_type(msg)
        if not media_info:
            return ""
        media_type, ext = media_info
        
        if media_type == 'sticker':
            return f"[primary][{self.t('sticker')} {ext}][/primary]"
        elif media_type == 'poll':
            poll = msg.media.poll
            return f"[primary][{self.t('poll')}: {poll.question}][/primary]"
            
        labels = {'img': 'IMG', 'video': 'VID', 'audio': 'AUD', 'document': 'DOC', 'gif': 'GIF', 'voice': 'VCE'}
        label = labels.get(media_type, media_type.upper())
        return f"[primary][{label}{ext}][/primary]"

    def parse_markdown(self, text):
        # Bold **text**
        text = re.sub(r'\*\*(.+?)\*\*', r'[bold]\1[/bold]', text)
        # Italic *text* or _text_
        text = re.sub(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)', r'[italic]\1[/italic]', text)
        text = re.sub(r'(?<!_)_(?!_)(.+?)(?<!_)_(?!_)', r'[italic]\1[/italic]', text)
        # Strikethrough ~~text~~
        text = re.sub(r'~~(.+?)~~', r'[strike]\1[/strike]', text)
        # Underline __text__
        text = re.sub(r'__(.+?)__', r'[underline]\1[/underline]', text)
        # Spoiler ||text||
        text = re.sub(r'\|\|(.+?)\|\|', r'[dim]\1[/dim]', text)
        return text

    async def start(self):
        session_file = f"{SESSION_NAME}.session"
        if os.path.exists(session_file):
            self.console.print(f"[primary]✓[/primary] {self.t('session')}")
        else:
            self.console.print(f"[primary]+[/primary] First login")
        await self.client.start()
        me = await self.client.get_me()
        self.console.print(f"[primary]✓[/primary] {self.t('logged_in')}: {me.first_name}\n")
        self.plugins.load_plugins()

        @self.client.on(events.NewMessage())
        async def handle_new_message(event):
            await self.on_new_message(event)

    async def update_read_status_loop(self):
        while self.running:
            if self.current_chat:
                try:
                    async for msg in self.client.iter_messages(self.current_chat, limit=30):
                        if msg.out:
                            key = f"{self.current_chat.id}_{msg.id}"
                            is_read = hasattr(msg, 'read_date') and msg.read_date is not None
                            self.message_read_status[key] = is_read
                            if hasattr(msg, 'reactions') and msg.reactions:
                                self.message_read_status[f"{key}_readers"] = msg.reactions
                except:
                    pass
            await asyncio.sleep(3)

    def animate_send(self):
        frames = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴']
        for i in range(3):
            sys.stdout.write(f"\r{frames[i % len(frames)]}")
            sys.stdout.flush()
            time.sleep(0.01)
        sys.stdout.write(f"\r")
        sys.stdout.flush()

    def get_status(self, msg):
        if msg.out:
            key = f"{self.current_chat.id}_{msg.id}"
            is_read = self.message_read_status.get(key, False)
            readers_key = f"{key}_readers"
            if readers_key in self.message_read_status:
                readers = self.message_read_status[readers_key]
                return f"[success]✓✓[{len(readers)}][/success]"
            return f"[success]✓✓[/success]" if is_read else f"[dim]✓[/dim]"
        return f"[dim]•[/dim]"

    async def show_msg_animated(self, msg):
        if not msg or not (msg.text or msg.media):
            return
        if msg.media:
            self.image_counter += 1
            self.media_list.append({'msg_id': msg.id, 'img_num': self.image_counter})
        self.display_counter += 1
        sender = "You" if msg.out else (msg.sender.first_name[:10] if hasattr(msg.sender, 'first_name') else "?")
        time_str = msg.date.strftime("%H:%M")
        status = self.get_status(msg)
        media_label = self.format_media_label(msg) if msg.media else ""
        
        sender_color = "primary" if msg.out else "accent"
        sender_prefix = "→" if msg.out else "←"
        edit_indicator = f"[dim]{self.t('edited')}[/dim] " if hasattr(msg, 'edit_date') and msg.edit_date else ""

        if msg.text:
            if '```' in msg.text:
                # Extract language if possible, default to python for now
                code_match = re.search(r'```(\w+)?\n(.*?)```', msg.text, re.DOTALL)
                if code_match:
                    lang = code_match.group(1) or 'python'
                    code = code_match.group(2)
                    syntax = Syntax(code, lang, theme="monokai", line_numbers=True)
                    self.console.print(f" {self.display_counter:2} [dim]{time_str}[/dim] {status} [{sender_color}]{sender_prefix} {sender}[/{sender_color}] | {edit_indicator}")
                    self.console.print(syntax)
                else:
                    # Fallback markdown
                    md = Markdown(msg.text)
                    self.console.print(f" {self.display_counter:2} [dim]{time_str}[/dim] {status} [{sender_color}]{sender_prefix} {sender}[/{sender_color}] | {edit_indicator}")
                    self.console.print(md)
            else:
                text = self.parse_markdown(msg.text[:200])
                self.console.print(f" {self.display_counter:2} [dim]{time_str}[/dim] {status} [{sender_color}]{sender_prefix} {sender}[/{sender_color}] | {edit_indicator}{text} {media_label}")
        else:
            self.console.print(f" {self.display_counter:2} [dim]{time_str}[/dim] {status} [{sender_color}]{sender_prefix} {sender}[/{sender_color}] | {edit_indicator}{media_label}")
            
        if msg.media and isinstance(msg.media, types.MessageMediaPoll):
            poll = msg.media.poll
            results = msg.media.results
            self.console.print(Panel(f"[bold]{poll.question}[/bold]", style="primary"))
            for i, answer in enumerate(poll.answers):
                percent = ""
                if results and results.results:
                    for res in results.results:
                        if res.option == answer.option:
                            if results.total_voters:
                                p = (res.voters / results.total_voters) * 100
                                percent = f" ({p:.1f}%)"
                self.console.print(f"  {i+1}. {answer.text}{percent}")

    async def on_new_message(self, event):
        if not self.current_chat or event.chat_id != self.current_chat.id:
            return
        msg = event.message
        self.message_cache[self.current_chat.id][msg.id] = msg
        if msg.id not in self.message_list:
            self.message_list.append(msg.id)

        if not msg.out:
            print() 

        await self.show_msg_animated(msg)

        draft = self.get_draft(self.current_chat.id)
        if draft:
            self.console.print(f"[dim][draft: {draft[:30]}...][/dim] ", end="")
        self.console.print(f"[primary]>[/primary] ", end="")

    async def list_chats(self, limit=None):
        table = Table(show_header=True, header_style="primary", box=None)
        table.add_column("#", style="dim", width=4)
        table.add_column(self.t('chats'), style="bold")
        table.add_column("Type", width=3)
        table.add_column("Unread", justify="right")

        self.dialogs = []
        async for d in self.client.iter_dialogs(limit=100):
            self.dialogs.append(d)
        
        for idx, d in enumerate(self.dialogs[:limit] if limit else self.dialogs, 1):
            name = d.name[:32]
            badge = self.get_type_badge(d.entity)
            unread = f"+{d.unread_count}" if d.unread_count > 0 else ""
            draft_indicator = "📝" if self.get_draft(d.id) else ""
            table.add_row(str(idx), f"{name} {draft_indicator}", badge, unread)

        self.console.print(table)
        print()

    async def select_chat(self, idx):
        try:
            idx = int(idx) - 1
            if 0 <= idx < len(self.dialogs):
                self.current_chat = self.dialogs[idx]
                self.console.print(f"\n[primary]→[/primary] {self.current_chat.name}\n")
                self.message_cache.clear()
                self.message_list.clear()
                self.media_list.clear()
                self.image_counter = 0
                self.display_counter = 0
                self.message_read_status.clear()

                draft = self.get_draft(self.current_chat.id)
                if draft:
                    self.console.print(f"[warning]📝 Draft: {draft}[/warning]\n")

                await self.show_messages(15)
                return True
            return False
        except:
            return False

    async def show_messages(self, limit=15):
        if not self.current_chat:
            self.console.print(f"[warning]{self.t('no_chat')}[/warning]")
            return

        chat_name = getattr(self.current_chat, 'name', None) or getattr(self.current_chat, 'title', 'Unknown')
        self.console.print(Panel(f"[bold]{self.t('history')} — {str(chat_name)[:40]}[/bold]", style="primary"))
        
        msgs = []
        try:
            async for m in self.client.iter_messages(self.current_chat, limit=limit):
                msgs.append(m)
        except:
            self.console.print(f"[error]{self.t('error')}[/error]")
            return

        for idx, msg in enumerate(reversed(msgs), 1):
            try:
                if not (msg.text or msg.media):
                    continue
                self.message_cache[self.current_chat.id][msg.id] = msg
                if msg.id not in self.message_list:
                    self.message_list.append(msg.id)
                if msg.out:
                    key = f"{self.current_chat.id}_{msg.id}"
                    is_read = hasattr(msg, 'read_date') and msg.read_date is not None
                    self.message_read_status[key] = is_read
                if msg.media:
                    self.image_counter += 1
                    if msg.id not in [m['msg_id'] for m in self.media_list]:
                        self.media_list.append({'msg_id': msg.id, 'img_num': self.image_counter})

                await self.show_msg_animated(msg)
            except:
                continue
        print()
        self.save_message_cache()

    async def search_messages(self, query):
        if not self.current_chat:
            self.console.print(f"[warning]{self.t('no_chat')}[/warning]")
            return
        self.console.print(f"\n[primary]{self.t('search')}: {query}[/primary]")
        found = 0
        try:
            async for msg in self.client.iter_messages(self.current_chat, search=query, limit=15):
                if msg.text:
                    found += 1
                    await self.show_msg_animated(msg)
        except:
            pass
        if found == 0:
            self.console.print(f"[dim]{self.t('not_found')}[/dim]")
        print()

    async def show_my_profile(self):
        try:
            me = await self.client.get_me()
            self.console.print(Panel(f"id: {me.id}\nname: {me.first_name} {me.last_name or ''}\nuser: @{me.username or 'none'}", title=self.t('profile'), border_style="primary"))
            full = await self.client.get_entity(me.id)
            if hasattr(full, 'about'):
                self.console.print(f"  bio: {full.about or 'none'}")
            print()
        except:
            self.console.print(f"[error]{self.t('error')}[/error]")

    async def list_contacts(self):
        try:
            contacts = await self.client(GetContactsRequest(hash=0))
            table = Table(show_header=True, header_style="primary", box=None)
            table.add_column("ID", style="dim")
            table.add_column("Name", style="bold")
            table.add_column("User")
            
            for u in contacts.users:
                table.add_row(str(u.id), f"{u.first_name} {u.last_name or ''}", f"@{u.username or ''}")
            self.console.print(table)
        except Exception as e:
            self.console.print(f"[error]{e}[/error]")

    async def change_username(self, username):
        try:
            self.animate_send()
            await self.client(UpdateUsernameRequest(username=username))
            self.console.print(f"[success]✓[/success] username @{username}")
        except Exception as e:
            self.console.print(f"[error]✗ {str(e)}[/error]")

    async def change_name(self, first_name, last_name=""):
        try:
            self.animate_send()
            await self.client(UpdateProfileRequest(first_name=first_name, last_name=last_name))
            self.console.print(f"[success]✓[/success] name changed")
        except Exception as e:
            self.console.print(f"[error]✗ {str(e)}[/error]")

    async def change_bio(self, bio):
        try:
            self.animate_send()
            await self.client(UpdateProfileRequest(about=bio))
            self.console.print(f"[success]✓[/success] bio changed")
        except Exception as e:
            self.console.print(f"[error]✗ {str(e)}[/error]")

    async def edit_message(self, num, new_text):
        if not self.current_chat:
            self.console.print(f"[warning]{self.t('no_chat')}[/warning]")
            return
        try:
            num = int(num) - 1
            if num < 0 or num >= len(self.message_list):
                self.console.print(f"[dim]invalid message number[/dim]")
                return

            msg_id = self.message_list[num]
            msg = await self.client.get_messages(self.current_chat, ids=msg_id)

            if not msg or not msg.out:
                self.console.print(f"[dim]can only edit your own messages[/dim]")
                return

            self.animate_send()
            await self.client.edit_message(self.current_chat, msg_id, new_text)
            self.console.print(f"[success]✓[/success] message edited")
            msg = await self.client.get_messages(self.current_chat, ids=msg_id)
            self.message_cache[self.current_chat.id][msg_id] = msg
        except Exception as e:
            self.console.print(f"[error]✗ {str(e)}[/error]")

    async def delete_message(self, num):
        if not self.current_chat:
            self.console.print(f"[warning]{self.t('no_chat')}[/warning]")
            return
        try:
            num = int(num) - 1
            if num < 0 or num >= len(self.message_list):
                self.console.print(f"[dim]invalid message number[/dim]")
                return

            msg_id = self.message_list[num]
            self.animate_send()
            await self.client.delete_messages(self.current_chat, [msg_id])
            self.console.print(f"[success]✓[/success] message deleted")

            if msg_id in self.message_cache.get(self.current_chat.id, {}):
                del self.message_cache[self.current_chat.id][msg_id]
            if msg_id in self.message_list:
                self.message_list.remove(msg_id)
        except Exception as e:
            self.console.print(f"[error]✗ {str(e)}[/error]")

    async def react_to_message(self, num, emoji):
        if not self.current_chat:
            self.console.print(f"[warning]{self.t('no_chat')}[/warning]")
            return
        try:
            num = int(num) - 1
            if num < 0 or num >= len(self.message_list):
                self.console.print(f"[dim]invalid message number[/dim]")
                return

            msg_id = self.message_list[num]
            self.animate_send()
            from telethon.tl.types import ReactionEmoji
            reaction = [ReactionEmoji(emoticon=emoji)]
            await self.client(SendReactionRequest(peer=self.current_chat, msg_id=msg_id, reaction=reaction))
            self.console.print(f"[success]✓[/success] reacted with {emoji}")
        except Exception as e:
            self.console.print(f"[error]✗ {str(e)}[/error]")

    async def change_theme(self, theme_name):
        if theme_name not in THEMES:
            self.console.print(f"[dim]available themes: {', '.join(THEMES.keys())}[/dim]")
            return
        self.theme = theme_name
        self.save_config()
        self.apply_theme()
        self.console.print(f"[success]✓[/success] theme changed to {theme_name}")

    async def send_to_user(self, username, text):
        try:
            username = username.lstrip('@')
            self.animate_send()
            user = await self.client.get_entity(username)
            await self.client.send_message(user, text)
            self.console.print(f"[success]✓[/success] sent to @{username}")
        except Exception as e:
            self.console.print(f"[error]✗ {str(e)}[/error]")

    async def logout(self):
        try:
            self.animate_send()
            self.save_message_cache()
            self.save_drafts()
            await self.client(LogOutRequest())
            self.console.print(f"[success]✓[/success] logged out")
            self.running = False
            return True
        except Exception as e:
            self.console.print(f"[error]✗ {str(e)}[/error]")
            return False

    async def forward_to_saved(self, num):
        if not self.current_chat:
            self.console.print(f"[warning]{self.t('no_chat')}[/warning]")
            return
        try:
            num = int(num) - 1
            if num < 0 or num >= len(self.message_list):
                self.console.print(f"[dim]invalid[/dim]")
                return
            msg_id = self.message_list[num]
            me = await self.client.get_me()
            saved_msgs = await self.client.get_entity(me.id)
            self.animate_send()
            await self.client.forward_messages(saved_msgs, msg_id, from_peer=self.current_chat)
            self.console.print(f"[success]✓[/success] forwarded")
        except:
            self.console.print(f"[error]{self.t('error')}[/error]")

    async def go_to_saved_messages(self):
        try:
            me = await self.client.get_me()
            self.current_chat = await self.client.get_entity(me.id)
            self.console.print(f"\n[primary]→[/primary] {self.t('saved')}\n")
            self.message_cache.clear()
            self.message_list.clear()
            self.media_list.clear()
            self.image_counter = 0
            self.display_counter = 0
            self.message_read_status.clear()
            await self.show_messages(15)
        except:
            self.console.print(f"[error]{self.t('error')}[/error]")

    async def slot_machine(self):
        if not self.current_chat:
            self.console.print(f"[warning]{self.t('no_chat')}[/warning]")
            return
        self.animate_send()
        try:
            msg = await self.client.send_message(self.current_chat, '🎰')
        except:
            self.console.print(f"[error]{self.t('error')}[/error]")
            return

        await asyncio.sleep(0.5)
        emojis = ['🍎', '🍊', '🍋', '🍌', '🍉', '🍇', '🍓', '7️⃣', '💎']
        r1, r2, r3 = random.choice(emojis), random.choice(emojis), random.choice(emojis)
        if r1 == r2 == r3:
            result = f"[primary]jackpot! {r1}{r2}{r3}[/primary]" if r1 == '7️⃣' else f"[white]win {r1}{r2}{r3}[/white]"
        elif r1 == r2 or r2 == r3:
            result = f"[dim]small win {r1}{r2}{r3}[/dim]"
        else:
            result = f"[dim]lose {r1}{r2}{r3}[/dim]"
        self.console.print(result)
        self.message_cache[self.current_chat.id][msg.id] = msg
        if msg.id not in self.message_list:
            self.message_list.append(msg.id)

    async def download_img(self, num):
        try:
            num = int(num)
            item = next((i for i in self.media_list if i['img_num'] == num), None)
            if not item:
                self.console.print(f"[dim]not found[/dim]")
                return
            msg = await self.client.get_messages(self.current_chat, ids=item['msg_id'])
            if not msg or not msg.media:
                self.console.print(f"[dim]no media[/dim]")
                return
            media_info = self.get_media_type(msg)
            folder = os.path.join(MEDIA_DIR, media_info[0]) if media_info else MEDIA_DIR
            if not os.path.exists(folder):
                os.makedirs(folder)
            file_path = await msg.download_media(file=folder)
            self.console.print(f"[success]✓[/success] {os.path.abspath(file_path)}")
        except:
            self.console.print(f"[error]{self.t('error')}[/error]")

    async def send_img(self, path):
        if not self.current_chat:
            self.console.print(f"[warning]{self.t('no_chat')}[/warning]")
            return
        if not os.path.exists(path):
            self.console.print(f"[dim]not found[/dim]")
            return
        self.animate_send()
        try:
            msg = await self.client.send_file(self.current_chat, path)
            self.message_cache[self.current_chat.id][msg.id] = msg
            if msg.id not in self.message_list:
                self.message_list.append(msg.id)
            await self.show_msg_animated(msg)
        except Exception as e:
            self.console.print(f"[error]{self.t('error')}: {e}[/error]")

    async def send_msg(self, text):
        if not self.current_chat:
            self.console.print(f"[warning]{self.t('no_chat')}[/warning]")
            return
        self.clear_draft(self.current_chat.id)
        self.animate_send()
        try:
            msg = await self.client.send_message(self.current_chat, text)
            self.message_cache[self.current_chat.id][msg.id] = msg
            if msg.id not in self.message_list:
                self.message_list.append(msg.id)
            await self.show_msg_animated(msg)
        except Exception as e:
            self.console.print(f"[error]{self.t('error')}: {e}[/error]")

    async def reply(self, num, text):
        if not self.current_chat:
            self.console.print(f"[warning]{self.t('no_chat')}[/warning]")
            return
        try:
            num = int(num) - 1
            if num < 0 or num >= len(self.message_list):
                return
            self.animate_send()
            msg = await self.client.send_message(self.current_chat, text, reply_to=self.message_list[num])
            self.message_cache[self.current_chat.id][msg.id] = msg
            if msg.id not in self.message_list:
                self.message_list.append(msg.id)
            await self.show_msg_animated(msg)
        except:
            pass

    def show_help(self):
        t = self.t
        help_text = f"""
[primary]ntc - n1ghtfallz Telegram Client[/primary]

[white]{t('h_chats')}[/white]
  ntc --list, ntc -l [n]           {t('cmd_list')}
  ntc --select, ntc -s <n>         {t('cmd_sel')}
  ntc --msg, ntc -m [n]            {t('cmd_msg')}
  ntc --search, ntc -sr <text>     {t('cmd_search')}
  ntc --text, ntc -t @user <text>  {t('cmd_send')}

[white]{t('h_msgs')}[/white]
  ntc --send, ntc -sd <text>       {t('cmd_send')}
  ntc --reply, ntc -r <#> <text>   {t('cmd_reply')}
  ntc --forward, ntc -f <#>        {t('cmd_fwd')}
  ntc --edit <#> <text>            {t('cmd_edit')}
  ntc --del, ntc -d <#>            {t('cmd_del')}
  ntc --react <#> <emoji>          {t('cmd_react')}

[white]{t('h_media')}[/white]
  ntc --img, ntc -i <n>            {t('cmd_dl')}
  ntc --send-img, ntc -si <path>   {t('cmd_up')}

[white]{t('h_prof')}[/white]
  ntc --mp                         {t('cmd_me')}
  ntc --cu <user>                  {t('cmd_user')}
  ntc --name, ntc -n <name>        {t('cmd_name')}
  ntc --bio, ntc -b <text>         {t('cmd_bio')}
  ntc --contacts, ntc -c           {t('cmd_contacts')}

[white]{t('h_set')}[/white]
  ntc --theme, ntc -th <name>      {t('cmd_theme')}
                                   (dark, light, purple, matrix)
  ntc --lang <code >               {t('cmd_lang')} (en, ru, uk, kk)

[white]{t('h_other')}[/white]
  ntc --logout, ntc -lo            {t('cmd_logout')}
  ntc --saved, ntc -sa             {t('cmd_saved')}
  ntc --slots, ntc -sl             {t('cmd_slots')}
  ntc --about, ntc -a              {t('cmd_about')}
  ntc --help, ntc -h               {t('cmd_help')}
  ntc --exit, ntc -e               {t('cmd_exit')}
"""
        self.console.print(Panel(help_text, title=t('help_title'), border_style="primary"))

    def show_about(self):
        about_text = f"""
[primary]ntc - n1ghtfallz Telegram Client[/primary]

owner: @n1ghtfallz
version: 1.2
coded via claude sonnet 4
language: python 3.14


[italic]made for fun by n1ght[/italic]
"""
        self.console.print(Panel(about_text, title=self.t('about_title'), border_style="primary"))

    def parse_command(self, cmd_input):
        parts = cmd_input.split()
        if not parts:
            return None, None, None

        if parts[0] == 'ntc':
            if len(parts) < 2:
                return 'send_direct', 'ntc', None

            if parts[1].startswith('-'):
                cmd_raw = parts[1]
                if cmd_raw.startswith('--'):
                    cmd = cmd_raw[2:]
                else:
                    alias = cmd_raw[1:]
                    cmd = CMD_ALIASES.get(alias, alias)

                args = ' '.join(parts[2:]) if len(parts) > 2 else None
                return cmd, args, None
            else:
                return 'send_direct', cmd_input, None
        else:
            if self.current_chat and not cmd_input.startswith('/'):
                self.save_draft(self.current_chat.id, cmd_input)
            return 'send_direct', cmd_input, None

    def get_input(self):
        return input(f"> ")

    async def run(self):
        await self.start()
        self.console.print(f"[dim]type 'ntc --help' for commands[/dim]\n")
        self.update_task = asyncio.create_task(self.update_read_status_loop())
        loop = asyncio.get_event_loop()

        while self.running:
            try:
                cmd_input = await loop.run_in_executor(None, self.get_input)
            except EOFError:
                break

            if not cmd_input or not cmd_input.strip():
                continue

            cmd, args, _ = self.parse_command(cmd_input.strip())

            if not cmd:
                continue

            match cmd:
                case 'list':
                    limit = int(args) if args and args.isdigit() else None
                    await self.list_chats(limit)
                case 'select':
                    if args:
                        await self.select_chat(args)
                case 'msg':
                    limit = int(args) if args and args.isdigit() else 15
                    await self.show_messages(limit)
                case 'search':
                    if args:
                        await self.search_messages(args)
                case 'send':
                    if args:
                        await self.send_msg(args)
                case 'reply':
                    if args and len(args.split()) >= 2:
                        parts = args.split(' ', 1)
                        await self.reply(parts[0], parts[1])
                case 'forward':
                    if args:
                        await self.forward_to_saved(args)
                case 'edit':
                    if args and len(args.split()) >= 2:
                        parts = args.split(' ', 1)
                        await self.edit_message(parts[0], parts[1])
                case 'del':
                    if args:
                        await self.delete_message(args)
                case 'react':
                    if args and len(args.split()) >= 2:
                        parts = args.split(' ', 1)
                        await self.react_to_message(parts[0], parts[1])
                case 'img':
                    if args:
                        await self.download_img(args)
                case 'send-img':
                    if args:
                        await self.send_img(args)
                case 'mp':
                    await self.show_my_profile()
                case 'contacts':
                    await self.list_contacts()
                case 'cu':
                    if args:
                        await self.change_username(args)
                case 'name':
                    if args:
                        name_parts = args.split(' ', 1)
                        first = name_parts[0]
                        last = name_parts[1] if len(name_parts) > 1 else ""
                        await self.change_name(first, last)
                case 'bio':
                    if args:
                        await self.change_bio(args)
                case 'theme':
                    if args:
                        await self.change_theme(args)
                case 'language' | 'lang':
                    if args and args in LANGUAGES:
                        self.language = args
                        self.save_config()
                        self.console.print(f"Language changed to {LANGUAGES[args]['name']}")
                        self.apply_theme()
                case 'text':
                    if args and len(args.split()) >= 2:
                        parts = args.split(' ', 1)
                        await self.send_to_user(parts[0], parts[1])
                case 'logout':
                    if await self.logout():
                        break
                case 'saved':
                    await self.go_to_saved_messages()
                case 'slots':
                    await self.slot_machine()
                case 'about':
                    self.show_about()
                case 'help':
                    self.show_help()
                case 'exit':
                    self.console.print(f"[dim]exit[/dim]")
                    self.running = False
                    break
                case 'send_direct':
                    if self.current_chat:
                        await self.send_msg(args)
                case _:
                    self.console.print(f"[dim]unknown: --{cmd}[/dim]")

            await asyncio.sleep(0.01)

        if self.update_task:
            self.update_task.cancel()

        self.save_message_cache()
        self.save_drafts()
        await self.client.disconnect()

async def main():
    parser = argparse.ArgumentParser(prog='ntc', add_help=False)
    parser.add_argument('--help', action='store_true')
    parser.add_argument('--about', action='store_true')
    parser.add_argument('--list', nargs='?', const=None)
    parser.add_argument('--select', type=int)
    parser.add_argument('--msg', type=int, nargs='?', const=15)
    parser.add_argument('--search', type=str)
    parser.add_argument('--send', type=str)
    parser.add_argument('--reply', nargs=2, metavar=('NUM', 'TEXT'))
    parser.add_argument('--forward', type=int)
    parser.add_argument('--edit', nargs=2, metavar=('NUM', 'TEXT'))
    parser.add_argument('--del', type=int, dest='delete')
    parser.add_argument('--react', nargs=2, metavar=('NUM', 'EMOJI'))
    parser.add_argument('--img', type=int)
    parser.add_argument('--send-img', type=str)
    parser.add_argument('--mp', action='store_true')
    parser.add_argument('--contacts', action='store_true')
    parser.add_argument('--cu', type=str)
    parser.add_argument('--name', type=str, nargs='+')
    parser.add_argument('--bio', type=str)
    parser.add_argument('--theme', type=str)
    parser.add_argument('--text', type=str, nargs='+')
    parser.add_argument('--logout', action='store_true')
    parser.add_argument('--saved', action='store_true')
    parser.add_argument('--slots', action='store_true')
    parser.add_argument('--lang', type=str)

    args = parser.parse_args()

    if any(vars(args).values()):
        cli = TelegramCLI()
        try:
            await cli.start()
            if args.help: cli.show_help()
            elif args.about: cli.show_about()
            elif args.list is not None: await cli.list_chats(args.list)
            elif args.select: await cli.select_chat(args.select)
            elif args.msg is not None: await cli.show_messages(args.msg)
            elif args.search: await cli.search_messages(args.search)
            elif args.send: await cli.send_msg(args.send)
            elif args.reply: await cli.reply(args.reply[0], args.reply[1])
            elif args.forward: await cli.forward_to_saved(args.forward)
            elif args.edit: await cli.edit_message(args.edit[0], args.edit[1])
            elif args.delete: await cli.delete_message(args.delete)
            elif args.react: await cli.react_to_message(args.react[0], args.react[1])
            elif args.img: await cli.download_img(args.img)
            elif args.send_img: await cli.send_img(args.send_img)
            elif args.mp: await cli.show_my_profile()
            elif args.contacts: await cli.list_contacts()
            elif args.cu: await cli.change_username(args.cu)
            elif args.name:
                first = args.name[0]
                last = ' '.join(args.name[1:]) if len(args.name) > 1 else ""
                await cli.change_name(first, last)
            elif args.bio: await cli.change_bio(args.bio)
            elif args.theme: await cli.change_theme(args.theme)
            elif args.text:
                username = args.text[0]
                text = ' '.join(args.text[1:])
                await cli.send_to_user(username, text)
            elif args.logout: await cli.logout()
            elif args.saved: await cli.go_to_saved_messages()
            elif args.slots: await cli.slot_machine()
            elif args.lang:
                if args.lang in LANGUAGES:
                    cli.language = args.lang
                    cli.save_config()
                    cli.console.print(f"Language changed to {LANGUAGES[args.lang]['name']}")
            
            await cli.client.disconnect()
        except KeyboardInterrupt:
            print(f"\\ninterrupted")
        except Exception as e:
            print(f"error: {e}")
    else:
        cli = TelegramCLI()
        try:
            await cli.run()
        except KeyboardInterrupt:
            print(f"\\nexit")

if __name__ == '__main__':
    asyncio.run(main())
