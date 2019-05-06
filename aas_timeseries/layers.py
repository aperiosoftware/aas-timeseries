import uuid
import weakref
import numpy as np
from traitlets import HasTraits
from astropy import units as u
from aas_timeseries.traits import (Unicode, CFloat, PositiveCFloat, Opacity, Color,
                                   UnicodeChoice, DataTrait, ColumnTrait, AstropyTime,
                                   AstropyQuantity)

__all__ = ['BaseLayer', 'Markers', 'Line', 'Range', 'VerticalLine',
           'VerticalRange', 'HorizontalLine', 'HorizontalRange', 'Text',
           'time_to_vega', 'TimeDependentLayer']

DEFAULT_COLOR = '#000000'


def time_to_vega(time):
    """
    Convert an `~astropy.time.Time` object into a string compatible with Vega.
    """

    year, month, day, hour, minute, second = time.datetime.timetuple()[:6]

    # Note that Vega assumes months are zero-based.
    month -= 1

    return f'datetime({year}, {month}, {day}, {hour}, {minute}, {second})'


class BaseLayer(HasTraits):
    """
    Base class for any layer object
    """

    label = Unicode(help='The label to use to designate the layers in the legend.')

    # Potential properties that could be implemented: toolTip

    def __init__(self, parent=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.uuid = str(uuid.uuid4())
        # NOTE: we use weakref to avoid circular references
        self.parent = weakref.ref(parent)

    def remove(self):
        """
        Remove the layer from the visualization.
        """
        if self.parent is None or self.parent() is None:
            raise Exception(f"Layer '{self.label}' is no longer in a figure/view")
        else:
            self.parent().remove(self)
            self.parent = None

    def to_vega(self):
        """
        Convert the layer to its Vega representation.
        """

    def to_mpl(self, ax, yunit=None):
        """
        Add the layer to a Matplotlib `~matplotlib.axes.Axes` instance.
        """

    @property
    def _required_xdata(self):
        """
        Return a list of (data, column) tuples giving the data/columns required
        for the x-axis of the layer.
        """
        return []

    @property
    def _required_ydata(self):
        """
        Return a list of (data, column) tuples giving the data/columns required
        for the y-axis of the layer.
        """
        return []


class TimeDependentLayer(BaseLayer):
    """
    A common class for all layers that depend on time
    """

    time_column = ColumnTrait(None, help='The column to use.')


MARKER_SHAPES = ['circle', 'square', 'cross', 'diamond', 'triangle-up',
                 'triangle-down', 'triangle-right', 'triangle-left']


class Markers(TimeDependentLayer):
    """
    A set of time series data points represented by markers.
    """

    data = DataTrait(help='The time series object containing the data.')
    column = ColumnTrait(None, help='The field in the time series containing the data.')
    error = ColumnTrait(None, help='The field in the time series '
                                   'containing the data uncertainties.')

    shape = UnicodeChoice('circle', help='The symbol shape.', choices=MARKER_SHAPES)

    size = PositiveCFloat(20, help='The area in pixels of the bounding box of the symbols.\n\n'
                                   'Note that this value sets the area of the symbol; the '
                                   'side lengths will increase with the square root of this '
                                   'value.')

    color = Color(None, help='The fill color of the symbols.')
    opacity = Opacity(1, help='The opacity of the fill color from 0 (transparent) to 1 (opaque).')

    edge_color = Color(None, help='The edge color of the symbol.')
    edge_opacity = Opacity(0.2, help='The opacity of the edge color from 0 (transparent) to 1 (opaque).')
    edge_width = PositiveCFloat(0, help='The thickness of the edge, in pixels.')

    def to_vega(self, yunit=None):

        # The main markers
        vega = [{'type': 'symbol',
                 'name': self.uuid,
                 'description': self.label,
                 'clip': True,
                 'from': {'data': self.data.uuid},
                 'encode': {'enter': {'x': {'scale': 'xscale', 'field': self.time_column},
                                      'y': {'scale': 'yscale', 'field': self.column},
                                      'shape': {'value': self.shape}},
                            'update': {'shape': {'value': self.shape},
                                       'size': {'value': self.size},
                                       'fill': {'value': self.color or DEFAULT_COLOR},
                                       'fillOpacity': {'value': self.opacity},
                                       'stroke': {'value': self.edge_color or DEFAULT_COLOR},
                                       'strokeOpacity': {'value': self.edge_opacity},
                                       'strokeWidth': {'value': self.edge_width}}}}]

        # The error bars (if requested)
        if self.error:
            vega.append({'type': 'rect',
                         'name': self.uuid,
                         'description': self.label,
                         'clip': True,
                         'from': {'data': self.data.uuid},
                         'encode': {'enter': {'x': {'scale': 'xscale', 'field': self.time_column},
                                              'y': {'scale': 'yscale', 'signal': f"datum['{self.column}'] - datum['{self.error}']"},
                                              'y2': {'scale': 'yscale', 'signal': f"datum['{self.column}'] + datum['{self.error}']"}},
                                    'update': {'shape': {'value': self.shape},
                                               'width': {'value': 1},
                                               'fill': {'value': self.color or DEFAULT_COLOR},
                                               'fillOpacity': {'value': self.opacity},
                                               'stroke': {'value': self.edge_color or DEFAULT_COLOR},
                                               'strokeOpacity': {'value': self.edge_opacity},
                                               'strokeWidth': {'value': self.edge_width}}}})

        return vega

    def to_mpl(self, ax, yunit=None):

        x = self.data.time_series[self.data.time_column].mjd
        y = self.data.column_to_values(self.column, yunit)

        ax.plot(x, y, '.', markersize=self.size,
                color=self.color or DEFAULT_COLOR,
                alpha=self.opacity)

        if self.error:
            yerr = self.data.column_to_values(self.error, yunit)
            ax.errorbar(x, y, yerr=yerr, fmt='none',
                        color=self.color or DEFAULT_COLOR,
                        alpha=self.opacity)

    @property
    def _required_xdata(self):
        return [(self.data, self.time_column)]

    @property
    def _required_ydata(self):
        return [(self.data, self.column), (self.data, self.error)]


class Line(TimeDependentLayer):
    """
    A set of time series data points connected by a line.
    """

    data = DataTrait(help='The time series object containing the data.')
    column = ColumnTrait(None, help='The field in the time series containing the data.')
    width = PositiveCFloat(1, help='The width of the line, in pixels.')

    color = Color(None, help='The color of the line.')
    opacity = Opacity(1, help='The opacity of the line from 0 (transparent) to 1 (opaque).')

    def to_vega(self, yunit=None):
        vega = {'type': 'line',
                'name': self.uuid,
                'description': self.label,
                'clip': True,
                'from': {'data': self.data.uuid},
                'encode': {'enter': {'x': {'scale': 'xscale', 'field': self.time_column},
                                     'y': {'scale': 'yscale', 'field': self.column},
                                     'stroke': {'value': self.color or DEFAULT_COLOR},
                                     'strokeOpacity': {'value': self.opacity},
                                     'strokeWidth': {'value': self.width}}}}
        return [vega]

    def to_mpl(self, ax, yunit=None):

        x = self.data.time_series[self.data.time_column].mjd
        y = self.data.column_to_values(self.column, yunit)

        ax.plot(x, y, '-',
                color=self.color or DEFAULT_COLOR,
                alpha=self.opacity)

    @property
    def _required_xdata(self):
        return [(self.data, self.time_column)]

    @property
    def _required_ydata(self):
        return [(self.data, self.column)]


class Range(TimeDependentLayer):
    """
    An interval defined by lower and upper values as a function of time.
    """

    data = DataTrait(help='The time series object containing the data.')
    column_lower = ColumnTrait(None, help='The field in the time series containing the lower value of the data range.')
    column_upper = ColumnTrait(None, help='The field in the time series containing the upper value of the data range.')

    color = Color(None, help='The fill color of the range.')
    opacity = Opacity(0.2, help='The opacity of the fill color from 0 (transparent) to 1 (opaque).')

    edge_color = Color(None, help='The edge color of the range.')
    edge_opacity = Opacity(0.2, help='The opacity of the edge color from 0 (transparent) to 1 (opaque).')
    edge_width = PositiveCFloat(0, help='The thickness of the edge, in pixels.')

    # Potential properties that could be implemented: strokeCap, strokeDash

    def to_vega(self, yunit=None):
        vega = {'type': 'area',
                'name': self.uuid,
                'description': self.label,
                'clip': True,
                'from': {'data': self.data.uuid},
                'encode': {'enter': {'x': {'scale': 'xscale', 'field': self.time_column},
                                     'y': {'scale': 'yscale', 'field': self.column_lower},
                                     'y2': {'scale': 'yscale', 'field': self.column_upper},
                                     'fill': {'value': self.color or DEFAULT_COLOR},
                                     'fillOpacity': {'value': self.opacity},
                                     'stroke': {'value': self.edge_color or DEFAULT_COLOR},
                                     'strokeOpacity': {'value': self.edge_opacity},
                                     'strokeWidth': {'value': self.edge_width}}}}

        return [vega]

    def to_mpl(self, ax, yunit=None):

        x = self.data.time_series[self.data.time_column].mjd
        y1 = self.data.column_to_values(self.column_lower, yunit)
        y2 = self.data.column_to_values(self.column_upper, yunit)

        ax.fill_between(x, y1, y2,
                        color=self.color or DEFAULT_COLOR,
                        alpha=self.opacity)

    @property
    def _required_xdata(self):
        return [(self.data, self.time_column)]

    @property
    def _required_ydata(self):
        return [(self.data, self.column_lower), (self.data, self.column_upper)]


class VerticalLine(BaseLayer):
    """
    A vertical line at a specific time.
    """

    time = AstropyTime(help='The date/time at which the vertical line is shown.')
    width = PositiveCFloat(1, help='The width of the line, in pixels.')

    color = Color(None, help='The color of the line.')
    opacity = Opacity(1, help='The opacity of the line from 0 (transparent) to 1 (opaque).')

    # Potential properties that could be implemented: strokeCap, strokeDash

    def to_vega(self, yunit=None):

        vega = {'type': 'rule',
                'name': self.uuid,
                'description': self.label,
                'clip': True,
                'encode': {'enter': {'x': {'scale': 'xscale', 'signal': time_to_vega(self.time)},
                                     'y': {'value': 0},
                                     'y2': {'field': {'group': 'height'}},
                                     'strokeWidth': {'value': self.width},
                                     'stroke': {'value': self.color or DEFAULT_COLOR},
                                     'strokeOpacity': {'value': self.opacity}}}}
        return [vega]

    def to_mpl(self, ax, yunit=None):
        ax.axvline(self.time.mjd,
                   color=self.color or DEFAULT_COLOR,
                   alpha=self.opacity)


class VerticalRange(BaseLayer):
    """
    A continuous range specified by a lower and upper time.
    """

    time_lower = AstropyTime(help='The date/time at which the range starts.')
    time_upper = AstropyTime(help='The date/time at which the range ends.')

    color = Color(None, help='The fill color of the range.')
    opacity = Opacity(0.2, help='The opacity of the fill color from 0 (transparent) to 1 (opaque).')

    edge_color = Color(None, help='The edge color of the range.')
    edge_opacity = Opacity(0.2, help='The opacity of the edge color from 0 (transparent) to 1 (opaque).')
    edge_width = PositiveCFloat(0, help='The thickness of the edge, in pixels.')

    # Potential properties that could be implemented: strokeCap, strokeDash

    def to_vega(self, yunit=None):

        vega = {'type': 'rect',
                'name': self.uuid,
                'description': self.label,
                'clip': True,
                'encode': {'enter': {'x': {'scale': 'xscale', 'signal': time_to_vega(self.time_lower)},
                                     'x2': {'scale': 'xscale', 'signal': time_to_vega(self.time_upper)},
                                     'y': {'value': 0},
                                     'y2': {'field': {'group': 'height'}},
                                     'fill': {'value': self.color or DEFAULT_COLOR},
                                     'fillOpacity': {'value': self.opacity},
                                     'stroke': {'value': self.edge_color or DEFAULT_COLOR},
                                     'strokeOpacity': {'value': self.edge_opacity},
                                     'strokeWidth': {'value': self.edge_width}}}}

        return [vega]

    def to_mpl(self, ax, yunit=None):
        ax.fill_betweenx([-1e30, 1e30], self.time_lower.mjd, self.time_upper.mjd,
                         color=self.color or DEFAULT_COLOR,
                         alpha=self.opacity)


class HorizontalLine(BaseLayer):
    """
    A horizontal line at a specific y value.
    """

    # TODO: validate value and allow it to be a quantity
    value = AstropyQuantity(help='The y value at which the horizontal line is shown.')
    width = PositiveCFloat(1, help='The width of the line, in pixels.')

    color = Color(None, help='The color of the line.')
    opacity = Opacity(1, help='The opacity of the line from 0 (transparent) to 1 (opaque).')

    # Potential properties that could be implemented: strokeCap, strokeDash

    def to_vega(self, yunit=None):

        if yunit is None:
            yunit = u.one

        value = self.value.to_value(yunit)

        vega = {'type': 'rule',
                'name': self.uuid,
                'description': self.label,
                'clip': True,
                'encode': {'enter': {'x': {'value': 0},
                                     'x2': {'field': {'group': 'width'}},
                                     'y': {'scale': 'yscale', 'value': value},
                                     'strokeWidth': {'value': self.width},
                                     'stroke': {'value': self.color or DEFAULT_COLOR},
                                     'strokeOpacity': {'value': self.opacity}}}}
        return [vega]

    def to_mpl(self, ax, yunit=None):
        if yunit is None:
            yunit = u.one
        ax.axhline(self.value.to_value(yunit),
                   color=self.color or DEFAULT_COLOR,
                   alpha=self.opacity)


class HorizontalRange(BaseLayer):
    """
    A continuous range specified by a lower and upper value.
    """

    value_lower = AstropyQuantity(help='The value at which the range starts.')
    value_upper = AstropyQuantity(help='The value at which the range ends.')

    color = Color(None, help='The fill color of the range.')
    opacity = Opacity(0.2, help='The opacity of the fill color from 0 (transparent) to 1 (opaque).')

    edge_color = Color(None, help='The edge color of the range.')
    edge_opacity = Opacity(0.2, help='The opacity of the edge color from 0 (transparent) to 1 (opaque).')
    edge_width = PositiveCFloat(0, help='The thickness of the edge, in pixels.')

    # Potential properties that could be implemented: strokeCap, strokeDash

    def to_vega(self, yunit=None):

        if yunit is None:
            yunit = u.one

        value_lower = self.value_lower.to_value(yunit)
        value_upper = self.value_upper.to_value(yunit)

        vega = {'type': 'rect',
                'name': self.uuid,
                'description': self.label,
                'clip': True,
                'encode': {'enter': {'x': {'value': 0},
                                     'x2': {'field': {'group': 'width'}},
                                     'y': {'scale': 'yscale', 'value': value_lower},
                                     'y2': {'scale': 'yscale', 'value': value_upper},
                                     'fill': {'value': self.color or DEFAULT_COLOR},
                                     'fillOpacity': {'value': self.opacity},
                                     'stroke': {'value': self.edge_color or DEFAULT_COLOR},
                                     'strokeOpacity': {'value': self.edge_opacity},
                                     'strokeWidth': {'value': self.edge_width}}}}
        return [vega]

    def to_mpl(self, ax, yunit=None):

        value_lower = self.value_lower.to_value(yunit)
        value_upper = self.value_upper.to_value(yunit)

        ax.fill_between([-1e30, 1e30], value_lower, value_upper,
                         color=self.color or DEFAULT_COLOR,
                         alpha=self.opacity)


class Text(BaseLayer):
    """
    A text label.
    """

    text = Unicode(help='The text label to show.')
    time = AstropyTime(help='The date/time at which the text is shown.')
    value = AstropyQuantity(help='The y value at which the text is shown.')
    weight = UnicodeChoice('normal', help='The weight of the text.',
                           choices=['normal', 'bold'])
    baseline = UnicodeChoice('alphabetic', help='The vertical text baseline.',
                             choices=['alphabetic', 'top', 'middle', 'bottom'])
    align = UnicodeChoice('left', help='The horizontal text alignment.',
                          choices=['left', 'center', 'right'])
    angle = CFloat(0, help='The rotation angle of the text in degrees (default 0).')

    color = Color(None, help='The color of the text.')
    opacity = Opacity(1, help='The opacity of the text from 0 (transparent) to 1 (opaque).')

    def to_vega(self, yunit=None):

        if yunit is None:
            yunit = u.one

        value = self.value.to_value(yunit)

        vega = {'type': 'text',
                'name': self.uuid,
                'description': self.label,
                'clip': True,
                'encode': {'enter': {'x': {'scale': 'xscale', 'signal': time_to_vega(self.time)},
                                     'y': {'scale': 'yscale', 'value': value},
                                     'text': {'value': self.text},
                                     'fill': {'value': self.color or DEFAULT_COLOR},
                                     'fillOpacity': {'value': self.opacity},
                                     'fontWeigth': {'value': self.weight},
                                     'baseline': {'value': self.baseline},
                                     'align': {'value': self.align},
                                     'angle': {'value': self.angle}}}}
        return [vega]

    def to_mpl(self, ax, yunit=None):

        if yunit is None:
            yunit = u.one

        x = self.time.mjd
        value = self.value.to_value(yunit)

        ax.text(x, value, self.text,
                color=self.color or DEFAULT_COLOR,
                alpha=self.opacity)
