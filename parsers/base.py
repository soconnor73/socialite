from abc import ABC, abstractmethod
from typing import List, Dict, Any

class BaseParser(ABC):
    """
    Abstract base class for all site-specific event parsers.
    """
    
    @abstractmethod
    def parse(self, html_content: bytes, **kwargs) -> List[Dict[str, Any]]:
        """
        Parses raw HTML content and returns a list of structured show dictionaries.
        
        Args:
            html_content: The raw HTML content (as bytes).
            **kwargs: Extra contextual arguments (e.g. year, base_url).
            
        Returns:
            A list of dictionaries representing parsed show/event structures:
            {
                'date': 'YYYY-MM-DD',
                'venue': 'Venue Name',
                'title': 'Event Title',
                'tour': 'Tour Name (optional)',
                'support_raw': 'Raw support text (optional)',
                'artists': ['Artist 1', 'Artist 2'],
                'link': 'http://...'
            }
        """
        pass
