import os, json
from dataclasses import dataclass
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, filters
)

# ================== НАЛАШТУВАННЯ ==================
BOT_TOKEN = "8592102357:AAHeNquaZWLKRUhFTcUuBkt1rOlsQcsx1Wg"
ADMIN_UID = 5585752273
ORDERS_FILE = "orders.json"
MIN_PROFIT = 50  # 🔥 мінімальна вигода

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN не знайдено")

# ================== СТАНИ ==================
WAIT_GAME = "WAIT_GAME"
WAIT_AMOUNT = "WAIT_AMOUNT"
WAIT_UID = "WAIT_UID"
WAIT_TIME = "WAIT_TIME"

# ================== ДАНІ ==================
@dataclass
class Offer:
    name: str
    price: int  # твоя собівартість

GAMES = {
    "pubg": "PUBG Mobile",
    "standoff": "Standoff 2",
    "brawl": "Brawl Stars",
    "roblox": "Roblox",
}

OFFERS = {
    "pubg": [
        Offer("60 UC", 45),
        Offer("300 + 25 UC", 225),
        Offer("600 + 60 UC", 450),
        Offer("1500 + 300 UC", 1100),
        Offer("3000 + 850 UC", 2300),
        Offer("6000 + 2100 UC", 4500),
    ],
    "standoff": [
        Offer("100 Gold", 50),
        Offer("500 Gold", 230),
        Offer("1000 Gold", 450),
        Offer("2500 Gold", 1100),
        Offer("5000 Gold", 2300),
    ],
    "brawl": [
        Offer("30 Gems", 89),
        Offer("80 Gems", 219),
        Offer("170 Gems", 449),
        Offer("360 Gems", 899),
        Offer("950 Gems", 2199),
        Offer("2000 Gems", 4499),
    ],
    "roblox": [
        Offer("400 R$", 249),
        Offer("800 R$", 499),
        Offer("1700 R$", 999),
        Offer("4500 R$", 2499),
    ],
}

DONATE_TIMES = [
    "Зараз", "2 год", "4 год", "10 год",
    "1 день", "2 дні", "3 дні", "5 днів", "10 днів"
]

# ================== ФАЙЛ ==================
def load_orders():
    if not os.path.exists(ORDERS_FILE):
        return []
    return json.load(open(ORDERS_FILE, "r", encoding="utf-8"))

def save_orders(data):
    json.dump(data, open(ORDERS_FILE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

# ================== ЛОГІКА ==================
def best_combo(game, budget):
    offers = sorted(OFFERS[game], key=lambda o: o.price, reverse=True)
    chosen, total = [], 0
    for o in offers:
        while total + o.price <= budget:
            chosen.append(o)
            total += o.price
    return chosen, total

async def clean_send(ctx, chat_id, text, kb=None):
    mid = ctx.user_data.get("last")
    if mid:
        try: await ctx.bot.delete_message(chat_id, mid)
        except: pass
    msg = await ctx.bot.send_message(chat_id, text, reply_markup=kb)
    ctx.user_data["last"] = msg.message_id

# ================== КНОПКИ ==================
def games_kb():
    return InlineKeyboardMarkup([[InlineKeyboardButton(v, callback_data=f"g:{k}")]
                                 for k, v in GAMES.items()])

def time_kb():
    return InlineKeyboardMarkup([[InlineKeyboardButton(t, callback_data=f"t:{t}")]
                                 for t in DONATE_TIMES])

# ================== ХЕНДЛЕРИ ==================
async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data.clear()
    ctx.user_data["state"] = WAIT_GAME
    await clean_send(ctx, update.effective_chat.id, "🎮 Обери гру:", games_kb())

async def callbacks(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    cid = q.message.chat.id

    if q.data.startswith("g:"):
        ctx.user_data["game"] = q.data[2:]
        ctx.user_data["state"] = WAIT_AMOUNT
        await clean_send(ctx, cid, "💰 Введи суму в грн:")

    elif q.data.startswith("t:"):
        ctx.user_data["time"] = q.data[2:]
        await finish(update, ctx)

async def text_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    text = update.message.text.strip()
    state = ctx.user_data.get("state")

    if state == WAIT_AMOUNT:
        if not text.isdigit():
            await clean_send(ctx, cid, "❗ Введи число")
            return
        budget = int(text)
        packs, cost = best_combo(ctx.user_data["game"], budget)
        profit = budget - cost

        if profit < MIN_PROFIT:
            await clean_send(ctx, cid,
                f"❌ Невигідно.\nМінімум прибутку: {MIN_PROFIT} грн\nСпробуй більшу суму.")
            return

        ctx.user_data.update({
            "budget": budget,
            "packs": packs,
            "cost": cost,
            "profit": profit,
            "state": WAIT_UID
        })

        txt = "📦 Я куплю:\n" + "\n".join(f"• {p.name}" for p in packs)
        txt += f"\n\n💰 Витрати: {cost} грн\n📈 Мій прибуток: {profit} грн\n\n🆔 Введи нік / UID:"
        await clean_send(ctx, cid, txt)

    elif state == WAIT_UID:
        ctx.user_data["uid"] = text
        ctx.user_data["state"] = WAIT_TIME
        await clean_send(ctx, cid, "⏰ Коли донат?", time_kb())

async def finish(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    d = ctx.user_data
    orders = load_orders()
    oid = len(orders) + 1

    order = {
        "id": oid,
        "game": GAMES[d["game"]],
        "packs": [p.name for p in d["packs"]],
        "budget": d["budget"],
        "cost": d["cost"],
        "profit": d["profit"],
        "uid": d["uid"],
        "time": d["time"],
        "date": datetime.now().strftime("%d.%m.%Y %H:%M")
    }

    orders.append(order)
    save_orders(orders)

    await clean_send(ctx, update.effective_chat.id, "✅ Заявка відправлена!")

    msg = (
        f"🆕 ЗАЯВКА #{oid}\n"
        f"🎮 {order['game']}\n"
        f"📦 {', '.join(order['packs'])}\n"
        f"💰 Бюджет: {order['budget']} грн\n"
        f"🧾 Витрати: {order['cost']} грн\n"
        f"📈 Прибуток: {order['profit']} грн\n"
        f"⏰ {order['time']}\n"
        f"🆔 UID: {order['uid']}"
    )

    await ctx.bot.send_message(ADMIN_UID, msg)
    ctx.user_data.clear()

async def profit_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    total = sum(o["profit"] for o in load_orders())
    await update.message.reply_text(f"📈 Загальний прибуток: {total} грн")

# ================== ЗАПУСК ==================
def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("profit", profit_cmd))
    app.add_handler(CallbackQueryHandler(callbacks))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
    print("✅ Бот працює")
    app.run_polling()

if __name__ == "__main__":
    main()
