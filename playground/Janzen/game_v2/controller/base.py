from ..io import UnoLogger
from colorama import init
from colorama import Fore, Back, Style


init()


class Controller(object):
    def __init__(self):
        self.logger = UnoLogger(name=type(self).__name__, color=Fore.LIGHTCYAN_EX)

    def __repr__(self):
        return "{}({})".format(type(self).__name__, self.format_attribute())

    def __str__(self):
        return "{}({})".format(type(self).__name__, self.format_attribute())

    def format_attribute(self):
        raise NotImplementedError
