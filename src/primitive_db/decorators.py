import time

from primitive_db.constants import CONFIRM_NO, CONFIRM_YES, ELAPSED_PRECISION


def handle_db_errors(func):
    """Перехватывает ошибки БД и выводит понятное сообщение."""

    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except FileNotFoundError:
            print(
                'Ошибка: Файл данных не найден. '
                'Возможно, база данных не инициализирована.'
            )
        except KeyError as e:
            name = e.args[0] if e.args else e
            print(f'Ошибка: Таблица или столбец {name} не найден.')
        except ValueError as e:
            print(f'Ошибка валидации: {e}')
        except Exception as e:
            print(f'Ошибка: {e}')
    return wrapper


def confirm_action(action_name):
    """Запрашивает подтверждение перед выполнением опасного действия."""

    def decorator(func):
        def wrapper(*args, **kwargs):
            confirm = input(
                f'Вы уверены, что хотите выполнить "{action_name}"? '
                f'[{CONFIRM_YES}/{CONFIRM_NO}]:'
            )
            if confirm == CONFIRM_YES:
                return func(*args, **kwargs)
            print('Действие отменено.')
        return wrapper
    return decorator


def log_time(func):
    """Выводит время выполнения обёрнутой функции."""

    def wrapper(*args, **kwargs):
        start_time = time.monotonic()
        result = func(*args, **kwargs)
        elapsed = time.monotonic() - start_time
        print(
            f'Функция {func.__name__} выполнилась за '
            f'{elapsed:.{ELAPSED_PRECISION}f} секунд.'
        )
        return result
    return wrapper


def create_cacher():
    """Создаёт замыкание для кэширования результатов по ключу."""
    cache = {}

    def cache_result(key, value_func):
        if key in cache:
            return cache[key]
        result = value_func()
        cache[key] = result
        return result

    return cache_result
