from qtpy.QtWebEngineWidgets import QWebEngineView, QWebEnginePage, WEBENGINE
from qtpy import QtGui, QtWidgets, QtCore

__all__ = ['get_qt_web_widget']


class TimeSeriesWebEnginePage(QWebEnginePage):
    """
    Subclass of QWebEnginePage that can check when WWT is ready for
    commands.
    """

    wwt_ready = QtCore.Signal()

    def __init__(self, parent=None):
        super(TimeSeriesWebEnginePage, self).__init__(parent=parent)
        if not WEBENGINE:
            self._frame = self.mainFrame()

    if WEBENGINE:

        def javaScriptConsoleMessage(self, level=None, message=None,
                                     line_number=None, source_id=None):
            print(f'{message} (level={level}, line_number={line_number}, '
                  f'source_id={source_id})')

        def _process_js_response(self, result):
            self._js_response_received = True
            self._js_response = result

        def runJavaScript(self, code, asynchronous=True):
            app = QtWidgets.QApplication.instance()
            if asynchronous:
                super(TimeSeriesWebEnginePage, self).runJavaScript(code)
            else:
                self._js_response_received = False
                self._js_response = None
                super(TimeSeriesWebEnginePage, self).runJavaScript(code, self._process_js_response)
                while not self._js_response_received:
                    app.processEvents()
                return self._js_response

    else:

        def javaScriptConsoleMessage(self, message=None, line_number=None,
                                     source_id=None):
            print(f'{message} (line_number={line_number}, '
                  f'source_id={source_id})')


class TimeSeriesWebEngineView(QWebEngineView):

    def save_to_file(self, filename):
        image = QtGui.QImage(self.size(), QtGui.QImage.Format_RGB32)
        painter = QtGui.QPainter(image)
        self.render(painter)
        image.save(filename)
        painter.end()


def get_qt_web_widget(url):
    web = TimeSeriesWebEngineView()
    page = TimeSeriesWebEnginePage()
    page.setView(web)
    web.setPage(page)
    web.setUrl(QtCore.QUrl(url))
    return web, page
