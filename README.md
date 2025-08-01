# 🕵️ Anonymous Confessions Telegram Bot with Moderation

A lightweight, privacy-first Telegram bot that lets users send **anonymous confessions** to a public channel — with built-in **moderation**, **multi-language support**, and **anti-spam** features.

---
U can find him: https://t.me/GhostNoteRobor

## ✅ Features

- 🔒 **Fully Anonymous** – No logs or user data stored
    
- 🌍 **Multi-language Support** – English, Ukrainian, and Russian
    
- 🚫 **Anti-Spam Protection** – Basic spam filtering built-in
    
- 👮 **Moderation System** – Admins approve/reject confessions before publishing
    
- 💬 **Private Use Only** – Works exclusively in Direct Messages (DMs)
    

---

## 🚀 Installation

```Bash
pip install aiogram python-dotenv
```
## ⚙️ Setup

1. **Create a `.env` file** in the root directory with the following content:
```.env
BOT_TOKEN=your_telegram_bot_token_here
MODERATION_CHAT_ID=-1001234567890   # Chat where confessions are sent for approval
TARGET_CHANNEL_ID=-1001234567890    # Channel where approved confessions are published

```
2. **Run the bot**:
```
python main.py
```
## 🛡 Moderation Workflow

1. User sends an anonymous message via private chat with the bot.
    
2. Message is forwarded to a **moderation chat**.
    
3. Admins approve or reject confessions with inline buttons.
    
4. Approved messages are posted in the **target channel**.

## 🗣 Supported Languages

- 🇬🇧 English
    
- 🇺🇦 Ukrainian
    
- 🇷🇺 Russian
    

Language is automatically detected based on user input or system locale.


## 🧩 Dependencies

- [aiogram](https://pypi.org/project/aiogram/) – Telegram Bot API framework
    
- [python-dotenv](https://pypi.org/project/python-dotenv/) – For managing environment variables
---

## 💡 Notes

- Ensure the bot has permission to post in the **target channel**.
    
- Add the bot and moderators to the **moderation group**.
    
- Designed to respect user privacy — no message logs or user IDs are stored.
