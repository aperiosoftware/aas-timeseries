import os
import tempfile

import pytest
from traitlets import TraitError

from astropy import units as u
from astropy.timeseries import TimeSeries

from aas_timeseries.visualization import InteractiveTimeSeriesFigure

DATA = os.path.abspath(os.path.join(os.path.dirname(__file__), 'data'))


def compare_to_reference_json(tmpdir, test_name):

    tmpdir = tmpdir.strpath

    expected_files = sorted(os.listdir(os.path.join(DATA, test_name)))
    actual_files = sorted(os.listdir(tmpdir))

    assert expected_files == actual_files

    for filename in expected_files:

        with open(os.path.join(DATA, test_name, filename)) as f:
            expected = f.read().strip()
        with open(os.path.join(tmpdir, filename)) as f:
            actual = f.read().strip()

        # Normalize line endings
        expected = expected.replace('\r\n', '\n').replace('\r', '\n')
        actual = actual.replace('\r\n', '\n').replace('\r', '\n')

        assert expected == actual


def test_basic(tmpdir, deterministic_uuid):

    ts = TimeSeries(time_start='2016-03-22T12:30:31', time_delta=3 * u.s, n_samples=5)
    ts['flux'] = [1, 2, 3, 4, 5]
    ts['error'] = [1, 2, 3, 4, 5]

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

    figure.save_vega_json(tmpdir.join('figure.json').strpath)

    compare_to_reference_json(tmpdir, 'basic')


def test_save_options_embed(tmpdir, deterministic_uuid):

    ts = TimeSeries(time_start='2016-03-22T12:30:31', time_delta=3 * u.s, n_samples=5)
    ts['flux'] = [1, 2, 3, 4, 5]
    ts['error'] = [1, 2, 3, 4, 5]

    figure = InteractiveTimeSeriesFigure()
    figure.add_markers(time_series=ts, column='flux', label='Markers')
    figure.save_vega_json(tmpdir.join('figure.json').strpath, embed_data=True)
    compare_to_reference_json(tmpdir, 'save_options_embed')


def test_save_options_no_minimize(tmpdir, deterministic_uuid):

    ts = TimeSeries(time_start='2016-03-22T12:30:31', time_delta=3 * u.s, n_samples=5)
    ts['flux'] = [1, 2, 3, 4, 5]
    ts['error'] = [1, 2, 3, 4, 5]

    figure = InteractiveTimeSeriesFigure()
    figure.add_markers(time_series=ts, column='flux', label='Markers')

    figure.save_vega_json(tmpdir.join('figure.json').strpath, minimize_data=False)
    compare_to_reference_json(tmpdir, 'save_options_no_minimize')


def test_save_options_export_bundle(tmpdir):

    ts = TimeSeries(time_start='2016-03-22T12:30:31', time_delta=3 * u.s, n_samples=5)
    ts['flux'] = [1, 2, 3, 4, 5]
    ts['error'] = [1, 2, 3, 4, 5]

    figure = InteractiveTimeSeriesFigure()
    figure.add_markers(time_series=ts, column='flux', label='Markers')

    figure.export_interactive_bundle(tmpdir.join('figure.zip').strpath)


def test_column_validation():

    # Test the validation provied by ColumnTrait

    ts = TimeSeries(time_start='2016-03-22T12:30:31', time_delta=3 * u.s, n_samples=5)
    ts['flux'] = [1, 2, 3, 4, 5]
    ts['error'] = [1, 2, 3, 4, 5]

    figure = InteractiveTimeSeriesFigure()
    with pytest.raises(TraitError) as exc:
        figure.add_markers(time_series=ts, column='flux2', label='Markers')
    assert exc.value.args[0] == 'flux2 is not a valid column name'


def test_limits(tmpdir):

    ts = TimeSeries(time_start='2016-03-22T12:30:31', time_delta=3 * u.s, n_samples=5)
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

    ts = TimeSeries(time_start='2016-03-22T12:30:31', time_delta=3 * u.s, n_samples=5)
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

    ts = TimeSeries(time_start='2016-03-22T12:30:31', time_delta=3 * u.s, n_samples=5)
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


