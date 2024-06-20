from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.service import Service

import time
import re

from logger import setup_logger

logger = setup_logger(__name__)


def normalize_phone_number(phone_number):
    digits = re.sub(r'\D', '', phone_number)
    if len(digits) == 11 and digits.startswith('8'):
        digits = '7' + digits[1:]
    elif len(digits) == 10:
        digits = '7' + digits
    normalized = f"+7-{digits[1:4]}-{digits[4:7]}-{digits[7:9]}-{digits[9:]}"
    return normalized


def get_ad_details(item_url):
    logger.info(f"Начало извлечения данных для объявления: {item_url}")
    chrome_options = Options()

    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--remote-debugging-port=9222")

    service = Service()
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.get(item_url)
    logger.debug("WebDriver загрузил страницу")

    ad_details = {
        'image_urls': [],
        'phone_number': '',
        'additional_info': {},
        'ad_link': item_url,
        'ad_id': item_url.split("/")[-1],
    }

    try:
        try:
            expand_photos_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CLASS_NAME, "js-photo-expand"))
            )
            expand_photos_button.click()
            logger.info("Изображения успешно раскрыты")
            time.sleep(5)
        except TimeoutException:
            logger.warning("Кнопка раскрытия изображений не найдена, извлекаем доступные изображения")

        photo_elements = driver.find_elements(By.CSS_SELECTOR,
                                              '.photo-gallery__item.js-photo-main, .photo-gallery__item.js-photo-slave')
        if len(photo_elements) > 1:
            photo_elements = photo_elements[1:]
        ad_details['image_urls'] = [photo.get_attribute('src').replace('md', 'xl') for photo in photo_elements]
        logger.info(f"Извлечено {len(ad_details['image_urls'])} изображений после удаления возможного дубликата")

        properties = driver.find_elements(By.CSS_SELECTOR, '.sale-properties .sale-property')
        for prop in properties:
            name = prop.find_element(By.CSS_SELECTOR, '.sale-property-name').text.replace(':', '').strip()
            value = prop.find_element(By.CSS_SELECTOR, '.sale-property-value').text.strip()
            ad_details['additional_info'][name] = value
        logger.info("Детали объявления успешно извлечены")

    except Exception as e:
        logger.error(f"Ошибка при извлечении данных объявления: {e}")
    finally:
        driver.quit()
        logger.debug("WebDriver закрыт")

    return ad_details
