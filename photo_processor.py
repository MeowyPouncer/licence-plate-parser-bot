import re
from collections import Counter, defaultdict
import tempfile
from logger import setup_logger
from nomeroff_net import pipeline
from nomeroff_net.tools import unzip
import requests
from PIL import Image
import io
import os

logger = setup_logger(__name__)


def is_valid_russian_plate(number):
    pattern = re.compile(r'^[АВЕКМНОРСТУХABEKMHOPCTYX]\d{3}[АВЕКМНОРСТУХABEKMHOPCTYX]{2}\d{2,3}$')
    if bool(pattern.match(number)):
        logger.debug(f"Номер {number} валиден.")
        return True
    else:
        logger.debug(f"Номер {number} невалиден.")
        return False


def translate_to_cyrillic(letter):
    transliteration_dict = {
        'A': 'А', 'B': 'В', 'E': 'Е', 'K': 'К', 'M': 'М',
        'H': 'Н', 'O': 'О', 'P': 'Р', 'C': 'С', 'T': 'Т',
        'Y': 'У', 'X': 'Х'
    }
    return transliteration_dict.get(letter, letter)


def convert_number_to_cyrillic(number):
    return ''.join(translate_to_cyrillic(letter) for letter in number)


def calculate_similarity(numbers):
    similarity_scores = []
    for i, number_i in enumerate(numbers):
        score = 0
        for j, number_j in enumerate(numbers):
            if i != j:
                score += sum(1 for a, b in zip(number_i, number_j) if a == b)
        similarity_scores.append(score)
    return similarity_scores

def filter_outliers(numbers, similarity_scores):
    average_score = sum(similarity_scores) / len(similarity_scores)
    return [number for number, score in zip(numbers, similarity_scores) if score >= average_score * 0.5]

def aggregate_symbol_statistics(recognized_numbers):
    symbol_stats = defaultdict(lambda: Counter())
    for number in recognized_numbers:
        for position, symbol in enumerate(number):
            symbol_stats[position][symbol] += 1
    return symbol_stats


def find_most_common_number(recognized_texts):
    recognized_numbers = [num for sublist in recognized_texts for num in sublist if num and is_valid_russian_plate(num)]

    if not recognized_numbers:
        return None

    similarity_scores = calculate_similarity(recognized_numbers)
    recognized_numbers = filter_outliers(recognized_numbers, similarity_scores)

    symbol_stats = aggregate_symbol_statistics(recognized_numbers)

    most_common_number = ""
    for position in sorted(symbol_stats.keys()):
        most_common_symbol, _ = symbol_stats[position].most_common(1)[0]
        most_common_number += most_common_symbol

    return convert_number_to_cyrillic(most_common_number)


def download_and_save_images(image_urls):
    temp_images_paths = []
    for url in image_urls:
        try:
            response = requests.get(url)
            if response.status_code == 200:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
                    image = Image.open(io.BytesIO(response.content))
                    image.save(tmp.name, "PNG")
                    temp_images_paths.append(tmp.name)
                    logger.debug(f"Изображение сохранено: {tmp.name}")
            else:
                logger.error(f"Ошибка HTTP {response.status_code} при скачивании изображения {url}.")
        except Exception as e:
            logger.error(f"Ошибка при скачивании или сохранении изображения {url}: {e}")
    return temp_images_paths


def recognize_number_plates(image_paths):
    if not image_paths:
        logger.info("Список путей к изображениям пуст.")
        return []
    try:
        number_plate_detection_and_reading = pipeline("number_plate_detection_and_reading", image_loader="opencv")
        _, _, _, _, _, _, _, _, texts = unzip(number_plate_detection_and_reading(image_paths))
        logger.debug(f"Распознанные номера: {texts}")
        return texts
    except Exception as e:
        logger.error(f"Ошибка при распознавании номеров: {e}")
        return []


def cleanup_temp_images(image_paths):
    for path in image_paths:
        try:
            os.remove(path)
            logger.debug(f"Временное изображение удалено: {path}")
        except Exception as e:
            logger.error(f"Ошибка при удалении изображения {path}: {e}")
