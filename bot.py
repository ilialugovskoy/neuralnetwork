import os, logging, requests, json, random, time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GROQ_KEY = os.environ.get("GROQ_KEY")

if not TELEGRAM_TOKEN or not GROQ_KEY:
    print("❌ Ошибка: TELEGRAM_TOKEN или GROQ_KEY не найдены!")
    exit(1)

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

def call_groq(prompt, system_prompt, max_tokens, temperature):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"}
    data = {"model": "llama-3.3-70b-versatile", "messages": [{"role": "system", "content": system_prompt}, {"role": "user", "content": prompt}], "temperature": temperature, "max_tokens": max_tokens}
    try:
        response = requests.post(url, headers=headers, json=data, timeout=45)
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
        return f"❌ Ошибка: {response.status_code}"
    except Exception as e:
        return f"❌ {str(e)}"

ANSWER_LENGTHS = {
    "краткий": {"max_tokens": 500, "temperature": 0.3, "system_prompt": "Отвечай кратко, 2-3 предложения."},
    "средний": {"max_tokens": 1200, "temperature": 0.5, "system_prompt": "Отвечай развёрнуто, 5-7 предложений."},
    "подробный": {"max_tokens": 2048, "temperature": 0.7, "system_prompt": "Отвечай максимально подробно."}
}

def get_main_menu():
    keyboard = [
        [InlineKeyboardButton("🤖 Задать вопрос", callback_data="ask")],
        [InlineKeyboardButton("📖 Объяснить тему", callback_data="explain")],
        [InlineKeyboardButton("🌍 Перевод", callback_data="translate_menu")],
        [InlineKeyboardButton("⚙️ Длина ответа", callback_data="length_menu")],
        [InlineKeyboardButton("📊 Статистика", callback_data="stats")],
    ]
    return InlineKeyboardMarkup(keyboard)

def get_back_menu():
    return InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data="back_main")]])

def get_length_menu():
    keyboard = [
        [InlineKeyboardButton("⚡ Краткий", callback_data="length_краткий")],
        [InlineKeyboardButton("📝 Средний", callback_data="length_средний")],
        [InlineKeyboardButton("📖 Подробный", callback_data="length_подробный")],
        [InlineKeyboardButton("🔙 Назад", callback_data="back_main")],
    ]
    return InlineKeyboardMarkup(keyboard)

TRANSLATE_LANGUAGES = [("🇬🇧 Английский", "english"), ("🇷🇺 Русский", "russian"), ("🇫🇷 Французский", "french"), ("🇩🇪 Немецкий", "german"), ("🇪🇸 Испанский", "spanish"), ("🇮🇹 Итальянский", "italian")]
def get_translate_menu():
    keyboard = []
    for name, code in TRANSLATE_LANGUAGES:
        keyboard.append([InlineKeyboardButton(name, callback_data=f"trans_{code}")])
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="back_main")])
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🌟 <b>Привет! Я МЕГА-БОТ!</b>\n\nВыбери действие 👇", parse_mode="HTML", reply_markup=get_main_menu())

async def handle_ask(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.replace("/ask", "").strip()
    if not text:
        await update.message.reply_text("✍️ Напиши свой вопрос!", reply_markup=get_back_menu())
        return
    length = context.user_data.get('answer_length', 'средний')
    config = ANSWER_LENGTHS[length]
    response = call_groq(text, config["system_prompt"], config["max_tokens"], config["temperature"])
    await update.message.reply_text(f"🤖 {response}", parse_mode="HTML", reply_markup=get_back_menu())

async def handle_explain(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.replace("/explain", "").strip()
    if not text:
        await update.message.reply_text("✍️ Напиши тему для объяснения!", reply_markup=get_back_menu())
        return
    length = context.user_data.get('answer_length', 'средний')
    config = ANSWER_LENGTHS[length]
    response = call_groq(f"Объясни тему: {text}", config["system_prompt"], config["max_tokens"], config["temperature"])
    await update.message.reply_text(f"📖 {response}", parse_mode="HTML", reply_markup=get_back_menu())

async def handle_translate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.replace("/translate", "").strip()
    target = context.user_data.get('translate_language', 'english')
    if not text:
        await update.message.reply_text("✍️ Напиши текст для перевода!", reply_markup=get_back_menu())
        return
    length = context.user_data.get('answer_length', 'средний')
    config = ANSWER_LENGTHS[length]
    response = call_groq(f"Переведи на {target}: {text}", config["system_prompt"], config["max_tokens"], config["temperature"])
    await update.message.reply_text(f"🌍 {response}", parse_mode="HTML", reply_markup=get_back_menu())

async def handle_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📊 <b>СТАТИСТИКА</b>\n\n🤖 Модель: Llama 3.3 70B\n⚡ Лимит: 14 400/день", parse_mode="HTML", reply_markup=get_back_menu())

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    if data == "back_main":
        await query.message.edit_text("🌟 <b>ГЛАВНОЕ МЕНЮ</b>", parse_mode="HTML", reply_markup=get_main_menu())
        return
    if data == "length_menu":
        await query.message.edit_text("⚙️ <b>ВЫБЕРИ ДЛИНУ ОТВЕТА</b>", parse_mode="HTML", reply_markup=get_length_menu())
        return
    if data.startswith("length_"):
        length = data.replace("length_", "")
        context.user_data['answer_length'] = length
        await query.message.edit_text(f"✅ Длина ответа: {length}", parse_mode="HTML", reply_markup=get_back_menu())
        return
    if data == "translate_menu":
        await query.message.edit_text("🌍 <b>ВЫБЕРИ ЯЗЫК</b>", parse_mode="HTML", reply_markup=get_translate_menu())
        return
    if data.startswith("trans_"):
        context.user_data['translate_language'] = data.replace("trans_", "")
        await query.message.edit_text("🌍 Напиши текст для перевода.", reply_markup=get_back_menu())
        return
    messages = {"ask": "✍️ Напиши свой вопрос!", "explain": "✍️ Напиши тему для объяснения!", "stats": "📊 /stats"}
    if data in messages:
        await query.message.edit_text(messages[data], reply_markup=get_back_menu())

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if not text:
        return
    if text.startswith("/"):
        return
    await handle_ask(update, context)

def main():
    print("🚀 Запуск бота...")
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ask", handle_ask))
    app.add_handler(CommandHandler("explain", handle_explain))
    app.add_handler(CommandHandler("translate", handle_translate))
    app.add_handler(CommandHandler("stats", handle_stats))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("✅ Бот запущен и готов к работе!")
    app.run_polling()

if __name__ == "__main__":
    main()
