"""
Anonymous Confessions Telegram Bot with Moderation
==================================================

Installation:
pip install aiogram python-dotenv

Setup:
1. Create .env file with:
   BOT_TOKEN=your_bot_token_here
   MODERATION_CHAT_ID=-1001234567890
   TARGET_CHANNEL_ID=-1001234567890

2. Run:
   python main.py

Features:
- Fully anonymous (no data storage, no logs)
- Multi-language support (EN, UK, RU)
- Anti-spam protection
- Moderation system
- Direct messages only
"""

import asyncio
import os
import re
import time
from typing import Dict, Optional

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandStart
from aiogram.types import (
    Message, 
    CallbackQuery, 
    InlineKeyboardMarkup, 
    InlineKeyboardButton,
    InputMediaPhoto
)
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
BOT_TOKEN = os.getenv('BOT_TOKEN')
MODERATION_CHAT_ID = int(os.getenv('MODERATION_CHAT_ID'))
TARGET_CHANNEL_ID = int(os.getenv('TARGET_CHANNEL_ID'))

# Bot initialization
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# In-memory storage for rate limiting (no persistent data)
user_last_message: Dict[int, float] = {}

# Multi-language support
MESSAGES = {
    'en': {
        'start': '🤐 Send me your anonymous confession.\n\nYour message will be reviewed by moderators before publication. \n\nAnd posted here: @GhostNoteAnon',
        'sent_for_moderation': '✅ Your message has been sent for moderation.',
        'approved': '✅ Your confession has been published!',
        'rejected': '❌ Your confession was rejected by moderators.',
        'rate_limit': '⏱ Please wait 30 seconds before sending another message.',
        'invalid_length': '📝 Message must be between 5 and 1000 characters.',
        'dm_only': '🔒 This bot works only in private messages.',
        'suspicious_content': '⚠️ Suspicious content detected.',
        'mod_new_confession': '📝 New confession for review:',
        'mod_approve': '✅ Approve',
        'mod_reject': '❌ Reject'
    },
    'uk': {
        'start': '🤐 Надішліть мені ваше анонімне повідомлення.\n\nВаше повідомлення буде переглянуто модераторами перед публікацією.\n\nТа опубліковано тут: @GhostNoteAnon',
        'sent_for_moderation': '✅ Ваше повідомлення надіслано на модерацію.',
        'approved': '✅ Ваше зізнання опубліковано!',
        'rejected': '❌ Ваше зізнання було відхилено модераторами.',
        'rate_limit': '⏱ Зачекайте 30 секунд перед надсиланням наступного повідомлення.',
        'invalid_length': '📝 Повідомлення має бути від 5 до 1000 символів.',
        'dm_only': '🔒 Цей бот працює тільки в особистих повідомленнях.',
        'suspicious_content': '⚠️ Виявлено підозрілий вміст.',
        'mod_new_confession': '📝 Нове зізнання на розгляд:',
        'mod_approve': '✅ Схвалити',
        'mod_reject': '❌ Відхилити'
    },
    'ru': {
        'start': '🤐 Отправьте мне ваше анонимное признание.\n\nВаше сообщение будет рассмотрено модераторами перед публикацией.\n\nИ опубликовано тут: @GhostNoteAnon',
        'sent_for_moderation': '✅ Ваше сообщение отправлено на модерацию.',
        'approved': '✅ Ваше признание опубликовано!',
        'rejected': '❌ Ваше признание было отклонено модераторами.',
        'rate_limit': '⏱ Подождите 30 секунд перед отправкой следующего сообщения.',
        'invalid_length': '📝 Сообщение должно быть от 5 до 1000 символов.',
        'dm_only': '🔒 Этот бот работает только в личных сообщениях.',
        'suspicious_content': '⚠️ Обнаружен подозрительный контент.',
        'mod_new_confession': '📝 Новое признание на рассмотрение:',
        'mod_approve': '✅ Одобрить',
        'mod_reject': '❌ Отклонить'
    }
}


def get_user_language(language_code: Optional[str]) -> str:
    """Determine user language based on language_code"""
    if not language_code:
        return 'en'
    
    lang = language_code.lower()
    if lang.startswith('uk'):
        return 'uk'
    elif lang.startswith('ru'):
        return 'ru'
    else:
        return 'en'

def get_message(lang: str, key: str) -> str:
    """Get localized message"""
    return MESSAGES.get(lang, MESSAGES['en']).get(key, MESSAGES['en'][key])

