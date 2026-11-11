from telebot.types import ReplyKeyboardMarkup, KeyboardButton


class Keyboards:
    @staticmethod
    def get_students_keyboard(students_list):
        """Генерирует клавиатуру со списком всех учащихся."""
        markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        buttons = [KeyboardButton(student) for student in students_list]
        markup.add(*buttons)

        # Кнопки для скачивания файлов теперь доступны всем
        markup.add(KeyboardButton("📥 Скачать Оценки"), KeyboardButton("📥 Скачать Пропуски"))

        return markup

    @staticmethod
    def get_months_keyboard(months_list):
        """Генерирует клавиатуру с доступными месяцами из БД."""
        markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        buttons = [KeyboardButton(month) for month in months_list]
        markup.add(*buttons)
        markup.add(KeyboardButton("⬅️ Назад к списку"))
        return markup

    @staticmethod
    def get_back_keyboard():
        """Генерирует клавиатуру для возврата из отчета."""
        markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        markup.add(KeyboardButton("⬅️ Назад к месяцам"), KeyboardButton("🏠 В главное меню"))
        return markup