import logging
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters, ConversationHandler, CallbackQueryHandler
from enum import Enum, auto
from enum import IntEnum
# ВАШ ТОКЕН!!! ОБЯЗАТЕЛЬНО замените на ваш токен
BOT_TOKEN = '7570956742:AAE3NLprO8RO96hfVTpnmE3UqQZRWlK3XH8'

# Настройка логгера
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Стадии для ConversationHandler
class ConversationStates(IntEnum):
    CHOOSING = 0
    WISH = 1
    STATUS = 2
    IMAGE = auto()
    TIME_END = auto()
    REMOVING_WISH = 2 # Новое состояние
# Глобальный словарь для хранения желаний
wishes = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_wishes = wishes.get(user_id, {})
    message = "✨ Привет! Я помогу тебе отслеживать твои желания! ✨\n"

    if user_wishes:
        message += "\nТвои желания:\n"
        for i, wish_key in enumerate(user_wishes):
            wish_data = user_wishes[wish_key]
            message += f"{i+1}. {wish_data.get('wish', 'Желание')} ({wish_data.get('status','')})\n"

    keyboard = [[InlineKeyboardButton("➕ Добавить желание", callback_data=f"add_wish:{len(wishes.get(user_id, {}))}"),
                     InlineKeyboardButton("➖ Удалить желание", callback_data="remove_wish")],
                [InlineKeyboardButton("📝 Все желания", callback_data="all_wishes")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(message, reply_markup=reply_markup)

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    context.user_data['user_id'] = user_id # Сохраняем user_id

    if query.data == "add_wish":
         await add_wish(update.callback_query.message, context)
         return ConversationStates.WISH

    if query.data == "remove_wish":
        return ConversationStates.REMOVING_WISH # Возвращаем состояние для удаления

    elif query.data == "all_wishes":
        await show_all_wishes(update.callback_query.message, context) # Не нужен возврат, show_all_wishes сама обрабатывает вывод
        return ConversationStates.CHOOSING # Остаемся в состоянии CHOOSING
async def remove_wish_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
     query = update.callback_query
     await query.answer()
     user_id = update.effective_user.id
     user_wishes = wishes.get(user_id, {})
     if user_wishes:
         keyboard = []
         for wish_key in user_wishes:
             keyboard.append([InlineKeyboardButton(f"❌ {user_wishes[wish_key]}", callback_data=f"delete:{wish_key}")])
         reply_markup = InlineKeyboardMarkup(keyboard)
         await query.edit_message_text("Выбери желание для удаления:", reply_markup=reply_markup)
         return ConversationStates.CHOOSING # Добавлен возврат
     else:
         await query.answer("У тебя нет желаний для удаления")
         return ConversationStates.CHOOSING # Добавлен возврат

async def show_all_wishes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_wishes = wishes.get(user_id, {})
    message = "📝 Все твои желания:\n"
    if user_wishes:
        for i, wish_key in enumerate(user_wishes):
            wish_data = user_wishes[wish_key]
            message += f"{i+1}. {wish_data.get('wish', 'Желание')} ({wish_data.get('status','')})\n"
        await update.message.reply_text(message)
    else:
        await update.message.reply_text("У тебя пока нет желаний. Используй /add_wish, чтобы добавить.")

async def add_wish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = context.user_data.get('user_id') # Используем сохраненный user_id
    await update.message.reply_text("Введите название желания:")
    return ConversationStates.WISH


async def wish_entered(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = context.user_data.get('user_id') # Получаем user_id
    wish_text = update.message.text
    wishes.setdefault(user_id, {}) # Создаем словарь для пользователя, если его еще нет
    wish_key = str(len(wishes[user_id])) # Генерируем ключ здесь
    wishes[user_id][wish_key] = wish_text # Добавляем желание
    context.data['wish'] = update.message.text
    await update.message.reply_text("👍 Желание добавлено! Теперь добавь статус:", reply_markup=ReplyKeyboardMarkup([["В процессе ⏳", "Выполнено ✅", "Отложено ⏸️"]], resize_keyboard=True, one_time_keyboard=True))
    return ConversationStates.STATUS

async def delete_wish(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    user_id = context.user_data.get('user_id')
    wish_key = query.data

    if user_id in wishes and wish_key in wishes[user_id]:
        del wishes[user_id][wish_key]
        await query.edit_message_text(text="Желание удалено!")
    else:
        await query.edit_message_text(text="Желание не найдено.")

    return ConversationStates.CHOOSING

async def status_entered(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    wishes.setdefault(user_id, {}).update({context.data.get('wish_key'): {"wish": context.data['wish'], "status": update.message.text}})
    await update.message.reply_text('Отлично! Теперь можешь добавить картинку (необязательно):', reply_markup=ReplyKeyboardRemove())
    return ConversationStates.IMAGE

async def image_entered(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if update.message.photo:
        photo_file = await update.message.photo[-1].get_file()
        photo_bytes = await photo_file.download_as_bytes() # Загружаем байты изображения
        wishes[user_id][context.data.get('wish_key')]["image"] = photo_bytes
    elif update.message.document:
        doc_file = await update.message.document.get_file()
        doc_bytes = await doc_file.download_as_bytes() # Загружаем байты документа
        wishes[user_id][context.data.get('wish_key')]["image"] = doc_bytes
    else:
        wishes[user_id][context.data.get('wish_key')]["image"] = None

    await update.message.reply_text('Супер! Укажи желаемую дату выполнения (в формате ГГГГ-ММ-ДД, необязательно):')
    return ConversationStates.TIME_END

async def time_end_entered(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    wishes[user_id][context.data.get('wish_key')]["time_end"] = update.message.text
    await update.message.reply_text('💫 Ваше желание успешно добавлено!')
    await start(update, context) # Возвращаемся к началу
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text('Действие отменено.', reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


def main():
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    conversation_handler = ConversationHandler(
    entry_points=[CommandHandler("start", start)],
    states={
        ConversationStates.CHOOSING: [
            CallbackQueryHandler(button_callback, pattern="^add_wish$"),
            CallbackQueryHandler(remove_wish_handler, pattern="^remove_wish$"), # Обработчик для удаления
            CallbackQueryHandler(show_all_wishes, pattern="^all_wishes$"), # Обработчик для просмотра всех желаний
            CallbackQueryHandler(delete_wish, pattern="^delete:") # Обработчик для удаления по кнопке

        ],
        ConversationStates.WISH: [MessageHandler(filters.TEXT & ~filters.COMMAND, wish_entered)],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)

    application.add_handler(conversation_handler)
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CallbackQueryHandler(button_callback))

    application.run_polling()

if __name__ == '__main__':
    main()
