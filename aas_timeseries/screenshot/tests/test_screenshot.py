import os

from astropy import units as u
from astropy_timeseries import TimeSeries

from aas_timeseries.visualization import InteractiveTimeSeriesFigure
from aas_timeseries.screenshot import interactive_screenshot


def test_interactive_screenshot(tmpdir):

    ts = TimeSeries(time='2016-03-22T12:30:31',
                    time_delta=3 * u.s, n_samples=5)
    ts['flux'] = [1, 2, 3, 4, 5]

    filename_json = tmpdir.join('figure.json').strpath
    filename_png = tmpdir.join('figure.png').strpath

    figure = InteractiveTimeSeriesFigure()
    figure.add_markers(time_series=ts, column='flux', label='Markers')

    figure.save_interactive(filename_json)

    interactive_screenshot(filename_json, filename_png)

    assert os.path.exists(filename_png)
