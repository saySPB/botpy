import telebot
from telebot import types
import json

# Замените на ваш токен
BOT_TOKEN = "7570956742:AAE3NLprO8RO96hfVTpnmE3UqQZRWlK3XH8" # Замените на ваш токен
bot = telebot.TeleBot(BOT_TOKEN)

USER_DATA_FILE = "user_data.json"

def load_user_data():
    try:
        with open(USER_DATA_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_user_data(data):
    with open(USER_DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

user_data = load_user_data()

# --- Клавиатуры ---
# (Оставьте ваши функции create_main_keyboard и create_wishes_keyboard здесь)
    
def create_main_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    markup.add(types.KeyboardButton("Мои желания"))

    markup_add = types.KeyboardButton("Добавить желание")
    markup_premium = types.KeyboardButton("Премиум (недоступно)") # Неактивная кнопка

    markup.row(markup_add, markup_premium) # Добавляем кнопки в ряд

    return markup


def create_wishes_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("Желания в процессе"))
    markup.add(types.KeyboardButton("Выполненные желания"))
    markup.add(types.KeyboardButton("Назад")) # Кнопка возврата
    return markup


#def create_priority_keyboard(wish_text):
#    markup = types.InlineKeyboardMarkup(row_width=3)
#    markup.add(
#        types.InlineKeyboardButton("⬆️", callback_data=f"up:{wish_text}"),
#        types.InlineKeyboardButton("⬇️", callback_data=f"down:{wish_text}"),
#        types.InlineKeyboardButton("✏️", callback_data=f"edit:{wish_text}"), # Добавлена кнопка "Редактировать"
#        types.InlineKeyboardButton("❌", callback_data=f"delete:{wish_text}"),
#        types.InlineKeyboardButton("Назад", callback_data="back_to_wishes")
#
#    )
#    return markup

# --- Обработчики ---

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    user_data.setdefault(user_id, {}) # Инициализируем данные пользователя
    user_data[user_id].setdefault('wishes', []) # Создаем список желаний если его нет

    bot.send_message(message.chat.id, "Добро пожаловать в бот желаний!", reply_markup=create_main_keyboard())

def show_completed_wishes(message):
    try:
        user_id = message.from_user.id
        completed_wishes = user_data.get(user_id, {}).get('completed_wishes', []) # Получаем выполненные желания

        if not completed_wishes:
            bot.send_message(message.chat.id, "У вас пока нет выполненных желаний.", reply_markup=create_wishes_keyboard()) # Убедитесь, что create_wishes_keyboard существует
            return

        response = "Ваши выполненные желания:\n"
        for i, wish in enumerate(completed_wishes):
            response += f"{i+1}. {wish}\n"

        bot.send_message(message.chat.id, response, reply_markup=create_wishes_keyboard()) # Убедитесь, что create_wishes_keyboard существует
    except Exception as e:
        print(f"Ошибка: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка при отображении выполненных желаний. Попробуйте еще раз.")

@bot.message_handler(content_types=['text'])
def handle_message(message):
    try:
        if message.text == "Мои желания":
            bot.send_message(message.chat.id, "Выберите категорию:", reply_markup=create_wishes_keyboard())
        elif message.text == "Желания в процессе":
            show_wishes_in_progress(message)
        elif message.text == "Добавить желание":
            add_wish(message)
        elif message.text == "Назад": # Обработка кнопки "Назад"
            bot.send_message(message.chat.id, "Главное меню:", reply_markup=create_main_keyboard())
        elif message.text == "Выполненные желания":
            show_completed_wishes(message) # Добавьте эту строку
    except Exception as e:
        print(f"Ошибка: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка. Попробуйте позже.")

def add_wish(message):
    user_id = message.from_user.id
    user_data.setdefault(user_id, {})['waiting_for_wish'] = True
    bot.send_message(message.chat.id, "Напишите ваше желание:", reply_markup=types.ReplyKeyboardRemove())

@bot.message_handler(func=lambda message: user_data.get(message.from_user.id, {}).get('waiting_for_wish', False)) # Безопасная проверка флага
def handle_wish_text(message):
    try:
        user_id = message.from_user.id
        wish_text = message.text
        user_data.setdefault(user_id, {}).setdefault('wishes', []).append(wish_text)
        save_user_data(user_data)
        bot.send_message(message.chat.id, f"Ваше желание '{wish_text}' добавлено в 'Желания в процессе'!", reply_markup=create_main_keyboard())
        user_data[user_id]['waiting_for_wish'] = False
    except Exception as e:
        print(f"Ошибка: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка при добавлении желания. Попробуйте еще раз.")

def show_wishes_in_progress(message):
    try:
        user_id = message.from_user.id
        wishes = user_data.get(user_id, {}).get('wishes', [])

        if not wishes:
            bot.send_message(message.chat.id, "У вас пока нет желаний в процессе.", reply_markup=create_wishes_keyboard())
            return

        response = "Ваши желания в процессе:\n"
        for i, wish in enumerate(wishes):
            response += f"{i+1}. {wish}\n"

        bot.send_message(message.chat.id, response, reply_markup=create_wishes_keyboard())
    except Exception as e:
        print(f"Ошибка: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка при отображении желаний. Попробуйте еще раз.")

# --- Запуск бота ---
bot.polling(none_stop=True)
