# Asaxiy Tech Support Bot — serverga deploy va Git

Bu qo‘llanma VPS serverda **Django** va **boshqa Telegram bot** allaqachon ishlayotgan holatda, **ularning ishiga xalaqit qilmasdan** faqat shu loyihani deploy qilish uchun.

---

## Nima uchun boshqa loyihalarga xalaqit bermaydi?

| Masala | Bu bot | Django / boshqa bot |
|--------|--------|---------------------|
| **Port** | Polling ishlatadi — **ochiq HTTP port kerak emas** | Django odatda 80/443/8000 |
| **Jarayon** | Alohida **systemd xizmati**, alohida katalog | O‘z xizmatlari |
| **Python** | **Alohida `venv`** loyiha ichida | O‘z virtualenv |
| **Ma’lumotlar** | `support.db` faqat shu katalogda | Alohida |
| **Token** | Faqat shu botning tokeni | Boshqa tokenlar |

**Muhim:** Bir xil `BOT_TOKEN` bilan ikkita joyda (masalan, kompyuter + server) botni **bir vaqtda** ishga tushirmang — Telegram `Conflict: other getUpdates` xatosini beradi. Deploydan oldin lokal botni to‘xtating yoki serverda yangi token ishlating.

---

## 1. Git: loyihani tayyorlash va push

### 1.1. Lokal mashinada (Windows yoki boshqa)

```bash
cd /path/to/techsupportbot
git init
git add .
git commit -m "Initial: Asaxiy tech support bot"
```

`.env` va `support.db` `.gitignore` da — ular **push qilinmaydi**. Token va parollar serverda alohida yaratiladi.

### 1.2. Remote (GitHub / GitLab / Bitbucket)

1. Bo‘sh repo yarating (masalan: `asaxiy-techsupportbot`).
2. Remote qo‘shing va push:

```bash
git branch -M main
git remote add origin https://github.com/SIZNING_ORG/asaxiy-techsupportbot.git
git push -u origin main
```

SSH ishlatsangiz:

```bash
git remote add origin git@github.com:SIZNING_ORG/asaxiy-techsupportbot.git
git push -u origin main
```

### 1.3. Keyingi o‘zgarishlar

```bash
git add .
git commit -m "Tavsif"
git push
```

---

## 2. Server (VPS) tayyori

Quyidagilar **root yoki sudo** bilan bajariladi (Ubuntu/Debian misol).

### 2.1. Python 3.10+ (agar yo‘q bo‘lsa)

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip git
```

**Tavsiya:** Serverda Python 3.11 yoki 3.12 ishlating (3.14 ixtiyoriy; loyiha 3.10+ bilan ishlaydi).

### 2.2. Loyihani alohida katalogga klonlash

Django yoki boshqa bot **boshqa papkada** — bu yerda faqat shu bot:

```bash
sudo mkdir -p /opt/asaxiy-techsupportbot
sudo chown $USER:$USER /opt/asaxiy-techsupportbot
cd /opt/asaxiy-techsupportbot
git clone https://github.com/SIZNING_ORG/asaxiy-techsupportbot.git .
# yoki SSH:
# git clone git@github.com:SIZNING_ORG/asaxiy-techsupportbot.git .
```

---

## 3. Virtual environment va bog‘liqliklar

**Django venv ichiga kirmang** — bu yerda alohida:

```bash
cd /opt/asaxiy-techsupportbot
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

---

## 4. `.env` faylini serverda yaratish

Gitda `.env` yo‘q. Serverda nusxa oling va to‘ldiring:

```bash
cd /opt/asaxiy-techsupportbot
cp .env.example .env
nano .env
```

To‘ldirilishi kerak bo‘lganlar (minimal):

- `BOT_TOKEN` — faqat **shu bot** uchun (boshqa bot tokeni bilan aralashtirmang).
- `SUPPORT_GROUP_ID`, `SUPPORT_TOPIC_*`, `ADMIN_*`
- `AZURE_OPENAI_*` (AI kerak bo‘lsa)

