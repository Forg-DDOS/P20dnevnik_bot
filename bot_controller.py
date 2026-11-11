import telebot
import os
from keyboards import Keyboards
from db_handler import ExcelDatabase
from config import BOT_TOKEN, TEACHER_IDS


class BotController:
    def __init__(self):
        self.bot = telebot.TeleBot(BOT_TOKEN)
        self.db = ExcelDatabase()
        self.user_states = {}
        self.register_handlers()

    def _find_student(self, text):
        if not text:
            return None
        text_lower = text.lower().strip()

        # Добавили новые слова в игнор-лист, чтобы поиск ученика на них не реагировал
        ignore_list = [
            "⬅️ назад к списку", "🏠 в главное меню", "⬅️ назад к месяцам",
            "📥 скачать оценки", "📥 скачать пропуски",
            "оценки", "пропуски", "скачать оценки", "скачать пропуски"
        ]

        months = [m.lower() for m in self.db.get_available_months()]
        if text_lower in ignore_list or text_lower in months:
            return None

        students = self.db.get_all_students()
        for student in students:
            if text_lower == student.lower():
                return student
        for student in students:
            if text_lower in student.lower():
                return student
        return None

    def register_handlers(self):
        @self.bot.message_handler(commands=['start'])
        def send_welcome(message):
            students = self.db.get_all_students()
            if not students:
                self.bot.send_message(message.chat.id, "База данных пуста. Добавьте файлы в папку DataBase.")
                return

            self.bot.send_message(
                message.chat.id,
                "Добро пожаловать в систему учета группы П-20!\nВыберите учащегося на клавиатуре или напишите его фамилию в чат:",
                reply_markup=Keyboards.get_students_keyboard(students)
            )

        @self.bot.message_handler(func=lambda msg: msg.text in ["⬅️ Назад к списку", "🏠 В главное меню"])
        def back_to_start(message):
            if message.from_user.id in self.user_states:
                del self.user_states[message.from_user.id]
            students = self.db.get_all_students()
            self.bot.send_message(
                message.chat.id, "Главное меню.\nВыберите учащегося или введите фамилию:",
                reply_markup=Keyboards.get_students_keyboard(students)
            )

        @self.bot.message_handler(func=lambda msg: msg.text == "⬅️ Назад к месяцам")
        def back_to_months(message):
            user_id = message.from_user.id
            if user_id in self.user_states:
                months = self.db.get_available_months()
                self.bot.send_message(
                    message.chat.id, "Выберите месяц:",
                    reply_markup=Keyboards.get_months_keyboard(months)
                )
            else:
                back_to_start(message)

        # --- ОБНОВЛЕНО: Бот реагирует на кнопки и на простой текст (оценки, пропуски) ---
        @self.bot.message_handler(func=lambda msg: msg.text and msg.text.lower().strip() in [
            "оценки", "пропуски", "скачать оценки", "скачать пропуски",
            "📥 скачать оценки", "📥 скачать пропуски"
        ])
        def request_download(message):
            user_id = message.from_user.id
            text = message.text.lower()

            # Определяем, какой файл нужен, по наличию слова
            action = 'download_grades' if "оценки" in text else 'download_absences'
            self.user_states[user_id] = {'action': action, 'data': None}

            months = self.db.get_available_months()
            doc_type = "Оценки" if action == 'download_grades' else "Пропуски"

            self.bot.send_message(
                message.chat.id,
                f"Подготовка файла: **{doc_type}**\nВыберите месяц:",
                reply_markup=Keyboards.get_months_keyboard(months),
                parse_mode="Markdown"
            )

        @self.bot.message_handler(func=lambda msg: msg.text in self.db.get_available_months())
        def process_month_selection(message):
            user_id = message.from_user.id
            if user_id not in self.user_states:
                self.bot.send_message(message.chat.id, "Сначала выберите учащегося или действие!")
                return

            state = self.user_states[user_id]
            month = message.text

            if not isinstance(state, dict):
                action = 'report'
                data = state
            else:
                action = state['action']
                data = state['data']

            if action == 'download_grades':
                file_path = os.path.join(self.db.db_path, month, 'Оценки.xlsx')
                if os.path.exists(file_path):
                    with open(file_path, 'rb') as f:
                        self.bot.send_document(message.chat.id, f, caption=f"Оценки за {month}")
                else:
                    self.bot.send_message(message.chat.id, f"Файл Оценки.xlsx за {month} не найден.")
                return

            elif action == 'download_absences':
                file_path = os.path.join(self.db.db_path, month, 'Пропуски.xlsx')
                if os.path.exists(file_path):
                    with open(file_path, 'rb') as f:
                        self.bot.send_document(message.chat.id, f, caption=f"Пропуски за {month}")
                else:
                    self.bot.send_message(message.chat.id, f"Файл Пропуски.xlsx за {month} не найден.")
                return

            elif action == 'report':
                student_name = data
                absences = self.db.get_student_absences(student_name, month)
                grades_str, avg_grade, subject_grades = self.db.get_student_grades(student_name, month)

                if subject_grades:
                    subjects_text = "\n".join([f"• {subj}: {grade}" for subj, grade in subject_grades.items()])
                else:
                    subjects_text = "Нет данных по предметам"

                if user_id in TEACHER_IDS:
                    contacts = self.db.get_student_contacts(student_name)
                    contacts_text = f"\n\n📞 **Контакты (только для преподавателя):**\n{contacts}"
                else:
                    contacts_text = ""

                report = (
                    f"📄 **Отчет по успеваемости**\n"
                    f"Учащийся: {student_name}\n"
                    f"Месяц: {month}\n\n"
                    f"📊 **Общие показатели:**\n"
                    f"Все оценки: {grades_str}\n"
                    f"Средний балл: {avg_grade}\n"
                    f"Пропуски: {absences}\n\n"
                    f"📚 **Оценки по предметам:**\n{subjects_text}"
                    f"{contacts_text}"
                )

                self.bot.send_message(
                    message.chat.id, report,
                    reply_markup=Keyboards.get_back_keyboard(),
                    parse_mode="Markdown"
                )

        @self.bot.message_handler(func=lambda msg: self._find_student(msg.text) is not None)
        def select_month_for_student(message):
            matched_student = self._find_student(message.text)
            self.user_states[message.from_user.id] = {'action': 'report', 'data': matched_student}
            months = self.db.get_available_months()
            self.bot.send_message(
                message.chat.id,
                f"Учащийся: {matched_student}\nВыберите месяц:",
                reply_markup=Keyboards.get_months_keyboard(months)
            )

        @self.bot.message_handler(func=lambda msg: True)
        def unknown_command(message):
            self.bot.send_message(message.chat.id,
                                  "Я не нашел такого учащегося в базе или не понял команду. Попробуйте еще раз или выберите из списка.")

    def run(self):
        print("Бот успешно запущен!")
        self.bot.infinity_polling(timeout=10, long_polling_timeout=5)