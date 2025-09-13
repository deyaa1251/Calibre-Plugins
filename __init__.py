# CRITICAL: Create this empty file first: plugin-import-name-arxiv_plugin.txt
# This file must be empty and present in your plugin ZIP for multi-file plugins

# __init__.py
from calibre.customize import InterfaceActionBase

class ArxivPluginBase(InterfaceActionBase):
    '''
    arXiv Search Plugin - Interface Action
    '''
    name = 'arXiv Search Plugin'
    description = 'Search and download papers from arXiv'
    supported_platforms = ['windows', 'osx', 'linux']
    author = 'Your Name'
    version = (1, 0, 0)
    minimum_calibre_version = (0, 7, 53)

    # This points to the actual plugin class in main.py
    actual_plugin = 'calibre_plugins.arxiv_plugin.main:ArxivSearchPlugin'

    def is_customizable(self):
        return False
