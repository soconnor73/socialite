import re
import datetime
from bs4 import BeautifulSoup
from typing import List, Dict, Any, Tuple, Optional
from .base import BaseParser


class VisitStPaulParser(BaseParser):
    """
    Parser for the Visit Saint Paul events calendar.
    URL: https://www.visitsaintpaul.com/events-calendar/

    Event listings are <article class="card card--alt card--info ..."> elements.
    Dates are read from the aria-label attribute on .cal-date:
        "From Jun 20, 2026 to Aug 16, 2026"
    The event title comes from h2.card__heading > a.
    The venue name is the first .card__address span.
    The external ticket/info link comes from .card__website > a[href].
    If no external link exists the visitsaintpaul.com detail URL is used.
    """

    MONTH_MAP = {
        'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
        'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12,
    }

    # Matches: "From Jun 20, 2026 to Aug 16, 2026"
    _DATE_RE = re.compile(
        r'From\s+([A-Za-z]+)\s+(\d+),\s*(\d{4})\s+to\s+([A-Za-z]+)\s+(\d+),\s*(\d{4})',
        re.IGNORECASE
    )

    def _clean(self, text: str) -> str:
        """Normalise whitespace and common Unicode replacements."""
        if not text:
            return ''
        text = text.replace('\xa0', ' ').replace('\u2011', '-')
        text = text.replace('\u2018', "'").replace('\u2019', "'")
        text = text.replace('\u201c', '"').replace('\u201d', '"')
        return ' '.join(text.split()).strip()

    def _parse_aria_dates(self, aria_label: str) -> Tuple[Optional[datetime.date], Optional[datetime.date]]:
        """
        Parse start and end dates from a cal-date aria-label string.
        e.g. "From Jun 20, 2026 to Aug 16, 2026" → (date(2026,6,20), date(2026,8,16))
        """
        if not aria_label:
            return None, None
        m = self._DATE_RE.search(aria_label)
        if not m:
            return None, None
        m1_str, d1, y1, m2_str, d2, y2 = m.groups()
        month1 = self.MONTH_MAP.get(m1_str[:3].lower())
        month2 = self.MONTH_MAP.get(m2_str[:3].lower())
        if not (month1 and month2):
            return None, None
        try:
            start = datetime.date(int(y1), month1, int(d1))
            end = datetime.date(int(y2), month2, int(d2))
            return start, end
        except ValueError:
            return None, None

    def parse(self, html_content: bytes, **kwargs) -> List[Dict[str, Any]]:
        """
        Parse Visit Saint Paul events calendar HTML.

        Args:
            html_content: Raw HTML bytes from the events calendar page.

        Returns:
            List of structured show dictionaries conforming to BaseParser contract.
        """
        soup = BeautifulSoup(html_content, 'html.parser')

        # Event cards are <article class="card card--alt card--info ...">
        # Non-event cards (blog/guide cards) use card--default instead of card--info.
        cards = soup.find_all('article', class_='card')
        shows: List[Dict[str, Any]] = []

        for card in cards:
            card_classes = card.get('class', [])
            if 'card--info' not in card_classes:
                # Skip blog/promotional cards
                continue

            # ── Title & detail link ──────────────────────────────────────────
            heading = card.find('h2', class_='card__heading')
            if not heading:
                continue
            title_a = heading.find('a', href=True)
            if not title_a:
                continue

            title = self._clean(title_a.get_text())
            detail_link = title_a.get('href', '').strip()
            if detail_link.startswith('/'):
                detail_link = 'https://www.visitsaintpaul.com' + detail_link

            # ── Dates ────────────────────────────────────────────────────────
            cal_date_el = card.find(class_='cal-date')
            if not cal_date_el:
                continue
            aria_label = cal_date_el.get('aria-label', '')
            start_date, end_date = self._parse_aria_dates(aria_label)
            if not start_date:
                continue

            # ── Venue ────────────────────────────────────────────────────────
            # The first card__address span is the venue name; subsequent ones
            # are the street address lines.
            address_spans = card.find_all(class_='card__address')
            venue = 'Saint Paul'
            if address_spans:
                venue = self._clean(address_spans[0].get_text())

            # ── External website link ────────────────────────────────────────
            website_el = card.find(class_='card__website')
            link = detail_link  # fallback to the VSP detail page
            if website_el:
                website_a = website_el.find('a', href=True)
                if website_a:
                    href = website_a.get('href', '').strip()
                    if href and href.startswith('http'):
                        link = href

            # ── Category / tour label ────────────────────────────────────────
            category = title_a.get('data-dms-category-name', '')
            category = self._clean(category)

            # ── Recurrence / schedule note ───────────────────────────────────
            recurs_el = card.find(class_='card__date-recurs')
            recurs_note = self._clean(recurs_el.get_text()) if recurs_el else ''

            # ── Artists ──────────────────────────────────────────────────────
            # VSP is a discovery aggregator — events are individual listings,
            # not necessarily music acts. We use the title as the sole artist.
            artists = [title]

            shows.append({
                'date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'venue': venue,
                'title': title,
                'tour': category,
                'support_raw': recurs_note,
                'artists': artists,
                'link': link,
            })

        return shows
