import asyncio

import logging

import os

import random

import sqlite3

import time

from datetime import datetime

from aiogram import Bot, Dispatcher, F, types

from aiogram.filters import Command

from aiogram.types import (

    InlineKeyboardMarkup,

    InlineKeyboardButton,

    ReplyKeyboardMarkup,

    KeyboardButton,

    LabeledPrice,

    PreCheckoutQuery,

    BotCommand,

    InputMediaPhoto,

    FSInputFile,

)

 

logging.basicConfig(level=logging.INFO)

 

BOT_TOKEN = "9297074957:AAH1MatXEIEX3QI8m2uj0n9iLJGH1I72hDI"

ADMIN_ID = 6921885296

COOLDOWN = 3 * 3600

DB_FILE = "game_v2.db"

 

BANNERS = {

    "welcome": "",

    "shop": "",

    "levels": "",

}

 

LEVELS = {

    1: {"name": "Наруто (Генин на минималках)", "need": 500, "reward": "Мишка (15 ⭐)", "photo": "AgACAgIAAxkBAAMxavmpcpkyR321bXlTcO03f0kLewYAAjweaxuKkshLF3b_juZ9rVIBAAMCAAN4AAM9BA"},

    2: {"name": "Танджиро (Угольный барон)", "need": 2000, "reward": "Кольцо (100 ⭐)", "photo": "AgACAgIAAxkBAAMzavmpev7gL0gD-vQSk67j96d0wv0AAj0eaxuKkshL00Zu3USVDb8BAAMCAAN5AAM9BA"},

    3: {"name": "Годжо Сатору (Без повязки)", "need": 6000, "reward": "NFT Pet Snake", "photo": "AgACAgIAAxkBAAM1avmpfkYMtA3verNLxRV7Tzo7liwAAj4eaxuKkshLL-zRwHyaDIgBAAMCAAN5AAM9BA"},

    4: {"name": "Итачи Учиха (Мастер яичницы)", "need": 10000, "reward": "NFT Input Key", "photo": "AgACAgIAAxkBAAM3avmpg_3ZLkv5F-4cuC3KuHTe794AAj8eaxuKkshLnTXQ_6BWI3oBAAMCAAN5AAM9BA"},

    5: {"name": "Сейлор Мун (В поисках обеда)", "need": 15000, "reward": "NFT Moon Pendant", "photo": "AgACAgIAAxkBAAM5avmpiJYXaFcLGINflYIF8kJk4kAAAkAeaxuKkshLXfUwICm8tfQBAAMCAAN5AAM9BA"},

    6: {"name": "Аня Форджер (Агент Сумрак-младший)", "need": 22000, "reward": "NFT Spy Agaric", "photo": "AgACAgIAAxkBAAM7avmpi2Kb1l36v_sHCfmFpXno8kkAAkEeaxuKkshLp4-8UNuOrlABAAMCAAN5AAM9BA"},

}

 

FARM_TEXTS = [

    "🍜 Герой плотно поел рамена в Ичираку и выдал +{gain}⚡!",

    "🧘‍♂️ Час медитации под водопадом (правда, он проспал) принесли +{gain}⚡!",

    "🔥 Сенсей наорал так громко, что чакра подскочила на +{gain}⚡!",

    "🍙 Нашёл в кармане вчерашний онигири и зарядился на +{gain}⚡!",

    "⚡ Вспомнил грустный флешбэк из детства и превозмог на +{gain}⚡!",

    "🐱 Погладил уличного кота и словил дзен на +{gain}⚡!",

    "💪 Сделал 100 отжиманий (ладно, 3 отжимания и 97 приседаний на диван): +{gain}⚡!"

]

 

WAIT_TEXTS = [

    "😴 Герой дрыхнет без задних ног! Потерпи ещё {h}ч {m}м.",

    "🍜 Он сейчас на обеде в Ичираку, не мешай! Возвращайся через {h}ч {m}м.",

    "🪫 Чакра на нуле, батарейка села. Зарядка закончится через {h}ч {m}м.",

    "🚽 Герой отошёл по важным делам шиноби. Будет через {h}ч {m}м.",

    "🎮 Он залип в приставку и отказывается тренироваться! Жди {h}ч {m}м."

]

 

bot = Bot(token=BOT_TOKEN)

dp = Dispatcher()

admin_state = {}

db = sqlite3.connect(DB_FILE)

cur = db.cursor()

 

 

def init_db():

    cur.execute("""

    CREATE TABLE IF NOT EXISTS users (

        user_id INTEGER PRIMARY KEY,

        username TEXT,

        level INTEGER DEFAULT 1,

        energy INTEGER DEFAULT 0,

        last_farm INTEGER DEFAULT 0,

        amulet_until INTEGER DEFAULT 0,

        stars_spent INTEGER DEFAULT 0

    )

    """)

 

    cur.execute("""

    CREATE TABLE IF NOT EXISTS claims (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        user_id INTEGER,

        username TEXT,

        level INTEGER,

        reward TEXT,

        status TEXT DEFAULT 'pending'

    )

    """)

 

    cur.execute("""

    CREATE TABLE IF NOT EXISTS payments (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        user_id INTEGER,

        username TEXT,

        item TEXT,

        amount INTEGER,

        created_at INTEGER

    )

    """)

 

    cur.execute("""

    CREATE TABLE IF NOT EXISTS promocodes (

        code TEXT PRIMARY KEY,

        energy INTEGER,

        uses_left INTEGER

    )

    """)

 

    cur.execute("""

    CREATE TABLE IF NOT EXISTS promo_used (

        user_id INTEGER,

        code TEXT,

        PRIMARY KEY (user_id, code)

    )

    """)

    db.commit()

 

 

