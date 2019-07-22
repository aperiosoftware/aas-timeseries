# Backport from Astropy - can be removed once Astropy 4.0 or later is required.
#
# Copyright (c) 2011-2017, Astropy Developers
#
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
# * Redistributions in binary form must reproduce the above copyright notice, this
#   list of conditions and the following disclaimer in the documentation and/or
#   other materials provided with the distribution.
# * Neither the name of the Astropy Team nor the names of its contributors may be
#   used to endorse or promote products derived from this software without
#   specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
# ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import re

import numpy as np

from datetime import datetime

from astropy.time import Time
from astropy import units as u
from astropy.utils.exceptions import ErfaError

__all__ = ['time_support']

__doctest_skip__ = ['*']

UNSUPPORTED_FORMATS = ('datetime', 'datetime64')
YMDHMS_FORMATS = ('fits', 'iso', 'isot', 'yday')
STR_FORMATS = YMDHMS_FORMATS + ('byear_str', 'jyear_str')


def time_support(*, scale=None, format=None, simplify=True):
    """
    Enable support for plotting `astropy.time.Time` instances in
    matplotlib.

    May be (optionally) used with a ``with`` statement.

      >>> import matplotlib.pyplot as plt
      >>> from astropy import units as u
      >>> from astropy import visualization
      >>> with visualization.time_support():  # doctest: +IGNORE_OUTPUT
      ...     plt.figure()
      ...     plt.plot(Time(['2016-03-22T12:30:31', '2016-03-22T12:30:38', '2016-03-22T12:34:40']))
      ...     plt.draw()

    Parameters
    ----------
    scale : str, optional
        The time scale to use for the times on the axis. If not specified,
        the scale of the first Time object passed to Matplotlib is used.
    format : str, optional
        The time format to use for the times on the axis. If not specified,
        the format of the first Time object passed to Matplotlib is used.
    simplify : bool, optional
        If possible, simplify labels, e.g. by removing 00:00:00.000 times from
        ISO strings if all labels fall on that time, or by removing the leading
        date when it is repeated.
    """

    import matplotlib.units as units
    from matplotlib.ticker import MaxNLocator, ScalarFormatter
    from astropy.visualization.wcsaxes.utils import select_step_hour, select_step_scalar

    class AstropyTimeLocator(MaxNLocator):

        # Note: we default to AutoLocator since many time formats
        # can just use this.

        def __init__(self, converter, *args, **kwargs):
            kwargs['nbins'] = 4
            super().__init__(*args, **kwargs)
            self._converter = converter

        def tick_values(self, vmin, vmax):

            # Where we put the ticks depends on the format we are using
            if self._converter.format in YMDHMS_FORMATS:

                # If we are here, we need to check what the range of values
                # is and decide how to find tick locations accordingly

                vrange = vmax - vmin

                if (self._converter.format != 'yday' and vrange > 31) or vrange > 366:  # greater than a month

                    # We need to be careful here since not all years and months have
                    # the same length

                    # Start off by converting the values from the range to
                    # datetime objects, so that we can easily extract the year and
                    # month.

                    try:
                        tmin = Time(vmin, scale=self._converter.scale, format='mjd').datetime
                        tmax = Time(vmax, scale=self._converter.scale, format='mjd').datetime
                    except ErfaError:
                        return []

                    # Find the range of years
                    ymin = tmin.year
                    ymax = tmax.year

                    if ymax > ymin + 1:  # greater than a year

                        # Find the step we want to use
                        ystep = int(select_step_scalar(max(1, (ymax - ymin) / 3)))

                        ymin = ystep * (ymin // ystep)

                        # Generate the years for these steps
                        times = []
                        for year in range(ymin, ymax + 1, ystep):
                            times.append(datetime(year=year, month=1, day=1))

                    else:  # greater than a month but less than a year

                        mmin = tmin.month
                        mmax = tmax.month + 12 * (ymax - ymin)

                        mstep = int(select_step_scalar(max(1, (mmax - mmin) / 3)))

                        mmin = mstep * max(1, mmin // mstep)

                        # Generate the months for these steps
                        times = []
                        for month in range(mmin, mmax + 1, mstep):
                            times.append(datetime(year=ymin + month // 12,
                                                  month=month % 12, day=1))

                    # Convert back to MJD
                    values = Time(times, scale=self._converter.scale).mjd

                elif vrange > 1:  # greater than a day

                    self.set_params(steps=[1, 2, 5, 10])
                    values = super().tick_values(vmin, vmax)

                else:

                    # Determine ideal step
                    dv = vrange / 3 * 24 << u.hourangle

                    # And round to nearest sensible value
                    dv = select_step_hour(dv).to_value(u.hourangle) / 24

                    # Determine tick locations
                    imin = np.ceil(vmin / dv)
                    imax = np.floor(vmax / dv)
                    values = np.arange(imin, imax + 1, dtype=np.int64) * dv

            else:

                values = super().tick_values(vmin, vmax)

            # Get rid of values outside of the input interval
            values = values[(values >= vmin) & (values <= vmax)]

            return values

        def __call__(self):
            vmin, vmax = self.axis.get_view_interval()
            return self.tick_values(vmin, vmax)

    class AstropyTimeFormatter(ScalarFormatter):

        def __init__(self, converter, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self._converter = converter
            self.set_useOffset(False)
            self.set_scientific(False)

        def __call__(self, value, pos=None):
            # Needed for Matplotlib <3.1
            if self._converter.format in STR_FORMATS:
                return self.format_ticks([value])[0]
            else:
                return super().__call__(value, pos=pos)

        def format_ticks(self, values):
            if len(values) == 0:
                return []
            if self._converter.format in YMDHMS_FORMATS:

                # Find spacing of labels in seconds - here we asssume the ticks
                # are evenly spaced, which they should be since we determined
                # them with the locator above.
                dv_sec = (values[1] - values[0]) * 3600 * 24
                if dv_sec < 1:
                    precision = int(np.ceil(-np.log10(dv_sec)))
                else:
                    precision = 0

                times = Time(values, format='mjd', scale=self._converter.scale, precision=precision)
                formatted = getattr(times, self._converter.format)
                if self._converter.simplify:
                    if self._converter.format in ('fits', 'iso', 'isot'):
                        separator = ' ' if self._converter.format == 'iso' else 'T'
                        # The regular expression is to check whether the time
                        # contains only zeros and separators.
                        if all([not re.match('[1-9]', x) for x in formatted]):
                            formatted = [x.split(separator)[0] for x in formatted]
                        else:
                            date_prev = None
                            for i in range(len(formatted)):
                                date, time = formatted[i].split(separator)
                                if date == date_prev:
                                    formatted[i] = time
                                date_prev = date
                    elif self._converter.format == 'yday':
                        if all([x.endswith(':001:00:00:00.000') for x in formatted]):
                            formatted = [x.split(':', 1)[0] for x in formatted]
                return formatted
            elif self._converter.format == 'byear_str':
                return Time(values, format='byear', scale=self._converter.scale).byear_str
            elif self._converter.format == 'jyear_str':
                return Time(values, format='jyear', scale=self._converter.scale).jyear_str
            else:
                return super().format_ticks(values)

    class MplTimeConverter(units.ConversionInterface):

        def __init__(self, scale=None, format=None, simplify=None):

            super().__init__()

            self.format = format
            self.scale = scale
            self.simplify = simplify

            # Keep track of original converter in case the context manager is
            # used in a nested way.
            self._original_converter = units.registry.get(Time)

            units.registry[Time] = self

        @property
        def format(self):
            return self._format

        @format.setter
        def format(self, value):
            if value in UNSUPPORTED_FORMATS:
                raise ValueError('time_support does not support format={0}'.format(value))
            self._format = value

        def __enter__(self):
            return self

        def __exit__(self, type, value, tb):
            if self._original_converter is None:
                del units.registry[Time]
            else:
                units.registry[Time] = self._original_converter

        def default_units(self, x, axis):
            if isinstance(x, tuple):
                x = x[0]
            if self.format is None:
                self.format = x.format
            if self.scale is None:
                self.scale = x.scale
            return 'astropy_time'

        def convert(self, value, unit, axis):
            """
            Convert a Time value to a scalar or array.
            """

            # For cases where Matplotlib doesn't implement the ConversionInterface
            if isinstance(value, (tuple, list)) and isinstance(value[0], Time):
                value = Time(value)

            # For Matplotlib < 2.2
            if not isinstance(value, Time):
                return value

            scaled = getattr(value, self.scale)
            if self.format in YMDHMS_FORMATS:
                return scaled.mjd
            elif self.format == 'byear_str':
                return scaled.byear
            elif self.format == 'jyear_str':
                return scaled.jyear
            else:
                return getattr(scaled, self.format)

        def axisinfo(self, unit, axis):
            """
            Return major and minor tick locators and formatters.
            """
            majloc = AstropyTimeLocator(self)
            majfmt = AstropyTimeFormatter(self)
            return units.AxisInfo(majfmt=majfmt,
                                  majloc=majloc,
                                  label='Time ({0})'.format(self.scale))

    return MplTimeConverter(scale=scale, format=format, simplify=simplify)
