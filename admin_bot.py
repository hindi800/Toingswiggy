#!/usr/bin/env python3
"""
Toing & Swiggy Bot Store — Admin Bot (Render-ready with Flask & Buttons)
"""

import asyncio
import json
import os
import threading
from datetime import datetime

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)
from flask import Flask, request, jsonify
from flask_cors import CORS

# ═══════════════════════════════════════════════════════════════
# 🔧 CONFIGURATION
# ═══════════════════════════════════════════════════════════════

BOT_TOKEN = os.environ.get("TELEGRAM_TOKEN", "9032273740:AAGTWc8tSOvD0PxGLcrD4XzB5g4_Ls14JBg")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "6657235468"))

DELIVERY_LINKS = {
    "toing": "https://t.me/AaluToingBot",
    "swiggy": "https://t.me/AaluSwiggyBot"
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
# 💬 DELIVERY MESSAGE GENERATOR (High-End English)
# ═══════════════════════════════════════════════════════════════

def get_delivery_message(product_key: str):
    """Generates a professional message with instructions based on the product."""
    
    toing_guide = (
        "ℹ️ *How to use Toing Bot*\n\n"
        "1️⃣ Tap *Open Toing* to launch the mini-app.\n"
        "2️⃣ Browse live restaurants and add dishes to cart.\n"
        "3️⃣ Checkout to get instant Toing UPI payment QR.\n"
        "4️⃣ Pay using GPay, PhonePe, or Paytm.\n\n"
        "*Commands:*\n"
        "• `/start` — Launch menu\n"
        "• `/login` — Link Toing account\n"
        "• `/mycode` — Get access code\n"
        "• `/cancel` — Cancel current action"
    )

    swiggy_guide = (
        "ℹ️ *How to use Swiggy Bot*\n\n"
        "1️⃣ Tap *Open Swiggy* to launch the mini-app.\n"
        "2️⃣ Browse live restaurants and add dishes to cart.\n"
        "3️⃣ Checkout to get instant Swiggy UPI payment QR.\n"
        "4️⃣ Pay using GPay, PhonePe, or Paytm.\n\n"
        "*Commands:*\n"
        "• `/start` — Launch menu\n"
        "• `/login` — Link Swiggy account\n"
        "• `/mycode` — Get access code\n"
        "• `/cancel` — Cancel current action"
    )

    if product_key == "combo":
        return (
            "🎉 *Payment Verified Successfully!*\n\n"
            "Thank you for purchasing the *Toing + Swiggy Combo*.\n"
            f"💰 Amount Paid: ₹{PRICES['combo']}\n\n"
            "🔗 *Your Access Links:*\n"
            f"• Toing Bot: {DELIVERY_LINKS['toing']}\n"
            f"• Swiggy Bot: {DELIVERY_LINKS['swiggy']}\n\n"
            "────────────────────\n\n"
            f"{toing_guide}\n\n"
            "────────────────────\n\n"
            f"{swiggy_guide}\n\n"
            "⚠️ *Please save these links.*\n"
            "For any support, contact: @toingstoreadminbot"
        )
    elif product_key == "toing":
        return (
            "🎉 *Payment Verified Successfully!*\n\n"
            "Thank you for purchasing the *Toing Bot*.\n"
            f"💰 Amount Paid: ₹{PRICES['toing']}\n\n"
            f"🔗 *Your Access Link:*\n{DELIVERY_LINKS['toing']}\n\n"
            "────────────────────\n\n"
            f"{toing_guide}\n\n"
            "⚠️ *Please save this link.*\n"
            "For any support, contact: @toingstoreadminbot"
        )
    elif product_key == "swiggy":
        return (
            "🎉 *Payment Verified Successfully!*\n\n"
            "Thank you for purchasing the *Swiggy Bot*.\n"
            f"💰 Amount Paid: ₹{PRICES['swiggy']}\n\n"
            f"🔗 *Your Access Link:*\n{DELIVERY_LINKS['swiggy']}\n\n"
            "────────────────────\n\n"
            f"{swiggy_guide}\n\n"
            "⚠️ *Please save this link.*\n"
            "For any support, contact: @toingstoreadminbot"
        )
    return "Error: Invalid Product."

# ═══════════════════════════════════════════════════════════════
# 🚀 COMMANDS & BUTTON HANDLERS
# ═══════════════════════════════════════════════════════════════

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        await update.message.reply_text("⛔ Unauthorized. Admin bot only.")
        return
    await update.message.reply_text(
        "🤖 *Toing Admin Bot Ready*\n\n"
        "You will receive payment verification requests with Inline Buttons.\n\n"
        "Manual Commands:\n"
        "• `/pending` — list pending\n"
        "• `/stats` — sales summary\n"
        "• `/approve <userId> <product>` — manual approve\n"
        "• `/reject <userId> <product>` — manual reject",
        parse_mode="Markdown",
    )

async def approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        return
    args = context.args
    if len(args) < 2:
        await update.message.reply_text("❌ Format: `/approve <userId> <product>`", parse_mode="Markdown")
        return
    try:
        user_id = int(args[0])
    except ValueError:
        await update.message.reply_text("❌ Invalid userId.")
        return
    product = args[1].lower()
    if product not in PRODUCT_NAMES:
        await update.message.reply_text("❌ Invalid product. Use: toing, swiggy, combo")
        return

    db = load_db()
    db["verified"].append({
        "user_id": user_id,
        "product": product,
        "amount": PRICES.get(product, 0),
        "verified_at": datetime.now().isoformat(),
    })
    db["pending"] = [p for p in db["pending"] if not (p.get("user_id") == user_id and p.get("product") == product)]
    save_db(db)

    try:
        msg = get_delivery_message(product)
        await context.bot.send_message(chat_id=user_id, text=msg, parse_mode="Markdown")
        await update.message.reply_text(f"✅ Approved manually for `{user_id}` ({product})", parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"⚠️ Approved in DB but failed to message `{user_id}`.\nError: {str(e)}", parse_mode="Markdown")

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
    if product not in PRODUCT_NAMES:
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
            text="❌ *Payment Not Verified*\n\nYour payment could not be verified.\nContact support: @toingstoreadminbot",
            parse_mode="Markdown",
        )
    except Exception:
        pass

    await update.message.reply_text(f"✅ Rejected manually for `{user_id}` ({product})", parse_mode="Markdown")

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

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles Approve/Reject Inline Button clicks"""
    query = update.callback_query
    await query.answer() # Acknowledge the button click

    if query.from_user.id != ADMIN_ID:
        await query.edit_message_text("⛔ Unauthorized.")
        return

    data = query.data.split("_")
    action = data[0]
    user_id = int(data[1])
    product = data[2]

    if action == "appr":
        db = load_db()
        db["verified"].append({
            "user_id": user_id,
            "product": product,
            "amount": PRICES.get(product, 0),
            "verified_at": datetime.now().isoformat(),
        })
        db["pending"] = [p for p in db["pending"] if not (p.get("user_id") == user_id and p.get("product") == product)]
        save_db(db)

        try:
            msg = get_delivery_message(product)
            await context.bot.send_message(chat_id=user_id, text=msg, parse_mode="Markdown")
            await query.edit_message_text(
                text=query.message.text + f"\n\n✅ *APPROVED*\nDelivery link sent to user successfully.*",
                parse_mode="Markdown"
            )
        except Exception as e:
            await query.edit_message_text(
                text=query.message.text + f"\n\n⚠️ *Approved in DB but failed to send message to user.*\nError: {str(e)[:50]}",
                parse_mode="Markdown"
            )

    elif action == "rej":
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
                text="❌ *Payment Not Verified*\n\nYour payment could not be verified.\nContact support: @toingstoreadminbot",
                parse_mode="Markdown",
            )
            await query.edit_message_text(
                text=query.message.text + f"\n\n❌ *REJECTED*\nUser notified successfully.*",
                parse_mode="Markdown"
            )
        except Exception:
            await query.edit_message_text(
                text=query.message.text + f"\n\n❌ *REJECTED*\n(User couldn't be notified, but DB updated).*",
                parse_mode="Markdown"
            )

async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if is_admin(update):
        await update.message.reply_text("❓ Unknown command. Use `/start`.", parse_mode="Markdown")

# ═══════════════════════════════════════════════════════════════
# 🌐 FLASK (Render keep-alive + webhook endpoint)
# ═══════════════════════════════════════════════════════════════

flask_app = Flask(__name__)
CORS(flask_app) # 👈 FIXED: Added CORS for Webhook requests

bot_loop = None
bot_app = None

@flask_app.route("/")
@flask_app.route("/health")
def health():
    return "OK", 200

@flask_app.route("/webhook", methods=["POST", "OPTIONS"])
def webhook():
    if request.method == "OPTIONS":
        return jsonify({"ok": True}), 200

    try:
        data = request.get_json(force=True, silent=True) or {}
    except Exception:
        data = {}

    if data.get("action") != "verify_payment":
        return jsonify({"ok": False, "error": "invalid action"}), 400

    user_id = data.get("user_id")
    product = str(data.get("product", "")).lower()
    utr = data.get("utr", "")
    amount = data.get("amount", "?")
    user_name = data.get("user_name", "User")
    username = data.get("username", "")

    if not user_id or product not in PRODUCT_NAMES:
        return jsonify({"ok": False, "error": "invalid payload"}), 400

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
        f"⏰ *Time:* {datetime.now().strftime('%d %b %Y, %I:%M %p')}"
    )

    keyboard = [
        [
            InlineKeyboardButton("✅ Approve", callback_data=f"appr_{user_id}_{product}"),
            InlineKeyboardButton("❌ Reject", callback_data=f"rej_{user_id}_{product}")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    try:
        if bot_loop and bot_app:
            fut = asyncio.run_coroutine_threadsafe(
                bot_app.bot.send_message(
                    chat_id=ADMIN_ID, 
                    text=msg, 
                    parse_mode="Markdown",
                    reply_markup=reply_markup
                ),
                bot_loop,
            )
            fut.result(timeout=10)
    except Exception as e:
        print(f"Webhook notify error: {e}")

    return jsonify({"ok": True}), 200

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
    app.add_handler(CommandHandler("approve", approve))
    app.add_handler(CommandHandler("reject", reject))
    app.add_handler(CommandHandler("pending", pending))
    app.add_handler(CommandHandler("stats", stats))
    
    # 👈 FIXED: CallbackQueryHandler added for Buttons to work
    app.add_handler(CallbackQueryHandler(button_callback))
    
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
