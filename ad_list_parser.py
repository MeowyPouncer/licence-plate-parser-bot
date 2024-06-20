import requests
import json
from bs4 import BeautifulSoup
from logger import setup_logger
from utils import get_phone_number

logger = setup_logger(__name__)


def save_last_processed_ad(ad_id):
    try:
        with open('volume/last_processed_ad.json', 'w') as f:
            json.dump({"last_processed_ad": ad_id}, f)
        logger.info(f"Сохранено последнее обработанное объявление: {ad_id}")
    except Exception as e:
        logger.error(f"Ошибка при сохранении последнего обработанного объявления: {e}")


def load_last_processed_ad():
    try:
        with open('volume/last_processed_ad.json', 'r') as f:
            data = json.load(f)
            last_ad = data.get("last_processed_ad")
            logger.info(f"Загружено последнее обработанное объявление: {last_ad}")
            return last_ad
    except FileNotFoundError:
        logger.warning("Файл  не найден. Создаём новый.")
        return None
    except Exception as e:
        logger.error(f"Ошибка при загрузке последнего обработанного объявления: {e}")
        return None


def parse_ads_list(url='https://autokochka.ru/sales/?sort=newest&page=4'):
    logger.info(f"Начало парсинга списка объявлений с {url}")
    last_processed_ad = load_last_processed_ad()
    ads_list = []

    response = requests.get(url)
    if response.status_code == 200:
        logger.info("Успешно получен ответ от сервера.")
        soup = BeautifulSoup(response.text, 'html.parser')
        sale_items = soup.find_all('div', class_='pure-g sale-item sale-block-item')

        if not sale_items:
            logger.warning("На странице не найдены объявления.")
            return ads_list

        for item in reversed(sale_items):
            data_id = item['data-id']
            if last_processed_ad and int(data_id) <= int(last_processed_ad):
                logger.debug(f"Объявление {data_id} уже было обработано.")
                continue

            title_link = item.find('a', class_='sale-link')
            title = title_link.text.strip()
            item_url = 'https://autokochka.ru' + title_link['href']
            chassis_info = item.find('div', class_='sale-chassis').text.strip()
            city = item.find('div', class_='sale-city').text.strip()
            price = item.find('div', class_='sale-price').text.strip()
            phone_number = get_phone_number(data_id)

            logger.debug(f"Найдено новое объявление: {title} с ID {data_id} и телефоном {phone_number}")

            ads_list.append({
                'data_id': data_id,
                'title': title,
                'item_url': item_url,
                'chassis_info': chassis_info,
                'price': price,
                'city': city,
                'phone_number': phone_number,
            })

        if ads_list:
            logger.info(f"Найдено {len(ads_list)} новых объявлений.")
            save_last_processed_ad(ads_list[-1]['data_id'])
        else:
            logger.info("Новых объявлений не найдено.")
    else:
        logger.error(f"Ошибка при получении страницы {url} с кодом ответа HTTP {response.status_code}")

    return ads_list

