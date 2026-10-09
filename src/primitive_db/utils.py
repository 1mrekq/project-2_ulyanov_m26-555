import json
import os

from primitive_db.constants import (
    DATA_DIR,
    ENCODING,
    META_FILE,
    READ_MODE,
    TABLE_FILE_EXTENSION,
    WRITE_MODE,
)


def _table_filepath(table_name):
    """Возвращает путь к JSON-файлу данных таблицы."""
    filename = f'{table_name}{TABLE_FILE_EXTENSION}'
    return os.path.join(DATA_DIR, filename)


def initialize_storage():
    """Создаёт каталог данных и файл метаданных, если их ещё нет."""
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(META_FILE):
        save_metadata(META_FILE, {})


def load_metadata(filepath):
    """Загружает метаданные БД из файла или возвращает пустой словарь."""
    try:
        with open(filepath, READ_MODE, encoding=ENCODING) as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        return {}


def save_metadata(filepath, data):
    """Сохраняет метаданные БД в файл."""
    try:
        with open(filepath, WRITE_MODE, encoding=ENCODING) as f:
            json.dump(data, f)
    except OSError:
        print(f'Не удалось сохранить данные в файл {filepath}')


def load_table_data(table_name):
    """Загружает данные таблицы из файла или возвращает пустой список."""
    try:
        with open(_table_filepath(table_name), READ_MODE, encoding=ENCODING) as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        return []


def save_table_data(table_name, data):
    """Сохраняет данные таблицы в JSON-файл."""
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(_table_filepath(table_name), WRITE_MODE, encoding=ENCODING) as f:
            json.dump(data, f)
    except OSError:
        print(f'Не удалось сохранить данные в файл {table_name}')


def delete_table_data(table_name):
    """Удаляет файл данных таблицы, если он существует."""
    path = _table_filepath(table_name)
    if os.path.exists(path):
        os.remove(path)
