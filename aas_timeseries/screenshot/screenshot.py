# The main function in this module takes a JSON file and renders it to
# a PNG file. This uses Qt to launch a WebEngine widget, and serves the
# required files using flask, then saves the screenshot of the contents
# of the widget with Qt.

import os
import shutil
import time
import tempfile

from qtpy import QtWidgets

from aas_timeseries.screenshot.data_server import get_data_server
from aas_timeseries.screenshot.qt_web_widget import get_qt_web_widget

__all__ = ['interactive_screenshot']

ROOT = os.path.dirname(__file__)
TIMEOUT = 60  # seconds
WAIT_TIME = 2  # seconds


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

    app = QtWidgets.QApplication.instance()
    if app is None:
        app = QtWidgets.QApplication([''])

    web, page = get_qt_web_widget(url)
    web.resize(600, 400)
    web.show()

    # Find the views that are present in the figure

    start = time.time()
    while time.time() - start < TIMEOUT:
        app.processEvents()
        ready = page.runJavaScript('(typeof(figure_ready) != "undefined") && figure_ready == 1;', asynchronous=False)
        if ready:
            break
    else:
        raise ValueError("Timed out while waiting for interactive figure to open")

    # Temporary: at the moment it seems the figure isn't quite ready for real
    # (https://github.com/aperiosoftware/timeseries.js/issues/65) so just wait
    # a little longer
    start = time.time()
    while time.time() - start < WAIT_TIME:
        app.processEvents()

    web.save_to_file(prefix + '.png')

    # Find the views that are present in the figure
    views = page.runJavaScript('figure.getViews();', asynchronous=False)

    if len(views) > 1:
        for view_index in range(1, len(views)):

            page.runJavaScript('figure.setView({0});'.format(view_index), asynchronous=False)

            # There is currently no way to know if the view has been actually
            # refreshed (https://github.com/aperiosoftware/timeseries.js/issues/64)
            # so just wait a little.

            start = time.time()
            while time.time() - start < WAIT_TIME:
                app.processEvents()

            web.save_to_file(prefix + '_view{0}.png'.format(view_index))

    web.close()
    app.processEvents()

    # We need to do this to force garbage collection and avoid a
    # segmentation fault.
    page = web = None  # noqa
