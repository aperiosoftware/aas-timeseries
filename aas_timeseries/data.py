import uuid

from astropy.units import Quantity, UnitsError

__all__ = ['Data']


class Data:

    def __init__(self, time_series):
        self.time_series = time_series
        self.uuid = str(uuid.uuid4())
        self.time_column = 'time'

    def column_to_values(self, colname, unit):

        # First make sure the column is a quantity
        quantity = Quantity(self.time_series[colname], copy=False)

        if quantity.unit.is_equivalent(unit):
            return quantity.to_value(unit)
        else:
            raise UnitsError(f"Cannot convert the units '{quantity.unit}' of "
                             f"column '{colname}' to the required units of "
                             f"'{unit}'")

    def unit(self, colname):
        return Quantity(self.time_series[colname], copy=False).unit
