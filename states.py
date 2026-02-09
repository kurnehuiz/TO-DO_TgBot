from aiogram.fsm.state import StatesGroup, State

class TaskStates(StatesGroup):
    waiting_for_task = State()           # Ожидание текста задачи
    waiting_for_deadline = State()       # Ожидание дедлайна
    waiting_for_category = State()       # Ожидание категории
    waiting_for_priority = State()       # Ожидание приоритета
    waiting_for_repeat = State()         # Ожидание повторения
    
    # Новые состояния для редактирования
    waiting_for_edit_choice = State()    # Ожидание выбора что редактировать
    waiting_for_edit_text = State()      # Ожидание нового текста
    waiting_for_edit_deadline = State()  # Ожидание нового дедлайна
    waiting_for_edit_category = State()  # Ожидание новой категории
    waiting_for_edit_priority = State()  # Ожидание нового приоритета
    
    # Состояние для поиска
    waiting_for_search = State()         # Ожидание ключевого слова для поиска