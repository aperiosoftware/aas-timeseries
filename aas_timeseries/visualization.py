import os
import tempfile
from io import StringIO
from json import dump, dumps
from zipfile import ZipFile

import numpy as np

from astropy.table import Table

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
    """

    def __init__(self, width=600, height=400, padding=36, resize=False):
        super().__init__()
        self._width = width
        self._height = height
        self._resize = resize
        self._padding = padding
        self._views = []

    def add_view(self, title, description=None, include=None, exclude=None, empty=False):

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

        view = View(inherited_layers=inherited_layers)

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
        json['width'] = self._width
        json['height'] = self._height
        json['padding'] = 0
        json['autosize'] = {'type': 'fit', 'resize': self._resize}

        # Data

        # We start off by checking which columns and data are going to be
        # required. We do this by iterating over the layers in the main
        # figure and the views and keeping track of the set of (data, column)
        # that are needed.
        if minimize_data:
            required_data = []
            for layer in self._layers:
                required_data.extend(layer._required_data())
            for view in self._views:
                for layer in view['view']._layers:
                    required_data.extend(layer._required_data())
            required_data = set(required_data)

        json['data'] = []

        for data in self._data.values():

            # Start off by constructing a new table with only the subset of
            # columns required, and the time as an ISO string.
            table = Table()
            table[data.time_column] = data.time_series.time.isot
            for colname in data.time_series.colnames:
                if colname != 'time' and (not minimize_data or (data, colname) in required_data):
                    table[colname] = data.time_series[colname]

            # Next up, we create the information for the 'parse' Vega key
            # which indicates the format for each column.
            parse = {}
            for colname in table.colnames:
                column = table[colname]
                if colname == data.time_column:
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
                table.write(data_filename, format='ascii.basic', delimiter=',')
                vega['url'] = data_filename

        # Layers

        json['marks'] = []
        for layer, settings in self._layers.items():
            json['marks'].extend(layer.to_vega())

        # Axes
        json['axes'] = [{'orient': 'bottom', 'scale': 'xscale',
                         'title': 'Time'},
                        {'orient': 'left', 'scale': 'yscale',
                         'title': 'Intensity'}]

        # Scales
        json['scales'] = [{'name': 'xscale',
                           'type': 'time',
                           'range': 'width',
                           'zero': False,
                           'padding': self._padding},
                          {'name': 'yscale',
                           'type': 'log' if self.ylog else 'linear',
                           'range': 'height',
                           'zero': False,
                           'padding': self._padding}]

        # Limits

        if self.xlim is None or self.ylim is None:

            all_times = []
            all_values = []

            # If there are symbol layers, we just use those to determine limits
            if any(isinstance(layer, Markers) for layer in self._layers):
                layer_types = (Markers,)
            else:
                layer_types = (Range, Line)

            for layer in self._layers:
                if isinstance(layer, layer_types):
                    all_times.append(np.min(layer.data.time_series.time))
                    all_times.append(np.max(layer.data.time_series.time))
                    all_values.append(np.nanmin(layer.data.time_series[layer.column]))
                    all_values.append(np.nanmax(layer.data.time_series[layer.column]))

            if len(all_times) > 0:
                xlim_auto = np.min(all_times), np.max(all_times)
            else:
                xlim_auto = None

            if len(all_values) > 0:
                ylim_auto = float(np.min(all_values)), float(np.max(all_values))
            else:
                ylim_auto = None

        xlim = xlim_auto if self.xlim is None else self.xlim
        ylim = ylim_auto if self.ylim is None else self.ylim

        if xlim is not None:
            json['scales'][0]['domain'] = ({'signal': time_to_vega(xlim[0])},
                                           {'signal': time_to_vega(xlim[1])})

        if ylim is not None:
            json['scales'][1]['domain'] = list(ylim)

        # Views

        if len(self._views) > 0:

            json['_views'] = []
            json['_extramarks'] = []

            for view in self._views:

                view_json = {'name': self.uuid,
                             'title': view['title'],
                             'description': view['description']}

                json['_views'].append(view_json)

                view_json['scales'] = [{'name': 'xscale',
                                        'type': 'time',
                                        'range': 'width',
                                        'zero': False,
                                        'padding': self._padding},
                                       {'name': 'yscale',
                                        'type': 'log' if view['view'].ylog else 'linear',
                                        'range': 'height',
                                        'zero': False,
                                        'padding': self._padding}]

                # Limits, if specified
                if view['view'].xlim is not None:
                    view_json['scales'][0]['domain'] = ({'signal': time_to_vega(view['view'].xlim[0])},
                                                        {'signal': time_to_vega(view['view'].xlim[1])})

                if view['view'].ylim is not None:
                    view_json['scales'][1]['domain'] = list(view['view'].ylim)

                # layers

                view_json['marks'] = []

                for layer, settings in view['view']._inherited_layers.items():
                    view_json['marks'].append({'name': layer.uuid, 'visible': settings['visible']})

                for layer, settings in view['view']._layers.items():
                    json['_extramarks'].extend(layer.to_vega())
                    view_json['marks'].append({'name': layer.uuid, 'visible': settings['visible']})

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
