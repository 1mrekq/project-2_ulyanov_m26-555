import time


def handle_db_errors(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except FileNotFoundError:
            print(
                "Ошибка: Файл данных не найден. "
                "Возможно, база данных не инициализирована."
            )
        except KeyError as e:
            name = e.args[0] if e.args else e
            print(f"Ошибка: Таблица или столбец {name} не найден.")
        except ValueError as e:
            print(f"Ошибка валидации: {e}")
        except Exception as e:
            print(f"Ошибка: {e}")
    return wrapper


def confirm_action(action_name):
    def decorator(func):
        def wrapper(*args, **kwargs):
            confirm = input(
                f'Вы уверены, что хотите выполнить "{action_name}"? [y/n]:'
            )
            if confirm == "y":
                return func(*args, **kwargs)
            print("Действие отменено.")
        return wrapper
    return decorator


def log_time(func):
    def wrapper(*args, **kwargs):
        start_time = time.monotonic()
        result = func(*args, **kwargs)
        elapsed = time.monotonic() - start_time
        print(
            f"Функция {func.__name__} выполнилась за {elapsed:1.3f} секунд."
        )
        return result
    return wrapper