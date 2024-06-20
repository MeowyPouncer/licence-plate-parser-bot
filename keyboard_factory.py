from telebot.types import ReplyKeyboardMarkup, KeyboardButton


class KeyboardFactory:
    @staticmethod
    def main_keyboard(is_admin=False):
        markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.add(KeyboardButton('Поиск по номеру'))
        if is_admin:
            markup.add(KeyboardButton('Управлять списками'))
        return markup

    @staticmethod
    def return_keyboard():
        markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.add(KeyboardButton("Вернуться в главное меню"))
        return markup

    @staticmethod
    def manage_lists_keyboard():
        markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.add(KeyboardButton('Просмотреть разрешённых пользователей'))
        markup.add(KeyboardButton('Просмотреть подписанных пользователей'))
        markup.add(KeyboardButton('Вернуться в главное меню'))
        return markup

    @staticmethod
    def users_keyboard():
        markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.row(KeyboardButton('Добавить'), KeyboardButton('Удалить'))
        markup.row(KeyboardButton('Вернуться в главное меню'))
        return markup

    @staticmethod
    def cancel_button():
        markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.add(KeyboardButton("Отменить действие"))
        return markup

    @staticmethod
    def decision_keyboard():
        markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.row(KeyboardButton("Да, удалить"), KeyboardButton("Отменить удаление"))
        return markup

    @staticmethod
    def choice_list_keyboard():
        markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.add(KeyboardButton("Разрешенные пользователи"))
        markup.add(KeyboardButton("Подписанные пользователи"))
        return markup