init_db()

 

 

def get_user(user_id, username=""):

    cur.execute(

        "SELECT user_id, username, level, energy, last_farm, amulet_until, stars_spent FROM users WHERE user_id = ?",

        (user_id,)

    )

    user = cur.fetchone()

    if not user:

        clean_name = username or "Без_ника"

        cur.execute("INSERT INTO users (user_id, username) VALUES (?, ?)", (user_id, clean_name))

        db.commit()

        return (user_id, clean_name, 1, 0, 0, 0, 0)

    _, old_uname, lvl, en, lf, am, st = user

    if username and old_uname != username:

        cur.execute("UPDATE users SET username = ? WHERE user_id = ?", (username, user_id))

        db.commit()

        return (user_id, username, lvl, en, lf, am, st)

    return user

 

 

def make_progress_bar(current: int, total: int, length: int = 10) -> str:

    if total <= 0:

        return "▓▓▓▓▓▓▓▓▓▓ 100%"

    ratio = min(max(current / total, 0.0), 1.0)

    filled = int(round(length * ratio))

    empty = length - filled

    percent = int(ratio * 100)

    bar = "▓" * filled + "░" * empty

    return f"[{bar}] {percent}%"

 

 

def bottom_menu_keyboard() -> ReplyKeyboardMarkup:

    return ReplyKeyboardMarkup(

        keyboard=[

            [KeyboardButton(text="⚡ Впитать энергию")],

            [KeyboardButton(text="🎴 Мой герой"), KeyboardButton(text="🛒 Лавка читера")],

            [KeyboardButton(text="🗺 Дорога славы"), KeyboardButton(text="🎟 Промокод")],

        ],

        resize_keyboard=True,

        input_field_placeholder="Выбери действие или введи /..."

    )

 

 

def main_keyboard(user_id, level, energy, need):

    buttons = []

    if level in LEVELS:

        if energy >= need:

            buttons.append([InlineKeyboardButton(text="🎁 ЗАБРАТЬ ПОДАРОК (Оставить заявку)", callback_data=f"claim_{user_id}")])

        else:

            buttons.append([InlineKeyboardButton(text="⚡ Впитать энергию", callback_data=f"farm_{user_id}")])

        buttons.append([

            InlineKeyboardButton(text="🛒 Лавка читера", callback_data=f"shop_{user_id}"),

            InlineKeyboardButton(text="🎟 Промокод", callback_data=f"promoinfo_{user_id}")

        ])

    buttons.append([InlineKeyboardButton(text="🗺 Дорога славы (Все 10 уровней)", callback_data=f"levels_{user_id}")])

    return InlineKeyboardMarkup(inline_keyboard=buttons)

 

 

def shop_keyboard(user_id):

    return InlineKeyboardMarkup(inline_keyboard=[

        [InlineKeyboardButton(text="🔮 Амулет удачи 48ч (50-150⚡) — 40 ⭐", callback_data=f"buy_amulet_{user_id}")],

        [InlineKeyboardButton(text="📦 Кейс с удачей (1-100⚡) — 25 ⭐", callback_data=f"buy_case_{user_id}")],

        [InlineKeyboardButton(text="⚡ Попытка прорыва уровня — 100 ⭐", callback_data=f"buy_skip_{user_id}")],

        [InlineKeyboardButton(text="⬅️ Вернуться к герою", callback_data=f"back_{user_id}")]

    ])

def get_card_text(user):

    _, uname, level, energy, last_farm, amulet_until, _ = user

    now = int(time.time())

 

    lvl_data = LEVELS.get(level)

    if not lvl_data:

        return (

            f"<blockquote>"

            f"🏆 <b>АНИМЕ-КАЧАЛКА ∙ УРОВЕНЬ {level} / 10</b>\n"

            f"👤 Сенсей: <b>@{uname}</b>"

            f"</blockquote>\n\n"

            "🔒 Вы настолько мощный, что сломали игру! Новые аниме-легенды и жирные NFT уже рисуются в секретной лаборатории. Ждите обнову!"

        )

 

    need = lvl_data.get("need")

    p_bar = make_progress_bar(energy, need)

    amulet_status = "🔥 Активен (50–100⚡)" if amulet_until > now else "💤 Спит (1–50⚡)"

 

    wait_time = (last_farm + COOLDOWN) - now

    if wait_time <= 0:

        timer_text = "🟢 <b>Статус:</b> Герой выспался и готов качаться!"

    else:

        hours = wait_time // 3600

        mins = (wait_time % 3600) // 60

        timer_text = f"⏳ <b>Перекур:</b> ещё {hours}ч {mins}м"

 

    return (

        f"<blockquote>"

        f"🎴 <b>УРОВЕНЬ {level} / 10 ∙ {lvl_data.get('name')}</b>\n"

        f"👤 Сенсей: <b>@{uname}</b>\n"

        f"🎁 Награда: <b>{lvl_data.get('reward')}</b>"

        f"</blockquote>\n\n"

        f"⚡ <b>Шкала чакры:</b>\n"

        f"<code>{p_bar}</code> (<b>{energy} / {need}</b>)\n\n"

        f"🔮 <b>Амулет удачи:</b> {amulet_status}\n"

        f"{timer_text}"

    )

 

 

