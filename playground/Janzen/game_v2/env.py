from .controller import EnvV1Controller


def make_env(version, stream=False, filename=None):
    if version == 1:
        return EnvV1Controller(stream, filename)
    else:
        raise Exception("Unknown version: {}".format(version))
