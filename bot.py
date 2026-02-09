import asyncio
import logging
from datetime import datetime

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

from config import TOKEN
from db_handler import db
from states import TaskStates
from Keyboards import (
    main_menu_keyboard,
    task_actions_keyboard,
    priority_keyboard,
    repeat_keyboard,
    edit_choice_keyboard,
    cancel_keyboard,
    categories_keyboard,
    back_to_menu_keyboard,
    filter_keyboard,
    deadline_keyboard
)
from reminders import reminder_loop

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("bot.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Инициализация бота и диспетчера
bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# ==================== КОМАНДЫ ====================

@dp.message(CommandStart())
async def command_start(message: Message):
    """Обработка команды /start"""
    welcome_text = (
        "👋 <b>Привет! Я ваш персональный To-Do бот!</b>\n\n"
        "Я помогу вам управлять задачами с:\n"
        "• 📝 Текстом задач\n"
        "• ⏰ Дедлайнами\n"
        "• 🏷️ Категориями\n"
        "• ⚡ Приоритетами\n"
        "• 🔄 Повторениями\n"
        "• 📊 Статистикой\n\n"
        "Используйте кнопки ниже для навигации:"
    )
    
    await message.answer(welcome_text, reply_markup=main_menu_keyboard())
    logger.info(f"🆕 Новый пользователь: {message.from_user.id}")

@dp.message(Command("help"))
async def command_help(message: Message):
    """Обработка команды /help"""
    help_text = (
        "📚 <b>Справка по командам:</b>\n\n"
        "<b>Основные команды:</b>\n"
        "/start - Перезапустить бота\n"
        "/help - Эта справка\n"
        "/stats - Статистика задач\n"
        "/search <текст> - Поиск задач\n\n"
        
        "<b>Управление задачами:</b>\n"
        "• Используйте кнопку '➕ Создать задачу' для добавления\n"
        "• В '📋 Мои задачи' просматривайте и управляйте задачами\n"
        "• Каждой задаче можно: ✅ Выполнить, ✏️ Редактировать, ❌ Удалить\n\n"
        
        "<b>Формат дедлайна:</b>\n"
        "ГГГГ-ММ-ДД ЧЧ:ММ\n"
        "Например: 2024-12-31 23:59\n\n"
        
        "<b>Напоминания:</b>\n"
        "Я автоматически напомню о дедлайнах за 1 час и при наступлении срока."
    )
    
    await message.answer(help_text, reply_markup=main_menu_keyboard())

@dp.message(Command("stats"))
async def command_stats(message: Message):
    """Обработка команды /stats"""
    await show_stats(message)

@dp.message(Command("search"))
async def command_search(message: Message, state: FSMContext):
    """Обработка команды /search"""
    args = message.text.split(maxsplit=1)
    
    if len(args) > 1:
        keyword = args[1]
        await search_tasks_action(message, keyword)
    else:
        await message.answer(
            "🔍 <b>Поиск задач</b>\n\n"
            "Введите ключевое слово для поиска:",
            reply_markup=cancel_keyboard()
        )
        await state.set_state(TaskStates.waiting_for_search)

# ==================== ГЛАВНОЕ МЕНЮ ====================

@dp.message(F.text == "🏠 Главное меню")
async def main_menu(message: Message, state: FSMContext):
    """Возврат в главное меню"""
    await state.clear()
    await message.answer(
        "Вы в главном меню 👇",
        reply_markup=main_menu_keyboard()
    )

# ==================== СОЗДАНИЕ ЗАДАЧИ ====================

@dp.message(F.text == "➕ Создать задачу")
async def add_task_start(message: Message, state: FSMContext):
    """Начало создания задачи"""
    await message.answer(
        "📝 <b>Создание новой задачи</b>\n\n"
        "Напишите текст задачи:",
        reply_markup=cancel_keyboard()
    )
    await state.set_state(TaskStates.waiting_for_task)

@dp.message(TaskStates.waiting_for_task)
async def process_task_text(message: Message, state: FSMContext):
    """Обработка текста задачи"""
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("❌ Создание задачи отменено", reply_markup=main_menu_keyboard())
        return
    
    await state.update_data(text=message.text)
    
    await message.answer(
        "⏰ <b>Установка дедлайна</b>\n\n"
        "Введите дату и время в формате:\n"
        "<code>ГГГГ-ММ-ДД ЧЧ:ММ</code>\n\n"
        "Пример: <code>2024-12-31 23:59</code>\n"
        "Или нажмите кнопку ниже:",
        reply_markup=deadline_keyboard()  # <-- Используем новую клавиатуру
    )
    await state.set_state(TaskStates.waiting_for_deadline)

@dp.message(TaskStates.waiting_for_deadline)
async def process_deadline(message: Message, state: FSMContext):
    """Обработка дедлайна"""
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("❌ Создание задачи отменено", reply_markup=main_menu_keyboard())
        return
    
    deadline = None
    
    if message.text == "❌ Без дедлайна":
        # Пользователь выбрал "без дедлайна"
        deadline = None
    else:
        # Пользователь ввел дату вручную
        try:
            dt = datetime.strptime(message.text.strip(), "%Y-%m-%d %H:%M")
            deadline = dt.isoformat()
            
            # Проверка на прошедшую дату
            if dt < datetime.now():
                await message.answer(
                    "⚠️ Вы указали прошедшую дату.\n"
                    "Всё равно использовать её?",
                    reply_markup=cancel_keyboard()
                )
                await state.update_data(deadline=deadline)
                return
                
        except ValueError:
            await message.answer(
                "❌ <b>Неверный формат!</b>\n\n"
                "Введите дату в формате:\n"
                "<code>ГГГГ-ММ-ДД ЧЧ:ММ</code>\n"
                "Пример: <code>2024-12-31 23:59</code>\n"
                "Или нажмите '❌ Без дедлайна'",
                reply_markup=deadline_keyboard()
            )
            return
    
    await state.update_data(deadline=deadline)
    
    # Получаем категории пользователя
    categories = db.get_user_categories(message.from_user.id)
    
    if categories:
        await message.answer(
            "🏷️ <b>Выберите категорию</b>\n\n"
            "Выберите из существующих или создайте новую:",
            reply_markup=categories_keyboard(categories)
        )
    else:
        await message.answer(
            "🏷️ <b>Укажите категорию</b>\n\n"
            "Напишите название категории (например: Работа, Учеба, Личное):",
            reply_markup=cancel_keyboard()
        )
    
    await state.set_state(TaskStates.waiting_for_category)

@dp.message(TaskStates.waiting_for_category)
async def process_category(message: Message, state: FSMContext):
    """Обработка категории"""
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("❌ Создание задачи отменено", reply_markup=main_menu_keyboard())
        return
    
    category = None
    if message.text != "❌ Без категории" and message.text != "➕ Новая категория":
        category = message.text.strip()
    
    await state.update_data(category=category)
    
    await message.answer(
        "⚡ <b>Выберите приоритет</b>",
        reply_markup=priority_keyboard()
    )
    await state.set_state(TaskStates.waiting_for_priority)

@dp.message(TaskStates.waiting_for_priority)
async def process_priority(message: Message, state: FSMContext):
    """Обработка приоритета"""
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("❌ Создание задачи отменено", reply_markup=main_menu_keyboard())
        return
    
    priority_map = {
        "Высокий 🔴": "Высокий",
        "Средний 🟡": "Средний",
        "Низкий 🟢": "Низкий",
        "❌ Без приоритета": None
    }
    
    priority = priority_map.get(message.text, message.text)
    await state.update_data(priority=priority)
    
    await message.answer(
        "🔄 <b>Повторение задачи</b>\n\n"
        "Выберите как часто повторять задачу:",
        reply_markup=repeat_keyboard()
    )
    await state.set_state(TaskStates.waiting_for_repeat)

@dp.message(TaskStates.waiting_for_repeat)
async def process_repeat_and_save(message: Message, state: FSMContext):
    """Обработка повторения и сохранение задачи"""
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("❌ Создание задачи отменено", reply_markup=main_menu_keyboard())
        return
    
    data = await state.get_data()
    
    # Сохраняем задачу в базу данных
    task_id = db.add_task(
        user_id=message.from_user.id,
        text=data["text"],
        deadline=data.get("deadline"),
        category=data.get("category"),
        priority=data.get("priority"),
        repeat=message.text.strip()
    )
    
    if task_id:
        # Формируем сообщение о созданной задаче
        task_info = f"📝 <b>Задача создана!</b>\n\n"
        task_info += f"<b>Текст:</b> {data['text']}\n"
        
        if data.get("deadline"):
            deadline_dt = datetime.fromisoformat(data["deadline"])
            task_info += f"<b>Дедлайн:</b> {deadline_dt.strftime('%d.%m.%Y %H:%M')}\n"
        
        if data.get("category"):
            task_info += f"<b>Категория:</b> {data['category']}\n"
        
        if data.get("priority"):
            task_info += f"<b>Приоритет:</b> {data['priority']}\n"
        
        task_info += f"<b>Повторение:</b> {message.text.strip()}\n\n"
        task_info += f"<i>ID задачи: {task_id}</i>"
        
        await message.answer(task_info, reply_markup=main_menu_keyboard())
    else:
        await message.answer(
            "❌ <b>Ошибка при создании задачи!</b>\n\n"
            "Попробуйте ещё раз.",
            reply_markup=main_menu_keyboard()
        )
    
    await state.clear()

# ==================== ПОКАЗ ЗАДАЧ ====================

@dp.message(F.text == "📋 Мои задачи")
async def show_tasks_menu(message: Message):
    """Показ меню задач"""
    await message.answer(
        "📋 <b>Ваши задачи</b>\n\n"
        "Выберите фильтр:",
        reply_markup=filter_keyboard()
    )

@dp.message(F.text == "📋 Все задачи")
async def show_all_tasks(message: Message):
    """Показ всех задач"""
    user_id = message.from_user.id
    logger.info(f"📋 Запрошены задачи для пользователя {user_id}")
    
    tasks = db.get_tasks(user_id, show_completed=True)
    logger.info(f"📋 Получено задач из БД: {len(tasks)}")
    
    for task in tasks:
        logger.info(f"Задача: ID={task['id']}, текст={task['text']}, выполнена={task['done']}")
    
    await display_tasks(message, tasks, "Все задачи")

@dp.message(F.text == "✅ Выполненные")
async def show_completed_tasks(message: Message):
    """Показ выполненных задач"""
    # Для простоты покажем все задачи и отфильтруем на стороне Python
    tasks = db.get_tasks(message.from_user.id, show_completed=True)
    completed_tasks = [task for task in tasks if task['done'] == 1]
    await display_tasks(message, completed_tasks, "Выполненные задачи")

@dp.message(F.text == "❌ Невыполненные")
async def show_incomplete_tasks(message: Message):
    """Показ невыполненных задач"""
    tasks = db.get_tasks(message.from_user.id, show_completed=False)
    await display_tasks(message, tasks, "Невыполненные задачи")

@dp.message(F.text == "🔴 Высокий приоритет")
async def show_high_priority_tasks(message: Message):
    """Показ задач с высоким приоритетом"""
    tasks = db.get_tasks(message.from_user.id, show_completed=False)
    high_tasks = [task for task in tasks if task['priority'] == 'Высокий']
    await display_tasks(message, high_tasks, "Задачи с высоким приоритетом")

@dp.message(F.text == "⏰ С дедлайном")
async def show_tasks_with_deadline(message: Message):
    """Показ задач с дедлайном"""
    tasks = db.get_tasks(message.from_user.id, show_completed=False)
    tasks_with_deadline = [task for task in tasks if task['deadline']]
    await display_tasks(message, tasks_with_deadline, "Задачи с дедлайном")

async def display_tasks(message: Message, tasks, title):
    """Отображение списка задач"""
    logger.info(f"📋 Отображение задач: {title}, количество: {len(tasks)}")
    
    if not tasks:
        await message.answer(
            f"📭 <b>{title}</b>\n\n"
            "Задач не найдено.",
            reply_markup=main_menu_keyboard()
        )
        return
    
    await message.answer(
        f"📋 <b>{title}</b>\n\n"
        f"Найдено задач: {len(tasks)}",
        reply_markup=main_menu_keyboard()
    )
    
    for task in tasks:
        logger.info(f"Отображаю задачу: {task['id']} - {task['text']}")
        status = "✅" if task['done'] == 1 else "❌"
        priority_icon = ""
        
        if task['priority'] == 'Высокий':
            priority_icon = "🔴"
        elif task['priority'] == 'Средний':
            priority_icon = "🟡"
        elif task['priority'] == 'Низкий':
            priority_icon = "🟢"
        
        task_text = f"{status} {priority_icon} <b>{task['text']}</b>\n"
        
        if task['deadline']:
            try:
                deadline_dt = datetime.fromisoformat(task['deadline'])
                task_text += f"⏰ {deadline_dt.strftime('%d.%m.%Y %H:%M')}\n"
            except:
                task_text += f"⏰ {task['deadline']}\n"
        
        if task['category']:
            task_text += f"🏷️ {task['category']}\n"
        
        if task['repeat'] and task['repeat'] != 'Нет':
            task_text += f"🔄 {task['repeat']}\n"
        
        task_text += f"<i>ID: {task['id']}</i>"
        
        await message.answer(
            task_text,
            reply_markup=task_actions_keyboard(task['id'])
        )

# ==================== CALLBACK ОБРАБОТЧИКИ ====================

@dp.callback_query(F.data.startswith("done_"))
async def callback_done_task(callback: CallbackQuery):
    """Обработка отметки задачи как выполненной"""
    task_id = int(callback.data.split("_")[1])
    
    if db.mark_done(task_id):
        await callback.message.answer("✅ Задача отмечена как выполненная")
        await callback.answer("Задача выполнена!")
    else:
        await callback.answer("❌ Ошибка при обновлении задачи", show_alert=True)

@dp.callback_query(F.data.startswith("delete_"))
async def callback_delete_task(callback: CallbackQuery):
    """Обработка удаления задачи"""
    task_id = int(callback.data.split("_")[1])
    
    # Получаем задачу для подтверждения
    task = db.get_task(task_id)
    
    if task and task['user_id'] == callback.from_user.id:
        # Создаем клавиатуру подтверждения
        confirm_kb = InlineKeyboardBuilder()
        confirm_kb.button(text="✅ Да, удалить", callback_data=f"confirm_delete_{task_id}")
        confirm_kb.button(text="❌ Нет, отменить", callback_data="cancel_delete")
        
        await callback.message.answer(
            f"❌ <b>Подтвердите удаление</b>\n\n"
            f"Задача: {task['text']}\n\n"
            "Вы уверены, что хотите удалить эту задачу?",
            reply_markup=confirm_kb.as_markup()
        )
        await callback.answer()
    else:
        await callback.answer("❌ Задача не найдена", show_alert=True)

@dp.callback_query(F.data.startswith("confirm_delete_"))
async def callback_confirm_delete(callback: CallbackQuery):
    """Подтверждение удаления задачи"""
    task_id = int(callback.data.split("_")[2])
    
    if db.delete_task(task_id):
        await callback.message.answer("❌ Задача удалена")
        await callback.answer("Задача удалена!")
    else:
        await callback.answer("❌ Ошибка при удалении задачи", show_alert=True)

@dp.callback_query(F.data == "cancel_delete")
async def callback_cancel_delete(callback: CallbackQuery):
    """Отмена удаления задачи"""
    await callback.message.answer("✅ Удаление отменено")
    await callback.answer()

@dp.callback_query(F.data.startswith("edit_"))
async def callback_edit_task(callback: CallbackQuery, state: FSMContext):
    """Начало редактирования задачи"""
    task_id = int(callback.data.split("_")[1])
    
    # Сохраняем ID задачи в состоянии
    await state.update_data(edit_task_id=task_id)
    
    await callback.message.answer(
        "✏️ <b>Редактирование задачи</b>\n\n"
        "Что вы хотите изменить?",
        reply_markup=edit_choice_keyboard()
    )
    
    await state.set_state(TaskStates.waiting_for_edit_choice)
    await callback.answer()

# ==================== РЕДАКТИРОВАНИЕ ЗАДАЧ ====================

@dp.message(TaskStates.waiting_for_edit_choice)
async def process_edit_choice(message: Message, state: FSMContext):
    """Обработка выбора что редактировать"""
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("❌ Редактирование отменено", reply_markup=main_menu_keyboard())
        return
    
    data = await state.get_data()
    task_id = data.get("edit_task_id")
    
    if not task_id:
        await message.answer("❌ Ошибка: задача не найдена", reply_markup=main_menu_keyboard())
        await state.clear()
        return
    
    if message.text == "📝 Текст":
        await message.answer("Введите новый текст задачи:", reply_markup=cancel_keyboard())
        await state.set_state(TaskStates.waiting_for_edit_text)
    
    elif message.text == "⏰ Дедлайн":
        await message.answer(
            "Введите новый дедлайн в формате:\n"
            "<code>ГГГГ-ММ-ДД ЧЧ:ММ</code>\n"
            "Или '❌ Без дедлайна'",
            reply_markup=cancel_keyboard()
        )
        await state.set_state(TaskStates.waiting_for_edit_deadline)
    
    elif message.text == "🏷️ Категория":
        categories = db.get_user_categories(message.from_user.id)
        
        if categories:
            await message.answer(
                "Выберите категорию:",
                reply_markup=categories_keyboard(categories)
            )
        else:
            await message.answer("Введите новую категорию:", reply_markup=cancel_keyboard())
        
        await state.set_state(TaskStates.waiting_for_edit_category)
    
    elif message.text == "⚡ Приоритет":
        await message.answer("Выберите приоритет:", reply_markup=priority_keyboard())
        await state.set_state(TaskStates.waiting_for_edit_priority)
    
    elif message.text == "🔄 Повторение":
        await message.answer("Выберите повторение:", reply_markup=repeat_keyboard())
        # Используем то же состояние, что и для создания
        await state.set_state(TaskStates.waiting_for_repeat)
    
    else:
        await message.answer("❌ Неверный выбор", reply_markup=main_menu_keyboard())
        await state.clear()

@dp.message(TaskStates.waiting_for_edit_text)
async def process_edit_text(message: Message, state: FSMContext):
    """Обработка нового текста задачи"""
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("❌ Редактирование отменено", reply_markup=main_menu_keyboard())
        return
    
    data = await state.get_data()
    task_id = data.get("edit_task_id")
    
    if db.update_task(task_id, text=message.text):
        await message.answer("✅ Текст задачи обновлён", reply_markup=main_menu_keyboard())
    else:
        await message.answer("❌ Ошибка при обновлении", reply_markup=main_menu_keyboard())
    
    await state.clear()

@dp.message(TaskStates.waiting_for_edit_deadline)
async def process_edit_deadline(message: Message, state: FSMContext):
    """Обработка нового дедлайна"""
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("❌ Редактирование отменено", reply_markup=main_menu_keyboard())
        return
    
    data = await state.get_data()
    task_id = data.get("edit_task_id")
    
    deadline = None
    if message.text != "❌ Без дедлайна":
        try:
            dt = datetime.strptime(message.text.strip(), "%Y-%m-%d %H:%M")
            deadline = dt.isoformat()
        except ValueError:
            await message.answer("❌ Неверный формат даты", reply_markup=main_menu_keyboard())
            await state.clear()
            return
    
    if db.update_task(task_id, deadline=deadline):
        await message.answer("✅ Дедлайн обновлён", reply_markup=main_menu_keyboard())
    else:
        await message.answer("❌ Ошибка при обновлении", reply_markup=main_menu_keyboard())
    
    await state.clear()

@dp.message(TaskStates.waiting_for_edit_category)
async def process_edit_category(message: Message, state: FSMContext):
    """Обработка новой категории"""
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("❌ Редактирование отменено", reply_markup=main_menu_keyboard())
        return
    
    data = await state.get_data()
    task_id = data.get("edit_task_id")
    
    category = None
    if message.text != "❌ Без категории" and message.text != "➕ Новая категория":
        category = message.text.strip()
    
    if db.update_task(task_id, category=category):
        await message.answer("✅ Категория обновлена", reply_markup=main_menu_keyboard())
    else:
        await message.answer("❌ Ошибка при обновлении", reply_markup=main_menu_keyboard())
    
    await state.clear()

@dp.message(TaskStates.waiting_for_edit_priority)
async def process_edit_priority(message: Message, state: FSMContext):
    """Обработка нового приоритета"""
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("❌ Редактирование отменено", reply_markup=main_menu_keyboard())
        return
    
    data = await state.get_data()
    task_id = data.get("edit_task_id")
    
    priority_map = {
        "Высокий 🔴": "Высокий",
        "Средний 🟡": "Средний",
        "Низкий 🟢": "Низкий",
        "❌ Без приоритета": None
    }
    
    priority = priority_map.get(message.text, message.text)
    
    if db.update_task(task_id, priority=priority):
        await message.answer("✅ Приоритет обновлён", reply_markup=main_menu_keyboard())
    else:
        await message.answer("❌ Ошибка при обновлении", reply_markup=main_menu_keyboard())
    
    await state.clear()

# ==================== ПОИСК ====================

@dp.message(F.text == "🔍 Поиск задач")
async def search_tasks_start(message: Message, state: FSMContext):
    """Начало поиска задач"""
    await message.answer(
        "🔍 <b>Поиск задач</b>\n\n"
        "Введите ключевое слово для поиска:",
        reply_markup=cancel_keyboard()
    )
    await state.set_state(TaskStates.waiting_for_search)

@dp.message(TaskStates.waiting_for_search)
async def process_search(message: Message, state: FSMContext):
    """Обработка поискового запроса"""
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("❌ Поиск отменён", reply_markup=main_menu_keyboard())
        return
    
    await search_tasks_action(message, message.text)
    await state.clear()

async def search_tasks_action(message: Message, keyword: str):
    """Выполнение поиска задач"""
    tasks = db.search_tasks(message.from_user.id, keyword)
    
    if not tasks:
        await message.answer(
            f"🔍 <b>Результаты поиска по '{keyword}'</b>\n\n"
            "Задач не найдено.",
            reply_markup=main_menu_keyboard()
        )
        return
    
    await message.answer(
        f"🔍 <b>Результаты поиска по '{keyword}'</b>\n\n"
        f"Найдено задач: {len(tasks)}",
        reply_markup=main_menu_keyboard()
    )
    
    for task in tasks:
        status = "✅" if task['done'] == 1 else "❌"
        
        task_text = f"{status} <b>{task['text']}</b>\n"
        
        if task['deadline']:
            try:
                deadline_dt = datetime.fromisoformat(task['deadline'])
                task_text += f"⏰ {deadline_dt.strftime('%d.%m.%Y %H:%M')}\n"
            except:
                task_text += f"⏰ {task['deadline']}\n"
        
        if task['category']:
            task_text += f"🏷️ {task['category']}\n"
        
        if task['priority']:
            task_text += f"⚡ {task['priority']}\n"
        
        await message.answer(
            task_text,
            reply_markup=task_actions_keyboard(task['id'])
        )

# ==================== СТАТИСТИКА ====================

@dp.message(F.text == "📊 Статистика")
async def show_stats(message: Message):
    """Показ статистики"""
    stats = db.get_user_stats(message.from_user.id)
    
    if not stats:
        await message.answer(
            "📊 <b>Статистика</b>\n\n"
            "У вас пока нет задач.",
            reply_markup=main_menu_keyboard()
        )
        return
    
    total = stats.get('total', 0)
    completed = stats.get('completed', 0)
    overdue = stats.get('overdue', 0)
    high_priority = stats.get('high_priority', 0)
    with_category = stats.get('with_category', 0)
    
    if total == 0:
        completion_rate = 0
    else:
        completion_rate = (completed / total) * 100
    
    stats_text = (
        f"📊 <b>Ваша статистика</b>\n\n"
        f"<b>Всего задач:</b> {total}\n"
        f"<b>Выполнено:</b> {completed} ({completion_rate:.1f}%)\n"
        f"<b>Просрочено:</b> {overdue}\n"
        f"<b>Высокий приоритет:</b> {high_priority}\n"
        f"<b>С категориями:</b> {with_category}\n\n"
    )
    
    if total > 0:
        if completion_rate == 100:
            stats_text += "🎉 <b>Отлично! Все задачи выполнены!</b>"
        elif completion_rate >= 80:
            stats_text += "👍 <b>Хорошая работа!</b>"
        elif completion_rate >= 50:
            stats_text += "💪 <b>Продолжайте в том же духе!</b>"
        else:
            stats_text += "📈 <b>Есть над чем поработать!</b>"
    
    await message.answer(stats_text, reply_markup=main_menu_keyboard())

# ==================== КАТЕГОРИИ ====================

@dp.message(F.text == "🏷️ Мои категории")
async def show_categories(message: Message):
    """Показ категорий пользователя"""
    categories = db.get_user_categories(message.from_user.id)
    
    if not categories:
        await message.answer(
            "🏷️ <b>Мои категории</b>\n\n"
            "У вас пока нет категорий.\n"
            "Создайте первую задачу с категорией!",
            reply_markup=main_menu_keyboard()
        )
        return
    
    categories_text = "🏷️ <b>Мои категории</b>\n\n"
    for i, category in enumerate(categories, 1):
        categories_text += f"{i}. {category}\n"
    
    categories_text += f"\nВсего категорий: {len(categories)}"
    
    await message.answer(categories_text, reply_markup=main_menu_keyboard())

# ==================== ОБРАБОТКА НЕИЗВЕСТНЫХ КОМАНД ====================

@dp.message()
async def unknown_command(message: Message):
    """Обработка неизвестных команд"""
    await message.answer(
        "🤔 <b>Неизвестная команда</b>\n\n"
        "Используйте кнопки меню или команды:\n"
        "/start - Перезапустить бота\n"
        "/help - Помощь\n"
        "/search - Поиск задач",
        reply_markup=main_menu_keyboard()
    )

# ==================== ЗАПУСК БОТА ====================

async def main():
    """Основная функция запуска бота"""
    logger.info("🚀 Бот запускается...")
    
    try:
        # Запускаем фоновую задачу для напоминаний
        asyncio.create_task(reminder_loop(bot))
        
        logger.info("✅ Фоновая задача напоминаний запущена")
        logger.info("✅ Бот готов к работе!")
        
        # Запускаем опрос обновлений
        await dp.start_polling(bot)
        
    except Exception as e:
        logger.error(f"❌ Критическая ошибка при запуске бота: {e}")
    finally:
        # Закрываем соединение с базой данных
        db.close()
        logger.info("🔌 Соединение с базой данных закрыто")

if __name__ == "__main__":
    asyncio.run(main())