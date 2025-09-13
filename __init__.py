from calibre.customize import InterfaceActionBase

class ArxivPluginBase(InterfaceActionBase):
    '''
    arXiv Search Plugin - Interface Action
    '''
    name = 'arXiv Search Plugin'
    description = 'Search and download papers from arXiv'
    supported_platforms = ['windows', 'osx', 'linux']
    author = 'Deyaa Khateeb'
    version = (1, 0, 0)
    minimum_calibre_version = (0, 7, 53)

    actual_plugin = 'calibre_plugins.arxiv_plugin.main:ArxivSearchPlugin'

    def is_customizable(self):
        return False
