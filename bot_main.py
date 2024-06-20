import asyncio
import os
import sys
from fastapi import FastAPI, Response
import uvicorn
from telebot.async_telebot import AsyncTeleBot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, Message
from db_worker import Session, Advertisement, CarNumber, search_ads_by_number
from keyboard_factory import KeyboardFactory
from logger import setup_logger
from state_manager import set_state, BotState, get_state
from utils import is_valid_number, read_json, add_user_to_json, create_keyboard, write_json, format_ads_info
from pathlib import Path


def get_base_path():
    if sys.platform == "linux" or sys.platform == "linux2":
        return Path("/app/volume")
    else:
        return Path("volume")


base_path = get_base_path()

allowed_users_path = base_path / "allowed_users.json"
subscribed_users_path = base_path / "subscribed_users.json"

TOKEN = os.getenv('BOT_TOKEN')
ADMINS = set(map(int, os.getenv('ADMINS', '').split(',')))
# ADMINS = [admin_id]

bot = AsyncTeleBot(TOKEN, parse_mode='HTML')

app = FastAPI()

temp_user_info = {}

logger = setup_logger(__name__)


async def prompt_for_user_deletion(message: Message, list_type):
    users = read_json(list_type)
    if not users:
        message_text = "Список пуст."
        await bot.send_message(message.chat.id, message_text, reply_markup=KeyboardFactory.return_keyboard())
        return
    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    for name in users.keys():
        markup.add(KeyboardButton(f"{name}"))
    markup.add(KeyboardButton("Отменить удаление"))
    await bot.send_message(message.chat.id, "Выберите пользователя для удаления:", reply_markup=markup)
    set_state(message.from_user.id, BotState.SELECT_USER_TO_DELETE)


async def display_users(message, file_path):
    list_type = "разрешённых пользователей" if file_path.name == "allowed_users.json" else "подписанных пользователей"

    users = read_json(file_path)
    if not users:
        await bot.send_message(message.chat.id, f"Список {list_type} пуст.")
        markup = KeyboardFactory.users_keyboard()
        await bot.send_message(message.chat.id, "Выберите дальнейшее действие:", reply_markup=markup)
    else:
        users_info = "\n".join([f" *{name}:* \n{user_id}" for name, user_id in users.items()])
        await bot.send_message(message.chat.id, f"* Список {list_type}*\n***\n{users_info}\n***",
                               parse_mode='Markdown')

        markup = KeyboardFactory.users_keyboard()
        await bot.send_message(message.chat.id, "Выберите дальнейшее действие:", reply_markup=markup)
    set_state(message.from_user.id, BotState.VIEWING_LIST)


@bot.message_handler(commands=['start', 'help'])
@bot.message_handler(func=lambda message: message.text == 'Вернуться в главное меню')
async def send_welcome(message: Message):
    allowed_users = read_json(allowed_users_path)  # Использование Path объекта для указания пути файла
    if message.from_user.id not in allowed_users.values():
        logger.info(f"Пользователь {message.from_user.id} пытается войти в бота. ID: {message.from_user.id}")
        await bot.send_message(message.chat.id, "Функционал бота вам недоступен.")
        set_state(message.from_user.id, BotState.ACCESS_DENIED)
        return

    buttons = ['Поиск по номеру']
    if message.from_user.id in ADMINS:
        buttons.append('Управлять списками')

    markup = create_keyboard(buttons)
    await bot.reply_to(message, "Выберите действие:", reply_markup=markup)
    set_state(message.from_user.id, BotState.INITIAL)
    logger.info(f"Received {message.text} command from user {message.from_user.id}")


@bot.message_handler(func=lambda message: message.text in ['Отменить действие', 'Отменить удаление'])
async def handle_cancel(message: Message):
    user_id = message.from_user.id
    list_type = temp_user_info.get(user_id, {}).get("list_type", allowed_users_path)

    if get_state(user_id) in [
        BotState.AWAITING_NAME_FOR_ADD,
        BotState.AWAITING_ID_FOR_ADD,
        BotState.AWAITING_DELETE_CONFIRMATION,
        BotState.SELECT_USER_TO_DELETE
    ]:
        await bot.send_message(user_id, "Операция отменена.", reply_markup=KeyboardFactory.return_keyboard())

        await display_users(message, list_type)


