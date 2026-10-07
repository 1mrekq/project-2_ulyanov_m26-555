from primitive_db.utils import load_metadata, save_metadata
from primitive_db.core import CreateTableException, DropTableException, create_table, list_tables, drop_table

import prompt
import shlex

METADATA_FILE = 'db_meta.json'

def print_create_table_success_message(table_name, table_metadata):
    columns_str = ', '.join([f'{k}:{v}' for k, v in table_metadata.items()])
    print(f'Таблица "{table_name}" успешно создана со столбцами: {columns_str}')

def print_drop_table_success_message(table_name):
    print(f'Таблица "{table_name}" успешно удалена.')

def print_error_message(error_message):
    print(f'Ошибка: {error_message}')

def print_invalid_value(command, command_args):
    value = ' '.join(command_args) if command_args else command
    print(f'Некорректное значение: {value}. Попробуйте снова.')

def exit_command(*args, **kwargs):
    quit()

def help_command(*args, **kwargs):
    print("\n***Процесс работы с таблицей***")
    print("Функции:")
    print("<command> create_table <имя_таблицы> <столбец1:тип> .. - создать таблицу")
    print("<command> list_tables - показать список всех таблиц")
    print("<command> drop_table <имя_таблицы> - удалить таблицу")
    
    print("\nОбщие команды:")
    print("<command> exit - выход из программы")
    print("<command> help - справочная информация\n") 

def run():
    help_command()

    while True:
        user_input = prompt.string('Введите команду: ')
        args = shlex.split(user_input)
        if not args:
            continue

        command = args[0]
        command_args = args[1:]

        if command == 'exit':
            exit_command()
        elif command == 'help':
            help_command()
        else:
            metadata = load_metadata(METADATA_FILE)

            try:
                match command:
                    case 'create_table':
                        if not command_args:
                            print_invalid_value(command, command_args)
                        else:
                            table_name = command_args[0]
                            columns = command_args[1:]
                            invalid_column = next(
                                (
                                    column
                                    for column in columns
                                    if column.count(':') != 1
                                ),
                                None,
                            )
                            if invalid_column is not None:
                                print_invalid_value(command, [invalid_column])
                           
                            else:
                                metadata = create_table(metadata, table_name, columns)
                                save_metadata(METADATA_FILE, metadata)
                                print_create_table_success_message(table_name, metadata[table_name])
                    case 'drop_table':
                        if len(command_args) != 1:
                            print_invalid_value(command, command_args)
                        else:
                            metadata = drop_table(metadata, command_args[0])
                            save_metadata(METADATA_FILE, metadata)
                            print_drop_table_success_message(command_args[0])
                    case 'list_tables':
                        if command_args:
                            print_invalid_value(command, command_args)
                        else:
                            list_tables(metadata)
                    case _:
                        print(f'Функции {command} нет. Попробуйте снова.')
            except (CreateTableException, DropTableException) as e:
                print_error_message(e)