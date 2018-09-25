class UnoLogger(object):
    def __init__(self, prefix):
        assert isinstance(prefix, str) and len(prefix) > 0
        self.prefix = prefix

    def __call__(self, string):
        print("{} {}".format(self.prefix, string))
