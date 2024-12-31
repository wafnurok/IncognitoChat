import sqlite3

# Подключение к базе данных
DB_PATH = 'bot_database.db'

def create_tables():
    """Создаёт таблицы базы данных, если их ещё нет."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_settings (
        user_id INTEGER PRIMARY KEY, -- ID пользователя
        age INTEGER,                 -- Возраст
        country TEXT,                -- Страна
        city TEXT,                   -- Город
        gender TEXT                  -- Пол (мужской/женский)
    )
    ''')
    
    conn.commit()
    conn.close()

def add_user(user_id):
    """Добавляет нового пользователя в базу данных, если его ещё нет."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
    INSERT OR IGNORE INTO user_settings (user_id, age, country, city, gender)
    VALUES (?, NULL, NULL, NULL, NULL)
    ''', (user_id,))
    
    conn.commit()
    conn.close()

def update_user_preferences(user_id, age=None, country=None, city=None, gender=None):
    """Обновляет настройки пользователя."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
    UPDATE user_settings
    SET age = COALESCE(?, age),
        country = COALESCE(?, country),
        city = COALESCE(?, city),
        gender = COALESCE(?, gender)
    WHERE user_id = ?
    ''', (age, country, city, gender, user_id))
    
    conn.commit()
    conn.close()

def get_user_preferences(user_id):
    """Возвращает настройки пользователя."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT age, country, city, gender
    FROM user_settings
    WHERE user_id = ?
    ''', (user_id,))
    
    result = cursor.fetchone()
    conn.close()
    
    if result:
        return {
            'age': result[0],
            'country': result[1],
            'city': result[2],
            'gender': result[3]
        }
    return None