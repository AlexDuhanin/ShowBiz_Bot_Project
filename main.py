from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
    CallbackQueryHandler,
    ConversationHandler
)
from gcalendar import Gcalendar
import datetime as dt
from dotenv import load_dotenv
import os

load_dotenv()
TOKEN = os.getenv('TELEGRAM_TOKEN') # токен от бота

calendar = Gcalendar()


(VOICE, START_VOICE, FREE_SLOT,
 NAME, CONTACT, END,
 GUITAR,
 ACCEPT, CANCEL, SUCCES) = range(0, 10)

ADMIN = 5181963292


def time_to_dt(time: str):
    """Преобразует строку в формате ISO в объект datetime."""
    tm = dt.datetime.fromisoformat(time)
    return tm


def time_to_str(time: dt.datetime):
    """Преобразует объект datetime в строку."""
    pass


def human_time(time: dt.datetime):
    """Форматирует объект datetime в удобочитаемую строку."""
    tm = dt.datetime.strftime(time, "%d.%m.%Y | %H:%M:%S")
    return tm


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает команду /start — показывает главное меню с выбором направления."""

    text = "Приветствие.\nВыберите направление:"
    keyboard = [[InlineKeyboardButton("Вокал", callback_data=str(VOICE))],
                [InlineKeyboardButton("Гитара", callback_data=str(GUITAR))]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(text=text, reply_markup=reply_markup)


async def voice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показывает доступные слоты для занятий вокалом из календаря."""
    user_data = context.user_data
    text = "Информация о занятиях вокала и пр."
    query = update.callback_query

    # Запрос к календарю "Свободный слот (вокал)"
    user_data["main_choose"] = "events_voice"
    events = user_data["events_voice"] = calendar.events_list(name="Свободный слот (вокал)")
    if not events:
        await query.edit_message_text(text="Свободных мест нет")
        return ConversationHandler.END

    keyboard = []
    for i, event in enumerate(events):
        start = event["start"]
        tm = human_time(time_to_dt(start["dateTime"]))
        keyboard.append([InlineKeyboardButton(f"{tm}", callback_data=f"{VOICE}-{i}")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.answer()
    await query.edit_message_text(text=text, reply_markup=reply_markup)
    return NAME


async def guitar(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показывает доступные слоты для занятий гитарой из календаря."""
    user_data = context.user_data
    text = "Информация о занятиях гитары и пр."
    query = update.callback_query

    # Запрос к календарю "Свободный слот (гитара)"
    user_data["main_choose"] = "events_guitar"
    events = user_data["events_guitar"] = calendar.events_list(name="Свободный слот (гитара)")
    if not events:
        await query.edit_message_text(text="Свободных мест нет")
        return ConversationHandler.END

    keyboard = []
    for i, event in enumerate(events):
        start = event["start"]
        tm = human_time(time_to_dt(start["dateTime"]))
        keyboard.append([InlineKeyboardButton(f"{tm}", callback_data=f"{GUITAR}-{i}")])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.answer()
    await query.edit_message_text(text=text, reply_markup=reply_markup)
    return NAME


async def name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Запрашивает у пользователя его имя после выбора слота."""
    user_data = context.user_data
    # message = update.effective_message.text
    text = "Введите свое имя:"
    query = update.callback_query
    await query.answer()
    event_choose = int(query.data.split("-")[1])
    user_data["event_choose"] = event_choose
    await update.effective_user.send_message(text=text)
    return CONTACT


async def contact(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Сохраняет имя пользователя и запрашивает контактные данные."""
    user_data = context.user_data
    message = update.effective_message.text  # Принять имя
    user_data["name"] = message
    text = "Введите свое контакт:"
    await update.message.reply_text(text=text)
    return ACCEPT


async def accept(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Сохраняет контактные данные и предлагает подтвердить бронь."""
    user_data = context.user_data
    message = update.effective_message.text  # Принять контакт
    user_data["contact"] = message
    text = "Подтвердите бронь"
    keyboard = [[InlineKeyboardButton("Да", callback_data=str(ACCEPT))],
                [InlineKeyboardButton("Отмена", callback_data=str(CANCEL))]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(text=text, reply_markup=reply_markup)
    return SUCCES  # succes


async def succes(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Подтверждает бронь: обновляет событие в календаре и уведомляет админа о новой записи"""
    user_data = context.user_data
    # Принять ACCEPT
    text = "Запись успешно завершена"
    query = update.callback_query
    await query.answer()
    await update.effective_user.send_message(text=text)

    event_choose = user_data[user_data["main_choose"]][user_data["event_choose"]]
    event_id = event_choose["id"]
    calendar.event_update(event_id=event_id, summary=user_data["name"],
                          color_id=3, description=f"Контакт: {user_data["contact"]}")
    # Информируем админа о новой записи
    tm = human_time(time_to_dt(event_choose["start"]["dateTime"]))
    text = f"Новая запись:\nВремя записи: {tm}\nКонтакт: {user_data["contact"]}"
    await context.bot.send_message(chat_id=ADMIN,
                                   text=text)
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = "Запись отменена"
    query = update.callback_query
    await query.answer()
    await update.effective_user.send_message(text=text)
    return ConversationHandler.END


# proxy_url = 'http://username:password@host:port' # или socks5://
# .proxy_url(proxy_url).get_updates_proxy_url(proxy_url)
# app = ApplicationBuilder.token(TOKEN).build()

app = ApplicationBuilder().token(TOKEN).build()

conv_handler_voice = ConversationHandler(
    entry_points=[CallbackQueryHandler(voice, pattern=f"^{VOICE}$")],
    states={
        NAME: [CallbackQueryHandler(name, pattern=f"^({VOICE})-")],
        CONTACT: [MessageHandler(filters.TEXT & ~filters.COMMAND, contact)],
        ACCEPT: [MessageHandler(filters.TEXT & ~filters.COMMAND, accept)],
        SUCCES: [CallbackQueryHandler(succes, pattern=str(ACCEPT)),
                 CallbackQueryHandler(cancel, pattern=str(CANCEL))],
    },
    fallbacks=[CommandHandler("start", start)],
)

conv_handler_guitar = ConversationHandler(
    entry_points=[CallbackQueryHandler(guitar, pattern=f"^{GUITAR}$")],
    states={
        NAME: [CallbackQueryHandler(name, pattern=f"^({GUITAR})-")],
        CONTACT: [MessageHandler(filters.TEXT & ~filters.COMMAND, contact)],
        ACCEPT: [MessageHandler(filters.TEXT & ~filters.COMMAND, accept)],
        SUCCES: [CallbackQueryHandler(succes, pattern=str(ACCEPT)),
                 CallbackQueryHandler(cancel, pattern=str(CANCEL))],
    },
    fallbacks=[CommandHandler("start", start)],
)

app.add_handler(CommandHandler("start", start))
app.add_handler(conv_handler_voice)
app.add_handler(conv_handler_guitar)

# app.add_handler(CommandHandler("hello", hello))
# app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

app.run_polling()