import os
import logging
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackContext,
    filters,
)

# ── Переменные ─────────────────────────────
BOT_TOKEN = "8117398622:AAH4VsGY1374oZGM737P2yBSCa9v-MO3oBo"  # Вставьте сюда ваш токен
ADMIN_CHAT_ID = 7549297357  # Ваш chat_id

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN не найден!")

# ── Логи ─────────────────────────────
logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
)
log = logging.getLogger("carrier-bot")

# ── Вопросы ──────────────────────────
questions = [
    "📛 Название компании?",
    "📍 Штат и город?",
    "👷 Какой тип водителей ищете?\nCDL-A, CDL-B, CDL-C, Non-CDL",
    "🚛 Типы трейлеров (можно выбрать несколько и нажать 'Дальше')",
    "💵 Ставка за милю (выберите все подходящие и нажмите 'Дальше')",
    "🏠 Home Time (один вариант)",
    "⚙️ Состояние автопарка (один вариант)",
    "📦 Дополнительная оплата (можно выбрать несколько и нажмите 'Дальше')",
    "💳 Депозит при устройстве (Есть/Нет)",
    "⏱ Минимальный опыт водителя",
    "📞 Номер телефона для связи (начните с +1)"
]

# ── Кнопки ───────────────────────────
TRAILER_KB = ReplyKeyboardMarkup(
    [
        ["Dry Van", "Reefer"],
        ["Flatbed", "Step Deck"],
        ["Tanker", "Carhauler"],
        ["Дальше"]
    ],
    one_time_keyboard=False,
    resize_keyboard=True
)

RATE_KB = ReplyKeyboardMarkup(
    [
        ["$0.60", "$0.65"],
        ["$0.70", "$0.75"],
        ["$0.80", "$0.85"],
        ["Дальше"]
    ],
    one_time_keyboard=False,
    resize_keyboard=True
)

HOME_TIME_KB = ReplyKeyboardMarkup(
    [["Каждые 7 дней"], ["Каждые 10–14 дней"], ["Каждые 2–3 недели"], ["Другой"]],
    one_time_keyboard=True,
    resize_keyboard=True
)

FLEET_KB = ReplyKeyboardMarkup(
    [["Новые"], ["1-2 года"], ["3-5 лет"], ["6+ лет"]],
    one_time_keyboard=True,
    resize_keyboard=True
)

EXTRA_PAY_KB = ReplyKeyboardMarkup(
    [
        ["Detention", "Layover"],
        ["Extra Stop", "Fuel Bonus"],
        ["Нет", "Дальше"]
    ],
    one_time_keyboard=False,
    resize_keyboard=True
)

DEPOSIT_KB = ReplyKeyboardMarkup(
    [["Есть"], ["Нет"]],
    one_time_keyboard=True,
    resize_keyboard=True
)

EXPERIENCE_KB = ReplyKeyboardMarkup(
    [["Без опыта"], ["Менее 1 года"], ["1-2 года"], ["3-5 лет"]],
    one_time_keyboard=True,
    resize_keyboard=True
)

# ── Состояние пользователя ───────────────────────────
user_state = {}  # chat_id -> {"step": int, "answers": list[str], "multi": list[str]}

# ── Команды ──────────────────────────
async def start(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    user_state[chat_id] = {"step": 0, "answers": [], "multi": []}
    await update.message.reply_text(
        "📝 Анкета на подбор водителей.\nОтвечайте по шагам. Начнём!",
        reply_markup=ReplyKeyboardRemove()
    )
    await update.message.reply_text(questions[0])


async def id_cmd(update: Update, context: CallbackContext):
    await update.message.reply_text(f"Ваш chat_id: {update.effective_chat.id}")


# ── Обработка сообщений ──────────────────────────────
async def handle_message(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    text = (update.message.text or "").strip()

    if chat_id not in user_state:
        await update.message.reply_text("Напишите /start, чтобы начать анкету.")
        return

    state = user_state[chat_id]
    step = state["step"]

    # ── Множественный выбор ──
    multi_choice_steps = {3: TRAILER_KB, 4: RATE_KB, 7: EXTRA_PAY_KB}
    if step in multi_choice_steps:
        if text != "Дальше":
            state["multi"].append(text)
            await update.message.reply_text(f"Вы выбрали: {', '.join(state['multi'])}")
            return
        else:
            state["answers"].append(", ".join(state["multi"]))
            state["multi"] = []
            state["step"] += 1
            step = state["step"]
    else:
        state["answers"].append(text)
        state["step"] += 1
        step = state["step"]

    # ── Следующий вопрос ──
    if step >= len(questions):
        a = state["answers"]
        result = (
            f"🆕 Новая анкета:\n"
            f"1) 📛 Название: {a[0]}\n"
            f"2) 📍 Штат и город: {a[1]}\n"
            f"3) 👷 Тип водителей: {a[2]}\n"
            f"4) 🚛 Типы трейлеров: {a[3]}\n"
            f"5) 💵 Ставка за милю: {a[4]}\n"
            f"6) 🏠 Home Time: {a[5]}\n"
            f"7) ⚙️ Состояние автопарка: {a[6]}\n"
            f"8) 📦 Доп. оплата: {a[7]}\n"
            f"9) 💳 Депозит: {a[8]}\n"
            f"10) ⏱ Опыт: {a[9]}\n"
            f"11) 📞 Телефон: {a[10]}"
        )
        if ADMIN_CHAT_ID:
            try:
                await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=result)
            except Exception as e:
                log.warning(f"Не удалось отправить админу: {e}")
        await update.message.reply_text(
            "✅ Благодарим за ответы! Мы свяжемся с вами.",
            reply_markup=ReplyKeyboardRemove()
        )
        user_state.pop(chat_id, None)
        return

    # ── Клавиатуры для вопросов ──
    kb_map = {
        3: TRAILER_KB,
        4: RATE_KB,
        5: HOME_TIME_KB,
        6: FLEET_KB,
        7: EXTRA_PAY_KB,
        8: DEPOSIT_KB,
        9: EXPERIENCE_KB,
    }
    kb = kb_map.get(step)
    await update.message.reply_text(questions[step], reply_markup=kb or ReplyKeyboardRemove())


# ── Запуск ───────────────────────────
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("id", id_cmd))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()


if __name__ == "__main__":
    main()
