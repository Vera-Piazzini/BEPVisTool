# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

import os
import sys

sys.path.insert(0, os.path.abspath('..'))

project = 'BEPVis Tool Documentation'
copyright = '2025, O. Vera-Piazzini, M. Scarpa'
author = 'O. Vera-Piazzini, M. Scarpa'
release = '1.00'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = ['sphinx.ext.autodoc', 
              'sphinx.ext.todo', 
              'sphinx.ext.viewcode', 
              'sphinx.ext.napoleon', 
              'sphinx_rtd_theme']

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
html_context = {"github_url": "https://github.com", # o il tuo dominio
                "github_user": "vera-piazzini", # Il tuo username
                "github_repo": "BEPVisTool", # Il nome esatto del repository
                "github_version": "main", # o "master", a seconda del branch che usi per GH Pages
                "conf_py_path": "/docs/" # o dove si trova il conf.py, se usi una sottocartella
}
html_baseurl = 'https://vera-piazzini.github.io/BEPVisTool/'