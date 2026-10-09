import json

import prompt
from prettytable import PrettyTable

from primitive_db.constants import (
    CACHE_KEY_DATA,
    CACHE_KEY_TABLE,
    CACHE_KEY_WHERE,
    CMD_CREATE_TABLE,
    CMD_DELETE,
    CMD_DROP_TABLE,
    CMD_EXIT,
    CMD_HELP,
    CMD_INFO,
    CMD_INSERT,
    CMD_LIST_TABLES,
    CMD_SELECT,
    CMD_UPDATE,
    COLUMN_ID_NAME,
    COLUMN_LIST_SEPARATOR,
    COLUMN_SEPARATOR,
    COLUMN_SEPARATORS_IN_DEFINITION,
    COMMAND_PROMPT,
    ID_LIST_SEPARATOR,
    KW_FROM,
    KW_INTO,
    KW_SET,
    KW_VALUES,
    KW_WHERE,
    META_FILE,
    TABLE_LIST_MARK,
    TABLE_NAME_ARG_COUNT,
    TOKEN_EQUALS,
)
from primitive_db.core import (
    create_table,
    delete,
    drop_table,
    insert,
    list_tables,
    select,
    table_info,
    update,
)
from primitive_db.decorators import create_cacher
from primitive_db.parser import (
    parse_delete_args,
    parse_insert_args,
    parse_select_args,
    parse_update_args,
    tokenize,
)
from primitive_db.utils import (
    delete_table_data,
    initialize_storage,
    load_metadata,
    load_table_data,
    save_metadata,
    save_table_data,
)

cache_result = create_cacher()


def _format_columns(table_metadata):
    """Форматирует описание столбцов таблицы в строку."""
    return COLUMN_LIST_SEPARATOR.join(
        f'{name}{COLUMN_SEPARATOR}{column_type}'
        for name, column_type in table_metadata.items()
    )


def print_create_table_success_message(table_name, table_metadata):
    """Печатает сообщение об успешном создании таблицы."""
    columns_str = _format_columns(table_metadata)
    print(f'Таблица "{table_name}" успешно создана со столбцами: {columns_str}')


def print_drop_table_success_message(table_name):
    """Печатает сообщение об успешном удалении таблицы."""
    print(f'Таблица "{table_name}" успешно удалена.')


def print_insert_into_table_success_message(table_name, data):
    """Печатает сообщение об успешном добавлении записи."""
    row_id = data[-1][COLUMN_ID_NAME]
    print(
        f'Запись с {COLUMN_ID_NAME}={row_id} успешно добавлена '
        f'в таблицу "{table_name}".'
    )


def print_update_table_success_message(table_name, updated_ids):
    """Печатает сообщение об успешном обновлении записей."""
    if len(updated_ids) == 1:
        print(
            f'Запись с {COLUMN_ID_NAME}={updated_ids[0]} в таблице '
            f'"{table_name}" успешно обновлена.'
        )
    elif len(updated_ids) > 1:
        ids = ID_LIST_SEPARATOR.join(updated_ids)
        print(
            f'Записи с {COLUMN_ID_NAME}={ids} в таблице "{table_name}" '
            f'успешно обновлены.'
        )


def print_delete_from_table_success_message(table_name, deleted_ids):
    """Печатает сообщение об успешном удалении записей."""
    if len(deleted_ids) == 1:
        print(
            f'Запись с {COLUMN_ID_NAME}={deleted_ids[0]} успешно удалена '
            f'из таблицы "{table_name}".'
        )
    elif len(deleted_ids) > 1:
        ids = ID_LIST_SEPARATOR.join(deleted_ids)
        print(
            f'Записи с {COLUMN_ID_NAME}={ids} успешно удалены из таблицы '
            f'"{table_name}".'
        )


def table_not_found_message(table_name):
    """Возвращает текст ошибки об отсутствии таблицы."""
    return f'Таблица "{table_name}" не существует.'


def print_error_message(error_message):
    """Печатает сообщение об ошибке."""
    print(f'Ошибка: {error_message}')


def print_invalid_value(command, command_args):
    """Печатает сообщение о некорректном значении команды."""
    value = ' '.join(command_args) if command_args else command
    print(f'Некорректное значение: {value}. Попробуйте снова.')


