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
        """
        Add markers, optionally with errorbars, to the figure.

        Parameters
        ----------
        data : `~aas_timeseries.TimeSeries`
            The time series object containing the data.
        column : str
            The field in the time series containing the data.
        error : str, optional
            The field in the time series containing the data uncertainties.
        shape : {'circle', 'square', 'cross', 'diamond', 'triangle-up', 'triangle-down', 'triangle-right', 'triangle-left'}, optional
            The symbol shape.
        size : float or int, optional
            The area in pixels of the bounding box of the symbols.  Note that this
            value sets the area of the symbol; the side lengths will increase with
            the square root of this value.
        color : str or tuple, optional
            The fill color of the symbols.
        opacity : float or int, optional
            The opacity of the fill color from 0 (transparent) to 1 (opaque).
        edge_color : str or tuple, optional
            The edge color of the symbol.
        edge_opacity : float or int, optional
            The opacity of the edge color from 0 (transparent) to 1 (opaque).
        edge_width : float or int, optional
            The thickness of the edge, in pixels.
        label : str, optional
            The label to use to designate the marks in the legend.
        """
        if id(time_series) not in self._data:
            self._data[id(time_series)] = Data(time_series)
        markers = Symbol(data=self._data[id(time_series)], **kwargs)
        # Note that we need to set the column after the data so that the
        # validation works.
        markers.column = column
        self._markers.append(markers)
        return markers

    def add_line(self, *, time_series=None, column=None, **kwargs):
        """
        Add a line to the figure.

        Parameters
        ----------
        data : `~aas_timeseries.TimeSeries`
            The time series object containing the data.
        column : str
            The field in the time series containing the data.
        width : float or int, optional
            The width of the line, in pixels.
        color : str or tuple, optional
            The color of the line.
        opacity : float or int, optional
            The opacity of the line from 0 (transparent) to 1 (opaque).
        label : str, optional
            The label to use to designate the marks in the legend.
        """

        if id(time_series) not in self._data:
            self._data[id(time_series)] = Data(time_series)
        line = Line(data=self._data[id(time_series)], **kwargs)
        # Note that we need to set the column after the data so that the
        # validation works.
        line.column = column
        self._markers.append(line)
        return line

    def add_range(self, *, time_series=None, column_lower=None, column_upper=None, **kwargs):
        """
        Add a time dependent range to the figure.

        Parameters
        ----------
        data : `~aas_timeseries.TimeSeries`
            The time series object containing the data.
        column_lower : str
            The field in the time series containing the lower value of the data
            range.
        column_upper : str
            The field in the time series containing the upper value of the data
            range.
        color : str or tuple, optional
            The fill color of the range.
        opacity : float or int, optional
            The opacity of the fill color from 0 (transparent) to 1 (opaque).
        edge_color : str or tuple, optional
            The edge color of the range.
        edge_opacity : float or int, optional
            The opacity of the edge color from 0 (transparent) to 1 (opaque).
        edge_width : float or int, optional
            The thickness of the edge, in pixels.
        label : str, optional
            The label to use to designate the marks in the legend.
        """
        if id(time_series) not in self._data:
            self._data[id(time_series)] = Data(time_series)
        range = Range(data=self._data[id(time_series)], **kwargs)
        # Note that we need to set the columns after the data so that the
        # validation works.
        range.column_lower = column_lower
        range.column_upper = column_upper
        self._markers.append(range)
        return range

    def add_vertical_line(self, time, **kwargs):
        """
        Add a vertical line to the figure.

        Parameters
        ----------
        time : `~astropy.time.Time`
            The date/time at which the vertical line is shown.
        width : float or int, optional
            The width of the line, in pixels.
        color : str or tuple, optional
            The color of the line.
        opacity : float or int, optional
            The opacity of the line from 0 (transparent) to 1 (opaque).
        label : str, optional
            The label to use to designate the marks in the legend.
        """
        line = VerticalLine(time=time, **kwargs)
        self._markers.append(line)
        return line

    def add_vertical_range(self, time_lower, time_upper, **kwargs):
        """
        Add a vertical range to the figure.

        Parameters
        ----------
        time_lower : `~astropy.time.Time`
            The date/time at which the range starts.
        time_upper : `~astropy.time.Time`
            The date/time at which the range ends.
        color : str or tuple, optional
            The fill color of the range.
        opacity : float or int, optional
            The opacity of the fill color from 0 (transparent) to 1 (opaque).
        edge_color : str or tuple, optional
            The edge color of the range.
        edge_opacity : float or int, optional
            The opacity of the edge color from 0 (transparent) to 1 (opaque).
        edge_width : float or int, optional
            The thickness of the edge, in pixels.
        label : str, optional
            The label to use to designate the marks in the legend.
        """
        range = VerticalRange(time_lower=time_lower, time_upper=time_upper, **kwargs)
        self._markers.append(range)
        return range

    def add_horizontal_line(self, value, **kwargs):
        """
        Add a horizontal line to the figure.

        Parameters
        ----------
        value : float or int
            The y value at which the horizontal line is shown.
        width : float or int, optional
            The width of the line, in pixels.
        color : str or tuple, optional
            The color of the line.
        opacity : float or int, optional
            The opacity of the line from 0 (transparent) to 1 (opaque).
        label : str, optional
            The label to use to designate the marks in the legend.
        """
        line = HorizontalLine(value=value, **kwargs)
        self._markers.append(line)
        return line

    def add_horizontal_range(self, value_lower, value_upper, **kwargs):
        """
        Add a horizontal range to the figure.

        Parameters
        ----------
        value_lower : float or int
            The value at which the range starts.
        value_upper : float or int
            The value at which the range ends.
        color : str or tuple, optional
            The fill color of the range.
        opacity : float or int, optional
            The opacity of the fill color from 0 (transparent) to 1 (opaque).
        edge_color : str or tuple, optional
            The edge color of the range.
        edge_opacity : float or int, optional
            The opacity of the edge color from 0 (transparent) to 1 (opaque).
        edge_width : float or int, optional
            The thickness of the edge, in pixels.
        label : str, optional
            The label to use to designate the marks in the legend.
        """
        range = HorizontalRange(value_lower=value_lower, value_upper=value_upper, **kwargs)
        self._markers.append(range)
        return range

    def add_text(self, **kwargs):
        """
        Add a text label to the figure.

        Parameters
        ----------
        time : `~astropy.time.Time`
            The date/time at which the text is shown.
        value : float or int
            The y value at which the text is shown.
        weight : {'normal', 'bold'}, optional
            The weight of the text.
        baseline : {'alphabetic', 'top', 'middle', 'bottom'}, optional
            The vertical text baseline.
        align : {'left', 'center', 'right'}, optional
            The horizontal text alignment.
        angle : float or int, optional
            The rotation angle of the text in degrees (default 0).
        text : str, optional
            The text label to show.
        color : str or tuple, optional
            The color of the text.
        opacity : float or int, optional
            The opacity of the text from 0 (transparent) to 1 (opaque).
        label : str, optional
            The label to use to designate the marks in the legend.
        """
        text = Text(**kwargs)
        self._markers.append(text)
        return text

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
