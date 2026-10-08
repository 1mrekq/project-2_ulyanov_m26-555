INT = 'int'
STR = 'str'
BOOL = 'bool'
ALLOWED_COLUMNS_TYPES = {INT, STR, BOOL}
COLUMN_ID_NAME = 'ID'
TYPE_CHECKERS = {
    INT: lambda value: isinstance(value, int) and not isinstance(value, bool),
    STR: lambda value: isinstance(value, str),
    BOOL: lambda value: isinstance(value, bool),
}


class CreateTableException(BaseException):
    def __init__(self, *args):
        super().__init__(*args)


class DropTableException(BaseException):
    def __init__(self, *args):
        super().__init__(*args)


class InsertIntoTableException(BaseException):
    def __init__(self, *args):
        super().__init__(*args)


class SelectFromTableException(BaseException):
    def __init__(self, *args):
        super().__init__(*args)


class UpdateTableException(BaseException):
    def __init__(self, *args):
        super().__init__(*args)


class DeleteFromTableException(BaseException):
    def __init__(self, *args):
        super().__init__(*args)


def create_table(metadata, table_name, columns):
    if table_name in metadata:
        raise CreateTableException(f'Таблица "{table_name}" уже существует.')

    created_columns = dict(column.split(':') for column in columns)
    for column_name, column_type in created_columns.items():
        if column_type not in ALLOWED_COLUMNS_TYPES:
            raise CreateTableException(
                f'В таблице {table_name} используется некорректный тип '
                f'{column_type} для столбца {column_name}'
            )

    if COLUMN_ID_NAME not in created_columns:
        created_columns = {COLUMN_ID_NAME: INT, **created_columns}
    return {**metadata, table_name: created_columns}


def drop_table(metadata, table_name):
    if table_name not in metadata:
        raise DropTableException(f'Таблица "{table_name}" не существует.')

    return {key: value for key, value in metadata.items() if key != table_name}


def list_tables(metadata):
    if len(metadata) == 0:
        print('Нет таблиц для отображения.')
        return

    for table_name in metadata.keys():
        print(f'- {table_name}')


def _matches_type(value, column_type):
    checker = TYPE_CHECKERS.get(column_type)
    return checker is not None and checker(value)


def insert(metadata, table_name, table_data, values):
    if table_name not in metadata:
        raise InsertIntoTableException(f'Таблица "{table_name}" не существует.')

    columns = metadata[table_name]
    column_names = [name for name in columns if name != COLUMN_ID_NAME]

    if len(values) != len(column_names):
        raise InsertIntoTableException(
            f'Количество значений не соответствует количеству столбцов '
            f'в таблице "{table_name}".'
        )

    row_values = {}
    for column_name, value in zip(column_names, values):
        expected_type = columns[column_name]
        if not _matches_type(value, expected_type):
            raise InsertIntoTableException(
                f'Значение "{value}" не соответствует типу "{expected_type}" '
                f'в столбце "{column_name}".'
            )
        row_values[column_name] = value

    new_id = max(
        (row[COLUMN_ID_NAME] for row in table_data),
        default=0,
    ) + 1
    new_row = {COLUMN_ID_NAME: new_id, **row_values}
    return table_data + [new_row]


def select(table_data, where_clause=None):
    if where_clause:
        key, value = next(iter(where_clause.items()))
        return [row for row in table_data if row.get(key) == value]
    return list(table_data)


def update(metadata, table_name, table_data, set_clause, where_clause):
    columns = metadata[table_name]
    for column_name, value in set_clause.items():
        if column_name not in columns:
            raise UpdateTableException(
                f'Столбец "{column_name}" не существует в таблице "{table_name}".'
            )
        expected_type = columns[column_name]
        if not _matches_type(value, expected_type):
            raise UpdateTableException(
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


def delete(table_data, where_clause):
    where_key, where_value = next(iter(where_clause.items()))
    return [row for row in table_data if row.get(where_key) != where_value]


def table_info(metadata, table_name, table_data):
    if table_name not in metadata:
        raise SelectFromTableException(f'Таблица "{table_name}" не существует.')

    columns = metadata[table_name]
    columns_str = ', '.join(
        f'{name}:{column_type}' for name, column_type in columns.items()
    )
    print(f'Таблица: {table_name}')
    print(f'Столбцы: {columns_str}')
    print(f'Количество записей: {len(table_data)}')
