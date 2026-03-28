"""
爬虫集合

所有爬虫已迁移到 Playwright，支持 JavaScript 渲染的网站。
基类: playwright_crawler.PlaywrightCrawler
"""
from .xiurenwang import XiurenwangCrawler
from .hotgirl import HotgirlCrawler

__all__ = [
    'XiurenwangCrawler',
    'HotgirlCrawler',
]
