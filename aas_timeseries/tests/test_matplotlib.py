# -*- coding: utf-8 -*-

from matplotlib import pyplot as plt

import pytest

from aas_timeseries.matplotlib import (PhaseAsDegreesLocator,
                                       PhaseAsDegreesFormatter,
                                       PhaseAsRadiansLocator,
                                       PhaseAsRadiansFormatter)


def get_ticklabels(axis):
    return [x.get_text() for x in axis.get_ticklabels()]


DEG_CASES = [((-20, 50), ['-5000°', '0°', '5000°', '10000°', '15000°']),
             ((0., 1.), ['0°', '60°', '120°', '180°', '240°', '300°', '360°']),
             ((0.3, 0.4), ['108°', '114°', '120°', '126°', '132°', '138°', '144°']),
             ((0.555, 0.556), ['199.84°', '199.92°', '200°', '200.08°', '200.16°'])]


@pytest.mark.parametrize(('limits', 'expected'), DEG_CASES)
def test_phase_degrees(tmpdir, limits, expected):

    fig = plt.figure()
    ax = fig.add_subplot(1, 1, 1)
    ax.xaxis.set_major_locator(PhaseAsDegreesLocator())
    ax.xaxis.set_major_formatter(PhaseAsDegreesFormatter())
    ax.set_xlim(*limits)
    fig.savefig(tmpdir.join('figure.png'))
    assert get_ticklabels(ax.xaxis) == expected


RAD_CASES = [((-20, 50), ['-32π', '-16π', '0', '16π', '32π', '48π', '64π', '80π', '96π']),
             ((0., 1.), ['0', 'π/2', 'π', '3π/2', '2π']),
             ((0.3, 0.4), ['5π/8', '11π/16', '3π/4']),
             ((0.555, 0.556), ['1.1104π', '1.1108π', '1.1113π', '1.1118π'])]


@pytest.mark.parametrize(('limits', 'expected'), RAD_CASES)
def test_phase_radians(tmpdir, limits, expected):

    fig = plt.figure()
    ax = fig.add_subplot(1, 1, 1)
    ax.xaxis.set_major_locator(PhaseAsRadiansLocator())
    ax.xaxis.set_major_formatter(PhaseAsRadiansFormatter())
    ax.set_xlim(*limits)
    fig.savefig(tmpdir.join('figure.png'))
    assert get_ticklabels(ax.xaxis) == expected
