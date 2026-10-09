import json
import os
from pathlib import Path


def load_metadata(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        return {}


def save_metadata(filepath, data):
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f)
    except OSError:
        print(f'Не удалось сохранить данные в файл {filepath}')


def load_table_data(table_name):
    try:
        with open(f'data/{table_name}.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        return []


def save_table_data(table_name, data):
    try:
        os.makedirs('data', exist_ok=True)
        with open(f'data/{table_name}.json', 'w', encoding='utf-8') as f:
            json.dump(data, f)
    except OSError:
        print(f'Не удалось сохранить данные в файл {table_name}')


def delete_table_data(table_name):
    path = Path(f'data/{table_name}.json')
    if path.exists():
        path.unlink()


def create_cacher():
    cache = {}

    def cache_result(key, value_func):
        if key in cache:
            return cache[key]
        result = value_func()
        cache[key] = result
        return result

    return cache_result