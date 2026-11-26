#!/usr/bin/env python3
"""
Toing & Swiggy Bot Store — Admin Bot (Render-ready with Flask)
Production-ready for python-telegram-bot==21.7
"""

import asyncio
import json
import os
import threading
from datetime import datetime

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)
from flask import Flask, request, jsonify

# ═══════════════════════════════════════════════════════════════
# 🔧 CONFIGURATION
# ═══════════════════════════════════════════════════════════════

BOT_TOKEN = os.environ.get("TELEGRAM_TOKEN", "9032273740:AAGTWc8tSOvD0PxGLcrD4XzB5g4_Ls14JBg")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "6657235468"))

DELIVERY_LINKS = {
    "toing": "https://t.me/YourToingBotDeliveryBot?start=toing_license",
    "swiggy": "https://t.me/YourSwiggyBotDeliveryBot?start=swiggy_license",
    "combo": "https://t.me/YourComboDeliveryBot?start=combo_license",
}

PRODUCT_NAMES = {
    "toing": "Toing Bot",
    "swiggy": "Swiggy Bot",
    "combo": "Toing + Swiggy Combo",
}

PRICES = {
    "toing": 199,
    "swiggy": 199,
    "combo": 299,
}

DB_FILE = "admin_bot_db.json"

# ═══════════════════════════════════════════════════════════════
# 💾 DATABASE
# ═══════════════════════════════════════════════════════════════

def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                data.setdefault("verified", [])
                data.setdefault("pending", [])
                data.setdefault("rejected", [])
                return data
        except Exception as e:
            print(f"DB load error: {e}")
    return {"verified": [], "pending": [], "rejected": []}

def save_db(db):
    try:
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(db, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"DB save error: {e}")

# ═══════════════════════════════════════════════════════════════
# 🛡️ ADMIN CHECK
# ═══════════════════════════════════════════════════════════════

def is_admin(update: Update) -> bool:
    return bool(update.effective_user and update.effective_user.id == ADMIN_ID)

# ═══════════════════════════════════════════════════════════════
# 🚀 COMMANDS
# ═══════════════════════════════════════════════════════════════

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        await update.message.reply_text("⛔ Unauthorized. Admin bot only.")
        return
    await update.message.reply_text(
        "🤖 *Toing Admin Bot Ready*\n\n"
        "Commands:\n"
        "• `/approve <userId> <product>` — deliver bot\n"
        "• `/reject <userId> <product>` — reject payment\n"
        "• `/pending` — list pending\n"
        "• `/stats` — sales summary\n\n"
        "*Products:* `toing`, `swiggy`, `combo`\n\n"
        "Example:\n`/approve 6657235468 toing`",
        parse_mode="Markdown",
    )

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        return
    await start(update, context)

async def approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        return
    args = context.args
    if len(args) < 2:
        await update.message.reply_text(
            "❌ Format: `/approve <userId> <product>`\nExample: `/approve 6657235468 toing`",
            parse_mode="Markdown",
        )
        return
    try:
        user_id = int(args[0])
    except ValueError:
        await update.message.reply_text("❌ Invalid userId. Numbers only.")
        return
    product = args[1].lower()
    if product not in DELIVERY_LINKS:
        await update.message.reply_text("❌ Invalid product. Use: toing, swiggy, combo")
        return

    db = load_db()
    link = DELIVERY_LINKS[product]
    product_name = PRODUCT_NAMES[product]
    price = PRICES[product]

    db["verified"].append({
        "user_id": user_id,
        "product": product,
        "amount": price,
        "verified_at": datetime.now().isoformat(),
    })
    db["pending"] = [p for p in db["pending"] if not (p.get("user_id") == user_id and p.get("product") == product)]
    save_db(db)

    try:
        await context.bot.send_message(
            chat_id=user_id,
            text=(
                f"🎉 *Payment Verified!*\n\n"
                f"✅ Product: *{product_name}*\n"
                f"💰 Amount: ₹{price}\n\n"
                f"🔗 *Your bot access link:*\n{link}\n\n"
                f"⚠️ Save this link.\n"
                f"Support: @toingstoreadminbot"
            ),
            parse_mode="Markdown",
            disable_web_page_preview=False,
        )
        await update.message.reply_text(
            f"✅ Approved!\n• User: `{user_id}`\n• Product: {product_name}\n• Link delivered ✅",
            parse_mode="Markdown",
        )
    except Exception as e:
        await update.message.reply_text(
            f"⚠️ Approved in DB but couldn't message `{user_id}`.\n"
            f"Error: `{str(e)[:100]}`\n\nManually send:\n{link}",
            parse_mode="Markdown",
        )

