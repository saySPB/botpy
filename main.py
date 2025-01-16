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


def create_priority_keyboard(wish_text, in_process=False):
    keyboard = telebot.types.InlineKeyboardMarkup()
    prefix = "in_process_" if in_process else ""

    delete_button = telebot.types.InlineKeyboardButton('❌', callback_data=f'{prefix}delete:{wish_text}')
    complete_button = telebot.types.InlineKeyboardButton('✅', callback_data=f'{prefix}complete:{wish_text}') # Новая кнопка

    keyboard.row(delete_button, complete_button) # Добавили кнопку на клавиатуру

    return keyboard

def complete_wish(call, wish_text, in_process):
    user_id = call.from_user.id
    try:
        if in_process:
            source_list = user_data[user_id]['wishes_in_process']
            target_list = user_data[user_id].get('completed_wishes', []) # Если нет, создаем
            user_data[user_id]['completed_wishes'] = target_list
        else:
            source_list = user_data[user_id]['wishes']
            target_list = user_data[user_id].get('completed_wishes', [])
            user_data[user_id]['completed_wishes'] = target_list

        source_list.remove(wish_text)
        target_list.append(wish_text)


        bot.answer_callback_query(call.id, "Желание выполнено!")

        

        # Покажем выполненные желания (опционально)
        show_completed_wishes(call.message)



    except ValueError:
        bot.answer_callback_query(call.id, "Желание не найдено")


def show_completed_wishes(message): # Новая функция для отображения выполненных желаний
    user_id = message.from_user.id
    completed_wishes = user_data.get(user_id, {}).get('completed_wishes', [])

    if completed_wishes:
        bot.send_message(message.chat.id, "Выполненные желания:")
        for i, wish in enumerate(completed_wishes):
            bot.send_message(message.chat.id, f"{i+1}. {wish}")
    else:
        bot.send_message(message.chat.id, "Все желания выполнены!!!")


# --- Обработчики ---

@bot.message_handler(commands=['start'])
def start(message):
    welcome_text = """
Что умеет WishBoardBot?

Наш бот сделает процесс создания карты желаний простым и увлекательным:

* Создание категорий: Раздели свои желания на разные сферы жизни (например, карьера, отношения, здоровье, путешествия) 🗂️
* Добавление желаний: Добавляй свои желания с помощью текста, изображений или голосовых сообщений 📝🖼️🎤
* Визуализация: Бот поможет тебе красиво оформить твою карту желаний 🤩
* Напоминания: Настраивай напоминания, чтобы не забывать о своих целях 🔔
* Отслеживание прогресса: Следи за тем, как твои желания становятся реальностью ✅"""
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    item1 = telebot.types.KeyboardButton("Действие 1")
    item2 = telebot.types.KeyboardButton("Действие 2")
    markup.add(item1, item2)

    bot.send_message(message.chat.id, welcome_text, reply_markup=markup)
    user_id = message.from_user.id
    user_data.setdefault(user_id, {}) # Инициализируем данные пользователя
    user_data[user_id].setdefault('wishes', []) # Создаем список желаний если его нет

    bot.send_message(message.chat.id,  "Добро пожаловать в бот желаний!", reply_markup=create_main_keyboard())
def show_wishes_in_progress(message):
    user_id = message.from_user.id
    user_data.setdefault(user_id, {}).setdefault('wishes', [])
    wishes = user_data[user_id]['wishes']
    if not wishes:
        bot.send_message(message.chat.id, "У вас пока нет желаний в процессе.", reply_markup=create_wishes_keyboard())
        return

    for i, wish in enumerate(wishes):
        priority = i + 1 # Приоритет от 1 до 10
        priority_text = f"{priority}. {wish}"
        bot.send_message(message.chat.id, priority_text, reply_markup=create_priority_keyboard(wish)) # передаем текст желания


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

@bot.message_handler(commands=['add_wish'])
def add_wish(message):
    msg = bot.send_message(message.chat.id, "Напишите ваше желание:")
    bot.register_next_step_handler(msg, process_wish_step)

