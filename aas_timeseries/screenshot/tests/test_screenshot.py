import os

from astropy import units as u
from astropy.timeseries import TimeSeries

from aas_timeseries.visualization import InteractiveTimeSeriesFigure
from aas_timeseries.screenshot import interactive_screenshot


def test_interactive_screenshot(tmpdir):

    ts = TimeSeries(time_start='2016-03-22T12:30:31',
                    time_delta=3 * u.s, n_samples=5)
    ts['flux'] = [1, 2, 3, 4, 5]

    filename_json = tmpdir.join('figure.json').strpath
    filename_png = tmpdir.join('figure').strpath

    figure = InteractiveTimeSeriesFigure()
    markers = figure.add_markers(time_series=ts, column='flux', label='Markers')
    figure.add_line(time_series=ts, column='flux', label='Line')

    figure.add_view(title="only markers", include=[markers])

    figure.save_vega_json(filename_json, embed_data=True)

    interactive_screenshot(filename_json, filename_png)

    assert os.path.exists(filename_png + '.png')
    assert os.path.exists(filename_png + '_view1.png')
