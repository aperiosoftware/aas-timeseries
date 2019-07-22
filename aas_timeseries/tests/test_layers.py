from unittest.mock import MagicMock
from aas_timeseries.data import Data
from aas_timeseries.layers import Markers


def test_tooltip_options():

    fig = MagicMock()
    time_series = MagicMock()
    time_series.colnames = ['the_time', 'the_flux', 'the_other']
    data = Data(time_series)

    marker = Markers(parent=fig)
    marker.data = data
    marker.time_column = 'the_time'
    marker.column = 'the_flux'

    tooltip = marker.to_vega()[0]['encode']['hover']['tooltip']
    assert tooltip == {'signal': "{'the_time': datum.the_time, 'the_flux': datum.the_flux}"}

    marker.tooltip = False

    assert 'hover' not in marker.to_vega()[0]['encode']

    marker.tooltip = ('the_time', 'the_other')
    tooltip = marker.to_vega()[0]['encode']['hover']['tooltip']
    assert tooltip == {'signal': "{'the_time': datum.the_time, 'the_other': datum.the_other}"}

    marker.tooltip = ['the_flux']
    tooltip = marker.to_vega()[0]['encode']['hover']['tooltip']
    assert tooltip == {'signal': "{'the_flux': datum.the_flux}"}

    marker.tooltip = {'the_time': 'Time', 'the_flux': 'Flux'}
    tooltip = marker.to_vega()[0]['encode']['hover']['tooltip']
    assert tooltip == {'signal': "{'Time': datum.the_time, 'Flux': datum.the_flux}"}
