from .controller import EnvV1Controller
from .controller import EnvV6Controller


def make_env(version, stream=False, filename=None):
    if version == 1:
        return EnvV1Controller(stream, filename)
    elif version == 6:
        return EnvV6Controller(stream, filename)
    else:
        raise Exception("Unknown version: {}".format(version))
