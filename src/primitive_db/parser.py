import shlex


def tokenize(user_input):
    lexer = shlex.shlex(user_input, posix=True, punctuation_chars='(),=')
    lexer.whitespace_split = True
    return list(lexer)


def parse_value(value):
    if value.lower() in ('true', 'false'):
        return value.lower() == 'true'
    try:
        return int(value)
    except ValueError:
        return value

def parse_comma_separated_values(tokens):
    if not tokens:
        return []

    values = []
    expect_value = True
    for token in tokens:
        if expect_value:
            if token == ',':
                return None
            values.append(parse_value(token))
            expect_value = False
        else:
            if token != ',':
                return None
            expect_value = True

    if expect_value:
        return None
    return values


def parse_insert_args(args):
    if (
        len(args) < 4
        or args[0] != 'into'
        or args[2] != 'values'
        or args[3] != '('
        or args[-1] != ')'
    ):
        return None

    values = parse_comma_separated_values(args[4:-1])
    if values is None:
        return None
    return args[1], values


def parse_select_args(args):
    if len(args) < 2 or args[0] != 'from':
        return None

    table_name = args[1]
    if len(args) == 2:
        return table_name, None

    if len(args) == 6 and args[2] == 'where' and args[4] == '=':
        return table_name, {args[3]: parse_value(args[5])}

    return None


def parse_update_args(args):
    if (
        len(args) != 9
        or args[1] != 'set'
        or args[3] != '='
        or args[5] != 'where'
        or args[7] != '='
    ):
        return None

    set_clause = {args[2]: parse_value(args[4])}
    where_clause = {args[6]: parse_value(args[8])}
    return args[0], set_clause, where_clause


def parse_delete_args(args):
    if (
        len(args) != 6
        or args[0] != 'from'
        or args[2] != 'where'
        or args[4] != '='
    ):
        return None

    return args[1], {args[3]: parse_value(args[5])}
