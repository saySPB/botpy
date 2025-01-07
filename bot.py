import logging
from telegram import ReplyKeyboardRemove
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters, ConversationHandler, CallbackQueryHandler
from enum import IntEnum

# Настройка логгера
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)
# Глобальный словарь для хранения желаний
wishes = {}

# Стадии для ConversationHandler
class ConversationStates(IntEnum):
    CHOOSING = 0
    WISH = 1
    REMOVING_WISH = 2 # Новое состояние

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("➕ Добавить желание", callback_data="add_wish")],
        [InlineKeyboardButton("➖ Удалить желание", callback_data="remove_wish")],
        [InlineKeyboardButton("📝 Все желания", callback_data="all_wishes")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Выберите действие:', reply_markup=reply_markup)
    return ConversationStates.CHOOSING

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    context.user_data['user_id'] = user_id

    if query.data == "add_wish":
        await add_wish(update.callback_query.message, context)
        return ConversationStates.WISH
    elif query.data == "remove_wish":
        return ConversationStates.REMOVING_WISH # Переход в состояние удаления
    elif query.data == "all_wishes":
        await show_all_wishes(update.callback_query.message, context)
        return ConversationStates.CHOOSING # Возвращаемся в состояние выбора после просмотра
        
async def add_wish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = context.user_data.get('user_id')
    await update.message.reply_text("Введите название желания:")
    return ConversationStates.WISH

async def wish_entered(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = context.user_data.get('user_id')
    wish_text = update.message.text

    wishes.setdefault(user_id, {})
    wish_key = str(len(wishes[user_id]))
    wishes[user_id][wish_key] = wish_text

    await update.message.reply_text(f"Желание '{wish_text}' добавлено!")
    return ConversationStates.CHOOSING # Возвращаемся в основное меню

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels and ends the conversation."""
    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name)
    await update.message.reply_text(
        'Действие отменено. Для начала используйте /start', reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END
async def remove_wish_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = context.user_data.get('user_id')
    user_wishes = wishes.get(user_id, {})

    if user_wishes:
        keyboard = []
        for wish_key in user_wishes:
            keyboard.append([InlineKeyboardButton(f"❌ {user_wishes[wish_key]}", callback_data=f"delete:{wish_key}")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("Выбери желание для удаления:", reply_markup=reply_markup)
    else:
        await query.answer("У тебя нет желаний для удаления")
    return ConversationStates.CHOOSING

async def delete_wish(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    user_id = context.user_data.get('user_id')
    wish_key = query.data.split(":")[1]

    if user_id in wishes and wish_key in wishes[user_id]:
        del wishes[user_id][wish_key]
        await query.edit_message_text("Желание удалено!")
    else:
        await query.edit_message_text("Желание не найдено.")

    return ConversationStates.CHOOSING

async def show_all_wishes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_wishes = wishes.get(user_id, {})
    message = "📝 Все твоижелания:\n"
    if user_wishes:
        for i, wish_key in enumerate(user_wishes):
            message += f"{i+1}. {user_wishes[wish_key]}\n" # Упрощено отображение
        await update.message.reply_text(message)

    else:
        await update.message.reply_text("У тебя пока нет желаний. Используй /add_wish, чтобы добавить.")

conversation_handler = ConversationHandler(
    entry_points=[CommandHandler("start", start)],
    states={
        ConversationStates.CHOOSING: [
            CallbackQueryHandler(button_callback, pattern="^add_wish$"),
            CallbackQueryHandler(remove_wish_handler, pattern="^remove_wish$"),
            CallbackQueryHandler(show_all_wishes, pattern="^all_wishes$"),
            CallbackQueryHandler(delete_wish, pattern="^delete:")
        ],
        ConversationStates.WISH: [MessageHandler(filters.TEXT & ~filters.COMMAND, wish_entered)],
        ConversationStates.REMOVING_WISH: [CallbackQueryHandler(delete_wish, pattern="^delete:")] # Обработчик для удаления
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)

# ВАШ ТОКЕН!!! ОБЯЗАТЕЛЬНО замените на ваш токен
BOT_TOKEN = '7570956742:AAE3NLprO8RO96hfVTpnmE3UqQZRWlK3XH8'


application = ApplicationBuilder().token(BOT_TOKEN).build()

application.add_handler(conversation_handler)

application.run_polling()
