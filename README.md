# Asaxiy Tech Support Telegram Bot

Asaxiy texnik qo‘llab-quvvatlash guruhiga keladigan muammolarni tartiblash, **yagona bazaga** yozish va **to‘liq avtomatik javob** berish uchun Telegram bot.

**VPS deploy, Git push va Django/boshqa botga xalaqit bermaslik:** batafsil qo‘llanma — **[INSTRUCTIONS.md](INSTRUCTIONS.md)**.

## Vazifalar

- **Muammolarni sort qilish** — MDM, To‘lov/Qarz/Shartnoma, Login, Boshqa kategoriyalari orqali
- **Yagona baza** — case’lar **SQLite** (`support.db`) da saqlanadi (Django DB bilan aralashmaydi)
- **Avtomatik javob** — AI (Azure OpenAI) guruh chat history (`source/messages.json`) asosida muammo turini aniqlaydi va taxminiy yechim taklif qiladi
- **Guruhga yuborish** — har bir case (vaqt, muammo turi, ariza beruvchi, screenshot) support Telegram guruhiga yuboriladi
- **To‘liq muammo turlari tugmalari** — botda barcha kategoriyalar tugmalar orqali mavjud

Chat history da muammolarni hal qiluvchi admin: **Saidjamol Qosimxonov** (@Saidjamol_Qosimxonov).

## Texnologiyalar

- Python 3.10+
- python-telegram-bot
- SQLite (`support.db`)
- Azure OpenAI (kategoriya + yechim taklifi)
- Chat history: `source/messages.json` (Telegram export)

## O‘rnatish

### 1. Repozitoriyani klonlash / fayllarni ochish

```bash
cd techsupportbot
```

### 2. Virtual muhit va kutubxonalar

```bash
python -m venv venv
venv\Scripts\activate   # Windows
pip install -r requirements.txt
```

### 3. Ma’lumotlar bazasi (SQLite)

Loyiha ildizida `support.db` fayli avtomatik yaratiladi; alohida DB serveri shart emas (Django loyihasidan mustaqil).

### 4. Sozlamalar (.env)

`.env` faylini loyiha ildizida yarating (`.env.example` dan nusxa oling):

```env
BOT_TOKEN=...

SUPPORT_GROUP_ID=-100xxxxxxxxxx
SUPPORT_TOPIC_MDM=13
SUPPORT_TOPIC_PAYMENT=6
SUPPORT_TOPIC_LOGIN=16
SUPPORT_TOPIC_OTHER=19

ADMIN_NAME=Saidjamol Qosimxonov
ADMIN_USERNAME=Saidjamol_Qosimxonov
ADMIN_TG_ID=1077771511

AZURE_OPENAI_ENDPOINT=https://....openai.azure.com/
AZURE_OPENAI_KEY=...
AZURE_OPENAI_DEPLOYMENT=support-model
AZURE_OPENAI_API_VERSION=2024-12-01-preview
```

- `BOT_TOKEN` — @BotFather dan olingan bot token
- `SUPPORT_GROUP_ID` — support guruhining ID si (minus bilan)
- `SUPPORT_TOPIC_*` — agar guruh forum bo‘lsa, mavzular ID lari
- Azure OpenAI — AI takliflar uchun (ixtiyoriy; bo‘lmasa kategoriya “other” va yechim bo‘sh)

### 5. Chat history

`source/messages.json` — Telegram dan export qilingan guruh chat history. Bot AI uchun shu fayldan o‘xshash muammo/javob misollarini oladi.

## Ishga tushirish

```bash
python main.py
```

Bot polling rejimida ishlaydi. Foydalanuvchi:

1. `/start` — salomlashish va “Yangi ariza” tugmasi
2. “Yangi ariza” yoki to‘g‘ridan-to‘g‘ri muammo matni/skrinshot — kategoriya tugmalari yoki AI orqali avtomatik kategoriya + yechim
3. Kategoriya tanlanganda — muammo matnini/skrinshotni yuboradi
4. Case yagona bazaga yoziladi va support guruhiga (vaqt, muammo turi, ariza beruvchi, screenshot) yuboriladi

## Loyiha tuzilishi

```
techsupportbot/
├── main.py              # Kirish nuqtasi
├── config.py            # .env sozlamalari
├── requirements.txt
├── README.md
├── source/
│   └── messages.json    # Guruh chat history (AI kontekst)
├── database/            # Yagona baza (SQLite)
│   ├── __init__.py
│   ├── connection.py   # Ulanish va jadval yaratish
│   ├── models.py       # Case, CaseCategory
│   └── repo.py         # Case CRUD
├── ai/                  # AI (Azure OpenAI + chat history)
│   ├── __init__.py
│   ├── chat_history.py # messages.json o‘qish
│   └── support_ai.py   # Kategoriya + yechim taklifi
└── bot/                 # Telegram bot
    ├── __init__.py
    ├── handlers.py     # /start, tugmalar, matn/foto, AI, DB, guruh
    ├── keyboards.py    # Kategoriya tugmalari
    └── group_sender.py # Case ni guruhga yuborish
```

Har bir modul va muhim funksiya/docstring orqali dokumentatsiyalangan.

## Litsenziya

Loyiha ichki ishlatish uchun.
