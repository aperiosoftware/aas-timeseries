Saving the interactive figure
=============================

To save the interactive figure to `Vega <https://vega.github.io/vega/>`_-
compliant JSON, use::

    fig.save_vega_json('my_figure.json')

By default, the data will be saved to separate CSV files, but you can also force
the data to be embedded inside the JSON file by using::

    fig.save_vega_json('my_figure.json', embed_data=True)

Finally, you can also export the JSON file and data files along with a template
HTML file to view your interactive figure to a zip file by using::

    fig.export_interactive_bundle('my_figure.zip', zip_bundle=True)
