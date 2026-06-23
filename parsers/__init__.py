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
from .visit_stpaul import VisitStPaulParser
from .dakota_jazz_club import DakotaJazzClubParser
from .berlin_jazz_club import BerlinJazzClubParser
from .crooners import CroonersSupperClubParser
from .visit_duluth import VisitDuluthParser
from .luminary_arts_center import LuminaryArtsCenterParser
from .utepils_brewery import UtepilsBreweryParser
from .pryes_brewing import PryesBrewingParser
from .mncba_workshops import MNCBAWorkshopsParser
from .coch_cooking_classes import CoCHCookingClassesParser
from .dame_errant_clay import DameErrantClayParser
from .mpls_parks import MplsParksParser
from .trylon_cinema import TrylonCinemaParser
from .parkway_theater import ParkwayTheaterParser
from .fillmore_minneapolis import FillmoreMinneapolisParser
from .litt_pinball_bar import LITTPinballBarParser
from .castle_danger_brewery import CastleDangerBreweryParser

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
    'ordway_theater': OrdwayParser,
    'visit_stpaul': VisitStPaulParser,
    'dakota_jazz_club': DakotaJazzClubParser,
    'berlin_jazz_club': BerlinJazzClubParser,
    'crooners': CroonersSupperClubParser,
    'visit_duluth': VisitDuluthParser,
    'luminary_arts_center': LuminaryArtsCenterParser,
    'utepils_brewery': UtepilsBreweryParser,
    'pryes_brewing': PryesBrewingParser,
    'mncba_workshops': MNCBAWorkshopsParser,
    'coch_cooking_classes': CoCHCookingClassesParser,
    'dame_errant_clay': DameErrantClayParser,
    'mpls_parks': MplsParksParser,
    'trylon_cinema': TrylonCinemaParser,
    'parkway_theater': ParkwayTheaterParser,
    'fillmore_minneapolis': FillmoreMinneapolisParser,
    'litt_pinball_bar': LITTPinballBarParser,
    'castle_danger_brewery': CastleDangerBreweryParser
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
