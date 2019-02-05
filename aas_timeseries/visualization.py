import uuid
import tempfile
from json import dump

from jupyter_aas_timeseries import TimeSeriesWidget

from aas_timeseries.colors import auto_assign_colors
from aas_timeseries.views import BaseView, View
from aas_timeseries.marks import time_to_vega

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
    resize : bool, optional
        Whether to resize the figure to the available space.
    """

    def __init__(self, width=600, height=400, resize=False):
        super().__init__()
        self._width = width
        self._height = height
        self._resize = resize
        self._views = []

    def add_view(self, title, description=None, include=None, exclude=None, empty=False):

        if empty:
            inherited_marks = {}
        elif include is not None:
            for mark in include:
                if mark not in self._markers:
                    raise ValueError(f'Layer {mark} does not exist')
            inherited_marks = {mark: self._markers[mark] for mark in include}
        elif exclude is not None:
            for mark in exclude:
                if mark not in self._markers:
                    raise ValueError(f'Layer {mark} does not exist')
            inherited_marks = {mark: self._markers[mark] for mark in self._markers if mark not in exclude}
        else:
            inherited_marks = self._markers.copy()

        view = View(inherited_marks=inherited_marks)

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

        colors = auto_assign_colors(self._markers)
        for marker, color in zip(self._markers, colors):
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
        for mark, settings in self._markers.items():
            json['marks'].extend(mark.to_vega())

        # Axes
        json['axes'] = [{'orient': 'bottom', 'scale': 'xscale',
                         'title': 'Time'},
                        {'orient': 'left', 'scale': 'yscale',
                         'title': 'Intensity'}]

        # Scales
        json['scales'] = [{'name': 'xscale', 'type': 'time',
                           'range': 'width', 'zero': False},
                          {'name': 'yscale', 'type': 'linear',
                           'range': 'height', 'zero': False}]

        # Limits, if specified
        if self.xlim is not None:
            json['scales'][0]['domain'] = ({'signal': time_to_vega(self.xlim[0])},
                                           {'signal': time_to_vega(self.xlim[1])})
        if self.ylim is not None:
            json['scales'][1]['domain'] = list(self.ylim)

        # Views

        if len(self._views) > 0:

            json['_views'] = []
            json['_extramarks'] = []

            for view in self._views:

                view_json = {'name': self.uuid,
                             'title': view['title'],
                             'description': view['description']}

                json['_views'].append(view_json)

                view_json['scales'] = [{'name': 'xscale', 'type': 'time',
                                        'range': 'width', 'zero': False},
                                       {'name': 'yscale', 'type': 'linear',
                                        'range': 'height', 'zero': False}]

                # Limits, if specified
                if view['view'].xlim is not None:
                    view_json['scales'][0]['domain'] = ({'signal': time_to_vega(view['view'].xlim[0])},
                                                        {'signal': time_to_vega(view['view'].xlim[1])})

                if view['view'].ylim is not None:
                    view_json['scales'][1]['domain'] = list(view['view'].ylim)

                # Markers

                view_json['markers'] = []

                for mark, settings in view['view']._inherited_marks.items():
                    view_json['markers'].append({'name': mark.uuid, 'visible': settings['visible']})

                for mark, settings in view['view']._markers.items():
                    json['_extramarks'].extend(mark.to_vega())
                    view_json['markers'].append({'name': mark.uuid, 'visible': settings['visible']})

        return json
