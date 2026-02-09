import os
from dotenv import load_dotenv

# Загружаем переменные из .env файла
load_dotenv()

# Получаем токен из переменных окружения
TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise ValueError("❌ Токен бота не найден! Убедитесь, что создали файл .env с BOT_TOKEN")