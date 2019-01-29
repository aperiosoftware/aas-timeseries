from collections import defaultdict

from palettable.colorbrewer.qualitative import Paired_5

from aas_timeseries.marks import Text, Symbol, Line, VerticalLine, HorizontalLine

__all__ = ['auto_assign_colors']

ALWAYS_BLACK = (Text,)
BLACK_IF_ONLY_ONE = (Symbol, Line, VerticalLine, HorizontalLine)


def auto_assign_colors(markers):

    colors = []

    markers_by_type = defaultdict(list)
    for marker in markers:
        markers_by_type[type(marker)].append(marker)

    offset = 0

    for marker in markers:
        if isinstance(marker, ALWAYS_BLACK):
            colors.append('#000000')
        elif isinstance(marker, BLACK_IF_ONLY_ONE) and len(markers_by_type[type(marker)]) == 1:
            colors.append('#000000')
        else:
            icolor = markers_by_type[type(marker)].index(marker)
            current = (offset + icolor) % 4
            colors.append(Paired_5.hex_colors[current])
            offset = current + 1

    return colors
