from collections import defaultdict

from palettable.colorbrewer.qualitative import Paired_5

from aas_timeseries.layers import Text, Markers, Line, VerticalLine, HorizontalLine

__all__ = ['auto_assign_colors']

ALWAYS_BLACK = (Text,)
BLACK_IF_ONLY_ONE = (Markers, Line, VerticalLine, HorizontalLine)


def auto_assign_colors(layers):

    colors = []

    layers_by_type = defaultdict(list)
    for marker in layers:
        layers_by_type[type(marker)].append(marker)

    offset = 0

    for marker in layers:
        if isinstance(marker, ALWAYS_BLACK):
            colors.append('#000000')
        elif isinstance(marker, BLACK_IF_ONLY_ONE) and len(layers_by_type[type(marker)]) == 1:
            colors.append('#000000')
        else:
            icolor = layers_by_type[type(marker)].index(marker)
            current = (offset + icolor) % 4
            colors.append(Paired_5.hex_colors[current])
            offset = current + 1

    return colors
