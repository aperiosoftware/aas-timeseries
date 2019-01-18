import uuid
from io import StringIO

from astropy.time import Time
from astropy.table import Table


class Data:
    def __init__(self, time_series):
        self.time_series = time_series
        self.uuid = str(uuid.uuid4())
        self.time_column = 'time'

    def to_vega(self):

        table = Table()
        table[self.time_column] = self.time_series.time.isot
        for colname in self.time_series.colnames:
            if colname != 'time':
                table[colname] = self.time_series[colname]

        s = StringIO()
        table.write(s, format='ascii.basic', delimiter=',')
        s.seek(0)
        csv_string = s.read()

        parse = {}
        for colname in table.colnames:
            column = table[colname]
            if colname == self.time_column:
                parse[colname] = 'date'
            elif column.dtype.kind in 'fi':
                parse[colname] = 'number'
            elif column.dtype.kind in 'b':
                parse[colname] = 'boolean'
            else:
                parse[colname] = 'string'

        vega = {'name': self.uuid,
                'values': csv_string,
                'format': {'type': 'csv',
                           'parse': parse}}

        return vega
