# ruff: noqa: E501
import io
import os
import re
import tempfile
import unittest
from unittest.mock import patch

from primitive_db.engine import run

PROMPT = 'Введите команду: '
CONFIRM_DROP = 'Вы уверены, что хотите выполнить "удаление таблицы"? [y/n]:'
CONFIRM_DELETE = (
    'Вы уверены, что хотите выполнить "удаление данных из таблицы"? [y/n]:'
)
LOG_TIME_RE = re.compile(
    r'Функция (insert|select) выполнилась за \d+\.\d{3} секунд\.?'
)

HELP = """\
***Процесс работы с таблицей***
Функции:
<command> create_table <имя_таблицы> <столбец1:тип> <столбец2:тип> .. - создать таблицу
<command> list_tables - показать список всех таблиц
<command> drop_table <имя_таблицы> - удалить таблицу
<command> exit - выход из программы
<command> help - справочная информация

***Операции с данными***

Функции:
<command> insert into <имя_таблицы> values (<значение1>, <значение2>, ...) - создать запись.
<command> select from <имя_таблицы> where <столбец> = <значение> - прочитать записи по условию.
<command> select from <имя_таблицы> - прочитать все записи.
<command> update <имя_таблицы> set <столбец1> = <новое_значение1> where <столбец_условия> = <значение_условия> - обновить запись.
<command> delete from <имя_таблицы> where <столбец> = <значение> - удалить запись.
<command> info <имя_таблицы> - вывести информацию о таблице.
<command> exit - выход из программы
<command> help - справочная информация
"""

SELECT_RESULT = """\
+----+--------+-----+-----------+
| ID |  name  | age | is_active |
+----+--------+-----+-----------+
| 1  | Sergei |  28 |    True   |
+----+--------+-----+-----------+
"""

CREATE_USERS_ERROR = 'Ошибка: Таблица или столбец users не найден.'
DROP_PRODUCTS_ERROR = 'Ошибка: Таблица или столбец products не найден.'


def expected_session(steps):
    parts = [HELP.rstrip('\n')]
    for command, responses in steps:
        parts.append(f'{PROMPT}{command}')
        for response in responses:
            parts.append(response.rstrip('\n'))
    return '\n'.join(parts) + '\n'


def normalize_log_time(text):
    return LOG_TIME_RE.sub(
        r'Функция \1 выполнилась за 0.000 секунд.',
        text,
    )


def run_session(commands, *, confirms=None, cwd):
    if not commands or commands[-1] != 'exit':
        commands = [*commands, 'exit']

    command_iter = iter(commands)
    confirm_iter = iter(confirms or [])
    stdout = io.StringIO()
    previous_cwd = os.getcwd()
    os.chdir(cwd)
    try:
        def fake_input(prompt=''):
            stdout.write(prompt)
            stdout.flush()
            if prompt.startswith('Вы уверены'):
                try:
                    answer = next(confirm_iter)
                except StopIteration:
                    answer = 'n'
            else:
                try:
                    answer = next(command_iter)
                except StopIteration:
                    answer = 'exit'
            stdout.write(f'{answer}\n')
            stdout.flush()
            return answer

        with patch('builtins.input', side_effect=fake_input), patch(
            'sys.stdout', stdout
        ):
            try:
                run()
            except SystemExit:
                pass
    finally:
        os.chdir(previous_cwd)

    text = stdout.getvalue()
    if text.endswith(f'{PROMPT}exit\n'):
        text = text[: -len(f'{PROMPT}exit\n')]
    elif text.endswith(f'{PROMPT}exit'):
        text = text[: -len(f'{PROMPT}exit')]
    if not text.endswith('\n'):
        text += '\n'
    return normalize_log_time(text)


class DatabaseCliE2ETest(unittest.TestCase):
    maxDiff = None

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.cwd = self._tmp.name

    def tearDown(self):
        self._tmp.cleanup()

    def test_table_commands_match_example(self):
        steps = [
            (
                'create_table users name:str age:int is_active:bool',
                [
                    (
                        'Таблица "users" успешно создана со столбцами: '
                        'ID:int, name:str, age:int, is_active:bool'
                    ),
                ],
            ),
            (
                'create_table users name:str',
                [CREATE_USERS_ERROR],
            ),
            ('list_tables', ['- users']),
            (
                'drop_table users',
                [
                    f'{CONFIRM_DROP}y',
                    'Таблица "users" успешно удалена.',
                ],
            ),
            (
                'drop_table products',
                [
                    f'{CONFIRM_DROP}y',
                    DROP_PRODUCTS_ERROR,
                ],
            ),
            ('help', [HELP]),
        ]
        actual = run_session(
            [command for command, _ in steps],
            confirms=['y', 'y'],
            cwd=self.cwd,
        )
        self.assertEqual(actual, expected_session(steps))

    def test_drop_table_can_be_cancelled(self):
        run_session(
            ['create_table users name:str age:int is_active:bool'],
            cwd=self.cwd,
        )
        steps = [
            (
                'drop_table users',
                [
                    f'{CONFIRM_DROP}n',
                    'Действие отменено.',
                ],
            ),
            ('list_tables', ['- users']),
        ]
        actual = run_session(
            [command for command, _ in steps],
            confirms=['n'],
            cwd=self.cwd,
        )
        self.assertEqual(actual, expected_session(steps))

    def test_data_commands_match_example(self):
        run_session(
            ['create_table users name:str age:int is_active:bool'],
            cwd=self.cwd,
        )
        steps = [
            (
                'insert into users values ("Sergei", 28, true)',
                [
                    'Функция insert выполнилась за 0.000 секунд.',
                    'Запись с ID=1 успешно добавлена в таблицу "users".',
                ],
            ),
            (
                'select from users where age = 28',
                [
                    'Функция select выполнилась за 0.000 секунд.',
                    SELECT_RESULT,
                ],
            ),
            (
                'update users set age = 29 where name = "Sergei"',
                ['Запись с ID=1 в таблице "users" успешно обновлена.'],
            ),
            (
                'delete from users where ID = 1',
                [
                    f'{CONFIRM_DELETE}y',
                    'Запись с ID=1 успешно удалена из таблицы "users".',
                ],
            ),
            (
                'info users',
                [
                    'Таблица: users\n'
                    'Столбцы: ID:int, name:str, age:int, is_active:bool\n'
                    'Количество записей: 0'
                ],
            ),
        ]
        actual = run_session(
            [command for command, _ in steps],
            confirms=['y'],
            cwd=self.cwd,
        )
        self.assertEqual(actual, expected_session(steps))


if __name__ == '__main__':
    unittest.main()
