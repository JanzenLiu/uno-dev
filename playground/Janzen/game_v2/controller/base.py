from ..io import UnoLogger
from colorama import init
from colorama import Fore, Back, Style


init()


class Controller(object):
    def __init__(self, stream=True, filename=None):
        assert isinstance(stream, bool)
        assert filename is None or isinstance(filename, str)
        self.stream = stream
        self.filename = filename
        self.logger = UnoLogger(name=type(self).__name__,
                                color=Fore.LIGHTCYAN_EX,
                                stream=stream,
                                filename=filename)

    def __repr__(self):
        return "{}({})".format(type(self).__name__, self.format_attribute())

    def __str__(self):
        return "{}({})".format(type(self).__name__, self.format_attribute())

    def format_attribute(self):
        raise NotImplementedError