def escape_markdown_v2(text: str) -> str:
    """Escape special characters for MarkdownV2"""
    # Characters that need to be escaped in MarkdownV2
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    for char in escape_chars:
        text = text.replace(char, f'\\{char}')
    return text
    """Escape special characters for MarkdownV2"""
    # Characters that need to be escaped in MarkdownV2
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    for char in escape_chars:
        text = text.replace(char, f'\\{char}')
    return text

def is_suspicious_content(text: str) -> bool:
    """Check if message contains suspicious content"""
    # Check for URLs
    if re.search(r'http[s]?://|www\.|t\.me/|@\w+', text, re.IGNORECASE):
        return True
    
    # Check if message is mostly emojis
    emoji_count = len(re.findall(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF\U00002702-\U000027B0\U000024C2-\U0001F251]', text))
    if emoji_count > len(text) * 0.3:
        return True
    
    # Check for repeated characters/words
    if re.search(r'(.)\1{4,}', text) or re.search(r'\b(\w+)\s+\1\b', text, re.IGNORECASE):
        return True
    
    return False

def check_rate_limit(user_id: int) -> bool:
    """Check if user is rate limited (30 seconds)"""
    current_time = time.time()
    last_message_time = user_last_message.get(user_id, 0)
    
    if current_time - last_message_time < 30:
        return True
    
    user_last_message[user_id] = current_time
    return False

@dp.message(CommandStart())
async def start_command(message: Message):
    """Handle /start command"""
    # Only work in private chats
    if message.chat.type != 'private':
        return
    
    lang = get_user_language(message.from_user.language_code)
    await message.answer(get_message(lang, 'start'))

@dp.message(F.chat.type == 'private')
async def handle_confession(message: Message):
    """Handle confession messages in private chat"""
    user_id = message.from_user.id
    text = message.text or message.caption or ""
    
    # Skip if no text and no photo
    if not text and not message.photo:
        return
    
    # If only photo without text, allow it
    if message.photo and not text:
        text = ""
    
    lang = get_user_language(message.from_user.language_code)
    
    # Check message length (only if there's text)
    if text and (len(text) < 5 or len(text) > 1000):
        await message.answer(get_message(lang, 'invalid_length'))
        return
    
    # Allow messages with only photo (no text length requirement)
    if not text and not message.photo:
        await message.answer(get_message(lang, 'invalid_length'))
        return
    
    # Check rate limit
    if check_rate_limit(user_id):
        await message.answer(get_message(lang, 'rate_limit'))
        return
    
    # Check for suspicious content (only in text)
    if text and is_suspicious_content(text):
        return  # Silently ignore suspicious content
    
    # Send to moderation
    await send_to_moderation(text, user_id, lang, message.photo)
    await message.answer(get_message(lang, 'sent_for_moderation'))

async def send_to_moderation(confession_text: str, user_id: int, user_lang: str, photo=None):
    """Send confession to moderation chat"""
    # Create callback data with user info (temporary, in memory only)
    callback_data_approve = f"approve_{user_id}_{user_lang}_{int(time.time())}"
    callback_data_reject = f"reject_{user_id}_{user_lang}_{int(time.time())}"
    
    # Create spoiler callback data
    callback_data_spoiler = f"spoiler_{user_id}_{user_lang}_{int(time.time())}"
    
    # Moderation keyboard
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="✅ Approve",
                callback_data=callback_data_approve
            ),
            InlineKeyboardButton(
                text="🫣 Spoiler", 
                callback_data=callback_data_spoiler
            ),
            InlineKeyboardButton(
                text="❌ Reject", 
                callback_data=callback_data_reject
            )
        ]
    ])
    
    # Format message for moderators
    if confession_text:
        mod_message = f"📝 New confession for review:\n\n{confession_text}\n\n👤 User Language: {user_lang.upper()}"
    else:
        mod_message = f"📝 New confession for review:\n\n[Photo only]\n\n👤 User Language: {user_lang.upper()}"
    
    # Send to moderation chat
    if photo:
        # Send photo with caption
        await bot.send_photo(
            chat_id=MODERATION_CHAT_ID,
            photo=photo[-1].file_id,  # Get highest resolution photo
            caption=mod_message,
            reply_markup=keyboard
        )
    else:
        # Send text only
        await bot.send_message(
            chat_id=MODERATION_CHAT_ID,
            text=mod_message,
            reply_markup=keyboard
        )

