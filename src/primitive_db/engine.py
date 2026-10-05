import prompt


def exit_command():
    quit()


def help_command():
    print('<command> exit - выйти из программы')
    print('<command> help - справочная информация')


commands = {
    'exit': exit_command,
    'help': help_command,
}


def intro():
    print('Первая попытка запустить проект!')
    print()
    print('***')


def welcome():
    intro()
    help_command()

    while True:
        command = prompt.string('Введите команду: ')
        if command == 'exit':
            exit_command()
        elif command in commands:
            print()
            commands[command]()