SQLite ishlatiladi: `support.db` avtomatik loyiha ildizida yaratiladi — **PostgreSQL Django bilan aralashmaydi**.

Huquqlar:

```bash
chmod 600 .env
```

---

## 5. systemd: fon rejimida ishga tushirish (Django ga tegmasdan)

Alohida xizmat nomi — boshqa servislar bilan nom ziddiyati bo‘lmasin.

Fayl: `/etc/systemd/system/asaxiy-techsupportbot.service`

```ini
[Unit]
Description=Asaxiy Tech Support Telegram Bot
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/opt/asaxiy-techsupportbot
Environment=PYTHONUNBUFFERED=1
ExecStart=/opt/asaxiy-techsupportbot/venv/bin/python /opt/asaxiy-techsupportbot/main.py
Restart=always
RestartSec=10

# Xavfsizlik: faqat loyiha papkasiga yozish
ReadWritePaths=/opt/asaxiy-techsupportbot

[Install]
WantedBy=multi-user.target
```

**Eslatma:**

- `User=www-data` o‘rniga o‘zingizning deploy foydalanuvchingizni qo‘yishingiz mumkin (masalan `deploy`). Asosiy shart: `.env` va `support.db` uchun o‘sha userda o‘qish/yozish huquqi bo‘lsin.
- Agar `www-data` ishlatsangiz:

```bash
sudo chown -R www-data:www-data /opt/asaxiy-techsupportbot
sudo chmod 600 /opt/asaxiy-techsupportbot/.env
```

Xizmatni yoqish:

```bash
sudo systemctl daemon-reload
sudo systemctl enable asaxiy-techsupportbot
sudo systemctl start asaxiy-techsupportbot
sudo systemctl status asaxiy-techsupportbot
```

Loglar:

```bash
journalctl -u asaxiy-techsupportbot -f
```

**To‘xtatish / qayta ishga tushirish:**

```bash
sudo systemctl stop asaxiy-techsupportbot
sudo systemctl start asaxiy-techsupportbot
sudo systemctl restart asaxiy-techsupportbot
```

---

## 6. Yangilanishlar (git pull + restart)

```bash
cd /opt/asaxiy-techsupportbot
sudo systemctl stop asaxiy-techsupportbot
git pull
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl start asaxiy-techsupportbot
```

---

## 7. Django va boshqa bot bilan ziddiyatlarni oldini olish

1. **Bitta token — bitta joy:** Shu bot tokeni faqat **shu serverdagi bitta** `asaxiy-techsupportbot` jarayonida ishlasin.
2. **Port:** Bu bot HTTP server ochmaydi — Nginx/Gunicorn/Django portlariga tegmaydi.
3. **CPU/RAM:** Juda yengil; kerak bo‘lsa `LimitNOFILE` yoki `Nice` systemd da sozlanadi (odatda shart emas).
4. **`source/messages.json`:** Katta bo‘lsa, git LFS yoki serverda alohida yuklash mumkin; agar repoda bo‘lsa `git pull` bilan keladi.

---

## 8. Tezkor tekshiruv ro‘yxati

- [ ] `git push` — `.env` repoda yo‘qligini tekshirish
- [ ] Serverda `venv` + `pip install -r requirements.txt`
- [ ] Serverda `.env` to‘liq
- [ ] `systemctl status asaxiy-techsupportbot` — `active (running)`
- [ ] Telegramda bot javob beradi
- [ ] Lokal/konflikt: boshqa joyda shu token bilan bot ishlamayapti

---

## 9. Muammo bo‘lsa

| Belgilar | Harakat |
|----------|---------|
| `Conflict: other getUpdates` | Boshqa mashina yoki ikkinchi jarayon — to‘xtating yoki token almashtiring |
| Bot javob bermaydi | `journalctl -u asaxiy-techsupportbot -n 100` |
| Permission denied `.env` | `chown` / `chmod 600` va `User=` systemd da mos |

Savollar uchun README.md dagi tuzilma bo‘limiga ham qarang.