def get_shop_text():

    return (

        "<blockquote>"

        "🛒 <b>ЛАВКА ЧИТЕРА ∙ TELEGRAM STARS ⭐</b>\n"

        "<i>Ускорь прокачку своего героя без ожидания</i>"

        "</blockquote>\n\n"

        "🔮 <b>Амулет удачи (40 ⭐)</b>\n"

        "└ На 48 часов отменяет лень героя — выпадает строго от <b>50 до 100⚡</b> за сбор!\n\n"

        "📦 <b>Кейс с удачей (25 ⭐)</b>\n"

        "└ Кот в мешке с энергией! Внутри от <b>1 до 100⚡</b> мгновенно и без таймера.\n\n"

        "⚡ <b>Попытка прорыва (100 ⭐)</b>\n"

        "└ Запрещённая техника сенсея! Даёт шанс мгновенно закрыть весь текущий уровень."

    )

 

 

def get_levels_text():

    text = (

        "<blockquote>"

        "🗺 <b>ДОРОГА СЛАВЫ ∙ ВСЕ 10 УРОВНЕЙ</b>\n"

        "<i>Качай героев и забирай подарки в профиль</i>"

        "</blockquote>\n\n"

    )

    for i in range(1, 11):

        lvl_data = LEVELS.get(i)

        if lvl_data:

            text += f"✅ <b>Ур. {i}:</b> {lvl_data.get('name')}\n   └ {lvl_data.get('need')}⚡ ➔ 🎁 <b>{lvl_data.get('reward')}</b>\n"

        else:

            text += f"🔒 <b>Ур. {i}:</b> Секретный босс <i>(Скоро...)</i>\n"

    return text

 

 

async def send_or_edit_screen(target, text: str, kb: InlineKeyboardMarkup, photo_id: str = "", is_edit: bool = False):

    if not is_edit:

        if photo_id:

            await target.answer_photo(photo=photo_id, caption=text, parse_mode="HTML", reply_markup=kb)

        else:

            await target.answer(text=text, parse_mode="HTML", reply_markup=kb)

        return

 

    if photo_id:

        if target.photo:

            await target.edit_media(media=InputMediaPhoto(media=photo_id, caption=text, parse_mode="HTML"), reply_markup=kb)

        else:

            await target.delete()

            await target.answer_photo(photo=photo_id, caption=text, parse_mode="HTML", reply_markup=kb)

    else:

        if target.photo:

            await target.delete()

            await target.answer(text=text, parse_mode="HTML", reply_markup=kb)

        else:

            await target.edit_text(text=text, parse_mode="HTML", reply_markup=kb)

 

 

async def send_or_edit_card(target, user, is_edit=False):

    uid, _, lvl, energy, _, _, _ = user

    lvl_data = LEVELS.get(lvl)

    need = lvl_data.get("need") if lvl_data else 0

    photo_id = lvl_data.get("photo") if lvl_data else ""

    text = get_card_text(user)

    kb = main_keyboard(uid, lvl, energy, need)

    await send_or_edit_screen(target, text, kb, photo_id=photo_id, is_edit=is_edit)

 

 

def check_owner(call: types.CallbackQuery, target_id: int):

    return call.from_user.id == target_id

@dp.message(Command("start"))

async def cmd_start(message: types.Message):

    user = get_user(message.from_user.id, message.from_user.username)

    _, uname, _, _, _, _, _ = user

    welcome_text = (

        f"👋 <b>Йо, @{uname}! Добро пожаловать в Аниме-Качалку!</b>\n\n"

        "<blockquote>"

        "1️⃣ Раз в 3 часа жми <b>«⚡ Впитать энергию»</b> — герой пойдёт тренироваться (или есть рамен) и принесёт от 1 до 50⚡.\n"

        "2️⃣ Заполнишь шкалу — забирай реальные <b>подарки Telegram и редкие NFT</b>!\n"

        "3️⃣ Лень ждать? Загляни в <b>🛒 Лавку читера</b> за Звёздами."

        "</blockquote>\n\n"

        "👇 <i>Используй удобное меню снизу или команды через /</i>"

    )

    kb_reply = bottom_menu_keyboard() if message.chat.type == "private" else None

    welcome_banner = BANNERS.get("welcome")

    if welcome_banner:

        await message.answer_photo(photo=welcome_banner, caption=welcome_text, parse_mode="HTML", reply_markup=kb_reply)

    else:

        await message.answer(welcome_text, parse_mode="HTML", reply_markup=kb_reply)

 

    await send_or_edit_card(message, user, is_edit=False)

 

 

@dp.message(Command("card"))

@dp.message(F.text == "🎴 Мой герой")

async def cmd_card(message: types.Message):

    user = get_user(message.from_user.id, message.from_user.username)

    await send_or_edit_card(message, user, is_edit=False)

 

 

@dp.message(Command("farm"))

@dp.message(F.text == "⚡ Впитать энергию")