class TestUnit:

    # Make sure that things work as expected when units are present, and that
    # the correct errors are raised when mixing data with and without units.

    def setup_method(self, method):

        self.ts = TimeSeries(time_start='2016-03-22T12:30:31', time_delta=3 * u.s, n_samples=5)
        self.ts['flux'] = [1, 2, 3, 4, 5]
        self.ts['error'] = [1, 2, 3, 4, 5]
        self.ts['flux_with_unit'] = [1, 2, 3, 4, 5] * u.Jy
        self.ts['error_with_unit'] = [1, 2, 3, 4, 5] * u.mJy

        self.figure = InteractiveTimeSeriesFigure()

    def test_basic(self, tmpdir):
        # Make sure things work for a simple example with just one layer
        self.figure.add_markers(time_series=self.ts, column='flux_with_unit', label='Markers')
        self.figure.save_vega_json(tmpdir.join('figure.json').strpath)

    def test_all_markers(self, tmpdir):
        # A test with all the layer types and convertible units
        self.figure.add_markers(time_series=self.ts, column='flux_with_unit', label='Markers')
        self.figure.add_line(time_series=self.ts, column='flux_with_unit', label='Line')
        self.figure.add_markers(time_series=self.ts, column='flux_with_unit', error='error_with_unit', label='Markers with Errors')
        self.figure.add_vertical_line(self.ts.time[3], label='Vertical Line')
        self.figure.add_vertical_range(self.ts.time[0], self.ts.time[-1], label='Vertical Range')
        self.figure.add_horizontal_line(3 * u.MJy, label='Horizontal Line')
        self.figure.add_horizontal_range(5000 * u.mJy, 6 * u.Jy, label='Horizontal Range')
        self.figure.add_range(time_series=self.ts, column_lower='flux_with_unit', column_upper='error_with_unit', label='Range')
        self.figure.add_text(time=self.ts.time[2], value=self.ts['flux_with_unit'][0], text='My Label', label='Range')
        self.figure.save_vega_json(tmpdir.join('figure.json').strpath)

    def test_compatible_limits(self, tmpdir):
        # Set the limits using compatible units
        self.figure.add_markers(time_series=self.ts, column='flux_with_unit', label='Markers')
        self.figure.ylim = (1e-6 * u.MJy, 6000 * u.mJy)
        view = self.figure.add_view('my view')
        view.ylim = (2e-6 * u.MJy, 4000 * u.mJy)
        self.figure.save_vega_json(tmpdir.join('figure.json').strpath)

    def test_incompatible_limits(self, tmpdir):
        # Set the limits using incompatible units
        self.figure.add_markers(time_series=self.ts, column='flux_with_unit', label='Markers')
        self.figure.ylim = 1, 6
        with pytest.raises(u.UnitsError) as exc:
            self.figure.save_vega_json(tmpdir.join('figure.json').strpath)
        assert exc.value.args[0] == 'Limits for y axis are dimensionless but expected units of Jy'

    def test_incompatible_limits_view(self, tmpdir):
        # Set the limits using incompatible units (with a view)
        self.figure.add_markers(time_series=self.ts, column='flux_with_unit', label='Markers')
        view = self.figure.add_view('my view')
        view.ylim = 1, 6
        with pytest.raises(u.UnitsError) as exc:
            self.figure.save_vega_json(tmpdir.join('figure.json').strpath)
        assert exc.value.args[0] == "Limits for y axis are dimensionless but expected units of Jy"

    def test_two_marker_layer_incompatible(self, tmpdir):
        self.figure.add_markers(time_series=self.ts, column='flux_with_unit', label='Markers')
        self.figure.add_markers(time_series=self.ts, column='flux', label='Markers')
        with pytest.raises(u.UnitsError) as exc:
            self.figure.save_vega_json(tmpdir.join('figure.json').strpath)
        assert exc.value.args[0] == "Cannot convert the units '' of column 'flux' to the required units of 'Jy'"

    def test_incompatible_overlays(self, tmpdir):
        self.figure.add_markers(time_series=self.ts, column='flux_with_unit', label='Markers')
        self.figure.add_markers(time_series=self.ts, column='flux', label='Markers')
        with pytest.raises(u.UnitsError) as exc:
            self.figure.save_vega_json(tmpdir.join('figure.json').strpath)
        assert exc.value.args[0] == "Cannot convert the units '' of column 'flux' to the required units of 'Jy'"

    def test_custom_yunit(self, tmpdir):
        self.figure.add_markers(time_series=self.ts, column='flux_with_unit', label='Markers')
        self.figure.yunit = u.MJy
        self.figure.save_vega_json(tmpdir.join('figure.json').strpath)
        self.figure.yunit = 'mJy'  # with a string
        self.figure.save_vega_json(tmpdir.join('figure.json').strpath)

    def test_custom_incompatible_yunit(self, tmpdir):
        self.figure.add_markers(time_series=self.ts, column='flux_with_unit', label='Markers')
        self.figure.yunit = u.m
        with pytest.raises(u.UnitsError) as exc:
            self.figure.save_vega_json(tmpdir.join('figure.json').strpath)
        assert exc.value.args[0] == "Cannot convert the units 'Jy' of column 'flux_with_unit' to the required units of 'm'"

    def test_empty_base_figure(self, tmpdir):
        # Check that things work fine if the only layer is in a view
        view = self.figure.add_view('my view')
        view.add_markers(time_series=self.ts, column='flux_with_unit', label='Markers')
        self.figure.save_vega_json(tmpdir.join('figure.json').strpath)

    def test_no_data_layers(self, tmpdir):
        # In the case where there are no layers that depend on data, the default
        # assumed unit is u.one so adding a line with a unit will raise an error.
        # In future we might want to consider making this work.
        self.figure.add_horizontal_line(3 * u.mJy, label='Line')
        with pytest.raises(u.UnitsError) as exc:
            self.figure.save_vega_json(tmpdir.join('figure.json').strpath)
        assert exc.value.args[0] == "'mJy' (spectral flux density) and '' (dimensionless) are not convertible"
