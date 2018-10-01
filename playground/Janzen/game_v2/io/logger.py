import logging
from colorama import init, Fore, Style


init()


class UnoLogger(logging.Logger):
    def __init__(self, name, color, stream=True, filename=None):
        assert isinstance(name, str) and len(name) > 0
        super().__init__(name, logging.INFO)
        self.color = color

        formatter = logging.Formatter("{}[%(name)s]{} %(message)s".format(self.color, Style.RESET_ALL))

        if stream:
            sh = logging.StreamHandler()
            sh.setFormatter(formatter)
            sh.setLevel(logging.INFO)
            self.addHandler(sh)

        if filename is not None:
            fh = logging.FileHandler(filename)
            fh.setFormatter(formatter)
            fh.setLevel(logging.INFO)
            self.addHandler(fh)

    def __call__(self, string, *args, **kwargs):
        self.info(string, *args, **kwargs)
