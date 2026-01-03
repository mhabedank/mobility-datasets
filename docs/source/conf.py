# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

import os
import sys

# Add source to path for autodoc
sys.path.insert(0, os.path.abspath("../../src"))

project = "Mobility Datasets"
copyright = "2025, Martin Habedank"
author = "Martin Habedank"
release = "0.1.0"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.autodoc",  # Auto-generate API docs
    "sphinx.ext.autosummary",  # Generate summary tables
    "sphinx.ext.napoleon",  # NumPy/Google docstring support
    "sphinx.ext.viewcode",  # Link to source code
    "sphinx.ext.intersphinx",  # Link to other docs
    "sphinx_click",  # CLI documentation
]

# Napoleon settings (for NumPy-style docstrings)
napoleon_google_docstring = False
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = True
napoleon_use_param = True
napoleon_use_rtype = True

# Autodoc settings
autodoc_member_order = "bysource"
autodoc_typehints = "description"

# Autosummary settings
autosummary_generate = True

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "numpy": ("https://numpy.org/doc/stable/", None),
    "pandas": ("https://pandas.pydata.org/docs/", None),
}

# HTML output
html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]

templates_path = ["_templates"]
exclude_patterns = []