@bot.message_handler(func=lambda message: get_state(message.from_user.id) == BotState.INITIAL)
async def main_menu_handler(message: Message):
    allowed_users = read_json(allowed_users_path)
    if message.text == 'Поиск по номеру' and message.from_user.id in allowed_users.values():
        markup = KeyboardFactory.return_keyboard()
        await bot.send_message(message.chat.id, "Введите номер для поиска:", reply_markup=markup)
        set_state(message.from_user.id, BotState.AWAITING_NUMBER_INPUT)
    elif message.text == 'Управлять списками' and message.from_user.id in ADMINS:
        markup = KeyboardFactory.manage_lists_keyboard()
        await bot.send_message(message.chat.id, "Выберите опцию:", reply_markup=markup)
        set_state(message.from_user.id, BotState.VIEWING_LIST)


@bot.message_handler(func=lambda message: get_state(message.from_user.id) == BotState.VIEWING_LIST)
async def viewing_list_handler(message: Message):
    user_id = message.from_user.id
    if message.text == 'Просмотреть разрешённых пользователей':
        await display_users(message, allowed_users_path)
        temp_user_info[user_id] = {"list_type": allowed_users_path}
    elif message.text == 'Просмотреть подписанных пользователей':
        await display_users(message, subscribed_users_path)
        temp_user_info[user_id] = {"list_type": subscribed_users_path}
    elif message.text in ['Добавить', 'Удалить']:
        if message.text == 'Добавить':
            list_type = temp_user_info.get(user_id, {}).get("list_type", "volume/allowed_users.json")
            set_state(user_id, BotState.AWAITING_NAME_FOR_ADD)
            markup = KeyboardFactory.cancel_button()
            await bot.send_message(message.chat.id,
                                   "Введите имя пользователя для добавления:",
                                   reply_markup=markup)
        elif message.text == 'Удалить':
            list_type = temp_user_info[user_id].get("list_type", allowed_users_path)
            await prompt_for_user_deletion(message, list_type)
    elif message.text == 'Вернуться в главное меню':
        await send_welcome(message)


@bot.message_handler(func=lambda message: get_state(message.from_user.id) == BotState.AWAITING_NUMBER_INPUT)
async def handle_number_input(message):
    number = message.text.upper().replace(" ", "").replace("-", "")
    markup = KeyboardFactory.return_keyboard()
    if is_valid_number(number):
        results = await search_ads_by_number(number)
        if results:
            formatted_ad = format_ads_info(results, ads_count=len(results))
            await bot.send_message(message.chat.id, formatted_ad, reply_markup=markup, parse_mode='HTML')
            set_state(message.from_user.id, BotState.INITIAL)
        else:
            formatted_ad = "Номер не найден в базе данных. Попробуйте ввести другой номер."
            await bot.send_message(message.chat.id, formatted_ad, reply_markup=markup, parse_mode='HTML')
    else:
        formatted_ad = (
            "Номер введен неверно. Пожалуйста, убедитесь, что номер соответствует формату A123BC45 и попробуйте снова.")
        await bot.send_message(message.chat.id, formatted_ad, reply_markup=markup, parse_mode='HTML')


@bot.message_handler(func=lambda message: get_state(message.from_user.id) == BotState.SELECT_USER_TO_DELETE)
async def handle_user_selection_for_deletion(message: Message):
    markup = KeyboardFactory.manage_lists_keyboard()
    if message.text == "Отменить удаление":
        await bot.send_message(message.chat.id, "Выберите действие:", reply_markup=markup)
        set_state(message.from_user.id, BotState.VIEWING_LIST)
    else:
        user_name_to_delete = message.text.replace("Удалить: ", "")
        list_type = temp_user_info[message.from_user.id]["list_type"]
        users = read_json(list_type)

        if user_name_to_delete in users:
            temp_user_info[message.from_user.id]["user_name_to_delete"] = user_name_to_delete
            markup = KeyboardFactory.decision_keyboard()
            await bot.send_message(message.chat.id,
                                   f"Вы уверены, что хотите удалить пользователя {user_name_to_delete}?",
                                   reply_markup=markup)
            set_state(message.from_user.id, BotState.AWAITING_DELETE_CONFIRMATION)
        else:
            await bot.send_message(message.chat.id,
                                   "Пользователь не найден. Пожалуйста, выберите пользователя из списка.",
                                   reply_markup=markup)
            set_state(message.from_user.id, BotState.VIEWING_LIST)


