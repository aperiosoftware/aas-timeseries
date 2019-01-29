from qtpy.QtWebEngineWidgets import QWebEngineView, QWebEnginePage, WEBENGINE
from qtpy import QtGui, QtCore

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