def process_wish_step(message):
    wish_text = message.text
    if not wish_text:
        bot.send_message(message.chat.id, "Вы не ввели желание. Попробуйте еще раз.")
        return # Прерываем функцию, если желание пустое
    user_id = message.from_user.id
    user_data.setdefault(user_id, {'wishes': []})['wishes'].append(wish_text) # Добавляем проверку на существование ключа 'wishes'
    bot.send_message(message.chat.id, f"Ваше желание '{wish_text}' добавлено!", reply_markup=create_main_keyboard())

@bot.message_handler(func=lambda message: message.text == "Показать желания")
def show_wishes(message):
    user_id = message.from_user.id
    wishes = user_data.get(user_id, {}).get('wishes', [])
    if wishes:
        wish_list = ""
        for i, wish in enumerate(wishes): # Используем enumerate для получения индекса
            wish_list += f"{i+1}. {wish}\n" # Добавляем номер к каждому желанию
            bot.send_message(message.chat.id, wish, reply_markup=create_priority_keyboard(wish)) # Отправляем каждое желание с клавиатурой
    else:
        bot.send_message(message.chat.id, "У вас пока нет желаний.")


@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    data = call.data.split(':')
    action = data[0]
    wish_text = ':'.join(data[1:]) # Объединяем текст желания обратно, если он содержит ':'

    in_process = action.startswith("in_process_")
    if in_process:
        action = action[11:] # Удаляем префикс "in_process_"

    elif action == "complete": # Обработчик новой кнопки
        complete_wish(call, wish_text, in_process)


def move_wish(call, wish_text, direction):
    user_id = call.from_user.id
    wishes = user_data.get(user_id, {}).get('wishes', [])
    try:
        index = wishes.index(wish_text)
        if direction == "up" and index > 0:
            wishes[index], wishes[index - 1] = wishes[index - 1], wishes[index]
        elif direction == "down" and index < len(wishes) - 1:
            wishes[index], wishes[index + 1] = wishes[index + 1], wishes[index]
        user_data[user_id]['wishes'] = wishes
        save_user_data(user_data)
        bot.edit_message_text(f"{index + 1 + (1 if direction == 'down' else -1)}. {wish_text}", call.message.chat.id, call.message.message_id, reply_markup=create_priority_keyboard(wish_text)) # Обновляем текст и клавиатуру
    except ValueError:
        bot.answer_callback_query(call.id, "Желание не найдено")

def delete_wish(call, wish_text):
    user_id = call.from_user.id
    wishes = user_data.get(user_id, {}).get('wishes', [])
    try:
        wishes.remove(wish_text)
        user_data[user_id]['wishes'] = wishes
        save_user_data(user_data)
        bot.delete_message(call.message.chat.id, call.message.message_id) # Удаляем сообщение с желанием
        bot.answer_callback_query(call.id, "Желание удалено")
    except ValueError:
        bot.answer_callback_query(call.id, "Желание не найдено")


def edit_wish(call, old_wish_text):
    msg = bot.send_message(call.message.chat.id, f"Редактируйте желание '{old_wish_text}':")
    bot.register_next_step_handler(msg, process_edit_wish, old_wish_text, call.message.message_id) # Передаем ID сообщения для редактирования


def process_edit_wish(message, old_wish_text, message_id_to_edit):
    user_id = message.from_user.id
    new_wish_text = message.text
    wishes = user_data.get(user_id, {}).get('wishes', [])
    try:
        index = wishes.index(old_wish_text)
        wishes[index] = new_wish_text
        user_data[user_id]['wishes'] = wishes
        save_user_data(user_data)
        bot.edit_message_text(f"{index+1}. {new_wish_text}", message.chat.id, message_id_to_edit, reply_markup=create_priority_keyboard(new_wish_text)) # Редактируем сообщение с желанием
    except ValueError:
        bot.send_message(message.chat.id, "Желание не найдено")


bot.polling(none_stop=True)
