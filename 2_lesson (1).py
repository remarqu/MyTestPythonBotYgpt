from yandexgpt import talk_to_yandex_gpt
import telebot
from telebot import types
import json
import os

bot = telebot.TeleBot(' ')

# Хранение диалогов в формате {chat_id: {'current': int, 'dialogs': {dialog_id: messages}}}
storage = {}
# Файл для хранения
DIALOGS_FILE = 'dialogs.json'
# Загрузка данных
if os.path.exists(DIALOGS_FILE):
  with open(DIALOGS_FILE, 'r') as f:
      try:
          storage = json.load(f)
          # Проверяем и приводим структуру к нужному виду
          for chat_id in storage:
              if isinstance(storage[chat_id], list):
                  # Если данные в старом формате (список сообщений)
                  storage[chat_id] = {
                      'current': 0,
                      'dialogs': {
                          '0': storage[chat_id]
                      }
                  }
              elif 'current' not in storage[chat_id]:
                  # Если нет поля current
                   storage[chat_id] = {
                      'current': 0,
                      'dialogs': storage[chat_id] if 'dialogs' in storage[chat_id] else {'0': []}
                  }
      except:
          storage = {}

def save_dialogs():
  with open(DIALOGS_FILE, 'w') as f:
      json.dump(storage, f)

def init_user(chat_id):
    if chat_id not in storage:
        storage[chat_id] = {
            'current': 0,
            'dialogs': {
                '0': []
            }
        }

def get_current_dialog(chat_id):
    init_user(chat_id)
    return storage[chat_id]['dialogs'][str(storage[chat_id]['current'])]

def create_main_markup():
  markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
  markup.add(types.KeyboardButton('/start'))
  markup.add(types.KeyboardButton('Диалоги'))
  return markup

def create_dialogs_markup(chat_id):
    markup = types.InlineKeyboardMarkup()
    
    # Кнопка создания нового диалога
    markup.add(types.InlineKeyboardButton(
        text="➕ Новый диалог",
        callback_data="new_dialog"
    ))
    
    # Кнопки для переключения между диалогами
    for dialog_id in storage[chat_id]['dialogs']:
        markup.add(types.InlineKeyboardButton(
            text=f"Диалог {dialog_id}" + (" (текущий)" if int(dialog_id) == storage[chat_id]['current'] else ""),
            callback_data=f"switch_{dialog_id}"
        ))

    # Кнопка просмотра диалогов
    markup.add(types.InlineKeyboardButton(
        text="📋 Показать все диалоги",
        callback_data="list_dialogs"
    ))
    
    return markup

@bot.message_handler(commands = ['start'])
def start(message):
  chat_id = str(message.chat.id)
  init_user(chat_id)
  save_dialogs()

  bot.send_message(
      chat_id,
      "Привет! Я чат-бот с Yandex GPT с управлением диалогами.",
      reply_markup=create_main_markup()
  )

@bot.message_handler(func=lambda message: message.text == 'Диалоги')
def show_dialogs_menu(message):
    chat_id = str(message.chat.id)
    init_user(chat_id)

    bot.send_message(
        chat_id,
        "Управление диалогами:",
        reply_markup=create_dialogs_markup(chat_id)
    )

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    chat_id = str(call.message.chat.id)
    init_user(chat_id)

    if call.data == "new_dialog":
        # Создаем новый диалог
        new_id = max([int(k) for k in storage[chat_id]['dialogs'].keys()] + [0]) + 1
        storage[chat_id]['dialogs'][str(new_id)] = []
        storage[chat_id]['current'] = new_id
        save_dialogs()

        bot.edit_message_text(
            "Создан новый диалог. Можете начинать общение!",
            chat_id=chat_id,
            message_id=call.message.message_id,
            reply_markup=create_dialogs_markup(chat_id)
        )

    elif call.data.startswith("switch_"):
        # Переключаем диалог
        dialog_id = int(call.data.split("_")[1])
        storage[chat_id]['current'] = dialog_id
        save_dialogs()

        bot.edit_message_text(
            f"Переключен на диалог {dialog_id}",
            chat_id=chat_id,
            message_id=call.message.message_id,
            reply_markup=create_dialogs_markup(chat_id)
        )
      
    elif call.data == "list_dialogs":
      # Показываем список диалогов
      response = "Ваши диалоги:\n"
      for dialog_id, messages in storage[chat_id]['dialogs'].items():
          status = " (текущий)" if int(dialog_id) == storage[chat_id]['current'] else ""
          msg_count = len([m for m in messages if m['role'] == 'user'])
          response += f"\nДиалог #{dialog_id}{status} - {msg_count} сообщ."

      bot.edit_message_text(
          response,
          chat_id=chat_id,
          message_id=call.message.message_id,
          reply_markup=create_dialogs_markup(chat_id)
      )

@bot.message_handler(commands=['reset'])
def reset(message):
    chat_id = str(message.chat.id)
    init_user(chat_id)
    current_dialog_id = str(storage[chat_id]['current'])
    storage[chat_id]['dialogs'][current_dialog_id] = []
    save_dialogs()
    bot.send_message(chat_id, "Текущий диалог сброшен.", reply_markup=create_main_markup())

@bot.message_handler(func=lambda message: True)
def handle_message(message):
  chat_id = str(message.chat.id)
  # Пропускаем команды
  if message.text.startswith('/'):
    return
  init_user(chat_id)
  dialog = get_current_dialog(chat_id)
  # Добавляем сообщение пользователя
  dialog.append({
      "role": "user",
      "text": message.text
  })
  # Получаем ответ от GPT
  response = talk_to_yandex_gpt(dialog)
  # Добавляем ответ ассистента
  dialog.append({
      "role": "assistant",
      "text": response
  })

  save_dialogs()
  bot.reply_to(message, response, reply_markup=create_main_markup())

bot.polling(none_stop=True)
