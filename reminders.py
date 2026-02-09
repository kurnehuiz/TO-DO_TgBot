import asyncio
from datetime import datetime, timedelta
from db_handler import db
import logging

logger = logging.getLogger(__name__)

async def reminder_loop(bot):
    """Цикл проверки напоминаний"""
    logger.info("⏰ Запущен цикл напоминаний")
    
    while True:
        try:
            tasks = db.get_tasks_with_deadline()
            now = datetime.now()
            
            for task in tasks:
                task_id = task['id']
                user_id = task['user_id']
                text = task['text']
                deadline_str = task['deadline']
                repeat = task['repeat']
                
                if deadline_str:
                    try:
                        deadline = datetime.fromisoformat(deadline_str)
                        
                        # Проверяем, если дедлайн наступил или просрочен
                        if now >= deadline:
                            # Отправляем уведомление
                            await bot.send_message(
                                user_id,
                                f"⏰ **Дедлайн!**\n\n"
                                f"Задача: {text}\n"
                                f"Срок: {deadline.strftime('%d.%m.%Y %H:%M')}\n\n"
                                f"Задача автоматически помечена как выполненная."
                            )
                            
                            # Помечаем как выполненную
                            db.mark_done(task_id)
                            
                            logger.info(f"📨 Отправлено напоминание для задачи {task_id} пользователю {user_id}")
                            
                            # Обработка повторяющихся задач
                            if repeat and repeat != "Нет":
                                await handle_repeated_task(task, deadline)
                                
                    except (ValueError, TypeError) as e:
                        logger.error(f"❌ Ошибка обработки дедлайна задачи {task_id}: {e}")
                        continue
            
            # Ждем 60 секунд перед следующей проверкой
            await asyncio.sleep(60)
            
        except Exception as e:
            logger.error(f"❌ Критическая ошибка в reminder_loop: {e}")
            await asyncio.sleep(300)  # Ждем 5 минут при ошибке

async def handle_repeated_task(task, old_deadline):
    """Обработка повторяющихся задач"""
    try:
        repeat = task['repeat']
        new_deadline = old_deadline
        
        if repeat == "Ежедневно":
            new_deadline = old_deadline + timedelta(days=1)
        elif repeat == "Еженедельно":
            new_deadline = old_deadline + timedelta(weeks=1)
        elif repeat == "Ежемесячно":
            # Просто добавляем 30 дней для упрощения
            new_deadline = old_deadline + timedelta(days=30)
        
        # Создаем новую задачу с новым дедлайном
        db.add_task(
            user_id=task['user_id'],
            text=task['text'],
            deadline=new_deadline.isoformat(),
            category=None,  # Можно добавить получение категории из БД
            priority=None,  # Можно добавить получение приоритета из БД
            repeat=repeat
        )
        
        logger.info(f"🔄 Создана повторяющаяся задача для пользователя {task['user_id']}")
        
    except Exception as e:
        logger.error(f"❌ Ошибка обработки повторяющейся задачи: {e}")

async def send_reminder(bot, user_id, text, deadline):
    """Отправка разового напоминания"""
    try:
        await bot.send_message(
            user_id,
            f"⏰ **Напоминание!**\n\n"
            f"Задача: {text}\n"
            f"Дедлайн: {deadline}"
        )
        return True
    except Exception as e:
        logger.error(f"❌ Ошибка отправки напоминания: {e}")
        return False