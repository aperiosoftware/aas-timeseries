Saving the interactive figure
=============================

To save the interactive figure to `Vega <https://vega.github.io/vega/>`_-
compliant JSON, use::

    fig.save_interactive('my_figure.json')

By default, the data will be saved to separate CSV files, but you can also force
the data to be embedded inside the JSON file by using::

    fig.save_interactive('my_figure.json', embed_data=True)

Finally, you can also save the JSON file and data files along with a template
HTML file to view your interactive figure to a zip file by using::

    fig.save_interactive('my_figure.zip', zip_bundle=True)
