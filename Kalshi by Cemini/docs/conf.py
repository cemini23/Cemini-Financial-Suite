import os
import sys
sys.path.insert(0, os.path.abspath('..'))

project = 'Kalshi by Cemini'
copyright = '2026, Cemini Financial'
author = 'Cemini Financial'
release = '1.8.0'

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode',
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store', 'venv']

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
