import psutil
import time
import os
from contextlib import contextmanager


def format_secs(secs, decimal=1) -> str:
    """Get formatted literal string for a time duration.

    Parameters
    ----------
    secs: int | float
        Number of seconds in the time duration.

    decimal: int
        Number of decimal places to round to in the literal string.

    Returns
    -------
    ret: string
        Formatted literal string for the time duration.

    Examples
    --------
    >>> format_secs(100)
    '1.7 minutes'

    >>> format_secs(10000)
    '2.8 hours'

    >>> format_secs(10000, 2)
    '2.78 hours'
    """
    assert isinstance(secs, int) or isinstance(secs, float)
    assert isinstance(decimal, int)
    if secs <= 60:
        ret = "{} seconds".format(round(secs, decimal))
    elif secs <= 60 * 60:
        ret = "{} minutes".format(round(secs/60.0, decimal))
    elif secs <= 60 * 60 * 24:
        ret = "{} hours".format(round(secs/(60 * 60), decimal))
    else:
        ret = "{} days".format(round(secs/(60 * 60 * 24), decimal))
    return ret


def _format_memory(num_units, decimal=2, units=None) -> str:
    """Helper function to format a memory size"""
    assert num_units >= 0
    assert isinstance(num_units, int) or isinstance(num_units, float)
    assert isinstance(decimal, int)
    units = ['B', 'KB', 'MB', 'GB', "TB"] if units is None else units
    if num_units < 1024 or len(units) == 1:
        ret = "{}{}".format(round(num_units, decimal), units[0])
    else:
        ret = _format_memory(num_units / 1024.0, decimal, units[1:])
    return ret


def format_memory(num_bytes, decimal=2):
    """Get formatted literal string for a memory size.

    Parameters
    ----------
    num_bytes: int
        Number of bytes

    decimal: int
        Number of decimal places to round to in the literal string.

    Returns
    -------
    ret: string
        Formatted literal string for the memory size.

    Examples
    --------
    >>> format_memory(10**5)
    '97.66KB'

    >>> format_memory(10**10, 1)
    '9.3GB'

    >>> format_memory(10**20)
    '90949470.18TB'
    """
    return _format_memory(num_units=num_bytes, decimal=decimal)


def format_memory_diff(num_bytes) -> str:
    """Get formatted literal string for a difference in memory size.

    Parameters
    ----------
    num_bytes: int
        Number of bytes in the memory difference.

    Returns
    -------
    ret: string
        Formatted literal string for the memory difference.

    Examples
    --------
    >>> format_memory_diff(2**24)
    '+16.0MB'

    >>> format_memory_diff(-2**28)
    '-256.0MB'
    """
    assert isinstance(num_bytes, int)
    sign = '+' if num_bytes >= 0 else '-'
    ret = "{}{}".format(sign, format_memory(abs(num_bytes)))
    return ret


def get_memory_bytes() -> int:
    """Get the memory usage in bytes of the current process."""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss


def get_memory_str() -> str:
    """Get formatted literal string for the memory usage of the current process."""
    return format_memory(get_memory_bytes())


def get_time_str(verbose_level="hour"):
    if verbose_level == "hour":
        return time.strftime("%H:%M:%S", time.gmtime())
    elif verbose_level == "day":
        return time.strftime("%b %d %H:%M:%S", time.gmtime())
    else:
        return None  # use raise ValueError instead later


@contextmanager
def profiler(task_name, moment_level="hour", verbose_memory=True, verbose_duration=True):
    t0 = time.time()
    m0 = get_memory_bytes()
    yield
    t_delta = time.time() - t0
    m_delta = get_memory_bytes() - m0

    msg = ""
    if moment_level is not None:
        msg += "[{}] ".format(get_time_str(moment_level))

    msg += "Finish {}.".format(task_name)
    if verbose_memory:
        msg += " △M: {}.".format(format_memory_diff(m_delta))
    if verbose_duration:
        msg += " △T: {}.".format(format_secs(t_delta))
    print(msg)
