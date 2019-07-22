Submitting an interactive figure to AAS Journals
================================================

To include an interactive figure in your paper, first make sure you export
the interactive figure(s) you have produced to a zip file (see also
:doc:`saving`)::

    fig.export_interactive_bundle('my_figure.zip')

and also be sure to export a static version of the figure for the PDF version
of the paper::

    fig.save_static('my_figure', format='pdf')

After you have generated the interactive figure ``.zip`` package and its
associated static figure please include them along with all the other necessary
manuscript files when you submit to the AAS peer review system at:

https://aas.msubmit.net/cgi-bin/main.plex

Addition information regarding author submission instructions can be found at:

https://journals.aas.org/author-resources/

For questions regarding integration of the interactive figure in the manuscript
please email data-editors@aas.org.
