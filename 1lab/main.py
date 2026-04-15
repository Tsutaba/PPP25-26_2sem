import requests
from bs4 import BeautifulSoup
import pandas as pd
import sqlite3
from datetime import datetime

# Извлечение данных
def extract_data():
    # Извлекает данные из двух источников:
    # 1. API (JSON);  2. Веб‑страница (HTML)
    raw_data = {}

    # Источник API
    try:
        response = requests.get('https://jsonplaceholder.typicode.com/posts')
        raw_data['api_source'] = response.json()
    except Exception as e:
        print(f"Ошибка при получении данных из API: {e}")
        raw_data['api_source'] = []

    # Источник HTML‑парсинг
    try:
        html_response = requests.get('https://httpbin.org/html')
        soup = BeautifulSoup(html_response.text, 'html.parser')

        # Ищем заголовок страницы как пример данных
        title = soup.find('title')
        if title:
            raw_data['html_source'] = [{'title': title.text, 'source': 'httpbin'}]
        else:
            raw_data['html_source'] = []
    except Exception as e:
        print(f"Ошибка при парсинге HTML: {e}")
        raw_data['html_source'] = []

    return raw_data

# Трансформация данных

def transform_data(raw_data):
    # Очищает и нормализует данные, приводит к единому формату
    transformed_data = []

    # Обработка данных из API
    for item in raw_data.get('api_source', []):
        transformed_item = {
            'title': item.get('title', '').strip(),
            'content': item.get('body', '').strip(),
            'price': 0,  # В API нет цены, ставим 0
            'date': datetime.now().strftime('%Y-%m-%d'),
            'source': 'jsonplaceholder',
            'category': 'API Data'
        }
        transformed_data.append(transformed_item)

    # Обработка данных из HTML
    for item in raw_data.get('html_source', []):
        transformed_item = {
            'title': item.get('title', '').strip(),
            'content': 'Parsed HTML content',
            'price': 0,
            'date': datetime.now().strftime('%Y-%m-%d'),
            'source': item.get('source', 'httpbin'),
            'category': 'HTML Data'
        }
        transformed_data.append(transformed_item)

    # Создаём DataFrame для удобства
    df = pd.DataFrame(transformed_data)

    # Очистка данных, удаление дубликатов
    df.drop_duplicates(subset=['title'], inplace=True)

    # Нормализация строк (приведение к нижнему регистру)
    df['title'] = df['title'].str.lower()
    df['category'] = df['category'].str.lower()

    # Заполнение пропущенных значений
    df.fillna('', inplace=True)

    return df

# Загрузка данных

def load_data(df):
    # Загружает данные в SQLite базу данных
    # Подключение к базе данных (создаст файл, если его нет)
    conn = sqlite3.connect('etl_database.db')

    try:
        # Создаём таблицу, если её нет
        conn.execute('''
            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT,
                price REAL,
                date TEXT,
                source TEXT,
                category TEXT
            )
        ''')

        # Загружаем данные в таблицу
        df.to_sql('items', conn, if_exists='append', index=False)

        print(f"Успешно загружено {len(df)} записей в базу данных")

    except Exception as e:
        print(f"Ошибка при загрузке данных: {e}")

    finally:
        conn.close()

# Основной ETL‑процесс

def run_etl():
    # Запускает полный ETL‑процесс
    print("Запуск ETL‑процесса...")

    print("1. Извлечение данных...")
    raw_data = extract_data()

    print("2. Трансформация данных...")
    transformed_df = transform_data(raw_data)

    print("3. Загрузка данных...")
    load_data(transformed_df)

    print("ETL‑процесс завершён")

if __name__ == '__main__':
    run_etl()
