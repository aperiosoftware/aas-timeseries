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


def interactive_screenshot(json_filename, png_filename):

    tmpdir = tempfile.mkdtemp()
    tmp_html = os.path.join(tmpdir, 'page.html')
    tmp_json = os.path.join(tmpdir, 'data.json')

    shutil.copy(os.path.join(ROOT, 'template.html'), tmp_html)
    shutil.copy(json_filename, tmp_json)

    server = get_data_server()
    url = server.serve_file(tmp_html)
    server.serve_file(tmp_json)

    app = QtWidgets.QApplication([''])

    web, page = get_qt_web_widget(url)
    web.resize(600, 400)
    web.show()

    start = time.time()
    while time.time() - start < 2:
        app.processEvents()

    web.save_to_file(png_filename)

    web.close()
    app.processEvents()

    # We need to do this to force garbage collection and avoid a
    # segmentation fault.
    page = web = None  # noqa
