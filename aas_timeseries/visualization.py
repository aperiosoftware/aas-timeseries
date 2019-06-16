import os
import tempfile
from io import StringIO
from json import dump
from zipfile import ZipFile

import numpy as np

from astropy.time import Time
from astropy.table import Table
from astropy import units as u

from astropy.visualization import quantity_support

from aas_timeseries.backports import time_support
from aas_timeseries.colors import auto_assign_colors
from aas_timeseries.views import BaseView, View

__all__ = ['InteractiveTimeSeriesFigure']


def pad_limits(limits, padding):
    vrange = (limits[1] - limits[0]) * padding
    return limits[0] - vrange, limits[1] + vrange


class InteractiveTimeSeriesFigure(BaseView):
    """
    An interactive time series figure.

    Parameters
    ----------
    width : int, optional
        The preferred width of the figure, in pixels.
    height : int, optional
        The preferred height of the figure, in pixels.
    padding : float, optional
        The padding inside the axes, as a fraction of the size of the axes
    resize : bool, optional
        Whether to resize the figure to the available space.
    title : str, optinal
        If views are added to the figure, this title is used for the default
        view, otherwise 'Default' is used.
    """

    def __init__(self, width=600, height=400, padding=0.1, resize=False, title=None, time_mode=None):
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

    def save_static(self, prefix, format='png', override_style=False):

        # Auto-assign colors if needed
        colors = auto_assign_colors(self._layers)
        for layer, color in zip(self._layers, colors):
            if override_style or layer.color is None:
                layer.color = color

        # Start off by figuring out what units we are using on the y axis.
        # Note that we check the consistency of the units only here for
        # simplicity otherwise any guessing while users add/remove layers is
        # tricky.
        if self.yunit == 'auto':
            yunit = self._guess_yunit()
        else:
            yunit = self.yunit

        from matplotlib import pyplot as plt

        for iview, view in enumerate([self] + self._views):

            if view is not self:
                view = view['view']

            with time_support(format='iso', scale='utc'):
                with quantity_support():

                    fig = plt.figure(figsize=(self._width / 100, self._height / 100))
                    ax = fig.add_axes([0.15, 0.1, 0.8, 0.88])

                    for layer in view.layers:
                        layer.to_mpl(ax, yunit=yunit)

            x_domain, y_domain = view._get_domains(yunit, as_vega=False)

            ax.set_xlim(*x_domain)
            ax.set_ylim(*y_domain)

            # Apply padding - we just get the limits again because the x limits
            # above may have been Time objects, so we get the limits again from
            # Matplotlib.
            ax.set_xlim(*pad_limits(ax.get_xlim(), self._padding))
            ax.set_ylim(*pad_limits(ax.get_ylim(), self._padding))

            if view is self:
                filename = prefix + '.' + format
            else:
                filename = prefix + '_view' + str(iview) + '.' + format

            if view._time_mode == 'absolute':
                x_title = view.xlabel or 'Time'
            elif view._time_mode == 'relative':
                x_title = view.xlabel or 'Relative Time'
            elif view._time_mode == 'phase':
                x_title = view.xlabel or 'Phase'

            ax.set_xlabel(x_title)
            ax.set_ylabel(view.ylabel)

            fig.savefig(filename)

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
            # columns required, and the time as an ISO string. Note that we
            # need to explicitly specify that we want UTC times, then add the
            # Z suffix since this isn't something that astropy does.
            table = Table()
            time_columns = []
            for colname in data.time_series.colnames:
                if (not minimize_data or (data, colname) in required_xdata | required_ydata):
                    column = data.time_series[colname]
                    if isinstance(column, Time):
                        table[colname] = np.char.add(column.utc.isot, 'Z')
                        time_columns.append(colname)
                    elif (data, colname) in required_xdata:
                        try:
                            table[colname] = data.column_to_values(colname, u.s)
                        except u.UnitsError:
                            table[colname] = data.column_to_values(colname, u.one)
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
                # NOTE: when embedding the data inside the JSON file, we should
                # just use simple Unix line endings inside the serialized table.
                csv_string = s.read().replace('\r\n', '\n')
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
            x_title = self.xlabel or 'Time'
            x_type = 'time'
            x_input = 'iso'
            x_output = 'auto'
        elif self._time_mode == 'relative':
            x_title = self.xlabel or 'Relative Time'
            x_type = 'number'
            x_input = 'seconds'
            x_output = 'auto'
        elif self._time_mode == 'phase':
            x_title = self.xlabel or 'Phase'
            x_type = 'number'
            x_input = 'phase'
            x_output = 'unity'

        json['_extend'] = {'scales': [{'name': 'xscale', 'input': x_input, 'output': x_output}]}

        json['axes'] = [{'orient': 'bottom', 'scale': 'xscale',
                         'title': x_title},
                        {'orient': 'left', 'scale': 'yscale',
                         'title': self.ylabel or ''}]

        # Scales
        json['scales'] = [{'name': 'xscale',
                           'type': x_type,
                           'range': 'width',
                           'zero': False,
                           'padding': self._padding * self._width},
                          {'name': 'yscale',
                           'type': 'log' if self.ylog else 'linear',
                           'range': 'height',
                           'zero': False,
                           'padding': self._padding * self._height}]

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
                    x_title = self.xlabel or 'Time'
                    x_type = 'time'
                    x_input = 'iso'
                    x_output = 'auto'
                elif view['view']._time_mode == 'relative':
                    x_title = self.xlabel or 'Relative Time'
                    x_type = 'number'
                    x_input = 'seconds'
                    x_output = 'auto'
                elif view['view']._time_mode == 'phase':
                    x_title = self.xlabel or 'Phase'
                    x_type = 'number'
                    x_input = 'phase'
                    x_output = 'unity'

                view_json['_extend'] = {'scales': [{'name': 'xscale', 'input': x_input, 'output': x_output}]}

                view_json['axes'] = [{'orient': 'bottom', 'scale': 'xscale',
                                 'title': x_title},
                                {'orient': 'left', 'scale': 'yscale',
                                 'title': self.ylabel or ''}]

                view_json['scales'] = [{'name': 'xscale',
                                        'type': x_type,
                                        'range': 'width',
                                        'zero': False,
                                        'padding': self._padding * self._width},
                                       {'name': 'yscale',
                                        'type': 'log' if view['view'].ylog else 'linear',
                                        'range': 'height',
                                        'zero': False,
                                        'padding': self._padding * self._height}]

                # Limits, if specified

                x_domain, y_domain = view['view']._get_domains(yunit)

                if x_domain is not None:
                    view_json['scales'][0]['domain'] = x_domain

                if y_domain is not None:
                    view_json['scales'][1]['domain'] = y_domain

                # layers

                view_json['markers'] = []

                for layer, settings in view['view']._inherited_layers.items():
                    for uuid in layer.uuids:
                        view_json['markers'].append({'name': uuid, 'visible': settings['visible']})

                for layer, settings in view['view']._layers.items():
                    json['_extend']['marks'].extend(layer.to_vega(yunit=yunit))
                    for uuid in layer.uuids:
                        view_json['markers'].append({'name': uuid, 'visible': settings['visible']})

        with open(filename, 'w') as f:
            dump(json, f, indent='  ')

    def preview_interactive(self):
        """
        Show an interactive version of the figure (only works in Jupyter
        notebook or lab).
        """
        # FIXME: should be able to do without a file
        from jupyter_aas_timeseries import TimeSeriesWidget
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
