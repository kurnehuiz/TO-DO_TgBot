from aiogram.types import (
    ReplyKeyboardMarkup, 
    KeyboardButton, 
    InlineKeyboardMarkup, 
    InlineKeyboardButton
)
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

def main_menu_keyboard():
    """Главное меню"""
    builder = ReplyKeyboardBuilder()
    
    builder.button(text="➕ Создать задачу")
    builder.button(text="📋 Мои задачи")
    builder.button(text="🔍 Поиск задач")
    builder.button(text="📊 Статистика")
    builder.button(text="🏷️ Мои категории")
    
    builder.adjust(2, 2, 1)
    return builder.as_markup(resize_keyboard=True)

def task_actions_keyboard(task_id: int):
    """Действия с задачей"""
    builder = InlineKeyboardBuilder()
    
    builder.button(text="✅ Выполнено", callback_data=f"done_{task_id}")
    builder.button(text="✏️ Редактировать", callback_data=f"edit_{task_id}")
    builder.button(text="❌ Удалить", callback_data=f"delete_{task_id}")
    
    builder.adjust(1, 2)
    return builder.as_markup()

def priority_keyboard():
    """Выбор приоритета"""
    builder = ReplyKeyboardBuilder()
    
    builder.button(text="Высокий 🔴")
    builder.button(text="Средний 🟡")
    builder.button(text="Низкий 🟢")
    builder.button(text="❌ Без приоритета")
    
    builder.adjust(2, 2)
    return builder.as_markup(resize_keyboard=True, one_time_keyboard=True)

def repeat_keyboard():
    """Выбор повторения"""
    builder = ReplyKeyboardBuilder()
    
    builder.button(text="Нет")
    builder.button(text="Ежедневно")
    builder.button(text="Еженедельно")
    builder.button(text="Ежемесячно")
    
    builder.adjust(2, 2)
    return builder.as_markup(resize_keyboard=True, one_time_keyboard=True)

def edit_choice_keyboard():
    """Выбор что редактировать"""
    builder = ReplyKeyboardBuilder()
    
    builder.button(text="📝 Текст")
    builder.button(text="⏰ Дедлайн")
    builder.button(text="🏷️ Категория")
    builder.button(text="⚡ Приоритет")
    builder.button(text="🔄 Повторение")
    builder.button(text="❌ Отмена")
    
    builder.adjust(2, 2, 2)
    return builder.as_markup(resize_keyboard=True, one_time_keyboard=True)

def cancel_keyboard():
    """Клавиатура с отменой"""
    builder = ReplyKeyboardBuilder()
    
    builder.button(text="❌ Отмена")
    
    return builder.as_markup(resize_keyboard=True, one_time_keyboard=True)

def categories_keyboard(categories):
    """Клавиатура с категориями пользователя"""
    builder = ReplyKeyboardBuilder()
    
    for category in categories[:8]:  # Ограничиваем 8 категориями
        builder.button(text=category)
    
    builder.button(text="➕ Новая категория")
    builder.button(text="❌ Без категории")
    
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True, one_time_keyboard=True)

def back_to_menu_keyboard():
    """Кнопка возврата в меню"""
    builder = ReplyKeyboardBuilder()
    
    builder.button(text="🏠 Главное меню")
    
    return builder.as_markup(resize_keyboard=True)

def filter_keyboard():
    """Фильтрация задач"""
    builder = ReplyKeyboardBuilder()
    
    builder.button(text="📋 Все задачи")
    builder.button(text="✅ Выполненные")
    builder.button(text="❌ Невыполненные")
    builder.button(text="⏰ С дедлайном")
    builder.button(text="🔴 Высокий приоритет")
    builder.button(text="🏠 Главное меню")
    
    builder.adjust(2, 2, 2)
    return builder.as_markup(resize_keyboard=True)

def deadline_keyboard():
    """Клавиатура для выбора дедлайна"""
    builder = ReplyKeyboardBuilder()
    
    builder.button(text="❌ Без дедлайна")
    builder.button(text="❌ Отмена")
    
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True, one_time_keyboard=True)