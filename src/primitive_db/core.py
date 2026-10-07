INT = 'int'
STR = 'str'
BOOL = 'bool'
ALLOWED_COLUMNS_TYPES = {'int', 'str', 'bool'}

class CreateTableException(BaseException):
    def __init__(self, *args):
        super().__init__(*args)

class DropTableException(BaseException):
    def __init__(self, *args):
        super().__init__(*args)

def create_table(metadata, table_name, columns):
    if table_name in metadata:
        raise CreateTableException(f'Таблица "{table_name}" уже существует.')

    created_columns = dict(column.split(':') for column in columns)
    for c, t in created_columns.items():
        if t not in ALLOWED_COLUMNS_TYPES:
            raise CreateTableException(f'В таблице {table_name} используется некорректный тип {t} для столбца {c}')

    if 'ID' not in created_columns:
        created_columns = {'ID': 'int', **created_columns}
    updated_meta = {**metadata, **{table_name: created_columns}}

    return updated_meta

def drop_table(metadata, table_name):
    if table_name not in metadata:
        raise DropTableException(f'Таблица "{table_name}" не существует.')

    updated_meta = {k: v for k, v in metadata.items() if k != table_name}

    return updated_meta

def list_tables(metadata):
    if len(metadata) == 0:
        print('Нет таблиц для отображения.')
        return

    for k in metadata.keys():
        print(f'- {k}')