async def cmd_farm_text(message: types.Message):

    user = get_user(message.from_user.id, message.from_user.username)

    uid, uname, level, energy, last_farm, amulet_until, _ = user

    now = int(time.time())

 

    lvl_data = LEVELS.get(level)

    if not lvl_data:

        return await message.reply("🔒 Все доступные герои уже на пике формы, ждите обновления!")

    need = lvl_data.get("need")

    if energy >= need:

        return await message.reply("🎁 Шкала полная! Хватит качать, жми кнопку подарка в 🎴 Мой герой (/card)!")

    if now - last_farm < COOLDOWN:

        rem = (last_farm + COOLDOWN) - now

        msg = random.choice(WAIT_TEXTS).format(h=rem // 3600, m=(rem % 3600) // 60)

        return await message.reply(f"@{uname}, {msg}")

 

    gain = random.randint(50, 150) if amulet_until > now else random.randint(1, 50)

    new_energy = min(energy + gain, need)

 

    cur.execute("UPDATE users SET energy = ?, last_farm = ? WHERE user_id = ?", (new_energy, now, uid))

    db.commit()

 

    phrase = random.choice(FARM_TEXTS).format(gain=gain)

    p_bar = make_progress_bar(new_energy, need)

    await message.reply(

        f"👤 @{uname}: {phrase}\n<code>{p_bar}</code> (<b>{new_energy}/{need}⚡</b>)",

        parse_mode="HTML"

    )

 

 

@dp.message(Command("shop"))

@dp.message(F.text == "🛒 Лавка читера")

async def cmd_shop_text(message: types.Message):

    uid = message.from_user.id

    get_user(uid, message.from_user.username)

    await send_or_edit_screen(

        message,

        get_shop_text(),

        shop_keyboard(uid),

        photo_id=BANNERS.get("shop"),

        is_edit=False

    )

 

 

@dp.message(Command("levels"))

@dp.message(F.text == "🗺 Дорога славы")

async def cmd_levels_text(message: types.Message):

    uid = message.from_user.id

    get_user(uid, message.from_user.username)

    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🎴 Моя карточка", callback_data=f"back_{uid}")]])

    await send_or_edit_screen(

        message,

        get_levels_text(),

        kb,

        photo_id=BANNERS.get("levels"),

        is_edit=False

    )

 

 

@dp.message(F.text == "🎟 Промокод")

async def btn_promo_hint(message: types.Message):

    await message.reply(

        "🎟 <b>Активация промокода</b>\n\n"

        "Чтобы получить бонусную энергию, введи команду с кодом из нашего канала:\n"

        "<code>/promo ТВОЙ_КОД</code>",

        parse_mode="HTML"

    )

 

 

@dp.message(Command("promo"))

async def cmd_promo(message: types.Message):

    user = get_user(message.from_user.id, message.from_user.username)

    uid, uname, level, energy, _, _, _ = user

 

    parts = (message.text or "").split(maxsplit=1)

    if len(parts) < 2:

        return await message.reply(

            "🎟 <b>Активация промокода</b>\n\nНапиши команду вместе с кодом, например:\n<code>/promo RAMEN2026</code>",

            parse_mode="HTML"

        )

 

    _, raw_code = parts

    code = raw_code.strip().upper()

 

    lvl_data = LEVELS.get(level)

    if not lvl_data:

        return await message.reply("🔒 Все доступные уровни уже пройдены, ждите обновления!")

 

    need = lvl_data.get("need")

    if energy >= need:

        return await message.reply("🎁 У тебя уже полная шкала энергии! Сначала забери подарок в 🎴 Мой герой (/card).")

 

    cur.execute("SELECT energy, uses_left FROM promocodes WHERE code = ?", (code,))

    promo = cur.fetchone()

    if not promo:

        return await message.reply("❌ Такого промокода не существует или он написан с ошибкой!")

 

    bonus_energy, uses_left = promo

    if uses_left <= 0:

        return await message.reply("💨 Увы, этот промокод уже разобрали! Следи за постами в канале, чтобы успеть первым.")

 

    cur.execute("SELECT 1 FROM promo_used WHERE user_id = ? AND code = ?", (uid, code))

    if cur.fetchone():

        return await message.reply("⚠️ Ты уже активировал этот промокод ранее!")

 

    new_energy = min(energy + bonus_energy, need)

    cur.execute("UPDATE users SET energy = ? WHERE user_id = ?", (new_energy, uid))

    cur.execute("UPDATE promocodes SET uses_left = uses_left - 1 WHERE code = ?", (code,))

    cur.execute("INSERT INTO promo_used (user_id, code) VALUES (?, ?)", (uid, code))

    db.commit()

 

    p_bar = make_progress_bar(new_energy, need)

    await message.reply(

        f"🎉 <b>Промокод</b> <code>{code}</code> <b>активирован!</b>\n"

        f"👤 @{uname} получил <b>+{bonus_energy}⚡</b>!\n"

        f"<code>{p_bar}</code> (<b>{new_energy}/{need}⚡</b>)",

        parse_mode="HTML"

    )

@dp.message(F.photo, F.from_user.id == ADMIN_ID)

async def admin_get_photo_id(message: types.Message):

    if admin_state.get(ADMIN_ID) == "broadcast":

        return

    *_, largest_photo = message.photo

    file_id = largest_photo.file_id

    await message.reply(f"🖼 <b>Код картинки (file_id):</b>\n<code>{file_id}</code>", parse_mode="HTML")

 

 

@dp.message(F.document, F.from_user.id == ADMIN_ID)

async def admin_restore_db(message: types.Message):

    global db, cur

    doc = message.document

    if not doc.file_name or not doc.file_name.endswith(".db"):

        return

    try:

        db.close()

        await bot.download(doc, destination=DB_FILE)

        db = sqlite3.connect(DB_FILE)

        cur = db.cursor()

        init_db()

        await message.reply("✅ <b>База данных успешно восстановлена из резервной копии!</b>", parse_mode="HTML")

    except Exception as e:

        db = sqlite3.connect(DB_FILE)

        cur = db.cursor()

        await message.reply(f"❌ Ошибка при восстановлении базы: <code>{e}</code>", parse_mode="HTML")

 

 

def get_admin_dashboard():

    now = int(time.time())

    cur.execute("SELECT COUNT(*), SUM(stars_spent) FROM users")

    total_users, total_stars = cur.fetchone()

    total_stars = total_stars or 0

 

    cur.execute("SELECT COUNT(*) FROM users WHERE last_farm >= ?", (now - 86400,))

    (active_24h,) = cur.fetchone()

 

    cur.execute("SELECT COUNT(*) FROM users WHERE last_farm >= ?", (now - 7 * 86400,))

    (active_7d,) = cur.fetchone()

 

    cur.execute("SELECT COUNT(*) FROM users WHERE last_farm = 0")

    (never_farmed,) = cur.fetchone()

 

    cur.execute("SELECT COUNT(*) FROM claims WHERE status = 'pending'")

    (pending_claims,) = cur.fetchone()

 

    cur.execute("SELECT COUNT(*) FROM claims WHERE status = 'done'")

    (done_claims,) = cur.fetchone()

 

    cur.execute("SELECT COUNT(*) FROM promocodes WHERE uses_left > 0")

    (active_promos,) = cur.fetchone()

 

    db_size_kb = round(os.path.getsize(DB_FILE) / 1024, 1) if os.path.exists(DB_FILE) else 0

 

    text = (

        f"👑 <b>Админ-панель и Аналитика</b>\n\n"

        f"👥 <b>Аудитория:</b>\n"

        f"∙ Всего в базе: <b>{total_users}</b>\n"

        f"∙ Активны за 24ч: <b>{active_24h}</b>\n"

        f"∙ Активны за 7 дней: <b>{active_7d}</b>\n"

        f"∙ Ни разу не качались: <b>{never_farmed}</b>\n\n"

        f"💰 <b>Финансы, Призы и Промо:</b>\n"

        f"∙ Заработано всего: <b>{total_stars} ⭐</b>\n"

        f"∙ Ожидают подарка: <b>{pending_claims} чел.</b>\n"

        f"∙ Выдано подарков: <b>{done_claims} шт.</b>\n"

        f"∙ Активных промокодов: <b>{active_promos} шт.</b>\n\n"

        f"💾 <b>База данных:</b> <code>{DB_FILE}</code> ({db_size_kb} КБ)"

    )

 

    kb = InlineKeyboardMarkup(inline_keyboard=[

        [InlineKeyboardButton(text=f"🎁 Заявки на подарки ({pending_claims})", callback_data="admin_claims")],

        [

            InlineKeyboardButton(text="🏆 Топ донатеров", callback_data="admin_top_donors"),

            InlineKeyboardButton(text="🧾 Платежи", callback_data="admin_payments")

        ],

        [

            InlineKeyboardButton(text="🎟 Промокоды", callback_data="admin_promos"),

            InlineKeyboardButton(text="📢 Рассылка", callback_data="admin_broadcast")

        ],

        [

            InlineKeyboardButton(text="💾 Скачать бэкап", callback_data="admin_backup"),

            InlineKeyboardButton(text="🔄 Обновить", callback_data="admin_refresh")

        ]

    ])

    return text, kb

 

 

@dp.message(Command("admin"))

async def cmd_admin(message: types.Message):

    if message.from_user.id != ADMIN_ID:

        return

    admin_state.pop(ADMIN_ID, None)

    text, kb = get_admin_dashboard()

    await message.answer(text, parse_mode="HTML", reply_markup=kb)

 

 

@dp.callback_query(F.data == "admin_refresh")

async def cb_admin_refresh(call: types.CallbackQuery):

    if call.from_user.id != ADMIN_ID:

        return

    admin_state.pop(ADMIN_ID, None)

    text, kb = get_admin_dashboard()

    await call.message.edit_text(text, parse_mode="HTML", reply_markup=kb)

 

 

@dp.callback_query(F.data == "admin_promos")

async def cb_admin_promos(call: types.CallbackQuery):

    if call.from_user.id != ADMIN_ID:

        return

    admin_state.pop(ADMIN_ID, None)

    cur.execute("SELECT code, energy, uses_left FROM promocodes WHERE uses_left > 0")

    rows = cur.fetchall()

 

    text = "🎟 <b>Активные промокоды:</b>\n\n"

    buttons = [[InlineKeyboardButton(text="➕ Создать промокод", callback_data="admin_new_promo")]]

 

    if not rows:

        text += "<i>Сейчас нет активных промокодов.</i>"

    else:

        for code, en, left in rows:

            text += f"∙ <code>{code}</code> — <b>+{en}⚡</b> (осталось {left} акт.)\n"

            buttons.append([InlineKeyboardButton(text=f"🗑 Удалить {code}", callback_data=f"del_promo_{code}")])

 

    buttons.append([InlineKeyboardButton(text="⬅️ Назад в админку", callback_data="admin_refresh")])

    await call.message.edit_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))

 

 

