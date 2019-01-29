from traitlets import HasTraits
from aas_timeseries.traits import (Unicode, Float, PositiveFloat, Any, Opacity, Color,
                                   UnicodeChoice, DataTrait, ColumnTrait, AstropyTime)

__all__ = ['Symbol', 'Line', 'Range', 'VerticalLine', 'VerticalRange',
           'HorizontalLine', 'HorizontalRange', 'Text']


def time_to_vega(time):
    """
    Convert an `~astropy.time.Time` object into a string compatible with Vega.
    """

    year, month, day, hour, minute, second = time.datetime.timetuple()[:6]

    # Note that Vega assumes months are zero-based.
    month -= 1

    return f'datetime({year}, {month}, {day}, {hour}, {minute}, {second})'


class BaseMark(HasTraits):
    """
    Base class for any mark object
    """
    label = Unicode(help='The label to use to designate the marks in the legend.')

    def to_vega(self):
        """
        Convert the mark to its Vega representation.
        """


SYMBOL_SHAPES = ['circle', 'square', 'cross', 'diamond', 'triangle-up',
                 'triangle-down', 'triangle-right', 'triangle-left']


class Symbol(BaseMark):
    """
    A set of time series data points represented by markers.
    """

    data = DataTrait(help='The time series object containing the data.')
    column = ColumnTrait(None, help='The field in the time series containing the data.')
    error = ColumnTrait(None, help='The field in the time series '
                                   'containing the data uncertainties.')

    shape = UnicodeChoice('circle', help='The symbol shape.', choices=SYMBOL_SHAPES)

    size = PositiveFloat(5, help='The area in pixels of the bounding box of the symbols.\n\n'
                                 'Note that this value sets the area of the symbol; the '
                                 'side lengths will increase with the square root of this '
                                 'value.')

    # NOTE: for now we implement a single color rather than a separate edge and
    # fill color
    color = Color('black', help='The color of the symbols.')
    opacity = Opacity(1, help='The opacity of the symbol from 0 (transparent) to 1 (opaque).')

    def to_vega(self):

        # The main markers
        vega = [{'type': 'symbol',
                 'description': self.label,
                 'from': {'data': self.data.uuid},
                 'encode': {'enter': {'x': {'scale': 'xscale', 'field': self.data.time_column},
                                      'y': {'scale': 'yscale', 'field': self.column},
                                      'shape': {'value': self.shape}},
                            'update':{'shape': {'value': self.shape},
                                      'size': {'value': self.size},
                                      'fill': {'value': self.color},
                                      'fillOpacity': {'value': self.opacity}}}}]

        # The error bars (if requested)
        if self.error:
            vega.append({'type': 'rect',
                         'description': self.label,
                         'from': {'data': self.data.uuid},
                         'encode': {'enter': {'x': {'scale': 'xscale', 'field': self.data.time_column},
                                         'y': {'scale': 'yscale', 'signal': f"datum['{self.column}'] - datum['{self.error}']"},
                                         'y2': {'scale': 'yscale', 'signal': f"datum['{self.column}'] + datum['{self.error}']"}},
                               'update':{'shape': {'value': self.shape},
                                         'width': {'value': 1},
                                         'fill': {'value': self.color},
                                         'fillOpacity': {'value': self.opacity}}}})

        return vega


class Line(BaseMark):
    """
    A set of time series data points connected by a line.
    """

    data = DataTrait(Nhelp='The time series object containing the data.')
    column = ColumnTrait(None, help='The field in the time series containing the data.')
    width = PositiveFloat(1, help='The width of the line, in pixels.')

    # NOTE: for now we implement a single color rather than a separate edge and
    # fill color
    color = Color('black', help='The color of the line.')
    opacity = Opacity(1, help='The opacity of the line from 0 (transparent) to 1 (opaque).')

    def to_vega(self):
        vega = {'type': 'line',
                'description': self.label,
                'from': {'data': self.data.uuid},
                'encode': {'enter': {'x': {'scale': 'xscale', 'field': self.data.time_column},
                                     'y': {'scale': 'yscale', 'field': self.column},
                                     'strokeWidth': {'value': self.width},
                                     'stroke': {'value': self.color},
                                     'strokeOpacity': {'value': self.opacity}}}}
        return [vega]


class Range(BaseMark):
    """
    An interval defined by lower and upper values as a function of time.
    """

    data = DataTrait(help='The time series object containing the data.')
    column_lower = ColumnTrait(None, help='The field in the time series containing the lower value of the data range.')
    column_upper = ColumnTrait(None, help='The field in the time series containing the upper value of the data range.')

    # NOTE: for now we implement a single color rather than a separate edge and
    # fill color
    color = Color('black', help='The color of the range.')
    opacity = Opacity(0.2, help='The opacity of the range from 0 (transparent) to 1 (opaque).')

    def to_vega(self):
        vega = {'type': 'area',
                'description': self.label,
                'from': {'data': self.data.uuid},
                'encode': {'enter': {'x': {'scale': 'xscale', 'field': self.data.time_column},
                                     'y': {'scale': 'yscale', 'field': self.column_lower},
                                     'y2': {'scale': 'yscale', 'field': self.column_upper},
                                     'fill': {'value': self.color},
                                     'fillOpacity': {'value': self.opacity},
                                     'stroke': {'value': self.color},
                                     'strokeOpacity': {'value': self.opacity}}}}
        return [vega]


