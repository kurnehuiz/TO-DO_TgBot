import sqlite3
from datetime import datetime, timedelta
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Database:
    def __init__(self, db_name="tasks.db"):
        self.conn = sqlite3.connect(db_name, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
        self.create_tables()
    
    def create_tables(self):
        """Создание таблиц в базе данных"""
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            text TEXT NOT NULL,
            done INTEGER DEFAULT 0,
            deadline TEXT,
            category TEXT DEFAULT 'Общее',
            priority TEXT DEFAULT 'Средний',
            repeat TEXT DEFAULT 'нет',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Создание индексов для быстрого поиска
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_id ON tasks(user_id)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_deadline ON tasks(deadline)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_category ON tasks(category)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_priority ON tasks(priority)")
        
        self.conn.commit()
        logger.info("✅ Таблицы базы данных созданы/проверены")
    
    def add_task(self, user_id, text, deadline=None, category=None, priority=None, repeat=None):
        """Добавление новой задачи"""
        try:
            self.cursor.execute("""
                INSERT INTO tasks (user_id, text, deadline, category, priority, repeat) 
                VALUES (?, ?, ?, ?, ?, ?)
            """, (user_id, text, deadline, category, priority, repeat))
            self.conn.commit()
            task_id = self.cursor.lastrowid
            logger.info(f"✅ Задача добавлена (ID: {task_id}) для пользователя {user_id}")
            return task_id
        except Exception as e:
            logger.error(f"❌ Ошибка при добавлении задачи: {e}")
            return None
    
    def get_tasks(self, user_id, show_completed=False, category=None, priority=None):
        """Получение задач пользователя с фильтрами"""
        try:
            query = """
                SELECT id, text, done, deadline, category, priority, repeat, created_at 
                FROM tasks 
                WHERE user_id = ?
            """
            params = [user_id]
            
            if not show_completed:
                query += " AND done = 0"
            
            if category:
                query += " AND category = ?"
                params.append(category)
            
            if priority:
                query += " AND priority = ?"
                params.append(priority)
            
            # Исправленный ORDER BY с правильным оформлением многострочной строки
            query += """ ORDER BY 
                CASE priority 
                    WHEN 'Высокий' THEN 1
                    WHEN 'Средний' THEN 2
                    WHEN 'Низкий' THEN 3
                    ELSE 4
                END,
                deadline ASC
            """
            
            self.cursor.execute(query, params)
            return self.cursor.fetchall()
        except Exception as e:
            logger.error(f"❌ Ошибка при получении задач: {e}")
            return []
    
    def get_task(self, task_id):
        """Получение конкретной задачи по ID"""
        try:
            self.cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
            return self.cursor.fetchone()
        except Exception as e:
            logger.error(f"❌ Ошибка при получении задачи {task_id}: {e}")
            return None
    
    def mark_done(self, task_id):
        """Отметка задачи как выполненной"""
        try:
            self.cursor.execute("""
                UPDATE tasks 
                SET done = 1, updated_at = CURRENT_TIMESTAMP 
                WHERE id = ?
            """, (task_id,))
            self.conn.commit()
            logger.info(f"✅ Задача {task_id} отмечена как выполненная")
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка при отметке задачи {task_id}: {e}")
            return False
    
    def mark_undone(self, task_id):
        """Отметка задачи как невыполненной"""
        try:
            self.cursor.execute("""
                UPDATE tasks 
                SET done = 0, updated_at = CURRENT_TIMESTAMP 
                WHERE id = ?
            """, (task_id,))
            self.conn.commit()
            logger.info(f"✅ Задача {task_id} отмечена как невыполненная")
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка при отметке задачи {task_id}: {e}")
            return False
    
    def delete_task(self, task_id):
        """Удаление задачи"""
        try:
            self.cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
            self.conn.commit()
            logger.info(f"✅ Задача {task_id} удалена")
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка при удалении задачи {task_id}: {e}")
            return False
    
    def update_task(self, task_id, **kwargs):
        """Обновление задачи"""
        try:
            if not kwargs:
                return False
            
            set_clause = ", ".join([f"{key} = ?" for key in kwargs.keys()])
            values = list(kwargs.values())
            values.append(task_id)
            
            query = f"""
                UPDATE tasks 
                SET {set_clause}, updated_at = CURRENT_TIMESTAMP 
                WHERE id = ?
            """
            
            self.cursor.execute(query, values)
            self.conn.commit()
            logger.info(f"✅ Задача {task_id} обновлена")
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка при обновлении задачи {task_id}: {e}")
            return False
    
    def get_tasks_with_deadline(self):
        """Получение задач с дедлайном"""
        try:
            self.cursor.execute("""
                SELECT id, user_id, text, deadline, repeat 
                FROM tasks 
                WHERE done = 0 AND deadline IS NOT NULL
                ORDER BY deadline ASC
            """)
            return self.cursor.fetchall()
        except Exception as e:
            logger.error(f"❌ Ошибка при получении задач с дедлайном: {e}")
            return []
    
    def search_tasks(self, user_id, keyword):
        """Поиск задач по ключевому слову"""
        try:
            self.cursor.execute("""
                SELECT id, text, done, deadline, category, priority, repeat 
                FROM tasks 
                WHERE user_id = ? AND text LIKE ?
                ORDER BY 
                    CASE priority 
                        WHEN 'Высокий' THEN 1
                        WHEN 'Средний' THEN 2
                        WHEN 'Низкий' THEN 3
                        ELSE 4
                    END,
                    deadline ASC
            """, (user_id, f"%{keyword}%"))
            return self.cursor.fetchall()
        except Exception as e:
            logger.error(f"❌ Ошибка при поиске задач: {e}")
            return []
    
    def get_user_stats(self, user_id):
        """Получение статистики пользователя"""
        try:
            self.cursor.execute("""
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN done = 1 THEN 1 ELSE 0 END) as completed,
                    COUNT(CASE WHEN deadline IS NOT NULL 
                              AND datetime(deadline) < datetime('now') 
                              AND done = 0 THEN 1 END) as overdue,
                    COUNT(CASE WHEN priority = 'Высокий' AND done = 0 THEN 1 END) as high_priority,
                    COUNT(CASE WHEN category IS NOT NULL THEN 1 END) as with_category
                FROM tasks 
                WHERE user_id = ?
            """, (user_id,))
            result = self.cursor.fetchone()
            return dict(result) if result else {}
        except Exception as e:
            logger.error(f"❌ Ошибка при получении статистики: {e}")
            return {}
    
    def get_user_categories(self, user_id):
        """Получение уникальных категорий пользователя"""
        try:
            self.cursor.execute("""
                SELECT DISTINCT category 
                FROM tasks 
                WHERE user_id = ? AND category IS NOT NULL AND category != ''
            """, (user_id,))
            return [row[0] for row in self.cursor.fetchall()]
        except Exception as e:
            logger.error(f"❌ Ошибка при получении категорий: {e}")
            return []
    
    def close(self):
        """Закрытие соединения с базой данных"""
        self.conn.close()

# Создаем глобальный экземпляр базы данных
db = Database()