"""Sphinx configuration: build the heron docs from the docstrings."""

project = "heron"
extensions = [
    "sphinx.ext.autodoc",  # read the docstrings of the modules
    "sphinx.ext.napoleon",  # understand the NumPy-style sections
]
napoleon_google_docstring = False  # this project writes NumPy style only
html_theme = "sphinx_rtd_theme"
exclude_patterns = ["_build"]
# Sphinx 9 would copy type comments into pydantic's annotations, and then
# FastAPI fails to import; heron uses annotations, not type comments.
autodoc_use_type_comments = False
