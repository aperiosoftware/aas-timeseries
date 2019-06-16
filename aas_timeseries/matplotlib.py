from fractions import Fraction
import numpy as np
from matplotlib.ticker import MaxNLocator, StrMethodFormatter, Formatter

__all__ = ['PhaseAsDegreesLocator', 'PhaseAsDegreesFormatter',
           'PhaseAsRadiansLocator', 'PhaseAsRadiansFormatter']


class PhaseAsDegreesLocator(MaxNLocator):
    """
    Matplotlib locator for phases in the range [0:1] as degrees.
    """

    def __init__(self, *args, **kwargs):
        kwargs['nbins'] = 6
        super().__init__(*args, **kwargs)

    def tick_values(self, vmin, vmax):
        values = super().tick_values(vmin * 360, vmax * 360) / 360.
        return values[(values >= vmin) & (values <= vmax)]

    def __call__(self):
        vmin, vmax = self.axis.get_view_interval()
        return self.tick_values(vmin, vmax)


class PhaseAsDegreesFormatter(StrMethodFormatter):
    """
    Matplotlib formatter for phases in the range [0:1] as degrees.
    """

    def __init__(self):
        return super().__init__('{x:g}\xb0')

    def __call__(self, value, pos=None):
        return super().__call__(value * 360, pos=pos)


class PhaseAsRadiansLocator(MaxNLocator):
    """
    Matplotlib locator for phases in the range [0:1] as radians.
    """

    def tick_values(self, vmin, vmax):
        if vmax - vmin > 2.:
            values = super().tick_values(vmin, vmax)
        else:
            power = np.ceil(-np.log2((vmax - vmin) / 3))
            imin = np.floor(vmin / 2**-power)
            imax = np.ceil(vmax / 2**-power)
            values = np.arange(imin, imax + 1) * 2 ** -power
        return values[(values >= vmin) & (values <= vmax)]

    def __call__(self):
        vmin, vmax = self.axis.get_view_interval()
        return self.tick_values(vmin, vmax)


class PhaseAsRadiansFormatter(Formatter):
    """
    Matplotlib formatter for phases in the range [0:1] as radians.
    """

    def __call__(self, value, pos=None):
        value = 2 * value
        fraction = Fraction(value).limit_denominator(1000000)
        top, bot = fraction.numerator, fraction.denominator
        if top < 100 and bot < 100:
            if top == 0:
                return '0'
            elif top == 1 and bot == 1:
                return '\u03c0'
            elif top == -1 and bot == 1:
                return '-\u03c0'
            elif top == 1:
                return '\u03c0/{0}'.format(bot)
            elif top == -1:
                return '-\u03c0/{0}'.format(bot)
            elif bot == 1:
                return '{0}\u03c0'.format(top)
            else:
                return '{0}\u03c0/{1}'.format(top, bot)
        else:
            return '{0:.5g}\u03c0'.format(value)
