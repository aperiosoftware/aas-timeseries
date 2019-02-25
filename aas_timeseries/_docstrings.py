# This file contains helper code to generate the parameters section
# of the top-level method docstrings based on the traits of the
# various layer objects. We do this statically rather than at run
# time since the docstrings should be readable when developers are
# reading code (not just users at runtime).

import os
from textwrap import wrap, indent

from aas_timeseries.layers import (Markers, Line, VerticalLine, VerticalRange,
                                   HorizontalLine, HorizontalRange, Range, Text)
from aas_timeseries.traits import (Unicode, Float, PositiveFloat, Any, Opacity,
                                   Color, UnicodeChoice, DataTrait, ColumnTrait,
                                   AstropyTime)

layers = [Markers, Line, VerticalLine, VerticalRange,
          HorizontalLine, HorizontalRange, Range, Text]

ORDER = ['time', 'value', 'time_lower', 'time_upper', 'value_lower',
         'value_upper', 'weight', 'baseline', 'align', 'angle', 'data',
         'column', 'error', 'column_lower', 'column_upper', 'text',
         'width', 'shape', 'size', 'color', 'opacity', 'edge_color',
         'edge_opacity', 'edge_width', 'label']

REQUIRED = ['data', 'column', 'column_lower', 'column_upper', 'time',
            'time_lower', 'time_upper', 'value', 'value_lower', 'value_upper']

TYPE = {
    Unicode: 'str',
    Float: 'float or int',
    PositiveFloat: 'float or int',
    Any: 'float',
    Opacity: 'float or int',
    Color: 'str or tuple',
    DataTrait: '`~astropy_timeseries.TimeSeries`',
    ColumnTrait: 'str',
    AstropyTime: '`~astropy.time.Time`'
}


def traits_to_docstring(cls):
    """
    Convert the documentation about traits to parameters in a docstring.
    """
    docstring = "Parameters\n----------\n"
    for name in sorted(cls.class_traits(), key=ORDER.index):
        trait = cls.class_traits()[name]
        if type(trait) == UnicodeChoice:
            type_str = '{' + ', '.join(f"'{x}'" for x in trait.choices) + '}'
        else:
            type_str = TYPE[type(trait)]
        if name in REQUIRED:
            optional_str = ''
        else:
            optional_str = ', optional'
        docstring += f'{name} : ' + type_str + optional_str + '\n'
        if trait.help:
            docstring += indent(os.linesep.join(wrap(trait.help, width=72)), ' ' * 4) + '\n'
        else:
            raise Exception(f"No help string found for trait '{name}'")
    docstring = indent(docstring, ' ' * 8)
    return docstring


if __name__ == "__main__":
    for cls in layers:
        print('-' * 80)
        print(cls)
        print("")
        print(traits_to_docstring(cls))
