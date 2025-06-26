# file: database.py
import sqlite3
import time



# НОВАЯ СТРОКА
DB_NAME = '/data/bot_database.db'

# Интервал по умолчанию (30 минут), если он не установлен
DEFAULT_REMINDER_INTERVAL_SECONDS = 30 * 60 

def init_db():
    """Инициализирует базу данных и создает таблицы, если их нет."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS groups (
        group_id INTEGER PRIMARY KEY,
        group_name TEXT NOT NULL,
        last_message_timestamp INTEGER NOT NULL,
        reminder_interval_seconds INTEGER NOT NULL 
    )
    ''')
    conn.commit()
    conn.close()
    print("База данных инициализирована.")

# --- НОВАЯ ФУНКЦИЯ для установки интервала в МИНУТАХ ---
def set_group_interval_minutes(group_id: int, interval_minutes: int):
    """Устанавливает новый интервал напоминаний в минутах для конкретной группы."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    # Конвертируем минуты в секунды
    interval_seconds = interval_minutes * 60
    
    cursor.execute('''
    UPDATE groups SET reminder_interval_seconds = ? WHERE group_id = ?
    ''', (interval_seconds, group_id))
    
    conn.commit()
    conn.close()
    print(f"Для группы {group_id} установлен интервал {interval_minutes} минут.")


def update_last_message_time(group_id: int, group_name: str):
    """Обновляет время последнего сообщения. Если группы нет, создает ее с интервалом по умолчанию."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    current_timestamp = int(time.time())
    
    cursor.execute('''
    INSERT OR IGNORE INTO groups (group_id, group_name, last_message_timestamp, reminder_interval_seconds)
    VALUES (?, ?, ?, ?)
    ''', (group_id, group_name, current_timestamp, DEFAULT_REMINDER_INTERVAL_SECONDS))
    
    cursor.execute('''
    UPDATE groups 
    SET last_message_timestamp = ?, group_name = ?
    WHERE group_id = ?
    ''', (current_timestamp, group_name, group_id))
    
    conn.commit()
    conn.close()

def get_groups_to_remind():
    """Возвращает список ID групп, которым нужно отправить напоминание."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    current_timestamp = int(time.time())
    
    cursor.execute('''
    SELECT group_id FROM groups
    WHERE (? - last_message_timestamp) > reminder_interval_seconds
    ''', (current_timestamp,))
    
    groups = [item[0] for item in cursor.fetchall()]
    
    conn.close()
    return groups