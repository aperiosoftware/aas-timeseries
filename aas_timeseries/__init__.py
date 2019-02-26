# Licensed under a 3-clause BSD style license - see LICENSE.rst

from pkg_resources import get_distribution, DistributionNotFound

__all__ = ['InteractiveTimeSeriesFigure']

try:
    __version__ = get_distribution(__name__).version
except DistributionNotFound:
    # package is not installed
    pass

from .visualization import InteractiveTimeSeriesFigure