async def reject(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        return
    args = context.args
    if len(args) < 2:
        await update.message.reply_text("❌ Format: `/reject <userId> <product>`", parse_mode="Markdown")
        return
    try:
        user_id = int(args[0])
    except ValueError:
        await update.message.reply_text("❌ Invalid userId.")
        return
    product = args[1].lower()
    if product not in DELIVERY_LINKS:
        await update.message.reply_text("❌ Invalid product.")
        return

    db = load_db()
    db["rejected"].append({
        "user_id": user_id,
        "product": product,
        "rejected_at": datetime.now().isoformat(),
    })
    db["pending"] = [p for p in db["pending"] if not (p.get("user_id") == user_id and p.get("product") == product)]
    save_db(db)

    try:
        await context.bot.send_message(
            chat_id=user_id,
            text=(
                "❌ *Payment Not Verified*\n\n"
                "Aapka payment verify nahi ho paya.\n"
                "Contact support: @toingstoreadminbot"
            ),
            parse_mode="Markdown",
        )
    except Exception:
        pass

    await update.message.reply_text(f"✅ Rejected user `{user_id}` for {product}", parse_mode="Markdown")

async def pending(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        return
    db = load_db()
    if not db["pending"]:
        await update.message.reply_text("✅ No pending verifications.")
        return
    text = "⏳ *Pending Verifications:*\n\n"
    for i, p in enumerate(db["pending"][-20:], 1):
        text += (
            f"{i}. User `{p.get('user_id', '?')}`\n"
            f"   Product: {PRODUCT_NAMES.get(p.get('product'), '?')}\n"
            f"   UTR: `{p.get('utr', '?')}`\n"
            f"   Amount: ₹{p.get('amount', '?')}\n\n"
        )
    text += "Use `/approve <userId> <product>` to deliver."
    await update.message.reply_text(text, parse_mode="Markdown")

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        return
    db = load_db()
    total_verified = len(db["verified"])
    total_revenue = sum(v.get("amount", 0) for v in db["verified"])
    pending_count = len(db["pending"])
    rejected_count = len(db["rejected"])

    by_product = {}
    for v in db["verified"]:
        p = v.get("product", "?")
        by_product[p] = by_product.get(p, 0) + 1

    text = (
        "📊 *Sales Summary*\n\n"
        f"✅ Verified: *{total_verified}*\n"
        f"⏳ Pending: *{pending_count}*\n"
        f"❌ Rejected: *{rejected_count}*\n\n"
        f"💰 Revenue: *₹{total_revenue}*\n\n"
        "*By Product:*\n"
    )
    for p, c in by_product.items():
        text += f"• {PRODUCT_NAMES.get(p, p)}: {c}\n"
    await update.message.reply_text(text, parse_mode="Markdown")

async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if is_admin(update):
        await update.message.reply_text("❓ Unknown command. Use `/help`.", parse_mode="Markdown")

async def handle_webhook_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles JSON webhook text messages forwarded by the website."""
    if not update.message or not update.message.text:
        return
    text = update.message.text.strip()
    if not text.startswith("{"):
        return
    try:
        data = json.loads(text)
    except Exception:
        return
    if data.get("action") != "verify_payment":
        return

    user_id = data.get("user_id")
    product = str(data.get("product", "")).lower()
    utr = data.get("utr", "")
    amount = data.get("amount", "?")
    user_name = data.get("user_name", "User")
    username = data.get("username", "")

    if not user_id or product not in DELIVERY_LINKS:
        return

    db = load_db()
    db["pending"].append({
        "user_id": user_id,
        "product": product,
        "utr": utr,
        "amount": amount,
        "user_name": user_name,
        "username": username,
        "timestamp": datetime.now().isoformat(),
    })
    save_db(db)

    msg = (
        f"🔔 *NEW PAYMENT VERIFICATION*\n\n"
        f"👤 *User:* {user_name}\n"
        f"📱 *Username:* {username or 'N/A'}\n"
        f"🆔 *ID:* `{user_id}`\n\n"
        f"📦 *Product:* {PRODUCT_NAMES[product]}\n"
        f"💰 *Amount:* ₹{amount}\n"
        f"🔢 *UTR:* `{utr}`\n\n"
        f"⏰ *Time:* {datetime.now().strftime('%d %b %Y, %I:%M %p')}\n\n"
        f"✅ Verify in UPI app, then send:\n"
        f"`/approve {user_id} {product}`"
    )
    try:
        await context.bot.send_message(chat_id=ADMIN_ID, text=msg, parse_mode="Markdown")
    except Exception as e:
        print(f"Failed to notify admin: {e}")

# ═══════════════════════════════════════════════════════════════
# 🌐 FLASK (Render keep-alive + webhook endpoint)
# ═══════════════════════════════════════════════════════════════

flask_app = Flask(__name__)
bot_loop = None
bot_app = None

@flask_app.route("/")
@flask_app.route("/health")
def health():
    return "OK", 200

@flask_app.route("/webhook", methods=["POST", "OPTIONS"])
def webhook():
    """HTTP endpoint for website to submit UTR directly."""
    if request.method == "OPTIONS":
        resp = jsonify({"ok": True})
        resp.headers["Access-Control-Allow-Origin"] = "*"
        resp.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
        resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
        return resp, 200

    try:
        data = request.get_json(force=True, silent=True) or {}
    except Exception:
        data = {}

    if data.get("action") != "verify_payment":
        resp = jsonify({"ok": False, "error": "invalid action"})
        resp.headers["Access-Control-Allow-Origin"] = "*"
        return resp, 400

    user_id = data.get("user_id")
    product = str(data.get("product", "")).lower()
    utr = data.get("utr", "")
    amount = data.get("amount", "?")
    user_name = data.get("user_name", "User")
    username = data.get("username", "")

    if not user_id or product not in DELIVERY_LINKS:
        resp = jsonify({"ok": False, "error": "invalid payload"})
        resp.headers["Access-Control-Allow-Origin"] = "*"
        return resp, 400

    db = load_db()
    db["pending"].append({
        "user_id": user_id,
        "product": product,
        "utr": utr,
        "amount": amount,
        "user_name": user_name,
        "username": username,
        "timestamp": datetime.now().isoformat(),
    })
    save_db(db)

    msg = (
        f"🔔 *NEW PAYMENT VERIFICATION*\n\n"
        f"👤 *User:* {user_name}\n"
        f"📱 *Username:* {username or 'N/A'}\n"
        f"🆔 *ID:* `{user_id}`\n\n"
        f"📦 *Product:* {PRODUCT_NAMES[product]}\n"
        f"💰 *Amount:* ₹{amount}\n"
        f"🔢 *UTR:* `{utr}`\n\n"
        f"⏰ *Time:* {datetime.now().strftime('%d %b %Y, %I:%M %p')}\n\n"
        f"✅ Verify in UPI app, then send:\n"
        f"`/approve {user_id} {product}`"
    )

    try:
        if bot_loop and bot_app:
            fut = asyncio.run_coroutine_threadsafe(
                bot_app.bot.send_message(chat_id=ADMIN_ID, text=msg, parse_mode="Markdown"),
                bot_loop,
            )
            fut.result(timeout=10)
    except Exception as e:
        print(f"Webhook notify error: {e}")

    resp = jsonify({"ok": True})
    resp.headers["Access-Control-Allow-Origin"] = "*"
    return resp, 200

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    flask_app.run(host="0.0.0.0", port=port, use_reloader=False, threaded=True)

# ═══════════════════════════════════════════════════════════════
# 🎬 MAIN
# ═══════════════════════════════════════════════════════════════

def main():
    global bot_loop, bot_app

    print("🤖 Starting Toing Admin Bot...")

    try:
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    bot_loop = loop

    app = Application.builder().token(BOT_TOKEN).build()
    bot_app = app

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("approve", approve))
    app.add_handler(CommandHandler("reject", reject))
    app.add_handler(CommandHandler("pending", pending))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_webhook_data))
    app.add_handler(MessageHandler(filters.COMMAND, unknown))

    threading.Thread(target=run_flask, daemon=True).start()
    print("✅ Bot running + Flask on PORT.")

    app.run_polling(
        allowed_updates=Update.ALL_TYPES,
        close_loop=False,
        drop_pending_updates=False,
    )

if __name__ == "__main__":
    main()
