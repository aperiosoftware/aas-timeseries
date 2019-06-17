Saving interactive and static figures
=====================================

Saving interactive figures
--------------------------

To save the interactive figure to `Vega <https://vega.github.io/vega/>`_-compliant
JSON, use the
:meth:`~aas_timeseries.InteractiveTimeSeriesFigure.save_vega_json` method::

    fig.save_vega_json('my_figure.json')

By default, the data will be saved to separate CSV files, but you can also force
the data to be embedded inside the JSON file by using::

    fig.save_vega_json('my_figure.json', embed_data=True)

Finally, you can also export the JSON file and data files along with a template
HTML file to view your interactive figure to a zip file by using the
:meth:`~aas_timeseries.InteractiveTimeSeriesFigure.export_interactive_bundle`
method::

    fig.export_interactive_bundle('my_figure.zip', zip_bundle=True)

Saving static figures
---------------------

You can also save a static version of your plots using Matplotlib by using
the :meth:`~aas_timeseries.InteractiveTimeSeriesFigure.save_static` method::

    fig.save_static('my_figure', format='pdf')

The first argument is the prefix for the final filename, rather than the full
filename - this is because in the case where views are present, files such as
``my_figure_view1.pdf`` will also be saved. The
:meth:`~aas_timeseries.InteractiveTimeSeriesFigure.save_static` method supports
all formats that are supported by the Matplotlib package.

If you want to customize the appearance of the plot, such as the font type you
can make use of the `Matplotlib rcparams
<https://matplotlib.org/users/customizing.html#matplotlib-rcparams>`_ settings.
