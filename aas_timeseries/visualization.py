from json import dump
from io import StringIO

from astropy.table import Table


__all__ = ['InteractiveTimeSeriesFigure']


class InteractiveTimeSeriesFigure:

    def __init__(self):
        self._data = {}

    def add_markers(self, ts, column, label):
        self._data[label] = (ts.time, ts[column])

    def save_interactive(self, filename):
        with open(filename, 'w') as f:
            dump(self._to_json(), f)

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
        json['data'] = []
        json['marks'] = []
        for label, (time, column) in self._data.items():

            # Create basic table with time and values
            table = Table()
            table['MJD'] = time.mjd
            table[column.info.name] = column

            s = StringIO()
            table.write(s, format='ascii.basic', delimiter=',')
            s.seek(0)
            csv_string = s.read()

            json['data'].append({'name': label,
                                 'values': csv_string,
                                 'format': {'type': 'csv',
                                            'parse': {'MJD': 'number',
                                                      column.info.name: 'number'}}})

            # Markers
            json['marks'].append({'type': 'symbol',
                                  'from': {'data': label},
                                  'encode': {'enter': {'x': {'scale': 'xscale', 'field': 'MJD'},
                                                       'y': {'scale': 'yscale', 'field': column.info.name},
                                                       'shape': {'value': 'circle'}}}})

        # Axes
        json['axes'] = [{'orient': 'bottom', 'scale': 'xscale', 'title': 'Time'},
                        {'orient': 'left', 'scale': 'yscale', 'title': 'Intensity'}]

        return json