@dp.callback_query(F.data == "admin_new_promo")

async def cb_admin_new_promo(call: types.CallbackQuery):

    if call.from_user.id != ADMIN_ID:

        return

    admin_state[ADMIN_ID] = "new_promo"

    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="❌ Отмена", callback_data="admin_promos")]])

    await call.message.edit_text(

        "➕ <b>Создание промокода</b>\n\n"

        "Отправь следующим сообщением данные через пробел в формате:\n"

        "<code>КОД ЭНЕРГИЯ КОЛИЧЕСТВО_АКТИВАЦИЙ</code>\n\n"

        "Пример: <code>RAMEN777 150 25</code>",

        parse_mode="HTML",

        reply_markup=kb

    )

 

 

@dp.callback_query(F.data.startswith("del_promo_"))

async def cb_del_promo(call: types.CallbackQuery):

    if call.from_user.id != ADMIN_ID:

        return

    _, _, code = call.data.split("_", maxsplit=2)

    cur.execute("DELETE FROM promocodes WHERE code = ?", (code,))

    db.commit()

    await call.answer(f"Промокод {code} удалён!", show_alert=True)

    await cb_admin_promos(call)

@dp.callback_query(F.data == "admin_backup")

async def cb_admin_backup(call: types.CallbackQuery):

    if call.from_user.id != ADMIN_ID:

        return

    db.commit()

    if not os.path.exists(DB_FILE):

        return await call.answer("Файл базы данных не найден!", show_alert=True)

    dt_str = datetime.now().strftime("%d.%m.%Y %H:%M")

    backup_doc = FSInputFile(DB_FILE, filename=f"backup_{DB_FILE}")

    await call.message.answer_document(

        document=backup_doc,

        caption=f"💾 <b>Резервная копия базы данных</b>\n📅 Дата: <code>{dt_str}</code>\n\n<i>Чтобы восстановить базу позже, просто отправьте этот файл боту в личку.</i>",

        parse_mode="HTML"

    )

    await call.answer("Бэкап отправлен в чат!")

 

 

