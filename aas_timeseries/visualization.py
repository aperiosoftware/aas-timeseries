import os
import tempfile
from io import StringIO
from json import dump
from zipfile import ZipFile

import numpy as np

from astropy.time import Time, TimeDelta
from astropy.table import Table
from astropy import units as u
from jupyter_aas_timeseries import TimeSeriesWidget

from aas_timeseries.colors import auto_assign_colors
from aas_timeseries.views import BaseView, View
from aas_timeseries.layers import time_to_vega, Markers, Range, Line

__all__ = ['InteractiveTimeSeriesFigure']


class InteractiveTimeSeriesFigure(BaseView):
    """
    An interactive time series figure.

    Parameters
    ----------
    width : int, optional
        The preferred width of the figure, in pixels.
    height : int, optional
        The preferred height of the figure, in pixels.
    padding : int, optional
        The padding inside the axes, in pixels
    resize : bool, optional
        Whether to resize the figure to the available space.
    title : str, optinal
        If views are added to the figure, this title is used for the default
        view, otherwise 'Default' is used.
    """

    def __init__(self, width=600, height=400, padding=36, resize=False, title=None, time_mode=None):
        super().__init__(time_mode=time_mode)
        self._width = width
        self._height = height
        self._resize = resize
        self._padding = padding
        self._yunit = 'auto'
        self._views = []
        self._title = title

    @property
    def yunit(self):
        """
        The unit to use for the y axis, or 'auto' to guess. If using data
        without quantities, this can be set to ``u.one``.
        """
        return self._yunit

    @yunit.setter
    def yunit(self, value):
        if isinstance(value, u.UnitBase) or value == 'auto':
            self._yunit = value
        else:
            self._yunit = u.Unit(value)

    def _guess_yunit(self):
        """
        Try and guess unit to use on the y axis based on the limits set and the
        data used.
        """

        # First check if the limits were set explicitly and if so use those
        # units if they were Quantities since it seems likely this was
        # deliberate.
        if self.ylim is not None and isinstance(self.ylim[0], u.Quantity):
            return self.ylim[0].unit

        # Next, check through all the data required by the layers, first in the
        # figure, then in the views, and return the first unit or lack of unit
        # found.
        for layer in self._layers:
            for (data, colname) in layer._required_ydata:
                return data.unit(colname)
        for view in self._views:
            for layer in view['view']._layers:
                for (data, colname) in layer._required_ydata:
                    return data.unit(colname)

        # Since we didn't find anything, let's assume that the y axis should
        # be dimensionless. In theory we could also go through non-data layers
        # and check the units used there.
        return u.one

    def add_view(self, title, description=None, include=None, exclude=None, empty=False, time_mode=None):

        if empty:
            inherited_layers = {}
        elif include is not None:
            for layer in include:
                if layer not in self._layers:
                    raise ValueError(f'Layer {layer} does not exist in base figure')
            inherited_layers = {layer: self._layers[layer] for layer in include}
        elif exclude is not None:
            for layer in exclude:
                if layer not in self._layers:
                    raise ValueError(f'Layer {layer} does not exist in base figure')
            inherited_layers = {layer: self._layers[layer] for layer in self._layers if layer not in exclude}
        else:
            inherited_layers = self._layers.copy()

        view = View(figure=self, inherited_layers=inherited_layers, time_mode=time_mode)

        self._views.append({'title': title, 'description': description, 'view': view})

        return view

    def export_interactive_bundle(self, filename, embed_data=False,
                                  minimize_data=True, override_style=False):
        """
        Create a bundle for the interactive figure containing an HTML file and
        JSON file along with any required CSV files.

        Parameters
        ----------
        filename : str
            The filename for the zip file
        embed_data : bool, optional
            Whether to embed the data in the JSON file (`True`) or include it
            in separate CSV files (`False`). The default is `False`.
        minimize_data : bool, optional
            Whether to include only data required for the visualization (`True`)
            or also other unused columns/fields in the time series (`False`).
            The default is `True`.
        override_style : bool, optional
            By default, any unspecified colors will be automatically chosen.
            If this parameter is set to `True`, all colors will be reassigned,
            even if already set.
        """

        start_dir = os.path.abspath('.')
        tmp_dir = tempfile.mkdtemp()
        os.chdir(tmp_dir)
        try:
            self.save_vega_json('figure.json', embed_data=embed_data)
        finally:
            os.chdir(start_dir)
        html_file = os.path.join(os.path.dirname(__file__), 'screenshot', 'template.html')
        with ZipFile(filename, 'w') as fzip:
            for filename in os.listdir(tmp_dir):
                fzip.write(os.path.join(tmp_dir, filename), os.path.basename(filename))
            fzip.write(html_file, 'index.html')

    def save_vega_json(self, filename, embed_data=False, minimize_data=True, override_style=False):
        """
        Export the JSON file, and optionally CSV data files.

        Parameters
        ----------
        filename : str
            The name of the JSON file
        embed_data : bool, optional
            Whether to embed the data in the JSON file (`True`) or include it
            in separate CSV files (`False`). The default is `False`.
        minimize_data : bool, optional
            Whether to include only data required for the visualization (`True`)
            or also other unused columns/fields in the time series (`False`).
            The default is `True`.
        override_style : bool, optional
            By default, any unspecified colors will be automatically chosen.
            If this parameter is set to `True`, all colors will be reassigned,
            even if already set.
        """

        # Start off by figuring out what units we are using on the y axis.
        # Note that we check the consistency of the units only here for
        # simplicity otherwise any guessing while users add/remove layers is
        # tricky.
        if self.yunit == 'auto':
            yunit = self._guess_yunit()
        else:
            yunit = self.yunit

        # Auto-assign colors if needed
        colors = auto_assign_colors(self._layers)
        for layer, color in zip(self._layers, colors):
            if override_style or layer.color is None:
                layer.color = color

        # Start off with empty JSON
        json = {}

        # Schema
        json['$schema'] = 'https://vega.github.io/schema/vega/v4.json'

        # Layout
        json['title'] = self._title or 'Default'
        json['width'] = self._width
        json['height'] = self._height
        json['padding'] = 0
        json['autosize'] = {'type': 'fit', 'resize': self._resize}

        json['_extend'] = {}

        # Data

        # We start off by checking which columns and data are going to be
        # required. We do this by iterating over the layers in the main
        # figure and the views and keeping track of the set of (data, column)
        # that are needed.
        required_xdata = []
        required_ydata = []
        for layer in self._layers:
            required_xdata.extend(layer._required_xdata)
            required_ydata.extend(layer._required_ydata)
        for view in self._views:
            for layer in view['view']._layers:
                required_xdata.extend(layer._required_xdata)
                required_ydata.extend(layer._required_ydata)
        required_xdata = set(required_xdata)
        required_ydata = set(required_ydata)

        json['data'] = []

        for data in self._data.values():

            # Start off by constructing a new table with only the subset of
            # columns required, and the time as an ISO string.
            table = Table()
            time_columns = []
            for colname in data.time_series.colnames:
                if (not minimize_data or (data, colname) in required_xdata | required_ydata):
                    column = data.time_series[colname]
                    if isinstance(column, Time):
                        table[colname] = column.isot
                        time_columns.append(colname)
                    elif (data, colname) in required_xdata:
                        table[colname] = data.column_to_values(colname, (u.one, u.s))
                    elif (data, colname) in required_ydata:
                        table[colname] = data.column_to_values(colname, yunit)
                    else:
                        table[colname] = column

            # Next up, we create the information for the 'parse' Vega key
            # which indicates the format for each column.
            parse = {}
            for colname in table.colnames:
                column = table[colname]
                if colname in time_columns:
                    parse[colname] = 'date'
                elif column.dtype.kind in 'fi':
                    parse[colname] = 'number'
                elif column.dtype.kind in 'b':
                    parse[colname] = 'boolean'
                else:
                    parse[colname] = 'string'

            vega = {'name': data.uuid,
                    'format': {'type': 'csv',
                               'parse': parse}}

            # We now either embed the CSV inside the JSON or create CSV files.
            # For now we use UUIDs for the data file names in the latter case
            # but in future we could find a way to preserve information about
            # the original filenames the data came from.
            if embed_data:
                s = StringIO()
                table.write(s, format='ascii.basic', delimiter=',')
                s.seek(0)
                csv_string = s.read()
                vega['values'] = csv_string
            else:
                data_filename = 'data_' + data.uuid + '.csv'
                data_path = os.path.join(os.path.dirname(filename), data_filename)
                table.write(data_path, format='ascii.basic', delimiter=',')
                vega['url'] = data_filename

            json['data'].append(vega)

        # Layers

        json['marks'] = []
        for layer, settings in self._layers.items():
            json['marks'].extend(layer.to_vega(yunit=yunit))

        # Axes

        # TODO: allow axis labels to be customized

        if self._time_mode == 'absolute':
            x_title = 'Time'
            x_type = 'time'
            x_input = 'iso'
            x_output = 'auto'
        elif self._time_mode == 'relative':
            x_title = 'Relative Time'
            x_type = 'number'
            x_input = 'seconds'
            x_output = 'auto'
        elif self._time_mode == 'phase':
            x_title = 'Phase'
            x_type = 'number'
            x_input = 'phase'
            x_output = 'phase'

        json['_extend'] = {'scales': [{'name': 'xscale', 'input': x_input, 'output': x_output}]}

        json['axes'] = [{'orient': 'bottom', 'scale': 'xscale',
                         'title': x_title},
                        {'orient': 'left', 'scale': 'yscale',
                         'title': 'Intensity'}]

        # Scales
        json['scales'] = [{'name': 'xscale',
                           'type': x_type,
                           'range': 'width',
                           'zero': False,
                           'padding': self._padding},
                          {'name': 'yscale',
                           'type': 'log' if self.ylog else 'linear',
                           'range': 'height',
                           'zero': False,
                           'padding': self._padding}]

        # Limits

        x_domain, y_domain = self._get_domains(yunit)

        if x_domain is not None:
            json['scales'][0]['domain'] = x_domain

        if y_domain is not None:
            json['scales'][1]['domain'] = y_domain

        # Views

        if len(self._views) > 0:

            json['_views'] = []
            json['_extend']['marks'] = []

            for view in self._views:

                view_json = {'name': self.uuid,
                             'title': view['title'],
                             'description': view['description']}

                json['_views'].append(view_json)

                if view['view']._time_mode == 'absolute':
                    x_title = 'Time'
                    x_type = 'time'
                    x_input = 'iso'
                    x_output = 'auto'
                elif view['view']._time_mode == 'relative':
                    x_title = 'Relative Time'
                    x_type = 'number'
                    x_input = 'seconds'
                    x_output = 'auto'
                elif view['view']._time_mode == 'phase':
                    x_title = 'Phase'
                    x_type = 'number'
                    x_input = 'phase'
                    x_output = 'phase'

                view_json['_extend'] = {'scales': [{'name': 'xscale', 'input': x_input, 'output': x_output}]}

                view_json['axes'] = [{'orient': 'bottom', 'scale': 'xscale',
                                 'title': x_title},
                                {'orient': 'left', 'scale': 'yscale',
                                 'title': 'Intensity'}]

                view_json['scales'] = [{'name': 'xscale',
                                        'type': x_type,
                                        'range': 'width',
                                        'zero': False,
                                        'padding': self._padding},
                                       {'name': 'yscale',
                                        'type': 'log' if view['view'].ylog else 'linear',
                                        'range': 'height',
                                        'zero': False,
                                        'padding': self._padding}]

                # Limits, if specified

                x_domain, y_domain = view['view']._get_domains(yunit)

                if x_domain is not None:
                    view_json['scales'][0]['domain'] = x_domain

                if y_domain is not None:
                    view_json['scales'][1]['domain'] = y_domain

                # layers

                view_json['markers'] = []

                for layer, settings in view['view']._inherited_layers.items():
                    view_json['markers'].append({'name': layer.uuid, 'visible': settings['visible']})

                for layer, settings in view['view']._layers.items():
                    json['_extend']['marks'].extend(layer.to_vega(yunit=yunit))
                    view_json['markers'].append({'name': layer.uuid, 'visible': settings['visible']})

        with open(filename, 'w') as f:
            dump(json, f, indent='  ')

    def preview_interactive(self):
        """
        Show an interactive version of the figure (only works in Jupyter
        notebook or lab).
        """
        # FIXME: should be able to do without a file
        tmpfile = tempfile.mktemp()
        self.save_vega_json(tmpfile, embed_data=True, minimize_data=True)
        widget = TimeSeriesWidget(tmpfile)
        return widget

    def remove(self, layer):
        """
        Remove a layer from the figure.
        """
        if layer in self._layers:
            self._layers.pop(layer)
            for view in self._views:
                if layer in view['view'].layers:
                    view['view'].remove(layer)
        else:
            raise ValueError(f"Layer '{layer.label}' is not in figure")
