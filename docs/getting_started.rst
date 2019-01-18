Getting started
===============

To get started, make sure you have a time series that you want to make
an interactive figure of, and read it in using the `astropy-timeseries
<http://astropy-timeseries.readthedocs.org>`_ package. Here we will adopt
the same example as in the astropy-timeseries documentation, and start by
retrieving an Kepler lightcurve::

    >>> from astropy.utils.data import get_pkg_data_filename
    >>> filename = get_pkg_data_filename('timeseries/kplr010666592-2009131110544_slc.fits')  # doctest: +REMOTE_DATA

and reading it in::

    >>> from astropy_timeseries import TimeSeries
    >>> ts = TimeSeries.read(filename, format='kepler.fits')  # doctest: +REMOTE_DATA
    >>> ts[:5]  # doctest: +REMOTE_DATA
    <TimeSeries length=5>
              time             timecorr   ...   pos_corr1      pos_corr2
                                  d       ...     pixels         pixels
             object            float32    ...    float32        float32
    ----------------------- ------------- ... -------------- --------------
    2009-05-02T00:41:40.338  6.630610e-04 ...  1.5822421e-03 -1.4463664e-03
    2009-05-02T00:42:39.187  6.630857e-04 ...  1.5743829e-03 -1.4540013e-03
    2009-05-02T00:43:38.045  6.631103e-04 ...  1.5665225e-03 -1.4616371e-03
    2009-05-02T00:44:36.894  6.631350e-04 ...  1.5586632e-03 -1.4692718e-03
    2009-05-02T00:45:35.752  6.631597e-04 ...  1.5508028e-03 -1.4769078e-03

We now take a look at how to make an interactive figure of this lightcurve. To
initialize a figure, use the :class:`aas_timeseries.InteractiveTimeSeriesFigure`
class::

    >>> from aas_timeseries import InteractiveTimeSeriesFigure
    >>> fig = InteractiveTimeSeriesFigure()

We can now add markers using::

    fig.add_markers(time_series=ts, column='sap_flux', label='SAP Flux')

The first argument is the whole time series object, while the second is the name
of the column to use for the specific markers, while the latter is used in the
legend of the plot. At this point, you could also add other time series, model
overlays, define different views, and so on - we will look at these shortly, but
for now let's assume we want to save the interactive figure. You can save the
figure to a JSON file using::

    fig.save_interactive('my-figure.json')