@dp.callback_query(F.data == "admin_top_donors")

async def cb_admin_top_donors(call: types.CallbackQuery):

    if call.from_user.id != ADMIN_ID:

        return

    cur.execute("SELECT username, user_id, stars_spent, level FROM users WHERE stars_spent > 0 ORDER BY stars_spent DESC LIMIT 10")

    rows = cur.fetchall()

    if not rows:

        return await call.answer("Покупок за Stars пока не было!", show_alert=True)

 

    text = "🏆 <b>Топ-10 донатеров бота:</b>\n\n"

    for idx, (uname, uid, spent, lvl) in enumerate(rows, start=1):

        text += f"{idx}. @{uname} (ID: <code>{uid}</code>) — <b>{spent} ⭐</b> (Ур. {lvl})\n"

 

    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="⬅️ Назад в админку", callback_data="admin_refresh")]])

    await call.message.edit_text(text, parse_mode="HTML", reply_markup=kb)

 

 

@dp.callback_query(F.data == "admin_payments")

async def cb_admin_payments(call: types.CallbackQuery):

    if call.from_user.id != ADMIN_ID:

        return

    cur.execute("SELECT username, item, amount, created_at FROM payments ORDER BY id DESC LIMIT 10")

    rows = cur.fetchall()

    if not rows:

        return await call.answer("История платежей пока пуста!", show_alert=True)

 

    item_names = {"amulet": "🔮 Амулет", "case": "📦 Кейс", "skip": "⚡ Прорыв"}

    text = "🧾 <b>Последние 10 покупок Stars:</b>\n\n"

    for uname, item, amount, ts in rows:

        dt = datetime.fromtimestamp(ts).strftime("%d.%m %H:%M")

        label = item_names.get(item, item)

        text += f"∙ <code>{dt}</code> | @{uname} — {label} (<b>{amount} ⭐</b>)\n"

 

    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="⬅️ Назад в админку", callback_data="admin_refresh")]])

    await call.message.edit_text(text, parse_mode="HTML", reply_markup=kb)

 

 

@dp.callback_query(F.data == "admin_broadcast")

async def cb_admin_broadcast(call: types.CallbackQuery):

    if call.from_user.id != ADMIN_ID:

        return

    admin_state[ADMIN_ID] = "broadcast"

    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="❌ Отмена", callback_data="admin_refresh")]])

    await call.message.edit_text(

        "📢 <b>Режим рассылки</b>\n\nОтправьте следующим сообщением текст (или фото с подписью), который получат все игроки бота.",

        parse_mode="HTML",

        reply_markup=kb

    )

 

 

@dp.message(F.from_user.id == ADMIN_ID, lambda m: admin_state.get(ADMIN_ID) in ("broadcast", "new_promo"))

async def process_admin_input(message: types.Message):

    mode = admin_state.pop(ADMIN_ID, None)

 

    if mode == "new_promo":

        parts = (message.text or "").split()

        if len(parts) != 3:

            return await message.reply("❌ Неверный формат! Нужно написать так: <code>RAMEN777 150 25</code>", parse_mode="HTML")

        raw_code, en_str, uses_str = parts

        try:

            code = raw_code.upper()

            energy_val = int(en_str)

            uses_val = int(uses_str)

            cur.execute("INSERT OR REPLACE INTO promocodes (code, energy, uses_left) VALUES (?, ?, ?)", (code, energy_val, uses_val))

            db.commit()

            await message.answer(

                f"✅ <b>Промокод создан!</b>\n\n"

                f"🎟 Код: <code>{code}</code>\n"

                f"⚡ Бонус: <b>+{energy_val}⚡</b>\n"

                f"👥 Активаций: <b>{uses_val}</b>\n\n"

                f"Игроки могут ввести: <code>/promo {code}</code>",

                parse_mode="HTML"

            )

        except ValueError:

            await message.reply("❌ Энергия и количество активаций должны быть числами!")

        return

 

    if mode == "broadcast":

        cur.execute("SELECT user_id FROM users")

        users = cur.fetchall()

        sent = 0

        for (uid,) in users:

            try:

                await message.copy_to(chat_id=uid)

                sent += 1

                await asyncio.sleep(0.05)

            except Exception:

                pass

        await message.answer(f"✅ <b>Рассылка завершена!</b>\nДоставлено: <b>{sent}</b> из {len(users)} игроков.", parse_mode="HTML")

 

 