@dp.callback_query(F.data.startswith(('approve_', 'reject_', 'spoiler_')))
async def handle_moderation(callback: CallbackQuery):
    """Handle moderation decisions"""
    data_parts = callback.data.split('_')
    action = data_parts[0]  # approve, reject, or spoiler
    user_id = int(data_parts[1])
    user_lang = data_parts[2]
    timestamp = data_parts[3]
    
    # Check if message has photo
    has_photo = callback.message.photo is not None
    
    if has_photo:
        # Extract confession text from photo caption
        confession_text = callback.message.caption or ""
        # Remove the moderation header to get clean confession
        if confession_text:
            confession_lines = confession_text.split('\n')
            clean_confession = '\n'.join(confession_lines[2:-2]) if len(confession_lines) > 4 else ""
        else:
            clean_confession = ""
        
        photo_file_id = callback.message.photo[-1].file_id
    else:
        # Extract confession text from the callback message
        confession_text = callback.message.text
        # Remove the moderation header to get clean confession
        confession_lines = confession_text.split('\n')
        clean_confession = '\n'.join(confession_lines[2:-2])  # Remove header and footer
        photo_file_id = None
    
    if action == 'approve':
        # Publish to target channel
        if has_photo:
            if clean_confession:
                await bot.send_photo(
                    chat_id=TARGET_CHANNEL_ID,
                    photo=photo_file_id,
                    caption=clean_confession
                )
            else:
                await bot.send_photo(
                    chat_id=TARGET_CHANNEL_ID,
                    photo=photo_file_id
                )
        else:
            await bot.send_message(
                chat_id=TARGET_CHANNEL_ID,
                text=clean_confession
            )
        
        # Notify user
        try:
            await bot.send_message(
                chat_id=user_id,
                text=get_message(user_lang, 'approved')
            )
        except:
            pass  # User might have blocked the bot
        
        # Update moderation message
        if has_photo:
            await callback.message.edit_caption(
                caption=f"✅ APPROVED\n\n{confession_text}",
                reply_markup=None
            )
        else:
            await callback.message.edit_text(
                f"✅ APPROVED\n\n{confession_text}",
                reply_markup=None
            )
    
    elif action == 'spoiler':
        # Publish to target channel with spoiler formatting
        if has_photo:
            if clean_confession:
                # Escape markdown and add spoiler formatting
                escaped_text = escape_markdown_v2(clean_confession)
                spoiler_text = f"||{escaped_text}||"
                await bot.send_photo(
                    chat_id=TARGET_CHANNEL_ID,
                    photo=photo_file_id,
                    caption=spoiler_text,
                    parse_mode="MarkdownV2",
                    has_spoiler=True  # Make photo itself a spoiler
                )
            else:
                await bot.send_photo(
                    chat_id=TARGET_CHANNEL_ID,
                    photo=photo_file_id,
                    has_spoiler=True  # Make photo itself a spoiler
                )
        else:
            # Escape markdown and add spoiler formatting
            escaped_text = escape_markdown_v2(clean_confession)
            spoiler_text = f"||{escaped_text}||"
            await bot.send_message(
                chat_id=TARGET_CHANNEL_ID,
                text=spoiler_text,
                parse_mode="MarkdownV2"
            )
        
        # Notify user
        try:
            await bot.send_message(
                chat_id=user_id,
                text=get_message(user_lang, 'approved')
            )
        except:
            pass  # User might have blocked the bot
        
        # Update moderation message
        if has_photo:
            await callback.message.edit_caption(
                caption=f"🫣 APPROVED WITH SPOILER\n\n{confession_text}",
                reply_markup=None
            )
        else:
            await callback.message.edit_text(
                f"🫣 APPROVED WITH SPOILER\n\n{confession_text}",
                reply_markup=None
            )
        
    elif action == 'reject':
        # Notify user
        try:
            await bot.send_message(
                chat_id=user_id,
                text=get_message(user_lang, 'rejected')
            )
        except:
            pass  # User might have blocked the bot
        
        # Update moderation message
        if has_photo:
            await callback.message.edit_caption(
                caption=f"❌ REJECTED\n\n{confession_text}",
                reply_markup=None
            )
        else:
            await callback.message.edit_text(
                f"❌ REJECTED\n\n{confession_text}",
                reply_markup=None
            )
    
    await callback.answer()

@dp.message()
async def handle_non_private(message: Message):
    """Handle messages in non-private chats"""
    if message.chat.type != 'private':
        lang = get_user_language(message.from_user.language_code)
        await message.answer(get_message(lang, 'dm_only'))

async def main():
    """Main bot function"""
    # Start polling
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())