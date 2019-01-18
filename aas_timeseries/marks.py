import uuid
from traitlets import Unicode, Float, Any, validate, HasTraits

# Get color from pywwt




class BaseMark(HasTraits):
    """
    Base class for any mark object
    """
    zindex = Float()


class Symbol(BaseMark):

    data = Any()
    label = Unicode()
    column = Unicode()
    shape = Unicode('circle')
    color = Unicode('#000000')
    opacity = Float(1)
    size = Float(10)

    def to_vega(self):
        vega = {'type': 'symbol',
                'description': self.label,
                'from': {'data': self.data.uuid},
                'encode': {'enter': {'x': {'scale': 'xscale', 'field': self.data.time_column},
                                     'y': {'scale': 'yscale', 'field': self.column},
                                     'shape': {'value': self.shape}},
                           'update':{'shape': {'value': self.shape},
                                     'zindex': {'value': self.zindex},
                                     'size': {'value': self.size},
                                     'fill': {'value': self.color},
                                     'fillOpacity': {'value': self.opacity}}}}
        return vega


class Line(BaseMark):

    data = Any()
    label = Unicode()
    column = Unicode()
    color = Unicode('#000000')
    opacity = Float(1)
    width = Float(1)

    def to_vega(self):
        vega = {'type': 'line',
                'description': self.label,
                'from': {'data': self.data.uuid},
                'encode': {'enter': {'x': {'scale': 'xscale', 'field': self.data.time_column},
                                     'y': {'scale': 'yscale', 'field': self.column},
                                     'zindex': {'value': self.zindex},
                                     'strokeWidth': {'value': self.width},
                                     'fill': {'value': self.color},
                                     'fillOpacity': {'value': self.opacity}}}}
        return vega
#
# class Rule(BaseMark):
#     pass
#
#
# class Area(BaseMark):
#     pass
#
#
# class Rect(BaseMark):  # used for error bars
#     pass
#
#
# class Text(BaseMark):
#
#     color = Unicode()
#     opacity = Float()
#
#     pass