@dp.callback_query(F.data == "admin_claims")

async def cb_admin_claims(call: types.CallbackQuery):

    if call.from_user.id != ADMIN_ID:

        return

    cur.execute("SELECT id, user_id, username, level, reward FROM claims WHERE status = 'pending' LIMIT 10")

    rows = cur.fetchall()

    if not rows:

        return await call.answer("Активных заявок нет!", show_alert=True)

 

    text = "🎁 <b>Невыданные подарки (нажмите чтобы закрыть заявку):</b>\n\n"

    buttons = []

    for cid, uid, uname, lvl, rew in rows:

        text += f"#{cid} | @{uname} (ID: <code>{uid}</code>) — Ур.{lvl} ({rew})\n"

        buttons.append([InlineKeyboardButton(text=f"✅ Выдано #{cid} (@{uname})", callback_data=f"done_claim_{cid}")])

 

    buttons.append([InlineKeyboardButton(text="⬅️ Назад в админку", callback_data="admin_refresh")])

    await call.message.edit_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))

 

 

@dp.callback_query(F.data.startswith("done_claim_"))

async def cb_done_claim(call: types.CallbackQuery):

    if call.from_user.id != ADMIN_ID:

        return

    _, _, cid_str = call.data.split("_")

    cid = int(cid_str)

    cur.execute("UPDATE claims SET status = 'done' WHERE id = ?", (cid,))

    db.commit()

    await call.answer(f"Заявка #{cid} отмечена как выполненная!", show_alert=True)

    await cb_admin_claims(call)

@dp.callback_query(F.data.startswith("promoinfo_"))

async def cb_promo_info(call: types.CallbackQuery):

    _, target_str = call.data.split("_")

    target_id = int(target_str)

    if not check_owner(call, target_id):

        return await call.answer("Это не твоя карточка! Напиши /card", show_alert=True)

    await call.answer(

        "🎟 Чтобы активировать секретный промокод из канала, отправь в чат команду:\n/promo ТВОЙ_КОД",

        show_alert=True

    )

 

 

@dp.callback_query(F.data.startswith("back_"))

async def cb_back(call: types.CallbackQuery):

    _, target_str = call.data.split("_")

    target_id = int(target_str)

    if not check_owner(call, target_id):

        return await call.answer("Руки прочь от чужого героя! Вызови своего командой /card", show_alert=True)

    user = get_user(target_id)

    await send_or_edit_card(call.message, user, is_edit=True)

 

 

@dp.callback_query(F.data.startswith("levels_"))

async def cb_levels(call: types.CallbackQuery):

    _, target_str = call.data.split("_")

    target_id = int(target_str)

    if not check_owner(call, target_id):

        return await call.answer("Вызови своё меню командой /card", show_alert=True)

    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="⬅️ Вернуться к герою", callback_data=f"back_{target_id}")]])

    await send_or_edit_screen(

        call.message,

        get_levels_text(),

        kb,

        photo_id=BANNERS.get("levels"),

        is_edit=True

    )

 

 

@dp.callback_query(F.data.startswith("farm_"))

