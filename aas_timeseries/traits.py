# The code in this module has been adapted from the PyWWT package which was
# originally released under the following license:
#
# Copyright (c) 2017, Thomas P. Robitaille, O. Justin Otor, and John ZuHone
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
# * Neither the name of the WorldWide Telescope project nor the names of its
#   contributors may be used to endorse or promote products derived from this
#   software without specific prior written permission.
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

import numpy as np

from traitlets import (TraitType, TraitError,
                       Any as OriginalAny,
                       Bool as OriginalBool,
                       CFloat as OriginalCFloat,
                       Int as OriginalInt,
                       Unicode as OriginalUnicode)

from astropy import units as u
from astropy.time import Time

try:
    from matplotlib.colors import to_hex
except ImportError:
    from matplotlib.colors import colorConverter, rgb2hex
    def to_hex(input):  # noqa
        return rgb2hex(colorConverter.to_rgb(input))

from aas_timeseries.data import Data

__all__ = ['Any', 'Bool', 'CFloat', 'PositiveCFloat', 'Int', 'Unicode',
           'UnicodeChoice', 'AstropyQuantity', 'DataTrait', 'ColumnTrait',
           'AstropyTime', 'Color', 'Opacity', 'Tooltip']


# We inherit the original trait classes to make sure that the docstrings are set


class Any(OriginalAny):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.help:
            self.__doc__ = self.help


class Bool(OriginalBool):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.help:
            self.__doc__ = self.help


class CFloat(OriginalCFloat):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.help:
            self.__doc__ = self.help


class PositiveCFloat(CFloat):

    def validate(self, obj, value):
        if value >= 0:
            return value
        else:
            raise TraitError('value should be positive')


class Int(OriginalInt):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.help:
            self.__doc__ = self.help


class Unicode(OriginalUnicode):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.help:
            self.__doc__ = self.help


class UnicodeChoice(Unicode):

    def __init__(self, *args, choices=[], **kwargs):
        super().__init__(*args, **kwargs)
        self.choices = choices
        choices_doc = []
        for choice in self.choices:
            if choice == self.default_value:
                choices_doc.append(f"``'{choice}'`` (default)")
            else:
                choices_doc.append(f"``'{choice}'``")
        self.__doc__ += '\n\nOne of ' + (', '.join(choices_doc)) + '.'

    def validate(self, obj, value):
        if value in self.choices:
            return value
        else:
            raise TraitError('value should be one of ' + ', '.join(f"'{choice}'" for choice in self.choices))


class AstropyQuantity(TraitType):

    default = 0 * u.one
    info_text = '\'Custom trait to handle astropy quantities with units\''

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.help:
            self.__doc__ = self.help

    def validate(self, obj, value):
        if isinstance(value, u.Quantity):
            return value
        elif np.isscalar(value) and np.isreal(value):
            return value * u.one
        self.error(obj, value)


class DataTrait(TraitType):

    default = None
    info_text = "'Custom trait to handle Data objects'"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.help:
            self.__doc__ = self.help

    def validate(self, obj, value):
        if isinstance(value, Data):
            return value
        else:
            raise TraitError('value should be a Data instance')


class ColumnTrait(Unicode):

    allow_none = True
    default = None
    info_text = "'Custom trait to handle columns of Data objects'"

    def validate(self, obj, value):
        if value is None:
            return value
        try:
            obj.data
        except TraitError:
            raise TraitError('data should be set before column')
        if value in obj.data.time_series.colnames:
            return value
        else:
            raise TraitError(f'{value} is not a valid column name')


class AstropyTime(TraitType):

    default = None
    info_text = "'Custom trait to handle astropy time'"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.help:
            self.__doc__ = self.help

    def validate(self, obj, value):
        if isinstance(value, Time):
            return value
        else:
            try:
                return Time(value)
            except ValueError:
                raise TraitError('value should be a Time instance')


class Color(TraitType):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.help:
            self.__doc__ = self.help

    def validate(self, obj, value):
        if value is None:
            return None
        elif isinstance(value, str) or (isinstance(value, tuple) and len(value) == 3):
            return to_hex(value)
        else:
            if hasattr(obj, 'opacity'):
                raise TraitError('color must be a string or a tuple of 3 or 4 floats')
            else:
                raise TraitError('color must be a string or a tuple of 3 floats')


class Opacity(OriginalCFloat):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.help:
            self.__doc__ = self.help

    def validate(self, obj, value):
        if 0 <= value <= 1:
            return value
        else:
            raise TraitError("opacity must be a value in the range [0:1]")


class Tooltip(TraitType):

    default = False
    info_text = "'Whether or not to show a tooltip, and optionally a list or dictionary of values to show'"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.help:
            self.__doc__ = self.help

    def validate(self, obj, value):
        if isinstance(value, (bool, tuple, list, dict)):
            return value
        else:
            raise TraitError('value should be a boolean, tuple, list, or dictionary')
