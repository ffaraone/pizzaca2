# -*- coding: utf-8 -*-
VERSION = (1, 0, 2)

__version__ = '.'.join([str(n) for n in VERSION])
__version_info__ = tuple([int(num) if num.isdigit() else num for num in __version__.replace('-', '.', 1).split('.')])


def get_version():
    return __version__
