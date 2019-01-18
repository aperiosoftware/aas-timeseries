from json import dump

from aas_timeseries.data import Data
from aas_timeseries.marks import Symbol, Line

__all__ = ['InteractiveTimeSeriesFigure']


class InteractiveTimeSeriesFigure:

    def __init__(self):
        self._data = {}
        self._markers = []

    def add_markers(self, *, time_series=None, column=None, label=None):
        if id(time_series) not in self._data:
            self._data[id(time_series)] = Data(time_series)
        self._markers.append(Symbol(data=self._data[id(time_series)],
                                    column=column,
                                    label=label))

    def add_line(self, *, time_series=None, column=None, label=None):
        if id(time_series) not in self._data:
            self._data[id(time_series)] = Data(time_series)
        self._markers.append(Line(data=self._data[id(time_series)],
                                  column=column,
                                  label=label))

    def save_interactive(self, filename):
        with open(filename, 'w') as f:
            dump(self._to_json(), f, indent='  ')

    def _to_json(self):

        # Start off with empty JSON
        json = {}

        # Schema
        json['$schema'] = 'https://vega.github.io/schema/vega/v4.json'

        # Layout
        json['width'] = 800
        json['height'] = 450
        json['padding'] = 0
        json['autosize'] = {'type': 'fit', 'resize': True}

        # Data
        json['data'] = [data.to_vega() for data in self._data.values()]
        json['marks'] = [mark.to_vega() for mark in self._markers]

        # Axes
        json['axes'] = [{'orient': 'bottom', 'scale': 'xscale', 'title': 'Time'},
                        {'orient': 'left', 'scale': 'yscale', 'title': 'Intensity'}]

        return json