def print_rows(rows, columns):
    """Печатает строки таблицы в виде PrettyTable."""
    table = PrettyTable()
    table.field_names = list(columns.keys())
    for row in rows:
        table.add_row([row.get(column) for column in table.field_names])
    print(table)


def print_list_tables(table_names):
    """Печатает список имён таблиц."""
    if not table_names:
        print('Нет таблиц для отображения.')
        return

    for table_name in table_names:
        print(f'{TABLE_LIST_MARK} {table_name}')


def print_table_info(table_name, columns, row_count):
    """Печатает информацию о таблице: столбцы и число записей."""
    columns_str = _format_columns(columns)
    print(f'Таблица: {table_name}')
    print(f'Столбцы: {columns_str}')
    print(f'Количество записей: {row_count}')


def exit_command(*args, **kwargs):
    """Завершает работу приложения."""
    quit()


def help_command(*args, **kwargs):
    """Печатает справочную информацию по командам."""
    print('***Процесс работы с таблицей***')
    print('Функции:')
    print(
        f'<command> {CMD_CREATE_TABLE} <имя_таблицы> <столбец1:тип> '
        f'<столбец2:тип> .. - создать таблицу'
    )
    print(f'<command> {CMD_LIST_TABLES} - показать список всех таблиц')
    print(f'<command> {CMD_DROP_TABLE} <имя_таблицы> - удалить таблицу')
    print(f'<command> {CMD_EXIT} - выход из программы')
    print(f'<command> {CMD_HELP} - справочная информация')
    print()
    print('***Операции с данными***')
    print()
    print('Функции:')
    print(
        f'<command> {CMD_INSERT} {KW_INTO} <имя_таблицы> {KW_VALUES} '
        f'(<значение1>, <значение2>, ...) - создать запись.'
    )
    print(
        f'<command> {CMD_SELECT} {KW_FROM} <имя_таблицы> {KW_WHERE} '
        f'<столбец> {TOKEN_EQUALS} <значение> '
        f'- прочитать записи по условию.'
    )
    print(
        f'<command> {CMD_SELECT} {KW_FROM} <имя_таблицы> '
        f'- прочитать все записи.'
    )
    print(
        f'<command> {CMD_UPDATE} <имя_таблицы> {KW_SET} <столбец1> '
        f'{TOKEN_EQUALS} <новое_значение1> {KW_WHERE} <столбец_условия> '
        f'{TOKEN_EQUALS} <значение_условия> - обновить запись.'
    )
    print(
        f'<command> {CMD_DELETE} {KW_FROM} <имя_таблицы> {KW_WHERE} '
        f'<столбец> {TOKEN_EQUALS} <значение> - удалить запись.'
    )
    print(
        f'<command> {CMD_INFO} <имя_таблицы> '
        f'- вывести информацию о таблице.'
    )
    print(f'<command> {CMD_EXIT} - выход из программы')
    print(f'<command> {CMD_HELP} - справочная информация')


def _is_column_definition(column):
    """Проверяет, что аргумент задаёт столбец в формате имя:тип."""
    return (
        column.count(COLUMN_SEPARATOR) == COLUMN_SEPARATORS_IN_DEFINITION
    )


