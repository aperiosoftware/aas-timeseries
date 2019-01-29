import tempfile
from json import dump

from jupyter_aas_timeseries import TimeSeriesWidget

from aas_timeseries.data import Data
from aas_timeseries.marks import Symbol, Line, VerticalLine, VerticalRange, HorizontalLine, HorizontalRange, Range, Text
from aas_timeseries.colors import auto_assign_colors

__all__ = ['InteractiveTimeSeriesFigure']


class InteractiveTimeSeriesFigure:
    """
    An interactive time series figure.
    """

    def __init__(self, width=600, height=400, resize=False):
        self._data = {}
        self._markers = []
        self._width = width
        self._height = height
        self._resize = resize

    def add_markers(self, *, time_series=None, column=None, **kwargs):
        if id(time_series) not in self._data:
            self._data[id(time_series)] = Data(time_series)
        markers = Symbol(data=self._data[id(time_series)], **kwargs)
        # Note that we need to set the column after the data so that the
        # validation works.
        markers.column = column
        self._markers.append(markers)

    def add_line(self, *, time_series=None, column=None, **kwargs):
        if id(time_series) not in self._data:
            self._data[id(time_series)] = Data(time_series)
        line = Line(data=self._data[id(time_series)], **kwargs)
        # Note that we need to set the column after the data so that the
        # validation works.
        line.column = column
        self._markers.append(line)

    def add_range(self, *, time_series=None, column_lower=None, column_upper=None, **kwargs):
        if id(time_series) not in self._data:
            self._data[id(time_series)] = Data(time_series)
        range = Range(data=self._data[id(time_series)], **kwargs)
        # Note that we need to set the columns after the data so that the
        # validation works.
        range.column_lower = column_lower
        range.column_upper = column_upper
        self._markers.append(range)

    def add_vertical_line(self, time, **kwargs):
        self._markers.append(VerticalLine(time=time, **kwargs))

    def add_vertical_range(self, time_lower, time_upper, **kwargs):
        self._markers.append(VerticalRange(time_lower=time_lower, time_upper=time_upper, **kwargs))

    def add_horizontal_line(self, value, **kwargs):
        self._markers.append(HorizontalLine(value=value, **kwargs))

    def add_horizontal_range(self, value_lower, value_upper, **kwargs):
        self._markers.append(HorizontalRange(value_lower=value_lower, value_upper=value_upper, **kwargs))

    def add_text(self, **kwargs):
        self._markers.append(Text(**kwargs))

    def save_interactive(self, filename, override_style=False):

        colors = auto_assign_colors(self._markers)
        for marker, color in zip(self._markers, colors):
            if override_style or marker.color is None:
                marker.color = color

        with open(filename, 'w') as f:
            dump(self._to_json(), f, indent='  ')

    def preview_interactive(self):
        # FIXME: should be able to do without a file
        tmpfile = tempfile.mktemp()
        self.save_interactive(tmpfile)
        widget = TimeSeriesWidget(tmpfile)
        return widget

    def _to_json(self):

        # Start off with empty JSON
        json = {}

        # Schema
        json['$schema'] = 'https://vega.github.io/schema/vega/v4.json'

        # Layout
        json['width'] = self._width
        json['height'] = self._height
        json['padding'] = 0
        json['autosize'] = {'type': 'fit', 'resize': self._resize}

        # Data
        json['data'] = [data.to_vega() for data in self._data.values()]
        json['marks'] = []
        for mark in self._markers:
            json['marks'].extend(mark.to_vega())

        # Axes
        json['axes'] = [{'orient': 'bottom', 'scale': 'xscale', 'title': 'Time'},
                        {'orient': 'left', 'scale': 'yscale', 'title': 'Intensity'}]

        # Scales
        json['scales'] = [{'name': 'xscale', 'type': 'time', 'range': 'width', 'zero': False},
                          {'name': 'yscale', 'type': 'linear', 'range': 'width', 'zero': False}]

        return json
