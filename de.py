import numpy as np
import tensorflow as tf

# Загрузка предварительно обученной модели MobileNetV2
model = tf.keras.applications.MobileNetV2(weights='imagenet', include_top=True)

# Загрузка и предобработка изображения
image = tf.keras.preprocessing.image.load_img('data/dataset/TextDetector/ocr_example/test/img/1000_X371HK96_0.png', target_size=(224, 224))
input_array = tf.keras.preprocessing.image.img_to_array(image)
input_array = np.array([input_array])  # Преобразование в батч
input_array = tf.keras.applications.mobilenet_v2.preprocess_input(input_array)

# Предсказание
predictions = model.predict(input_array)

# Декодирование предсказаний
decoded_predictions = tf.keras.applications.mobilenet_v2.decode_predictions(predictions, top=1)[0]
print(decoded_predictions)
