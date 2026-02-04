from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters
)

# =========================
# 🔴 ВСТАВ СВІЙ ТОКЕН ТУТ
# =========================
BOT_TOKEN = "8592102357:AAHeNquaZWLKRUhFTcUuBkt1rOlsQcsx1Wg"

# твій Telegram ID (щоб заявки приходили ТОБІ)
ADMIN_ID = 5585752273

# =========================
# ДАНІ ПРО ДОНАТ
# =========================
GAMES = {
    "pubg": {
        "name": "PUBG Mobile",
        "packs": [
            ("60 UC", 45),
            ("300+25 UC", 225),
            ("600+60 UC", 450),
            ("1500+300 UC", 1100),
        ]
    },
    "standoff": {
        "name": "Standoff 2",
        "packs": [
            ("100 Gold", 50),
            ("500 Gold", 230),
            ("1000 Gold", 450),
        ]
    },
    "roblox": {
        "name": "Roblox",
        "packs": [
            ("400 Robux", 249),
            ("800 Robux", 499),
            ("1700 Robux", 999),
        ]
    }
}

# =========================
# /start
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🎮 PUBG Mobile", callback_data="game_pubg")],
        [InlineKeyboardButton("🔫 Standoff 2", callback_data="game_standoff")],
        [InlineKeyboardButton("🧱 Roblox", callback_data="game_roblox")],
    ]
    await update.message.reply_text(
        "Привіт 👋\nОбери гру:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# =========================
# ВИБІР ГРИ
# =========================
async def choose_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    game_key = query.data.replace("game_", "")
    context.user_data["game"] = game_key

    await query.edit_message_text(
        f"🎮 Обрано: {GAMES[game_key]['name']}\n\n"
        "💰 Напиши, скільки в тебе є гривень (числом):"
    )

# =========================
# ОБРОБКА СУМИ
# =========================
async def handle_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "game" not in context.user_data:
        return

    try:
        amount = int(update.message.text)
    except ValueError:
        await update.message.reply_text("❌ Введи ЧИСЛО (наприклад: 500)")
        return

    game = GAMES[context.user_data["game"]]
    available = [p for p in game["packs"] if p[1] <= amount]

    if not available:
        await update.message.reply_text("❌ За цю суму нічого не можу запропонувати.")
        return

    text = f"💸 За {amount} грн можна:\n\n"
    for name, price in available:
        text += f"✅ {name} — {price} грн\n"

    text += "\n✍️ Напиши:\nНИК\nПАРОЛЬ\nЧАС (2 год / 1 день і т.д.)"

    context.user_data["amount"] = amount
    await update.message.reply_text(text)

# =========================
# ЗАЯВКА
# =========================
async def handle_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "amount" not in context.user_data:
        return

    user = update.message.from_user
    text = update.message.text

    order_text = (
        "📥 НОВА ЗАЯВКА\n\n"
        f"👤 Від: {user.full_name} (@{user.username})\n"
        f"🎮 Гра: {GAMES[context.user_data['game']]['name']}\n"
        f"💰 Сума: {context.user_data['amount']} грн\n\n"
        f"📄 Дані:\n{text}"
    )

    await context.bot.send_message(chat_id=ADMIN_ID, text=order_text)
    await update.message.reply_text("✅ Заявка відправлена! Чекай 😉")

    context.user_data.clear()

# =========================
# MAIN
# =========================
def main():
    print("🚀 Bot started")
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(choose_game, pattern="^game_"))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex(r"^\d+$"), handle_amount))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_order))

    app.run_polling()

if __name__ == "__main__":
    main()
