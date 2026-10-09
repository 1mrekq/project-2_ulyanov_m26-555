import shlex

from primitive_db.constants import (
    DELETE_TOKEN_COUNT,
    FALSE_LITERAL,
    FROM_CLAUSE_LENGTH,
    INSERT_PREFIX_LENGTH,
    KW_FROM,
    KW_INTO,
    KW_SET,
    KW_VALUES,
    KW_WHERE,
    PUNCTUATION_CHARS,
    TOKEN_CLOSE_PAREN,
    TOKEN_COMMA,
    TOKEN_EQUALS,
    TOKEN_OPEN_PAREN,
    TRUE_LITERAL,
    UPDATE_TOKEN_COUNT,
    VALUES_WRAPPER_LENGTH,
    WHERE_CLAUSE_LENGTH,
)


def tokenize(user_input):
    """Разбивает строку команды на токены с учётом кавычек и скобок."""
    lexer = shlex.shlex(
        user_input, posix=True, punctuation_chars=PUNCTUATION_CHARS
    )
    lexer.whitespace_split = True
    return list(lexer)


def parse_value(value):
    """Преобразует строковый литерал в bool, int или оставляет строкой."""
    normalized = value.lower()
    if normalized == TRUE_LITERAL:
        return True
    if normalized == FALSE_LITERAL:
        return False
    try:
        return int(value)
    except ValueError:
        return value


def parse_comma_separated_values(tokens):
    """Разбирает список значений, разделённых запятыми."""
    if not tokens:
        return []

    values = []
    expect_value = True
    for token in tokens:
        if expect_value:
            if token == TOKEN_COMMA:
                return None
            values.append(parse_value(token))
            expect_value = False
        else:
            if token != TOKEN_COMMA:
                return None
            expect_value = True

    if expect_value:
        return None
    return values


def parse_insert_args(args):
    """Разбирает аргументы команды insert into ... values (...)."""
    if len(args) < INSERT_PREFIX_LENGTH:
        return None

    keyword_into, table_name, keyword_values, *tail = args
    if keyword_into != KW_INTO or keyword_values != KW_VALUES:
        return None
    if len(tail) < VALUES_WRAPPER_LENGTH:
        return None

    open_paren, *raw_values, close_paren = tail
    if open_paren != TOKEN_OPEN_PAREN or close_paren != TOKEN_CLOSE_PAREN:
        return None

    values = parse_comma_separated_values(raw_values)
    if values is None:
        return None
    return table_name, values


def parse_select_args(args):
    """Разбирает аргументы команды select from ... [where ...]."""
    if len(args) < FROM_CLAUSE_LENGTH:
        return None

    keyword_from, table_name, *tail = args
    if keyword_from != KW_FROM:
        return None
    if not tail:
        return table_name, None
    if len(tail) != WHERE_CLAUSE_LENGTH:
        return None

    keyword_where, column, equals, raw_value = tail
    if keyword_where != KW_WHERE or equals != TOKEN_EQUALS:
        return None
    return table_name, {column: parse_value(raw_value)}


def parse_update_args(args):
    """Разбирает аргументы команды update ... set ... where ...."""
    if len(args) != UPDATE_TOKEN_COUNT:
        return None

    (
        table_name,
        keyword_set,
        set_column,
        set_equals,
        set_raw,
        keyword_where,
        where_column,
        where_equals,
        where_raw,
    ) = args
    if (
        keyword_set != KW_SET
        or set_equals != TOKEN_EQUALS
        or keyword_where != KW_WHERE
        or where_equals != TOKEN_EQUALS
    ):
        return None

    return (
        table_name,
        {set_column: parse_value(set_raw)},
        {where_column: parse_value(where_raw)},
    )


def parse_delete_args(args):
    """Разбирает аргументы команды delete from ... where ...."""
    if len(args) != DELETE_TOKEN_COUNT:
        return None

    (
        keyword_from,
        table_name,
        keyword_where,
        column,
        equals,
        raw_value,
    ) = args
    if (
        keyword_from != KW_FROM
        or keyword_where != KW_WHERE
        or equals != TOKEN_EQUALS
    ):
        return None

    return table_name, {column: parse_value(raw_value)}
