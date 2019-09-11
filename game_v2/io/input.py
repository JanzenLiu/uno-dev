def get_input(msg, err, parser=None, checker=None, constructor=None):
    assert isinstance(msg, str)
    assert isinstance(err, str)
    assert parser is None or callable(parser)
    assert checker is None or callable(checker)
    assert constructor is None or callable(constructor)

    while True:
        try:
            print(msg)
            inp = input()
            if parser is not None:
                inp = parser(inp)
            if checker is None or checker(inp):
                break
            else:
                print(err)
        except ValueError:
            print(err)

    if constructor is not None:
        inp = constructor(inp)
    return inp