async def cb_farm(call: types.CallbackQuery):

    _, target_str = call.data.split("_")

    target_id = int(target_str)

    if not check_owner(call, target_id):

        return await call.answer("Не трогай чужого персонажа! Напиши /card", show_alert=True)

 

    user = get_user(target_id)

    uid, _, level, energy, last_farm, amulet_until, _ = user

    now = int(time.time())

 

    lvl_data = LEVELS.get(level)

    if not lvl_data:

        return await call.answer("Уровень в разработке!", show_alert=True)

 

    if now - last_farm < COOLDOWN:

        rem = (last_farm + COOLDOWN) - now

        msg = random.choice(WAIT_TEXTS).format(h=rem // 3600, m=(rem % 3600) // 60)

        return await call.answer(msg, show_alert=True)

 

    gain = random.randint(50, 150) if amulet_until > now else random.randint(1, 50)

    new_energy = min(energy + gain, lvl_data.get("need"))

 

    cur.execute("UPDATE users SET energy = ?, last_farm = ? WHERE user_id = ?", (new_energy, now, uid))

    db.commit()

 

    phrase = random.choice(FARM_TEXTS).format(gain=gain)

    await call.answer(phrase, show_alert=True)

    updated_user = get_user(uid)

    await send_or_edit_card(call.message, updated_user, is_edit=True)

 

 

@dp.callback_query(F.data.startswith("claim_"))

async def cb_claim(call: types.CallbackQuery):

    _, target_str = call.data.split("_")

    target_id = int(target_str)

    if not check_owner(call, target_id):

        return await call.answer("Это чужой приз, даже не пытайся!", show_alert=True)

 

    user = get_user(target_id)

    uid, uname, level, energy, _, _, _ = user

    lvl_data = LEVELS.get(level)

    if not lvl_data or energy < lvl_data.get("need"):

        return await call.answer("Рановато! Сначала докачай энергию до конца!", show_alert=True)

 

    reward_name = lvl_data.get("reward")

    next_level = level + 1

 

    cur.execute("INSERT INTO claims (user_id, username, level, reward) VALUES (?, ?, ?, ?)", (uid, uname, level, reward_name))

    cur.execute("UPDATE users SET level = ?, energy = 0 WHERE user_id = ?", (next_level, uid))

    db.commit()

 

    await bot.send_message(

        ADMIN_ID,

        f"🎉 <b>НОВАЯ ЗАЯВКА НА ПОДАРОК!</b>\nИгрок: @{uname} (ID: <code>{uid}</code>)\nУровень: {level}\nПриз: <b>{reward_name}</b>\n\nУправление заявками: /admin",

        parse_mode="HTML"

    )

 

    await call.answer("🎉 Красавчик! Голубь с заявкой на подарок уже летит к админу!", show_alert=True)

    updated_user = get_user(uid)

    await send_or_edit_card(call.message, updated_user, is_edit=True)

 

 

@dp.callback_query(F.data.startswith("shop_"))

async def cb_shop(call: types.CallbackQuery):

    _, target_str = call.data.split("_")

    target_id = int(target_str)

    if not check_owner(call, target_id):

        return await call.answer("Открой свою лавку командой /shop", show_alert=True)

 

    await send_or_edit_screen(

        call.message,

        get_shop_text(),

        shop_keyboard(target_id),

        photo_id=BANNERS.get("shop"),

        is_edit=True

    )

 

 

@dp.callback_query(F.data.startswith("buy_"))

async def cb_buy(call: types.CallbackQuery):

    _, item, target_str = call.data.split("_")

    target_id = int(target_str)

    if not check_owner(call, target_id):

        return await call.answer("Это чужое меню!", show_alert=True)

 

    prices_map = {

        "amulet": ("Амулет удачи на 48ч", "Добыча 50-150 энергии без лени героя", 40),

        "case": ("Кейс с удачей", "Случайный бонус от 1 до 100 энергии прямо сейчас", 25),

        "skip": ("Попытка прорыва уровня", "Запрещённая техника мгновенного закрытия уровня", 100),

    }

    title, desc, amount = prices_map.get(item)

    await call.message.answer_invoice(

        title=title,

        description=desc,

        payload=item,

        currency="XTR",

        prices=[LabeledPrice(label=title, amount=amount)]

    )

    await call.answer()

 

 

@dp.pre_checkout_query()

async def process_pre_checkout(pre_checkout_query: PreCheckoutQuery):

    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)

 

 

@dp.message(F.successful_payment)

async def process_payment(message: types.Message):

    payload = message.successful_payment.invoice_payload

    paid_stars = message.successful_payment.total_amount

    uid = message.from_user.id

    user = get_user(uid, message.from_user.username)

    _, uname, level, energy, _, amulet_until, _ = user

    now = int(time.time())

 

    cur.execute("UPDATE users SET stars_spent = stars_spent + ? WHERE user_id = ?", (paid_stars, uid))

    cur.execute(

        "INSERT INTO payments (user_id, username, item, amount, created_at) VALUES (?, ?, ?, ?, ?)",

        (uid, uname, payload, paid_stars, now)

    )

    db.commit()

 

    lvl_data = LEVELS.get(level)

    if not lvl_data:

        return

 

    need = lvl_data.get("need")

 

    if payload == "amulet":

        new_until = max(amulet_until, now) + (48 * 3600)

        cur.execute("UPDATE users SET amulet_until = ? WHERE user_id = ?", (new_until, uid))

        db.commit()

        await message.answer("🔮 <b>Амулет удачи надет!</b> Ближайшие 48 часов твой герой пашет как проклятый (50–150⚡)!", parse_mode="HTML")

 

    elif payload == "case":

        bonus = random.randint(1, 100)

        new_energy = min(energy + bonus, need)

        cur.execute("UPDATE users SET energy = ? WHERE user_id = ?", (new_energy, uid))

        db.commit()

        await message.answer(f"📦 <b>Ты вскрыл ящик и вытащил +{bonus}⚡!</b> Герой в шоке, но доволен!", parse_mode="HTML")

 

    elif payload == "skip":

        if random.randint(1, 100) <= 5:

            cur.execute("UPDATE users SET energy = ? WHERE user_id = ?", (need, uid))

            db.commit()

            await message.answer("🔥 <b>БЕЗУМИЕ! Запрещённая техника сработала!</b> Уровень пройден за секунду! Беги забирать подарок в /card!", parse_mode="HTML")

        else:

            await message.answer("💨 <b>ПУФ! Техника пшикнула дымом...</b> Герой закашлялся, прорыв не удался. Попробуй ещё раз!", parse_mode="HTML")

 

 

async def set_bot_commands():

    commands = [

        BotCommand(command="card", description="🎴 Мой аниме-герой и энергия"),

        BotCommand(command="farm", description="⚡ Отправить героя на тренировку"),

        BotCommand(command="shop", description="🛒 Лавка читера (Бусты за Stars)"),

        BotCommand(command="levels", description="🗺 Дорога славы (Все 10 уровней)"),

        BotCommand(command="promo", description="🎟 Ввести секретный промокод"),

    ]

    await bot.set_my_commands(commands)

 

 

async def main():

    await set_bot_commands()

    await bot.delete_webhook(drop_pending_updates=True)

    await dp.start_polling(bot)

 

 
for handler in dp.message.handlers:

    if handler.callback == _orig_start:

        handler.callback = cmd_start_with_ref

    elif handler.callback == _orig_cmd_farm:

        handler.callback = cmd_farm_with_ref

 

for handler in dp.callback_query.handlers:

    if handler.callback == _orig_cb_farm:

        handler.callback = cb_farm_with_ref
if __name__ == "__main__":

    asyncio.run(main())
