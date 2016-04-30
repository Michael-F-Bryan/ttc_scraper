import os
import errno
from . import logger


class BrowserError(RuntimeErroror):
    pass

class LoginError(BrowserError):
    pass


_suffixes = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
def humansize(nbytes, decimals=2):
    """
    Convert a number of bytes into it's human readable string using SI 
    suffixes.

    Note
    ----
    1 KB = 1024 bytes

    Parameters
    ----------
    nbytes: int
        The total number of bytes
    decimals: int
        The number of decimal places to round to

    Returns
    -------
    string
        The human readable size.

    """
    if nbytes == 0: return '0 B'
    i = 0
    while nbytes >= 1024 and i < len(_suffixes)-1:
        nbytes /= 1024.
        i += 1
    f = ('{}'.format(round(nbytes, decimals)))
    f = f.rstrip('0').rstrip('.')
    return '%s %s' % (f, _suffixes[i])


def mkdir(path):
    try:
        os.makedirs(path)
        logger.debug('Made directory: {}'.format(path))
    except OSError as e:
        if e.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise
        

def get_logger(name, log_file, log_level=None):
    """
    Get a logger object which is set up properly with the correct formatting,
    logfile, etc.

    Parameters
    ----------
    name: str
        The __name__ of the module calling this function.
    log_file: str
        The filename of the file to log to.

    Returns
    -------
    logging.Logger
        A logging.Logger object that can be used to log to a common file.
    """
    logger = logging.getLogger(name)
    logger.setLevel(log_level or logging.INFO)

    if log_file == 'stdout':
        handler = logging.StreamHandler(sys.stdout)
    else:
        handler = logging.FileHandler(log_file)

    if not len(logger.handlers):
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s: %(message)s',
            datefmt='%Y/%m/%d %I:%M:%S %p'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger

