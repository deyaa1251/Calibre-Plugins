# main.py
import os
import subprocess
import re
import xml.etree.ElementTree as ET
import urllib.request
import urllib.parse

from calibre.gui2.actions import InterfaceAction
from calibre.gui2 import error_dialog, info_dialog

# Qt imports with proper fallbacks
try:
    from PyQt5.Qt import (QDialog, QVBoxLayout, QHBoxLayout, QLineEdit,
                         QPushButton, QLabel, QListWidget, QTextEdit, QListWidgetItem)
except ImportError:
    try:
        from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLineEdit,
                                   QPushButton, QLabel, QListWidget, QTextEdit, QListWidgetItem)
    except ImportError:
        from qt.core import (QDialog, QVBoxLayout, QHBoxLayout, QLineEdit,
                           QPushButton, QLabel, QListWidget, QTextEdit, QListWidgetItem)

from calibre.library import db
from calibre.ebooks.metadata.book.base import Metadata
class ArxivSearchDialog(QDialog):
    def __init__(self, parent=None):
        QDialog.__init__(self, parent)
        self.setWindowTitle('arXiv Search')
        self.resize(800, 600)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Search section
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel('Search arXiv:'))

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText('Enter search terms (e.g., "quantum computing")...')
        self.search_input.returnPressed.connect(self.do_search)
        search_layout.addWidget(self.search_input)

        self.search_btn = QPushButton('Search')
        self.search_btn.clicked.connect(self.do_search)
        search_layout.addWidget(self.search_btn)

        layout.addLayout(search_layout)

        # Results section
        self.results_list = QListWidget()
        self.results_list.itemSelectionChanged.connect(self.display_selected_paper)
        layout.addWidget(self.results_list)

        # Details display
        self.details_text = QTextEdit()
        self.details_text.setReadOnly(True)
        layout.addWidget(self.details_text)

        # Close button
        close_btn = QPushButton('Close')
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)


        fetch_btn = QPushButton('fetch')
        fetch_btn.clicked.connect(self.fetch_html)
        layout.addWidget(fetch_btn)
        # Set focus to search input
        self.search_input.setFocus()


        self.current_selected = None

    def do_search(self):
        query = self.search_input.text().strip()
        if not query:
            self.details_text.setText("Please enter search terms.")
            return

        self.details_text.setText("Searching arXiv...")
        self.search_btn.setEnabled(False)
        self.results_list.clear()

        try:
            papers = self.search_arxiv(query)
            if papers:
                self.display_results(papers)
            else:
                self.details_text.setText("No results found for your query.")
        except Exception as e:
            error_msg = f"Search failed: {str(e)}"
            self.details_text.setText(error_msg)
            print(f"arXiv Plugin Error: {error_msg}")  # Debug output
        finally:
            self.search_btn.setEnabled(True)

    def search_arxiv(self, query):
        """Search arXiv and return multiple results"""
        # Build the arXiv API URL
        base_url = "http://export.arxiv.org/api/query"
        params = {
            'search_query': query,
            'start': 0,
            'max_results': 10,  # Increased number of results
            'sortBy': 'relevance',
            'sortOrder': 'descending'
        }

        url = f"{base_url}?{urllib.parse.urlencode(params)}"
        print(f"arXiv Plugin: Searching URL: {url}")  # Debug

        # Make the HTTP request
        req = urllib.request.Request(url)
        req.add_header('User-Agent', 'Calibre-arXiv-Plugin/1.0')

        with urllib.request.urlopen(req, timeout=15) as response:
            xml_data = response.read().decode('utf-8')

        # Parse the XML response
        root = ET.fromstring(xml_data)
        ns = {'atom': 'http://www.w3.org/2005/Atom'}

        # Find all entries
        papers = []
        for entry in root.findall('atom:entry', ns):
            paper = {}

            # Title
            title_elem = entry.find('atom:title', ns)
            if title_elem is not None:
                paper['title'] = title_elem.text.strip().replace('\n', ' ')
            else:
                paper['title'] = 'No title available'

            # Authors
            authors = []
            for author in entry.findall('atom:author', ns):
                name_elem = author.find('atom:name', ns)
                if name_elem is not None:
                    authors.append(name_elem.text.strip())
            paper['authors'] = ', '.join(authors) if authors else 'Unknown authors'

            # Abstract/Summary
            summary_elem = entry.find('atom:summary', ns)
            if summary_elem is not None:
                paper['summary'] = summary_elem.text.strip()
            else:
                paper['summary'] = 'No abstract available'

            # Published date
            published_elem = entry.find('atom:published', ns)
            if published_elem is not None:
                paper['published'] = published_elem.text[:10]  # Just the date part
            else:
                paper['published'] = 'Unknown date'

            # arXiv ID
            id_elem = entry.find('atom:id', ns)
            if id_elem is not None:
                arxiv_url = id_elem.text.strip()
                paper['arxiv_id'] = arxiv_url.split('/')[-1]
                paper['arxiv_url'] = arxiv_url
            else:
                paper['arxiv_id'] = 'Unknown ID'
                paper['arxiv_url'] = 'N/A'

            papers.append(paper)

        return papers

    def display_results(self, papers):
        """Display papers as selectable cards"""
        self.results_list.clear()
        for i, paper in enumerate(papers):
            item = QListWidgetItem()
            item.setData(1, paper)  # Store paper data in item
            item.setText(f"{i+1}. {paper['title']}\n    by {paper['authors'][:50]}...")
            self.results_list.addItem(item)

        # Select first item
        if self.results_list.count() > 0:
            self.results_list.setCurrentRow(0)

    def display_selected_paper(self):
        """Display details of selected paper"""
        self.current_selected = self.results_list.currentItem()
        current = self.results_list.currentItem()
        if current:
            paper = current.data(1)
            html_content = f"""
            <h2>{paper['title']}</h2>
            <p><strong>Authors:</strong> {paper['authors']}</p>
            <p><strong>Published:</strong> {paper['published']}</p>
            <p><strong>arXiv ID:</strong> {paper['arxiv_id']}</p>
            <p><strong>arXiv URL:</strong> <a href="{paper['arxiv_url']}">{paper['arxiv_url']}</a></p>
            <h3>Abstract:</h3>
            <p>{paper['summary']}</p>
            """
            self.details_text.setHtml(html_content)

    def fetch_html(self):
        """fetches the html of the response"""
        current = self.current_selected
        paper = current.data(1)
        paper_url = paper['arxiv_url']
        paper_html = re.sub(r'(https?://arxiv\.org/)abs/', r'\1html/', paper_url)
        req = urllib.request.Request(paper_html)
        temp_html_path = os.path.expanduser('~/tempfiles/temp.html')
        temp_epub_path = os.path.expanduser('~/tempfiles/temp.epub')
        with urllib.request.urlopen(req, timeout=15) as response:
            xml_data = response.read().decode('utf-8')
        print(xml_data)
        with open(temp_html_path, 'w') as f:
            f.write(xml_data)
        subprocess.run(['ebook-convert', temp_html_path, temp_epub_path])

        # Add to Calibre library

        # Create metadata for the book
        mi = Metadata(paper.get('title', 'Unknown Title'))
        mi.authors = paper.get('authors', ['Unknown Author'])

        # Add book to library
        calibre_db = db('~/Calibre Library').new_api  # Adjust path to your Calibre library
        calibre_db.add_books([(mi, {'EPUB': temp_epub_path})])



    # def fetch_html(self):
    #     """fetches the html of the response"""
    #     current = self.current_selected
    #     paper = current.data(1)
    #     paper_url = paper['arxiv_url']
    #     paper_html = re.sub(r'(https?://arxiv\.org/)abs/', r'\1html/', paper_url)
    #     req = urllib.request.Request(paper_html)
    #     temp_html_path = os.path.expanduser('~/tempfiles/temp.html')
    #     temp_epub_path = os.path.expanduser('~/tempfiles/temp.epub')
    #     with urllib.request.urlopen(req, timeout=15) as response:
    #         xml_data = response.read().decode('utf-8')
    #     print(xml_data)
    #     with open(temp_html_path, 'w') as f:
    #         f.write(xml_data)
    #     subprocess.run(['ebook-convert', temp_html_path, temp_epub_path])

    #     print(xml_data)
class ArxivSearchPlugin(InterfaceAction):

    name = 'arXiv Search Plugin'  # Must match the plugin name

    # Define the action spec: (text, icon_path, tooltip, keyboard_shortcut)
    action_spec = ('arXiv Search', None, 'Search arXiv papers and add them to library', 'Ctrl+Shift+A')

    def genesis(self):
        """
        Called once when the plugin is loaded.
        Set up the action behavior.
        """
        print("arXiv Plugin: genesis() called - plugin loading...")

        # Connect the action to our handler
        self.qaction.triggered.connect(self.show_search_dialog)

        print("arXiv Plugin: Successfully loaded!")

    def show_search_dialog(self):
        """
        Show the arXiv search dialog.
        Called when user clicks the toolbar button or uses keyboard shortcut.
        """
        print("arXiv Plugin: show_search_dialog() called!")

        try:
            # Create and show the dialog
            dialog = ArxivSearchDialog(self.gui)
            dialog.exec_()
            print("arXiv Plugin: Dialog closed successfully")

        except Exception as e:
            print(f"arXiv Plugin: Error showing dialog: {str(e)}")
            # Show error to user
            error_dialog(self.gui, 'arXiv Plugin Error',
                        f'Failed to open search dialog: {str(e)}',
                        show=True)
