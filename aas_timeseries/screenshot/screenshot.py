# The main function in this module takes a JSON file and renders it to
# a PNG file. This uses Qt to launch a WebEngine widget, and serves the
# required files using tornado, then saves the screenshot of the contents
# of the widget with Qt.

import os
import json
import shutil
import time
import tempfile

from qtpy import QtWidgets

from aas_timeseries.screenshot.data_server import get_data_server
from aas_timeseries.screenshot.qt_web_widget import get_qt_web_widget

__all__ = ['interactive_screenshot']

ROOT = os.path.dirname(__file__)
TIMEOUT = 60  # seconds
WAIT_TIME = 0.1  # seconds

SET_VIEW_CODE = """
var view_ready = false;

function on_view_ready() {{
    view_ready = true;
}}

figure.setView({0}, {{'callback': on_view_ready}});
"""


def wait_for_true(app, page, var):
    """
    Wait until variable ``var`` is ``true`` in Javascript.
    """
    start = time.time()
    while time.time() - start < TIMEOUT:
        app.processEvents()
        ready = page.runJavaScript('(typeof({0}) != "undefined") && {0} == 1;'.format(var), asynchronous=False)
        if ready:
            break
    else:
        raise ValueError("Timed out while waiting for {0}==true".format(var))

    # Wait a little longer just to be sure
    start = time.time()
    while time.time() - start < WAIT_TIME:
        app.processEvents()


def interactive_screenshot(json_filename, prefix):
    """
    Given a JSON file, save the figure to one or more PNG files. If multiple
    views are present, each view will result in a separate PNG file.
    """

    tmpdir = tempfile.mkdtemp()
    tmp_html = os.path.join(tmpdir, 'page.html')
    tmp_json = os.path.join(tmpdir, 'figure.json')

    shutil.copy(os.path.join(ROOT, 'template.html'), tmp_html)
    shutil.copy(json_filename, tmp_json)

    server = get_data_server()
    url = server.serve_file(tmp_html)
    server.serve_file(tmp_json)

    # Check if we need to serve any csv files
    with open(json_filename) as f:
        figure = json.load(f)
    for data in figure['data']:
        if 'url' in data:
            server.serve_file(os.path.join(os.path.dirname(json_filename), data['url']))

    app = QtWidgets.QApplication.instance()
    if app is None:
        app = QtWidgets.QApplication([''])

    web, page = get_qt_web_widget(url)
    web.resize(figure['width'], figure['height'])
    web.show()

    # Wait for figure to be ready

    wait_for_true(app, page, 'figure_ready')

    web.save_to_file(prefix + '.png')

    # Find the views that are present in the figure
    views = page.runJavaScript('figure.getViews();', asynchronous=False)

    if len(views) > 1:
        for view_index in range(1, len(views)):

            page.runJavaScript(SET_VIEW_CODE.format(view_index), asynchronous=False)

            wait_for_true(app, page, 'view_ready')

            web.save_to_file(prefix + '_view{0}.png'.format(view_index))

    web.close()
    app.processEvents()

    # We need to do this to force garbage collection and avoid a
    # segmentation fault.
    page = web = None  # noqa
