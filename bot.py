"""
Telegram Qabul Bot (UZ / RU / EN)
---------------------------------
Foydalanuvchi spamga tushib qolganida ham o‘quv markaz admini bilan bog‘lanishga
imkon beradi. Bot 3 tilda ishlaydi.

Oqim
====
/start  → tilni tanlash  → ism  → familiya  → telefon  → xabar  → tasdiqlash ✅/❌

Admin `/reply <user_id> <matn>` buyrug‘i bilan javob qaytara oladi.
"""
import os
import logging
from enum import Enum, auto
from typing import Final

try:
    from dotenv import load_dotenv
    load_dotenv()
except ModuleNotFoundError:
    pass  # .env optional

from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.constants import ParseMode
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# ─────────────────── Config ───────────────────
BOT_TOKEN: Final[str] = os.getenv("BOT_TOKEN", "8180900089:AAH3qJtVtPhtNLMdb7m9rULkieNSMmXH5Ic")
ADMIN_ID:  Final[int] = int(os.getenv("ADMIN_ID", "7683691800"))

logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# ───────────── Conversation States ────────────
class Form(Enum):
    NAME = auto()
    SURNAME = auto()
    PHONE = auto()
    MESSAGE = auto()
    CONFIRM = auto()

# ───────────────  Translations  ───────────────
TRANSLATIONS = {
    "greeting":   {"uz": "Tilni tanlang:", "ru": "Выберите язык:",           "en": "Choose your language:"},
    "ask_name":   {"uz": "Ismingizni kiriting:", "ru": "Введите ваше имя:",     "en": "Enter your name:"},
    "ask_surname":{"uz": "Familiyangizni kiriting:", "ru": "Введите фамилию:",   "en": "Enter your surname:"},
    "ask_phone":  {"uz": "Telefon raqamingizni +998… formatida kiriting:", "ru": "Введите номер +998…:", "en": "Enter phone in +998… format:"},
    "ask_message":{"uz": "Adminlarga yuboriladigan xabar matnini kiriting:", "ru": "Введите сообщение для админов:", "en": "Enter message for admins:"},
    "confirmation":{"uz": "Maʼlumotlar toʻgʻrimi?", "ru": "Данные верны?",     "en": "Are the details correct?"},
    "thanks":     {"uz": "Rahmat! Xabaringiz adminga yuborildi.", "ru": "Спасибо! Сообщение отправлено администратору.", "en": "Thanks! Message sent to admin."},
    "cancelled":  {"uz": "Bekor qilindi. /start bilan yana urinib ko‘ring.", "ru": "Отменено. Повторите /start.", "en": "Cancelled. Try again with /start."},
    "btn_yes":    {"uz": "✅ Ha", "ru": "✅ Да", "en": "✅ Yes"},
    "btn_no":     {"uz": "❌ Bekor", "ru": "❌ Отмена", "en": "❌ Cancel"},
}

def tr(key: str, lang: str) -> str:
    return TRANSLATIONS[key][lang]

# ─────────────── Handlers ───────────────
async def choose_lang(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    keyboard = ReplyKeyboardMarkup([["O'zbekcha", "Русский", "English"]], resize_keyboard=True, one_time_keyboard=True)
    await update.message.reply_text("Tilni tanlang / Select language / Выберите язык:", reply_markup=keyboard)
    return Form.NAME

async def ask_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang_map = {"O'zbekcha": "uz", "Русский": "ru", "English": "en"}
    context.user_data["lang"] = lang_map.get(update.message.text, "uz")
    await update.message.reply_text(tr("ask_name", context.user_data["lang"]), reply_markup=ReplyKeyboardRemove())
    return Form.SURNAME

async def ask_surname(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["name"] = update.message.text.strip()
    await update.message.reply_text(tr("ask_surname", context.user_data["lang"]))
    return Form.PHONE

async def ask_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["surname"] = update.message.text.strip()
    await update.message.reply_text(tr("ask_phone", context.user_data["lang"]))
    return Form.MESSAGE

async def ask_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["phone"] = update.message.text.strip()
    await update.message.reply_text(tr("ask_message", context.user_data["lang"]))
    return Form.CONFIRM

async def confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["user_message"] = update.message.text.strip()
    lang = context.user_data.get("lang", "uz")
    summary = (
        f"<b>Tasdiqlang:</b>\n\n"
        f"<b>Ism:</b> {context.user_data['name']}\n"
        f"<b>Familiya:</b> {context.user_data['surname']}\n"
        f"<b>Telefon:</b> {context.user_data['phone']}\n"
        f"<b>Xabar:</b> {context.user_data['user_message']}\n\n"
        f"{tr('confirmation', lang)}"
    )
    keyboard = ReplyKeyboardMarkup([[tr("btn_yes", lang), tr("btn_no", lang)]], one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_html(summary, reply_markup=keyboard)
    return Form.CONFIRM

async def finish(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = context.user_data.get("lang", "uz")
    text = update.message.text
    if text == tr("btn_yes", lang):
        info = (
            f"📩 <b>Yangi murojaat</b>\n"
            f"ID: <code>{update.effective_user.id}</code>\n"
            f"Ism: {context.user_data['name']}\n"
            f"Familiya: {context.user_data['surname']}\n"
            f"Telefon: {context.user_data['phone']}\n"
            f"Xabar: {context.user_data['user_message']}"
        )
        await context.bot.send_message(ADMIN_ID, info, parse_mode=ParseMode.HTML)
        await update.message.reply_text(tr("thanks", lang), reply_markup=ReplyKeyboardRemove())
    else:
        await update.message.reply_text(tr("cancelled", lang), reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    lang = context.user_data.get("lang", "uz")
    await update.message.reply_text(tr("cancelled", lang), reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

async def admin_reply(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("Bu buyruq faqat admin uchun.")
        return
    parts = update.message.text.split(maxsplit=2)
    if len(parts) < 3:
        await update.message.reply_text("Foydalanish: /reply <user_id> <matn>")
        return
    try:
        await context.bot.send_message(int(parts[1]), parts[2])
        await update.message.reply_text("Xabar yuborildi ✅")
    except Exception as e:
        logger.error("Cannot send message: %s", e)
        await update.message.reply_text("Xatolik: foydalanuvchiga xabar yuborilmadi ❌")

# ─────────────── main ───────────────

def main() -> None:
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", choose_lang)],
        states={
            Form.NAME:    [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_name)],
            Form.SURNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_surname)],
            Form.PHONE:   [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_phone)],
            Form.MESSAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_message)],
            Form.CONFIRM: [
                MessageHandler(filters.Regex("^(✅ Ha|✅ Да|✅ Yes|❌ Bekor|❌ Отмена|❌ Cancel)$"), finish),
                MessageHandler(filters.TEXT & ~filters.COMMAND, confirm),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv)
    app.add_handler(CommandHandler("reply", admin_reply))
    app.run_polling(close_loop=False)

if __name__ == "__main__":
    main()
