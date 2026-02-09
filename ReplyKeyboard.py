from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def main_keyboard():
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Добавить задачу", callback_data="add")],
        [InlineKeyboardButton(text="📋 Мои задачи", callback_data="list")]
    ])
    return kb

def done_delete_buttons(task_id):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Готово", callback_data=f"done_{task_id}")],
        [InlineKeyboardButton(text="❌ Удалить", callback_data=f"delete_{task_id}")]
    ])
    return kb