import os
import requests
from ad_list_parser import parse_ads_list
from ad_details_parser import get_ad_details
from photo_processor import download_and_save_images, recognize_number_plates, cleanup_temp_images, \
    find_most_common_number
from db_worker import add_advertisement
import json
from logger import setup_logger
import time

logger = setup_logger(__name__)


def save_failed_ads(failed_ads):
    filename = 'volume/failed_ads.json'
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            try:
                existing_ads = json.load(f)
            except json.JSONDecodeError:
                existing_ads = []
    else:
        existing_ads = []

    updated_ads = list(set(existing_ads + failed_ads))

    with open(filename, 'w') as f:
        json.dump(updated_ads, f, indent=4, sort_keys=True)
    logger.info("Обновлённый список URL необработанных объявлений сохранен в файле failed_ads.json.")


def notify_bot_about_new_ad(ad_detail):
    url = 'http://localhost:8000/notify/'
    data = {
        'title': ad_detail['title'],
        'price': ad_detail['price'],
        'ad_link': ad_detail['ad_link'],
        'drive': ad_detail['additional_info'].get('Привод', ''),
        'city': ad_detail['additional_info'].get('Город', ''),
        'year': ad_detail['additional_info'].get('Год', ''),
        'phone_number': ad_detail.get('phone_number', 'Ещё не определён')
    }
    response = requests.post(url, json=data)
    if response.status_code == 200:
        print("Уведомление успешно отправлено")
    else:
        print(f"Ошибка при отправке уведомления: {response.status_code}, {response.text}")


def main_process():
    logger.info("Начало работы функции main_process.")
    ads_list = parse_ads_list()
    # for ad in ads_list:
    #     chassis_parts = ad['chassis_info'].split(", ")
    #     drive_type = "Нет данных"
    #     if len(chassis_parts) >= 2:
    #         drive_type_raw = chassis_parts[1]
    #         drive_type = drive_type_raw.split()[0].capitalize()
    #
    #     title_parts = ad['title'].split(", ")
    #     year = "Нет данных"
    #     if len(title_parts) > 1 and title_parts[-1].strip().isdigit() and len(title_parts[-1].strip()) == 4:
    #         year = title_parts[-1].strip()
    #         title_without_year = ", ".join(title_parts[:-1]).strip()
    #     else:
    #         title_without_year = ad['title']
    #
    #     ad_detail = {
    #         "title": title_without_year,
    #         "ad_link": ad["item_url"],
    #         "additional_info": {
    #             "Привод": drive_type,
    #             "Город": ad["city"],
    #             "Год": year,
    #         },
    #         "price": ad['price'],
    #         "phone_number": ad.get('phone_number', 'Ещё не определён')
    #     }
    #
    #     # notify_bot_about_new_ad(ad_detail)
    if not ads_list:
        logger.info("Новых объявлений для обработки не найдено. Процесс завершён.")
        return

    failed_ads = []

    for ad in ads_list:
        title_parts = ad['title'].split(", ")
        if len(title_parts) > 1 and title_parts[-1].strip().isdigit() and len(title_parts[-1].strip()) == 4:
            title_without_year = ", ".join(title_parts[:-1]).strip()
        else:
            title_without_year = ad['title']

        logger.info(f"Обработка объявления: {title_without_year} с URL: {ad['item_url']}")

        ad_detail = get_ad_details(ad['item_url'])
        ad_detail['title'] = title_without_year
        ad_detail['ad_id'] = ad['data_id']
        ad_detail['phone_number'] = ad['phone_number']
        ad_detail['price'] = ad['price']
        if not ad_detail['image_urls']:
            logger.warning(f"Изображения не найдены для объявления: {ad['item_url']}. Попытка повторного запроса "
                           f"через 120 cекунд.")
            time.sleep(120)
            ad_detail = get_ad_details(ad['item_url'])
            ad_detail['title'] = title_without_year
            ad_detail['ad_id'] = ad['data_id']
            logger.debug(f"ad_detail['ad_id'] = {ad_detail['ad_id'] } - ad['data_id'] = {ad['data_id']}")
            ad_detail['phone_number'] = ad['phone_number']
            ad_detail['price'] = ad['price']
            logger.warning(f"Повторная попытка добавления объявления: {ad_detail}")
            if not ad_detail['image_urls']:
                logger.warning(f"Изображения по-прежнему не найдены для объявления: {ad['item_url']}. Объявление "
                               f"будет помечено как неудачное.")
                failed_ads.append(ad['data_id'])
                continue

        temp_images_paths = download_and_save_images(ad_detail['image_urls'])
        recognized_texts = recognize_number_plates(temp_images_paths)

        if not any(recognized_texts):
            logger.warning(
                f"Номера не распознаны для объявления: {ad['item_url']}. Объявление будет помечено как неудачное.")
            failed_ads.append(ad['data_id'])

        else:
            most_common_number = find_most_common_number(recognized_texts)
            if most_common_number:
                ad_detail.update({
                    'car_number': most_common_number,
                    'phone_number': ad_detail.get('phone_number', '')
                })
                try:
                    logger.info(f"Добавление объявления в базу данных: {ad_detail}")
                    if add_advertisement(ad_detail):
                        logger.info(f"Объявление {title_without_year} успешно добавлено в базу данных.")
                    else:
                        logger.info(f"Объявление {title_without_year} c {ad['ad_id']} уже существует в базе данных.")
                except Exception as e:
                    logger.error(f"Ошибка при добавлении объявления в базу данных: {e}")
            else:
                logger.warning(
                    f"Не удалось идентифицировать наиболее часто встречающийся номер для объявления: {ad['item_url']}.")
                failed_ads.append(ad['data_id'])

        cleanup_temp_images(temp_images_paths)

    if failed_ads:
        save_failed_ads(failed_ads)
    logger.info("Завершение работы функции main_process.")


if __name__ == "__main__":
    main_process()