@bot.message_handler(func=lambda message: get_state(message.from_user.id) == BotState.AWAITING_DELETE_CONFIRMATION)
async def handle_deletion_confirmation(message: Message):
    if message.text.lower() == "да, удалить":
        user_name_to_delete = temp_user_info[message.from_user.id]["user_name_to_delete"]
        list_type = temp_user_info[message.from_user.id]["list_type"]
        users = read_json(list_type)
        if user_name_to_delete in users:
            del users[user_name_to_delete]
            write_json(list_type, users)
            # TODO: Установка состояния для удалённого пользователя
            # set_state(user_name_to_delete, BotState.ACCESS_DENIED)
            await bot.send_message(message.chat.id, f"Пользователь {user_name_to_delete} удален.",
                                   reply_markup=KeyboardFactory.manage_lists_keyboard())
        else:
            await bot.send_message(message.chat.id, "Не удалось удалить пользователя.",
                                   reply_markup=KeyboardFactory.manage_lists_keyboard())
        set_state(message.from_user.id, BotState.VIEWING_LIST)
    elif message.text.lower() == "Отменить удаление":
        await bot.send_message(message.chat.id, "Удаление отменено.",
                               reply_markup=KeyboardFactory.manage_lists_keyboard())
        set_state(message.from_user.id, BotState.VIEWING_LIST)


@bot.message_handler(func=lambda message: get_state(message.from_user.id) == BotState.AWAITING_NAME_FOR_ADD)
async def awaiting_name_for_add_handler(message: Message):
    user_id = message.from_user.id
    user_name = message.text
    temp_user_info[user_id]["name"] = user_name
    set_state(user_id, BotState.AWAITING_ID_FOR_ADD)
    markup = KeyboardFactory.cancel_button()
    await bot.send_message(message.chat.id, f"Введите ID для {user_name}:", reply_markup=markup)


@bot.message_handler(func=lambda message: get_state(message.from_user.id) == BotState.AWAITING_ID_FOR_ADD)
async def awaiting_id_for_add_handler(message: Message):
    user_id = message.from_user.id
    if message.text.isdigit():
        user_id_to_add = int(message.text)
        user_name = temp_user_info[user_id].get("name")
        list_type = temp_user_info[user_id].get("list_type", "volume/allowed_users.json")

        if add_user_to_json(list_type, user_id_to_add, user_name):
            await bot.send_message(message.chat.id, f"Пользователь {user_name} с ID {user_id_to_add} успешно добавлен.")
            await display_users(message, list_type)
            set_state(user_id, BotState.VIEWING_LIST)
        else:
            await bot.send_message(message.chat.id, f"Пользователь с ID {user_id_to_add} уже существует.")
    else:
        logger.error(f"Некорректное значение {user_id}")
        markup = KeyboardFactory.cancel_button()
        await bot.send_message(message.chat.id, "ID должен быть числом. Пожалуйста, попробуйте еще раз.",
                               reply_markup=markup)


async def run_bot():
    await bot.infinity_polling()


@app.post("/notify/")
async def notify_new_ad(ad_detail: dict):
    subscribed_users = read_json(subscribed_users_path)
    session = Session()
    try:
        car_number = ad_detail.get('car_number')
        if not car_number:
            car_number = 'отсутствует / не определён'

        existing_ads = session.query(Advertisement).join(CarNumber).filter(CarNumber.number == car_number).all()

        ads_count = len(existing_ads)

        if ads_count > 1:
            ad_links = [ad.ad_link for ad in existing_ads if ad.ad_link != ad_detail['ad_link']]
            ad_detail['existing_ads_links'] = ad_links

        ad_info = [ad_detail]
        message = format_ads_info(ad_info, is_new_ad=True, ads_count=ads_count if ads_count > 1 else None)

        for user_id in subscribed_users.values():
            try:
                await bot.send_message(user_id, message, parse_mode='HTML')
            except Exception as e:
                logger.error(f"Ошибка при отправке уведомления пользователю {user_id}: {e}")
        logger.info("Уведомление о новом объявлении отправлено.")
    except Exception as e:
        logger.error(f"Ошибка при отправке уведомления о новом объявлении: {e}")
    finally:
        session.close()

    return Response("OK", status=200)


async def run_server():
    config = uvicorn.Config(app=app, host="127.0.0.1", port=8000, loop="asyncio")
    server = uvicorn.Server(config)
    await server.serve()


async def main():
    bot_task = asyncio.create_task(run_bot())
    server_task = asyncio.create_task(run_server())
    await asyncio.gather(bot_task, server_task)

if __name__ == '__main__':
    asyncio.run(main())
