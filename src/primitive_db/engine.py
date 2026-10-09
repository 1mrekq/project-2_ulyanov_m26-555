import json

import prompt
from prettytable import PrettyTable

from primitive_db.core import (
    CreateTableException,
    DeleteFromTableException,
    DropTableException,
    InsertIntoTableException,
    SelectFromTableException,
    UpdateTableException,
    create_table,
    delete,
    drop_table,
    insert,
    list_tables,
    select,
    table_info,
    update,
)
from primitive_db.parser import (
    parse_delete_args,
    parse_insert_args,
    parse_select_args,
    parse_update_args,
    tokenize,
)
from primitive_db.utils import (
    create_cacher,
    delete_table_data,
    load_metadata,
    load_table_data,
    save_metadata,
    save_table_data,
)

METADATA_FILE = 'db_meta.json'
cache_result = create_cacher()

def print_create_table_success_message(table_name, table_metadata):
    columns_str = ', '.join([f'{k}:{v}' for k, v in table_metadata.items()])
    print(f'Таблица "{table_name}" успешно создана со столбцами: {columns_str}')

def print_drop_table_success_message(table_name):
    print(f'Таблица "{table_name}" успешно удалена.')

def print_insert_into_table_success_message(table_name, data):
    print(f'Запись с ID={data[-1]["ID"]} успешно добавлена в таблицу "{table_name}".')

def print_update_table_success_message(table_name, updated_ids):
    if len(updated_ids) == 1:
        print(
            f'Запись с ID={updated_ids[0]} в таблице "{table_name}" '
            f'успешно обновлена.'
        )
    elif len(updated_ids) > 1:
        ids = ','.join(updated_ids)
        print(
            f'Записи с ID={ids} в таблице "{table_name}" успешно обновлены.'
        )

def print_delete_from_table_success_message(table_name, deleted_ids):
    if len(deleted_ids) == 1:
        print(
            f'Запись с ID={deleted_ids[0]} успешно удалена из таблицы '
            f'"{table_name}".'
        )
    elif len(deleted_ids) > 1:
        ids = ','.join(deleted_ids)
        print(
            f'Записи с ID={ids} успешно удалены из таблицы "{table_name}".'
        )

def print_error_message(error_message):
    print(f'Ошибка: {error_message}')

def print_invalid_value(command, command_args):
    value = ' '.join(command_args) if command_args else command
    print(f'Некорректное значение: {value}. Попробуйте снова.')

def print_rows(rows, columns):
    table = PrettyTable()
    table.field_names = list(columns.keys())
    for row in rows:
        table.add_row([row.get(column) for column in table.field_names])
    print(table)

def exit_command(*args, **kwargs):
    quit()

def help_command(*args, **kwargs):
    print("***Процесс работы с таблицей***")
    print("Функции:")
    print(
        "<command> create_table <имя_таблицы> <столбец1:тип> "
        "<столбец2:тип> .. - создать таблицу"
    )
    print("<command> list_tables - показать список всех таблиц")
    print("<command> drop_table <имя_таблицы> - удалить таблицу")
    print("<command> exit - выход из программы")
    print("<command> help - справочная информация")
    print()
    print("***Операции с данными***")
    print()
    print("Функции:")
    print(
        "<command> insert into <имя_таблицы> values "
        "(<значение1>, <значение2>, ...) - создать запись."
    )
    print(
        "<command> select from <имя_таблицы> where <столбец> = <значение> "
        "- прочитать записи по условию."
    )
    print("<command> select from <имя_таблицы> - прочитать все записи.")
    print(
        "<command> update <имя_таблицы> set <столбец1> = <новое_значение1> "
        "where <столбец_условия> = <значение_условия> - обновить запись."
    )
    print(
        "<command> delete from <имя_таблицы> where <столбец> = <значение> "
        "- удалить запись."
    )
    print("<command> info <имя_таблицы> - вывести информацию о таблице.")
    print("<command> exit - выход из программы")
    print("<command> help - справочная информация")


def run():
    help_command()

    while True:
        user_input = prompt.string('Введите команду: ')
        try:
            args = tokenize(user_input)
        except ValueError:
            print_invalid_value(user_input, [])
            continue

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
                                metadata = create_table(
                                    metadata, table_name, columns
                                )
                                if metadata is None:
                                    continue
                                save_metadata(METADATA_FILE, metadata)
                                save_table_data(table_name, [])
                                print_create_table_success_message(
                                    table_name, metadata[table_name]
                                )
                    case 'drop_table':
                        if len(command_args) != 1:
                            print_invalid_value(command, command_args)
                        else:
                            table_name = command_args[0]
                            metadata = drop_table(metadata, table_name)
                            if metadata is None:
                                continue
                            save_metadata(METADATA_FILE, metadata)
                            delete_table_data(table_name)
                            print_drop_table_success_message(table_name)
                    case 'list_tables':
                        if command_args:
                            print_invalid_value(command, command_args)
                        else:
                            list_tables(metadata)
                    case 'insert':
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
                    case 'select':
                        parsed = parse_select_args(command_args)
                        if parsed is None:
                            print_invalid_value(command, command_args)
                        else:
                            table_name, where_clause = parsed
                            if table_name not in metadata:
                                raise SelectFromTableException(
                                    f'Таблица "{table_name}" не существует.'
                                )
                            table_data = load_table_data(table_name)
                            cache_key = json.dumps(
                                {
                                    'table': table_name,
                                    'where': where_clause,
                                    'data': table_data,
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
                    case 'update':
                        parsed = parse_update_args(command_args)
                        if parsed is None:
                            print_invalid_value(command, command_args)
                        else:
                            table_name, set_clause, where_clause = parsed
                            if table_name not in metadata:
                                raise UpdateTableException(
                                    f'Таблица "{table_name}" не существует.'
                                )
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
                            updated_ids = [str(row_id) for row_id in updated_ids]
                            print_update_table_success_message(
                                table_name, updated_ids
                            )
                    case 'delete':
                        parsed = parse_delete_args(command_args)
                        if parsed is None:
                            print_invalid_value(command, command_args)
                        else:
                            table_name, where_clause = parsed
                            if table_name not in metadata:
                                raise DeleteFromTableException(
                                    f'Таблица "{table_name}" не существует.'
                                )
                            table_data = load_table_data(table_name)
                            ids_before_delete = set([row['ID'] for row in table_data])
                            table_data = delete(table_data, where_clause)
                            if table_data is None:
                                continue
                            ids_after_delete = set([row['ID'] for row in table_data])
                            save_table_data(table_name, table_data)
                            deleted_ids = [
                                str(row_id)
                                for row_id in ids_before_delete - ids_after_delete
                            ]
                            print_delete_from_table_success_message(
                                table_name, deleted_ids
                            )
                    case 'info':
                        if len(command_args) != 1:
                            print_invalid_value(command, command_args)
                        else:
                            table_name = command_args[0]
                            table_data = load_table_data(table_name)
                            table_info(metadata, table_name, table_data)
                    case _:
                        print(f'Функции {command} нет. Попробуйте снова.')
            except (
                CreateTableException,
                DropTableException,
                InsertIntoTableException,
                SelectFromTableException,
                UpdateTableException,
                DeleteFromTableException,
            ) as e:
                print_error_message(e)
