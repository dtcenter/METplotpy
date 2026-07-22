# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# http://www.sphinx-doc.org/en/master/config

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
import sys
sys.path.insert(0, os.path.abspath('.'))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__),
                                                os.pardir)))
print(sys.path)

from metplotpy import __version__ as version

# -- Project information -----------------------------------------------------

project = 'METplotpy'
copyright = '2026, NSF NCAR'
author = 'UCAR/NSF NCAR, NOAA, CSU/CIRA, and CU/CIRES'
author_list = 'Adriaansen, D.,  C. Kalb, D. Fillmore, T. Jensen, L. Goodrich, M. Win-Gildenmeister, T. Burek, and H. Fisher'
verinfo = version
release = f'{version}'
release_year = '2026'

release_date = f'{release_year}-05-07'

copyright = f'{release_year}, {author}'

# if set, adds "Last updated on " followed by
# the date in the specified format
html_last_updated_fmt = '%c'

# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
# Adding 'sphinx_design' to use drop-down menus in release_notes. 
extensions = ['sphinx.ext.autodoc',
              'sphinx.ext.intersphinx',
              'sphinx_gallery.gen_gallery',
              'sphinx_design',
              'sphinx_rtd_theme',]

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# Suppress certain warning messages
suppress_warnings = ['ref.citation']

# -- Sphinx control -----------------------------------------------------------
sphinx_gallery_conf = {
      'examples_dirs': [os.path.join('..', 'examples')],
      'gallery_dirs': ['examples']
}
    

# -- Options for HTML output -------------------------------------------------

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = 'sphinx_rtd_theme'
html_theme_path = ["_themes", ]
html_js_files = ['pop_ver.js']
html_css_files = ['theme_override.css','custom.css']

# The name of an image file (relative to this directory) to place at the top
# of the sidebar.
html_logo = os.path.join('_static','met_plotpy_logo_2019_09.png')

# Control html_sidebars
# Include global TOC instead of local TOC by default
#html_sidebars = { '**': ['globaltoc.html','relations.html','sourcelink.html','searchbox.html']}

# -- Intersphinx control -----------------------------------------------------

numfig = True

numfig_format = {
        'figure': 'Figure %s',
        }

# -- linkcheck builder configuration ----------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-the-linkcheck-builder

linkcheck_timeout = 10
linkcheck_retries = 2
linkcheck_workers = 8

linkcheck_ignore = [
    # add regex patterns for URLs that should be skipped, e.g.:
    # r'https://dtcenter\.org/.*',   # if this site blocks automated requests
    # r'https://matplotlib\.org/.*',        # occasionally rate-limits automated clients
    # r'https://scitools\.org\.uk/cartopy/.*',  # occasionally slow
    r'https://doi\.org/.*', # DOI redirectors often 403 non-browser requests
    # bmcnoldy.rsmas.miami.edu sends an incomplete SSL certificate chain
    # (missing intermediate cert). Browsers work around this via AIA
    # fetching; curl/Python do not. Confirmed 2026-07 via curl -v
    # ("SSL certificate problem: unable to get local issuer certificate").
    # Re-check periodically and remove once fixed server-side.
    r'https://bmcnoldy\.rsmas\.miami\.edu/.*',
]

linkcheck_allowed_redirects = {
    # map of regex -> regex for redirects that are fine to follow
}

linkcheck_anchors = True
linkcheck_anchors_ignore = ['^!']

# -- Export variables --------------------------------------------------------

rst_epilog = """                                                                                                                                    
.. |copyright|    replace:: {copyrightstr}                                                                                                          
.. |author_list|  replace:: {author_liststr}                                                                                                        
.. |release_date| replace:: {release_datestr}                                                                                                       
.. |release_year| replace:: {release_yearstr}                                                                                                       
""".format(copyrightstr    = copyright,
           author_liststr  = author_list,
           release_datestr = release_date,
           release_yearstr = release_year)