def run():
    """Запускает основной цикл обработки команд пользователя."""
    initialize_storage()
    help_command()

    while True:
        user_input = prompt.string(COMMAND_PROMPT)
        try:
            args = tokenize(user_input)
        except ValueError:
            print_invalid_value(user_input, [])
            continue

        if not args:
            continue

        command, *command_args = args

        if command == CMD_EXIT:
            exit_command()
        elif command == CMD_HELP:
            help_command()
        else:
            metadata = load_metadata(META_FILE)

            if command == CMD_CREATE_TABLE:
                if not command_args:
                    print_invalid_value(command, command_args)
                else:
                    table_name, *columns = command_args
                    invalid_column = next(
                        (
                            column
                            for column in columns
                            if not _is_column_definition(column)
                        ),
                        None,
                    )
                    if invalid_column is not None:
                        print_invalid_value(command, [invalid_column])
                    else:
                        metadata = create_table(
                            metadata, table_name, columns
                        )
                        if metadata is None:
                            continue
                        save_metadata(META_FILE, metadata)
                        save_table_data(table_name, [])
                        print_create_table_success_message(
                            table_name, metadata[table_name]
                        )
            elif command == CMD_DROP_TABLE:
                if len(command_args) != TABLE_NAME_ARG_COUNT:
                    print_invalid_value(command, command_args)
                else:
                    [table_name] = command_args
                    metadata = drop_table(metadata, table_name)
                    if metadata is None:
                        continue
                    save_metadata(META_FILE, metadata)
                    delete_table_data(table_name)
                    print_drop_table_success_message(table_name)
            elif command == CMD_LIST_TABLES:
                if command_args:
                    print_invalid_value(command, command_args)
                else:
                    print_list_tables(list_tables(metadata))
            elif command == CMD_INSERT:
                parsed = parse_insert_args(command_args)
                if parsed is None:
                    print_invalid_value(command, command_args)
                else:
                    table_name, values = parsed
                    table_data = load_table_data(table_name)
                    table_data = insert(
                        metadata, table_name, table_data, values
                    )
                    if table_data is None:
                        continue
                    save_table_data(table_name, table_data)
                    print_insert_into_table_success_message(
                        table_name, table_data
                    )
            elif command == CMD_SELECT:
                parsed = parse_select_args(command_args)
                if parsed is None:
                    print_invalid_value(command, command_args)
                else:
                    table_name, where_clause = parsed
                    if table_name not in metadata:
                        print_error_message(
                            table_not_found_message(table_name)
                        )
                        continue
                    table_data = load_table_data(table_name)
                    cache_key = json.dumps(
                        {
                            CACHE_KEY_TABLE: table_name,
                            CACHE_KEY_WHERE: where_clause,
                            CACHE_KEY_DATA: table_data,
                        },
                        sort_keys=True,
                    )
                    rows = cache_result(
                        cache_key,
                        lambda: select(table_data, where_clause),
                    )
                    if rows is None:
                        continue
                    print_rows(rows, metadata[table_name])
            elif command == CMD_UPDATE:
                parsed = parse_update_args(command_args)
                if parsed is None:
                    print_invalid_value(command, command_args)
                else:
                    table_name, set_clause, where_clause = parsed
                    if table_name not in metadata:
                        print_error_message(
                            table_not_found_message(table_name)
                        )
                        continue
                    table_data = load_table_data(table_name)
                    result = update(
                        metadata,
                        table_name,
                        table_data,
                        set_clause,
                        where_clause,
                    )
                    if result is None:
                        continue
                    table_data, updated_ids = result
                    save_table_data(table_name, table_data)
                    updated_ids = [
                        str(row_id) for row_id in updated_ids
                    ]
                    print_update_table_success_message(
                        table_name, updated_ids
                    )
            elif command == CMD_DELETE:
                parsed = parse_delete_args(command_args)
                if parsed is None:
                    print_invalid_value(command, command_args)
                else:
                    table_name, where_clause = parsed
                    if table_name not in metadata:
                        print_error_message(
                            table_not_found_message(table_name)
                        )
                        continue
                    table_data = load_table_data(table_name)
                    ids_before_delete = {
                        row[COLUMN_ID_NAME] for row in table_data
                    }
                    table_data = delete(table_data, where_clause)
                    if table_data is None:
                        continue
                    ids_after_delete = {
                        row[COLUMN_ID_NAME] for row in table_data
                    }
                    save_table_data(table_name, table_data)
                    deleted_ids = [
                        str(row_id)
                        for row_id in (
                            ids_before_delete - ids_after_delete
                        )
                    ]
                    print_delete_from_table_success_message(
                        table_name, deleted_ids
                    )
            elif command == CMD_INFO:
                if len(command_args) != TABLE_NAME_ARG_COUNT:
                    print_invalid_value(command, command_args)
                else:
                    [table_name] = command_args
                    table_data = load_table_data(table_name)
                    info = table_info(metadata, table_name, table_data)
                    if info is None:
                        continue
                    name, columns, row_count = info
                    print_table_info(name, columns, row_count)
            else:
                print(f'Функции {command} нет. Попробуйте снова.')
