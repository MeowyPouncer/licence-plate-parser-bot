import json
import re
import requests
from logger import setup_logger
from telebot.types import ReplyKeyboardMarkup, KeyboardButton


logger = setup_logger(__name__)

def read_json(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"Файл не найден: {file_path}")
        return {}

def write_json(file_path, data):
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except IOError as e:
        logger.error(f"Ошибка при записи в {file_path}: {e}")


def add_user_to_json(file_path, user_id, user_name):
    users = read_json(file_path)
    if user_id in users.values():
        logger.error(f"Пользователь с ID {user_id} уже существует в {file_path}")
        return False
    else:
        users[user_name] = user_id
        write_json(file_path, users)
        return True


def remove_user_from_json(file_path, user_name):
    users = read_json(file_path)
    if user_name in users:
        del users[user_name]
        write_json(file_path, users)

def is_valid_number(number):
    return bool(re.match(r'^[АВЕКМНОРСТУХABEKMHOPCTYX]\d{3}[АВЕКМНОРСТУХABEKMHOPCTYX]{2}\d{2,3}$', number))

def create_keyboard(buttons, one_time_keyboard=True, row_width=2):
    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=one_time_keyboard)
    for i in range(0, len(buttons), row_width):
        row_buttons = [KeyboardButton(button) for button in buttons[i:i + row_width]]
        markup.add(*row_buttons)
    return markup

def get_phone_number(sale_id):
    phone_url = f"https://autokochka.ru/ajax/sale/getPhone/?sale_id={sale_id}"
    response = requests.get(phone_url)
    if response.status_code == 200:
        data = response.json()
        if data.get("ok"):
            return data.get("data", {}).get("phone")
        else:
            logger.warning(f"Не удалось получить номер телефона для объявления {sale_id}")
    else:
        logger.error(f"Ошибка при получении телефонного номера с кодом ответа HTTP {response.status_code}")
    return None

def format_ads_info(ads_info, is_new_ad=False, ads_count=None):
    if not ads_info:
        return "Номер не найден в базе данных."

    header = "🆕 Новое объявление:\n" if is_new_ad else ""
    # ads_count_header = f"Других объявлений с таким номером: {ads_count}" if ads_count and ads_count > 1 else ""
    formatted_ads = []  # Начинаем список с заголовка и информации о количестве объявлений

    for ad in ads_info:
        ad_text = (
            f"{header}"
            f"<b>Марка и модель:</b> {ad['title']}, {ad['year']}\n"
            f"<b>Привод:</b> {ad['drive']}\n"
            f"<b>Город:</b> {ad['city']}\n"
            f"<b>Номер:</b> {ad.get('car_number', 'Не определён')}\n"
            f"<b>Цена:</b> {ad['price']}\n"
            f"<b>Телефон:</b> {ad['phone_number']}\n"
            f"{ad['ad_link']}"
        )
        formatted_ads.append(ad_text)

        if 'existing_ads_links' in ad and ad['existing_ads_links']:
            existing_ads_text = "\n👀 Других объявлений с этим номером:\n" + "\n".join(
                [f"\n{link}" for link in ad['existing_ads_links']]
            )
            formatted_ads.append(existing_ads_text)

    # Добавляем информацию о количестве объявлений только один раз, в начало сообщения
    # if ads_count_header:
    #     formatted_ads.insert(0, ads_count_header)

    return "\n\n".join(formatted_ads)
