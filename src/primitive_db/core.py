from primitive_db.constants import (
    BOOL,
    COLUMN_ID_NAME,
    COLUMN_SEPARATOR,
    DELETE_DATA_ACTION,
    DROP_TABLE_ACTION,
    EMPTY_TABLE_MAX_ID,
    ID_INCREMENT,
    INT,
    STR,
    VALID_TYPES,
)
from primitive_db.decorators import confirm_action, handle_db_errors, log_time

TYPE_CHECKERS = {
    INT: lambda value: isinstance(value, int) and not isinstance(value, bool),
    STR: lambda value: isinstance(value, str),
    BOOL: lambda value: isinstance(value, bool),
}


@handle_db_errors
def create_table(metadata, table_name, columns):
    """Создаёт таблицу в метаданных и возвращает обновлённые метаданные."""
    if table_name in metadata:
        raise KeyError(table_name)

    created_columns = dict(
        column.split(COLUMN_SEPARATOR) for column in columns
    )
    for column_name, column_type in created_columns.items():
        if column_type not in VALID_TYPES:
            raise ValueError(
                f'В таблице {table_name} используется некорректный тип '
                f'{column_type} для столбца {column_name}'
            )

    if COLUMN_ID_NAME not in created_columns:
        created_columns = {COLUMN_ID_NAME: INT, **created_columns}
    return {**metadata, table_name: created_columns}


@confirm_action(DROP_TABLE_ACTION)
@handle_db_errors
def drop_table(metadata, table_name):
    """Удаляет таблицу из метаданных и возвращает обновлённые метаданные."""
    if table_name not in metadata:
        raise KeyError(table_name)

    return {key: value for key, value in metadata.items() if key != table_name}


def list_tables(metadata):
    """Возвращает список имён таблиц из метаданных."""
    return list(metadata.keys())


def _matches_type(value, column_type):
    """Проверяет, соответствует ли значение ожидаемому типу столбца."""
    checker = TYPE_CHECKERS.get(column_type)
    return checker is not None and checker(value)


@handle_db_errors
@log_time
def insert(metadata, table_name, table_data, values):
    """Добавляет запись в таблицу и возвращает обновлённые данные."""
    if table_name not in metadata:
        raise KeyError(table_name)

    columns = metadata[table_name]
    column_names = [name for name in columns if name != COLUMN_ID_NAME]

    if len(values) != len(column_names):
        raise ValueError(
            f'Количество значений не соответствует количеству столбцов '
            f'в таблице "{table_name}".'
        )

    row_values = {}
    for column_name, value in zip(column_names, values):
        expected_type = columns[column_name]
        if not _matches_type(value, expected_type):
            raise ValueError(
                f'Значение "{value}" не соответствует типу "{expected_type}" '
                f'в столбце "{column_name}".'
            )
        row_values[column_name] = value

    new_id = max(
        (row[COLUMN_ID_NAME] for row in table_data),
        default=EMPTY_TABLE_MAX_ID,
    ) + ID_INCREMENT
    new_row = {COLUMN_ID_NAME: new_id, **row_values}
    return table_data + [new_row]


@handle_db_errors
@log_time
def select(table_data, where_clause=None):
    """Возвращает записи таблицы, опционально отфильтрованные по where."""
    if where_clause:
        key, value = next(iter(where_clause.items()))
        return [row for row in table_data if row.get(key) == value]
    return list(table_data)


@handle_db_errors
def update(metadata, table_name, table_data, set_clause, where_clause):
    """Обновляет записи по условию и возвращает данные с ID изменений."""
    columns = metadata[table_name]
    for column_name, value in set_clause.items():
        if column_name not in columns:
            raise KeyError(column_name)
        expected_type = columns[column_name]
        if not _matches_type(value, expected_type):
            raise ValueError(
                f'Значение "{value}" не соответствует типу "{expected_type}" '
                f'в столбце "{column_name}".'
            )

    where_key, where_value = next(iter(where_clause.items()))
    updated_ids = []
    for row in table_data:
        if row.get(where_key) == where_value:
            for key, value in set_clause.items():
                row[key] = value
            updated_ids.append(row[COLUMN_ID_NAME])
    return table_data, updated_ids


@confirm_action(DELETE_DATA_ACTION)
@handle_db_errors
def delete(table_data, where_clause):
    """Удаляет записи по условию и возвращает оставшиеся данные."""
    where_key, where_value = next(iter(where_clause.items()))
    return [row for row in table_data if row.get(where_key) != where_value]


@handle_db_errors
def table_info(metadata, table_name, table_data):
    """Возвращает имя таблицы, столбцы и количество записей."""
    if table_name not in metadata:
        raise KeyError(table_name)

    columns = metadata[table_name]
    return table_name, columns, len(table_data)
