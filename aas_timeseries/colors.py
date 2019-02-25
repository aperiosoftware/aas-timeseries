from collections import defaultdict

from palettable.colorbrewer.qualitative import Paired_5

from aas_timeseries.layers import Text, Markers, Line, VerticalLine, HorizontalLine

__all__ = ['auto_assign_colors']

ALWAYS_BLACK = (Text,)
BLACK_IF_ONLY_ONE = (Markers, Line, VerticalLine, HorizontalLine)


def auto_assign_colors(layers):

    colors = []

    layers_by_type = defaultdict(list)
    for layer in layers:
        layers_by_type[type(layer)].append(layer)

    offset = 0

    for layer in layers:
        if isinstance(layer, ALWAYS_BLACK):
            colors.append('#000000')
        elif isinstance(layer, BLACK_IF_ONLY_ONE) and len(layers_by_type[type(layer)]) == 1:
            colors.append('#000000')
        else:
            icolor = layers_by_type[type(layer)].index(layer)
            current = (offset + icolor) % 4
            colors.append(Paired_5.hex_colors[current])
            offset = current + 1

    return colors
