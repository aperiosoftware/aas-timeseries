import tempfile
from json import dump

import numpy as np

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
            for mark in include:
                if mark not in self._layers:
                    raise ValueError(f'Layer {mark} does not exist in base figure')
            inherited_layers = {mark: self._layers[mark] for mark in include}
        elif exclude is not None:
            for mark in exclude:
                if mark not in self._layers:
                    raise ValueError(f'Layer {mark} does not exist in base figure')
            inherited_layers = {mark: self._layers[mark] for mark in self._layers if mark not in exclude}
        else:
            inherited_layers = self._layers.copy()

        view = View(inherited_layers=inherited_layers)

        self._views.append({'title': title, 'description': description, 'view': view})

        return view

    def save_interactive(self, filename, override_style=False):
        """
        Save a Vega-compatible JSON file that contains the specification for
        the interactive figure.

        Parameters
        ----------
        filename : str
            The filename for the JSON file.
        override_style : bool, optional
            By default, any unspecified colors will be automatically chosen.
            If this parameter is set to `True`, all colors will be reassigned,
            even if already set.
        """

        colors = auto_assign_colors(self._layers)
        for marker, color in zip(self._layers, colors):
            if override_style or marker.color is None:
                marker.color = color

        with open(filename, 'w') as f:
            dump(self._to_json(), f, indent='  ')

    def preview_interactive(self):
        """
        Show an interactive version of the figure (only works in Jupyter
        notebook or lab).
        """
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
        for mark, settings in self._layers.items():
            json['marks'].extend(mark.to_vega())

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
            if any(isinstance(mark, Markers) for mark in self._layers):
                layer_types = (Markers,)
            else:
                layer_types = (Range, Line)

            for mark in self._layers:
                if isinstance(mark, layer_types):
                    all_times.append(np.min(mark.data.time_series.time))
                    all_times.append(np.max(mark.data.time_series.time))
                    all_values.append(np.nanmin(mark.data.time_series[mark.column]))
                    all_values.append(np.nanmax(mark.data.time_series[mark.column]))

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

                for mark, settings in view['view']._inherited_layers.items():
                    view_json['marks'].append({'name': mark.uuid, 'visible': settings['visible']})

                for mark, settings in view['view']._layers.items():
                    json['_extramarks'].extend(mark.to_vega())
                    view_json['marks'].append({'name': mark.uuid, 'visible': settings['visible']})

        return json
