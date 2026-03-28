"""
爬虫集合
"""
from .wallhaven import WallhavenCrawler
from .xiurenwang import XiurenwangCrawler
from .everiaclub import EveriaclubCrawler
from .tuiimg import TuiimgCrawler
from .hotgirl import HotgirlCrawler
from .kanxiaojiejie import KanxiaojiejieCrawler
from .nsfwpicx import NsfwpicxCrawler
from .hitxhot import HitxhotCrawler
from .asiantolick import AsiantolickCrawler

__all__ = [
    'WallhavenCrawler',
    'XiurenwangCrawler',
    'EveriaclubCrawler',
    'TuiimgCrawler',
    'HotgirlCrawler',
    'KanxiaojiejieCrawler',
    'NsfwpicxCrawler',
    'HitxhotCrawler',
    'AsiantolickCrawler',
]
