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
    error = Unicode(allow_none=True)
    shape = Unicode('circle')
    color = Unicode('#000000')
    opacity = Float(1)
    size = Float(10)

    def to_vega(self):

        # The main markers
        vega = [{'type': 'symbol',
                 'description': self.label,
                 'from': {'data': self.data.uuid},
                 'encode': {'enter': {'x': {'scale': 'xscale', 'field': self.data.time_column},
                                      'y': {'scale': 'yscale', 'field': self.column},
                                      'shape': {'value': self.shape}},
                            'update':{'shape': {'value': self.shape},
                                      'zindex': {'value': self.zindex},
                                      'size': {'value': self.size},
                                      'fill': {'value': self.color},
                                      'fillOpacity': {'value': self.opacity}}}}]

        # The error bars (if requested)
        if self.error:
            vega.append({'type': 'rect',
                         'description': self.label,
                         'from': {'data': self.data.uuid},
                         'encode': {'enter': {'x': {'scale': 'xscale', 'field': self.data.time_column},
                                         'y': {'scale': 'yscale', 'signal': f"datum['{self.column}'] - datum['{self.error}']"},
                                         'y2': {'scale': 'yscale', 'signal': f"datum['{self.column}'] + datum['{self.error}']"}},
                               'update':{'shape': {'value': self.shape},
                                         'zindex': {'value': self.zindex},
                                         'width': {'value': 1},
                                         'fill': {'value': self.color},
                                         'fillOpacity': {'value': self.opacity}}}})


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
                                     'stroke': {'value': self.color},
                                     'strokeOpacity': {'value': self.opacity}}}}
        return [vega]


class Range(BaseMark):

    data = Any()
    label = Unicode()
    column_lower = Unicode()
    column_upper = Unicode()
    color = Unicode('#000000')
    opacity = Float(1)

    def to_vega(self):
        vega = {'type': 'area',
                'description': self.label,
                'from': {'data': self.data.uuid},
                'encode': {'enter': {'x': {'scale': 'xscale', 'field': self.data.time_column},
                                     'y': {'scale': 'yscale', 'field': self.column_lower},
                                     'y2': {'scale': 'yscale', 'field': self.column_upper},
                                     'zindex': {'value': self.zindex},
                                     'fill': {'value': self.color},
                                     'fillOpacity': {'value': self.opacity}}}}
        return [vega]


class VerticalLine(BaseMark):

    label = Unicode()
    time = Any()
    color = Unicode('#000000')
    opacity = Float(1)
    width = Float(1)

    def to_vega(self):

        # FIXME: this is just a quick shortcut hack
        datetime = 'datetime' + str(tuple(self.time.datetime.timetuple()[:6]))

        vega = {'type': 'rule',
                'description': self.label,
                # FIXME: find a way to represent an infinite vertical line
                'encode': {'enter': {'x': {'scale': 'xscale', 'signal': datetime},
                                     'y': {'scale': 'yscale', 'value': -1e8},
                                     'y2': {'scale': 'yscale', 'value': 1e8},
                                     'zindex': {'value': self.zindex},
                                     'strokeWidth': {'value': self.width},
                                     'stroke': {'value': self.color},
                                     'strokeOpacity': {'value': self.opacity}}}}
        return [vega]


class VerticalRange(BaseMark):

    label = Unicode()
    from_time = Any()
    to_time = Any()
    color = Unicode('#000000')
    opacity = Float(1)
    width = Float(1)

    def to_vega(self):

        # FIXME: this is just a quick shortcut hack
        from_time = 'datetime' + str(tuple(self.from_time.datetime.timetuple()[:6]))
        to_time = 'datetime' + str(tuple(self.to_time.datetime.timetuple()[:6]))

        vega = {'type': 'rect',
                'description': self.label,
                # FIXME: find a way to represent an infinite vertical line
                'encode': {'enter': {'x': {'scale': 'xscale', 'signal': from_time},
                                     'x2': {'scale': 'xscale', 'signal': to_time},
                                     'y': {'scale': 'yscale', 'value': -1e8},
                                     'y2': {'scale': 'yscale', 'value': 1e8},
                                     'zindex': {'value': self.zindex},
                                     'fill': {'value': self.color},
                                     'fillOpacity': {'value': self.opacity}}}}
        return [vega]


class Text(BaseMark):

    label = Unicode()
    text = Unicode()
    x = Any()
    y = Float()
    color = Unicode('#000000')
    opacity = Float(1)
    weight = Unicode('normal')
    baseline = Unicode('middle')
    align = Unicode('left')
    angle = Float(0)

    def to_vega(self):

        datetime = 'datetime' + str(tuple(self.x.datetime.timetuple()[:6]))

        vega = {'type': 'text',
                'description': self.label,
                'encode': {'enter': {'x': {'scale': 'xscale', 'signal': datetime},
                                     'y': {'scale': 'yscale', 'value': self.y},
                                     'zindex': {'value': self.zindex},
                                     'fill': {'value': self.color},
                                     'fillOpacity': {'value': self.opacity},
                                     'fontWeigth': {'value': self.weight},
                                     'baseline': {'value': self.baseline},
                                     'align': {'value': self.align},
                                     'angle': {'value': self.angle}}}}
        return [vega]
