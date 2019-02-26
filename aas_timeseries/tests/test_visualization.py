import pytest
from traitlets import TraitError

from astropy import units as u
from astropy_timeseries import TimeSeries

from aas_timeseries.visualization import InteractiveTimeSeriesFigure


def test_basic(tmpdir):

    ts = TimeSeries(time='2016-03-22T12:30:31', time_delta=3 * u.s, n_samples=5)
    ts['flux'] = [1, 2, 3, 4, 5]
    ts['error'] = [1, 2, 3, 4, 5]

    filename = tmpdir.join('figure.json').strpath

    figure = InteractiveTimeSeriesFigure()
    figure.add_markers(time_series=ts, column='flux', label='Markers')
    figure.add_line(time_series=ts, column='flux', label='Line')
    figure.add_markers(time_series=ts, column='flux', error='error', label='Markers with Errors')
    figure.add_vertical_line(ts.time[3], label='Vertical Line')
    figure.add_vertical_range(ts.time[0], ts.time[-1], label='Vertical Range')
    figure.add_horizontal_line(3, label='Horizontal Line')
    figure.add_horizontal_range(5, 6, label='Horizontal Range')
    figure.add_range(time_series=ts, column_lower='flux', column_upper='error', label='Range')
    figure.add_text(time=ts.time[2], value=float(ts['flux'][0]), text='My Label', label='Range')
    figure.save_vega_json(filename)


def test_save_options(tmpdir):

    ts = TimeSeries(time='2016-03-22T12:30:31', time_delta=3 * u.s, n_samples=5)
    ts['flux'] = [1, 2, 3, 4, 5]
    ts['error'] = [1, 2, 3, 4, 5]

    figure = InteractiveTimeSeriesFigure()
    figure.add_markers(time_series=ts, column='flux', label='Markers')
    figure.save_vega_json(tmpdir.join('figure1.json').strpath, embed_data=True)
    figure.save_vega_json(tmpdir.join('figure2.json').strpath, minimize_data=False)
    figure.export_interactive_bundle(tmpdir.join('figure.zip').strpath)


def test_column_validation():

    # Test the validation provied by ColumnTrait

    ts = TimeSeries(time='2016-03-22T12:30:31', time_delta=3 * u.s, n_samples=5)
    ts['flux'] = [1, 2, 3, 4, 5]
    ts['error'] = [1, 2, 3, 4, 5]

    figure = InteractiveTimeSeriesFigure()
    with pytest.raises(TraitError) as exc:
        figure.add_markers(time_series=ts, column='flux2', label='Markers')
    assert exc.value.args[0] == 'flux2 is not a valid column name'


def test_limits(tmpdir):

    ts = TimeSeries(time='2016-03-22T12:30:31', time_delta=3 * u.s, n_samples=5)
    ts['flux'] = [1, 2, 3, 4, 5]
    ts['error'] = [1, 2, 3, 4, 5]

    filename = tmpdir.join('figure.json').strpath

    figure = InteractiveTimeSeriesFigure()
    figure.add_markers(time_series=ts, column='flux', label='Markers')
    figure.xlim = ts.time[0], ts.time[-1]
    figure.ylim = 0, 10
    figure.save_vega_json(filename)

    with pytest.raises(TypeError) as exc:
        figure.xlim = 0, 1
    assert exc.value.args[0] == 'xlim should be a typle of two Time instances'

    with pytest.raises(ValueError) as exc:
        figure.xlim = ts.time[0], ts.time[-1], ts.time[-4]
    assert exc.value.args[0] == 'xlim should be a tuple of two elements'


def test_views(tmpdir):

    ts = TimeSeries(time='2016-03-22T12:30:31', time_delta=3 * u.s, n_samples=5)
    ts['flux'] = [1, 2, 3, 4, 5]
    ts['error'] = [1, 2, 3, 4, 5]

    filename = tmpdir.join('figure.json').strpath

    figure = InteractiveTimeSeriesFigure()

    markers = figure.add_markers(time_series=ts, column='flux', label='Markers')
    line = figure.add_line(time_series=ts, column='flux', label='Line')

    # By default views inherit all layers from base figure
    view1 = figure.add_view('Test1')
    assert figure.layers == [markers, line]
    assert view1.layers == [markers, line]

    # And we can add view-specific layers to them
    vertical = view1.add_vertical_line(ts.time[3], label='Vertical Line')
    assert figure.layers == [markers, line]
    assert view1.layers == [markers, line, vertical]

    # But adding layers to the figure after the view is created doesnt' cause
    # them to get added to the view
    horizontal = figure.add_horizontal_line(3., label='Horizontal Line')
    assert figure.layers == [markers, line, horizontal]
    assert view1.layers == [markers, line, vertical]

    # We can use include to specify which initial layers to include
    view2 = figure.add_view('Test1', include=[markers])
    assert view2.layers == [markers]

    # and exclude to, well, exclude layers
    view3 = figure.add_view('Test1', exclude=[markers])
    assert view3.layers == [line, horizontal]

    # We also provide an 'empty' shortcut that means include=[]
    view4 = figure.add_view('Test1', empty=True)
    assert view4.layers == []

    # We tell the user if the include or exclude list contain invalid values
    with pytest.raises(ValueError) as exc:
        figure.add_view('Test1', exclude=[vertical])
    assert 'does not exist in base figure' in exc.value.args[0]
    with pytest.raises(ValueError) as exc:
        figure.add_view('Test1', include=[vertical])
    assert 'does not exist in base figure' in exc.value.args[0]

    figure.save_vega_json(filename)


def test_remove():

    ts = TimeSeries(time='2016-03-22T12:30:31', time_delta=3 * u.s, n_samples=5)
    ts['flux'] = [1, 2, 3, 4, 5]
    ts['error'] = [1, 2, 3, 4, 5]

    figure = InteractiveTimeSeriesFigure()
    assert len(figure.layers) == 0
    markers = figure.add_markers(time_series=ts, column='flux', label='Markers')
    assert len(figure.layers) == 1
    line = figure.add_line(time_series=ts, column='flux', label='Line')
    assert len(figure.layers) == 2

    view = figure.add_view('Test view')
    assert len(view.layers) == 2

    range = view.add_vertical_range(ts.time[0], ts.time[-1], label='Vertical Range')

    assert len(figure.layers) == 2
    assert len(view.layers) == 3

    # Removing using the .remove() method on a layer removes it from the
    # figure and all views where it is.
    line.remove()
    assert len(figure.layers) == 1
    assert len(view.layers) == 2

    # Removing from the .remove() method on a view removes it just from the view
    view.remove(markers)
    assert len(figure.layers) == 1
    assert len(view.layers) == 1

    # Check removing a view-specific layer
    range.remove()
    assert len(figure.layers) == 1
    assert len(view.layers) == 0

    # Remove last layer from figure
    markers.remove()

    with pytest.raises(Exception) as exc:
        markers.remove()
    assert exc.value.args[0] == "Layer 'Markers' is no longer in a figure/view"

    with pytest.raises(Exception) as exc:
        figure.remove(markers)
    assert exc.value.args[0] == "Layer 'Markers' is not in figure"

    with pytest.raises(Exception) as exc:
        view.remove(markers)
    assert exc.value.args[0] == "Layer 'Markers' is not in view"