class VerticalLine(BaseMark):
    """
    A vertical line at a specific time.
    """

    time = AstropyTime(help='The date/time at which the vertical line is shown.')
    width = PositiveFloat(1, help='The width of the line, in pixels.')

    # NOTE: for now we implement a single color rather than a separate edge and
    # fill color
    color = Color('black', help='The color of the line.')
    opacity = Opacity(1, help='The opacity of the line from 0 (transparent) to 1 (opaque).')

    def to_vega(self):

        vega = {'type': 'rule',
                'description': self.label,
                'encode': {'enter': {'x': {'scale': 'xscale', 'signal': time_to_vega(self.time)},
                                     'y': {'value': 0},
                                     'y2': {'field': {'group': 'height'}},
                                     'strokeWidth': {'value': self.width},
                                     'stroke': {'value': self.color},
                                     'strokeOpacity': {'value': self.opacity}}}}
        return [vega]


class VerticalRange(BaseMark):
    """
    A continuous range specified by a lower and upper time.
    """

    time_lower = AstropyTime(help='The date/time at which the range starts.')
    time_upper = AstropyTime(help='The date/time at which the range ends.')

    # NOTE: for now we implement a single color rather than a separate edge and
    # fill color
    color = Color('black', help='The color of the range.')
    opacity = Opacity(0.2, help='The opacity of the range from 0 (transparent) to 1 (opaque).')

    def to_vega(self):

        vega = {'type': 'rect',
                'description': self.label,
                'encode': {'enter': {'x': {'scale': 'xscale', 'signal': time_to_vega(self.time_lower)},
                                     'x2': {'scale': 'xscale', 'signal': time_to_vega(self.time_upper)},
                                     'y': {'value': 0},
                                     'y2': {'field': {'group': 'height'}},
                                     'fill': {'value': self.color},
                                     'fillOpacity': {'value': self.opacity}}}}
        return [vega]


class HorizontalLine(BaseMark):
    """
    A horizontal line at a specific y value.
    """

    # TODO: validate value and allow it to be a quantity
    value = Float(help='The y value at which the horizontal line is shown.')
    width = PositiveFloat(1, help='The width of the line, in pixels.')

    # NOTE: for now we implement a single color rather than a separate edge and
    # fill color
    color = Color('black', help='The color of the line.')
    opacity = Opacity(1, help='The opacity of the line from 0 (transparent) to 1 (opaque).')

    def to_vega(self):

        vega = {'type': 'rule',
                'description': self.label,
                'encode': {'enter': {'x': {'value': 0},
                                     'x2': {'field': {'group': 'width'}},
                                     'y': {'scale': 'yscale', 'value': self.value},
                                     'strokeWidth': {'value': self.width},
                                     'stroke': {'value': self.color},
                                     'strokeOpacity': {'value': self.opacity}}}}
        return [vega]


class HorizontalRange(BaseMark):
    """
    A continuous range specified by a lower and upper value.
    """

    value_lower = Float(help='The value at which the range starts.')
    value_upper = Float(help='The value at which the range ends.')

    # NOTE: for now we implement a single color rather than a separate edge and
    # fill color
    color = Color('black', help='The color of the range.')
    opacity = Opacity(0.2, help='The opacity of the range from 0 (transparent) to 1 (opaque).')

    def to_vega(self):

        vega = {'type': 'rect',
                'description': self.label,
                'encode': {'enter': {'x': {'value': 0},
                                     'x2': {'field': {'group': 'width'}},
                                     'y': {'scale': 'yscale', 'value': self.value_lower},
                                     'y2': {'scale': 'yscale', 'value': self.value_upper},
                                     'fill': {'value': self.color},
                                     'fillOpacity': {'value': self.opacity}}}}
        return [vega]


class Text(BaseMark):
    """
    A text label.
    """

    text = Unicode(help='The text label to show.')
    time = AstropyTime(help='The date/time at which the text is shown.')
    value = PositiveFloat(help='The y value at which the text is shown.')
    weight = UnicodeChoice('normal', help='The weight of the text.',
                           choices=['normal', 'bold'])
    baseline = UnicodeChoice('alphabetic', help='The vertical text baseline.',
                             choices=['alphabetic', 'top', 'middle', 'bottom'])
    align = UnicodeChoice('left', help='The horizontal text alignment.',
                          choices=['left', 'center', 'right'])
    angle = Float(0, help='The rotation angle of the text in degrees (default 0).')

    # NOTE: for now we implement a single color rather than a separate edge and
    # fill color
    color = Color('black', help='The color of the text.')
    opacity = Opacity(1, help='The opacity of the text from 0 (transparent) to 1 (opaque).')

    def to_vega(self):

        vega = {'type': 'text',
                'description': self.label,
                'encode': {'enter': {'x': {'scale': 'xscale', 'signal': time_to_vega(self.time)},
                                     'y': {'scale': 'yscale', 'value': self.value},
                                     'fill': {'value': self.color},
                                     'fillOpacity': {'value': self.opacity},
                                     'fontWeigth': {'value': self.weight},
                                     'baseline': {'value': self.baseline},
                                     'align': {'value': self.align},
                                     'angle': {'value': self.angle}}}}
        return [vega]
