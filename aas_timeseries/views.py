import uuid
from collections import OrderedDict

import numpy as np

from astropy.time import Time, TimeDelta
from astropy import units as u
from astropy.units import Quantity
from aas_timeseries.data import Data
from aas_timeseries.layers import BaseLayer, Markers, Line, VerticalLine, VerticalRange, HorizontalLine, HorizontalRange, Range, Text, time_to_vega

__all__ = ['BaseView', 'View']

VALID_TIME_FORMATS = {}
VALID_TIME_FORMATS['absolute'] = ['jd', 'mjd', 'unix', 'iso', 'auto']
VALID_TIME_FORMATS['relative'] = ['seconds', 'hours', 'days', 'years']
VALID_TIME_FORMATS['phase'] = ['unity', 'degrees', 'radians']

VALID_TIME_MODES = ['absolute', 'relative', 'phase']


class BaseView:
    """
    Base class for view-like objects (both the base figure and the actual views)
    """

    def __init__(self, time_mode=None):
        self.uuid = str(uuid.uuid4())
        self._data = OrderedDict()
        self._layers = OrderedDict()
        self._xlim = None
        self._ylim = None
        self._ylog = False
        self._xlabel = ''
        self._ylabel = ''
        self._time_format = ''

        if time_mode is not None and time_mode not in VALID_TIME_MODES:
            raise ValueError("time_mode should be one of " + "/".join(VALID_TIME_MODES))

        self._time_mode = time_mode or 'absolute'

    @property
    def time_mode(self):
        return self._time_mode

    @property
    def ylog(self):
        """
        Whether the y axis is linear (`False`) or log (`True`).
        """
        return self._ylog

    @ylog.setter
    def ylog(self, value):
        self._ylog = value

    @property
    def xlabel(self):
        """
        The label to use for the x-axis. If not specified, this is determined
        automatically from the type of x-axis.
        """
        if self._xlabel:
            return self._xlabel
        else:
            if self._time_mode == 'absolute':
                return 'Time'
            elif self._time_mode == 'relative':
                return 'Relative Time ({0})'.format(self.time_format[0])
            elif self._time_mode == 'phase':
                return 'Phase'

    @xlabel.setter
    def xlabel(self, value):
        self._xlabel = value

    @property
    def ylabel(self):
        """
        The label to use for the y-axis.
        """
        return self._ylabel

    @ylabel.setter
    def ylabel(self, value):
        self._ylabel = value

    @property
    def xlim(self):
        """
        The x/time limits of the view.
        """
        return self._xlim

    @xlim.setter
    def xlim(self, range):
        if not isinstance(range, (tuple, list)) or len(range) != 2:
            raise ValueError("xlim should be a tuple of two elements")
        start, end = range
        if isinstance(start, str):
            start = Time(start)
        if isinstance(end, str):
            end = Time(end)
        if not isinstance(start, Time) or not isinstance(end, Time):
            raise TypeError("xlim should be a typle of two Time instances")
        self._xlim = start, end

    @property
    def ylim(self):
        """
        The y limits of the view.
        """
        return self._ylim

    @ylim.setter
    def ylim(self, range):
        if isinstance(range[0], u.Quantity) is isinstance(range[1], u.Quantity):
            if isinstance(range[0], u.Quantity):
                if not range[0].unit.is_equivalent(range[1].unit):
                    raise u.UnitsError(f'The units of ymin ({range[0].unit}) are '
                                       f'not compatible with the units of ymax ({range[1].unit})')
        else:
            raise ValueError('Either both or neither limit has to be specified '
                             'as a Quantity')
        self._ylim = range

    @property
    def time_format(self):
        """
        The format to use for the x-axis.
        """
        if self._time_format:
            return self._time_format
        else:
            if self._time_mode == 'absolute':
                return 'auto'
            elif self._time_mode == 'relative':
                return 'seconds'
            elif self._time_mode == 'phase':
                return 'unity'

    @time_format.setter
    def time_format(self, value):
        if value in VALID_TIME_FORMATS[self._time_mode]:
            self._time_format = value
        else:
            raise ValueError('time_format should be one of ' + '/'.join(VALID_TIME_FORMATS[self._time_mode]))

    def _validate_time_column(self, time_series, time_column):
        column = time_series[time_column]
        if self._time_mode == 'absolute':
            if not isinstance(column, Time) or isinstance(column, TimeDelta):
                raise TypeError('When in absolute time mode, the time column should be a Time object')
        elif self._time_mode == 'relative':
            if not isinstance(column, (TimeDelta, Quantity)) or (isinstance(column, Quantity) and column.unit.physical_type != 'time'):
                raise TypeError('When in relative time model, the time column should be a TimeDelta or Quantity object with time units')
        elif self._time_mode == 'phase':
            if not isinstance(column, np.ndarray) or (isinstance(column, Quantity) and column.unit.physical_type != 'dimensionless'):
                raise TypeError('When in relative time model, the time column should be a plain array or a dimensionless Quantity')
        else:
            raise ValueError('time_mode should be one of absolute/relative/phase')

    def add_markers(self, *, time_series=None, column=None, time_column='time', **kwargs):
        """
        Add markers, optionally with errorbars, to the figure.

        Parameters
        ----------
        data : `~astropy.timeseries.TimeSeries`
            The time series object containing the data.
        column : str
            The field in the time series containing the data.
        time_column : str, optional
            The field to use for the time on the x-axis.
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
            The label to use to designate the layer in the legend.

        Returns
        -------
        layer : `~aas_timeseries.layers.Markers`
        """
        self._validate_time_column(time_series, time_column)
        if id(time_series) not in self._data:
            self._data[id(time_series)] = Data(time_series)
        markers = Markers(parent=self, data=self._data[id(time_series)], **kwargs)
        # Note that we need to set the column after the data so that the
        # validation works.
        markers.column = column
        markers.time_column = time_column
        self._layers[markers] = {'visible': True}
        return markers

    def add_line(self, *, time_series=None, column=None, time_column='time', **kwargs):
        """
        Add a line to the figure.

        Parameters
        ----------
        data : `~astropy.timeseries.TimeSeries`
            The time series object containing the data.
        column : str
            The field in the time series containing the data.
        time_column : str, optional
            The field to use for the time on the x-axis.
        width : float or int, optional
            The width of the line, in pixels.
        color : str or tuple, optional
            The color of the line.
        opacity : float or int, optional
            The opacity of the line from 0 (transparent) to 1 (opaque).
        label : str, optional
            The label to use to designate the layer in the legend.

        Returns
        -------
        layer : `~aas_timeseries.layers.Line`
        """
        self._validate_time_column(time_series, time_column)
        if id(time_series) not in self._data:
            self._data[id(time_series)] = Data(time_series)
        line = Line(parent=self, data=self._data[id(time_series)], **kwargs)
        # Note that we need to set the column after the data so that the
        # validation works.
        line.column = column
        line.time_column = time_column
        self._layers[line] = {'visible': True}
        return line

    def add_range(self, *, time_series=None, column_lower=None, column_upper=None, time_column='time', **kwargs):
        """
        Add a time dependent range to the figure.

        Parameters
        ----------
        data : `~astropy.timeseries.TimeSeries`
            The time series object containing the data.
        column_lower : str
            The field in the time series containing the lower value of the data
            range.
        column_upper : str
            The field in the time series containing the upper value of the data
            range.
        time_column : str, optional
            The field to use for the time on the x-axis.
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
            The label to use to designate the layer in the legend.

        Returns
        -------
        layer : `~aas_timeseries.layers.Range`
        """
        self._validate_time_column(time_series, time_column)
        if id(time_series) not in self._data:
            self._data[id(time_series)] = Data(time_series)
        range = Range(parent=self, data=self._data[id(time_series)], **kwargs)
        # Note that we need to set the columns after the data so that the
        # validation works.
        range.column_lower = column_lower
        range.column_upper = column_upper
        range.time_column = time_column
        self._layers[range] = {'visible': True}
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
            The label to use to designate the layer in the legend.

        Returns
        -------
        layer : `~aas_timeseries.layers.VerticalLine`
        """
        line = VerticalLine(parent=self, time=time, **kwargs)
        self._layers[line] = {'visible': True}
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
            The label to use to designate the layer in the legend.

        Returns
        -------
        layer : `~aas_timeseries.layers.VerticalRange`
        """
        range = VerticalRange(parent=self, time_lower=time_lower, time_upper=time_upper, **kwargs)
        self._layers[range] = {'visible': True}
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
            The label to use to designate the layer in the legend.

        Returns
        -------
        layer : `~aas_timeseries.layers.HorizontalLine`
        """
        line = HorizontalLine(parent=self, value=value, **kwargs)
        self._layers[line] = {'visible': True}
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
            The label to use to designate the layer in the legend.

        Returns
        -------
        layer : `~aas_timeseries.layers.HorizontalRange`
        """
        range = HorizontalRange(parent=self, value_lower=value_lower, value_upper=value_upper, **kwargs)
        self._layers[range] = {'visible': True}
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
            The label to use to designate the layer in the legend.

        Returns
        -------
        layer : `~aas_timeseries.layers.Text`
        """
        text = Text(parent=self, **kwargs)
        self._layers[text] = {'visible': True}
        return text

    @property
    def layers(self):
        return list(self._layers)

    def _get_domains(self, yunit, as_vega=True):

        if self.xlim is None or self.ylim is None:

            all_times = []
            all_values = []

            # If there are symbol layers, we just use those to determine limits
            if any(isinstance(layer, Markers) for layer in self.layers):
                layer_types = (Markers,)
            else:
                layer_types = (Range, Line)

            for layer in self.layers:
                if isinstance(layer, layer_types):

                    if self._time_mode == 'absolute':
                        all_times.append(np.min(layer.data.time_series[layer.time_column]))
                        all_times.append(np.max(layer.data.time_series[layer.time_column]))
                    elif self._time_mode == 'relative':
                        all_times.append(np.nanmin(layer.data.column_to_values(layer.time_column, u.s)))
                        all_times.append(np.nanmax(layer.data.column_to_values(layer.time_column, u.s)))
                    elif self._time_mode == 'phase':
                        all_times.append(np.nanmin(layer.data.column_to_values(layer.time_column, u.one)))
                        all_times.append(np.nanmax(layer.data.column_to_values(layer.time_column, u.one)))

                    all_values.append(np.nanmin(layer.data.column_to_values(layer.column, yunit)))
                    all_values.append(np.nanmax(layer.data.column_to_values(layer.column, yunit)))

            if len(all_times) > 0:
                xlim_auto = np.min(all_times), np.max(all_times)
            else:
                xlim_auto = None

            if len(all_values) > 0:
                ylim_auto = float(np.min(all_values)), float(np.max(all_values))
            else:
                ylim_auto = None

        if self.xlim is None:
            xlim = xlim_auto
        else:
            xlim = self.xlim

        if self.ylim is None:
            ylim = ylim_auto
        else:
            ylim = self.ylim
            if isinstance(ylim[0], u.Quantity):
                ylim = ylim[0].to_value(yunit), ylim[1].to_value(yunit)
            elif yunit is not u.one:
                raise u.UnitsError(f'Limits for y axis are dimensionless but '
                                   f'expected units of {yunit}')

        xlim = xlim_auto if xlim is None else xlim
        ylim = ylim_auto if ylim is None else ylim

        if xlim is not None:
            if self._time_mode == 'absolute' and as_vega:
                x_domain = ({'signal': time_to_vega(xlim[0])},
                            {'signal': time_to_vega(xlim[1])})
            else:
                x_domain = list(xlim)
        else:
            x_domain = None

        if ylim is not None:
            y_domain = list(ylim)
        else:
            y_domain = None

        return x_domain, y_domain


class View(BaseView):

    def __init__(self, figure=None, inherited_layers=None, time_mode=None):
        super().__init__(time_mode=time_mode)
        self._figure = figure
        self._inherited_layers = inherited_layers or OrderedDict()
        self._data = figure._data
        self.ylabel = figure.ylabel

    def show(self, layers):
        self._set_visible(layers, True)

    def hide(self, layers):
        self._set_visible(layers, False)

    def _set_visible(self, layers, visible):
        if isinstance(layers, BaseLayer):
            layers = [layers]
        for layer in layers:
            if layer in self._layers:
                self._layers[layer]['visible'] = visible
            elif layer in self._inherited_layers:
                self._inherited_layers[layer]['visible'] = visible
            else:
                raise ValueError(f'Layer {layer} not in view')

    def remove(self, layer):
        """
        Remove a layer from the view.
        """
        if layer in self._inherited_layers:
            self._inherited_layers.pop(layer)
        elif layer in self._layers:
            self._layers.pop(layer)
        else:
            raise ValueError(f"Layer '{layer.label}' is not in view")

    @property
    def layers(self):
        return list(self._inherited_layers) + list(self._layers)
