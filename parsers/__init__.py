from .base import BaseParser
from .first_avenue import FirstAvenueParser
from .grand_casino_arena import GrandCasinoArenaParser
from .acme_comedy_club import AcmeComedyClubParser
from .guthrie_theater import GuthrieTheaterParser
from .minneapolis import MinneapolisParser
from .mn_united_fc import MNUnitedFCParser
from .minnesota_twins import MinnesotaTwinsParser
from .target_center import TargetCenterParser
from .minnesota_orchestra import MinnesotaOrchestraParser
from .hennepin_arts import HennepinArtsParser
from .us_bank_stadium import USBankStadiumParser
from .northrop_auditorium import NorthropAuditoriumParser
from .ordway import OrdwayParser

PARSER_REGISTRY = {
    'first_avenue': FirstAvenueParser,
    'grand_casino_arena': GrandCasinoArenaParser,
    'acme_comedy_club': AcmeComedyClubParser,
    'guthrie_theater': GuthrieTheaterParser,
    'minneapolis': MinneapolisParser,
    'mn_united_fc': MNUnitedFCParser,
    'minnesota_twins': MinnesotaTwinsParser,
    'target_center': TargetCenterParser,
    'minnesota_orchestra': MinnesotaOrchestraParser,
    'hennepin_arts': HennepinArtsParser,
    'us_bank_stadium': USBankStadiumParser,
    'northrop_auditorium': NorthropAuditoriumParser,
    'ordway_theater': OrdwayParser
}

def get_parser(site_name: str) -> BaseParser:
    """
    Factory function to retrieve a parser instance by site name.
    
    Args:
        site_name: The identifier of the site parser to load (e.g. 'first_avenue')
    """
    parser_class = PARSER_REGISTRY.get(site_name.lower())
    if not parser_class:
        raise ValueError(f"No parser registered for site: {site_name}. "
                         f"Available parsers: {list(PARSER_REGISTRY.keys())}")
    return parser_class()
