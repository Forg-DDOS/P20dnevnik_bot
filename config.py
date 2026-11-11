# config.py
import os

BOT_TOKEN = '8905456250:AAGhZJZ8hWqm86wCPI3HRijn5fcekCNWfQA'

# Добавьте сюда Telegram ID преподавателей (числа без кавычек, через запятую)
TEACHER_IDS = [1744983088]

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'DataBase')