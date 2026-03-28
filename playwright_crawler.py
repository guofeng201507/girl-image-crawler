"""
Playwright 爬虫基类模块
使用 Playwright 进行页面渲染，支持 JavaScript 渲染的网站
"""
import re
import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Optional, Iterator
from dataclasses import dataclass
from urllib.parse import urljoin

from lxml import etree
from playwright.sync_api import sync_playwright, Page, Browser, BrowserContext, Playwright

from config import SITE_CONFIGS, DOWNLOAD_ROOT, PLAYWRIGHT_CONFIG
from downloader import Downloader

logger = logging.getLogger(__name__)


@dataclass
class ImageItem:
    """图片项数据类"""
    url: str
    title: str
    folder_name: str
    filename: str
    meta: Optional[Dict] = None


@dataclass
class GalleryItem:
    """图集项数据类"""
    url: str
    title: str
    image_count: int
    category: str = ""
    meta: Optional[Dict] = None


class PlaywrightCrawler(ABC):
    """Playwright 爬虫基类"""
    
    def __init__(self, site_key: str):
        """
        初始化爬虫
        
        Args:
            site_key: 站点配置键名
        """
        self.site_key = site_key
        self.config = SITE_CONFIGS.get(site_key, {})
        if not self.config:
            raise ValueError(f"未知的站点: {site_key}")
        
        self.name = self.config['name']
        self.base_url = self.config['base_url']
        self.download_dir = DOWNLOAD_ROOT / self.config['download_dir']
        
        # Playwright 配置
        self.headless = PLAYWRIGHT_CONFIG.get('headless', True)
        self.timeout = PLAYWRIGHT_CONFIG.get('timeout', 30000)
        self.wait_until = PLAYWRIGHT_CONFIG.get('wait_until', 'networkidle')
        
        # 初始化 Playwright
        self._playwright: Optional[Playwright] = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None
        
        # 创建下载器
        self.downloader = Downloader()
        
        # 统计
        self.stats = {
            'total': 0,
            'success': 0,
            'failed': 0,
            'skipped': 0,
        }
        
        logger.info(f"初始化爬虫: {self.name}")
    
    def _start_browser(self):
        """启动浏览器"""
        if self._playwright is None:
            self._playwright = sync_playwright().start()
            self._browser = self._playwright.chromium.launch(headless=self.headless)
            self._context = self._browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                viewport={'width': 1920, 'height': 1080}
            )
            self._page = self._context.new_page()
            self._page.set_default_timeout(self.timeout)
            logger.debug("浏览器已启动")
    
    @property
    def page(self) -> Page:
        """获取页面对象，按需启动浏览器"""
        if self._page is None:
            self._start_browser()
        return self._page
    
    def get_page_content(self, url: str, wait_selector: Optional[str] = None) -> Optional[etree._Element]:
        """
        获取页面内容
        
        Args:
            url: 页面URL
            wait_selector: 等待的选择器（可选）
        
        Returns:
            etree._Element: HTML元素，失败返回None
        """
        try:
            self.page.goto(url, wait_until=self.wait_until, timeout=self.timeout)
            
            # 如果指定了等待选择器，等待元素出现
            if wait_selector:
                self.page.wait_for_selector(wait_selector, timeout=self.timeout)
            
            # 获取页面内容
            content = self.page.content()
            return etree.HTML(content)
            
        except Exception as e:
            logger.warning(f"获取页面失败: {url} - {e}")
            return None
    
    def scroll_to_bottom(self, scroll_pause: float = 1.0, max_scrolls: int = 10):
        """
        滚动到页面底部（用于懒加载）
        
        Args:
            scroll_pause: 每次滚动后的暂停时间（秒）
            max_scrolls: 最大滚动次数
        """
        for _ in range(max_scrolls):
            # 获取当前滚动高度
            prev_height = self.page.evaluate("document.body.scrollHeight")
            
            # 滚动到底部
            self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            
            # 等待新内容加载
            self.page.wait_for_timeout(int(scroll_pause * 1000))
            
            # 检查是否有新内容
            new_height = self.page.evaluate("document.body.scrollHeight")
            if new_height == prev_height:
                break
    
    def normalize_filename(self, filename: str) -> str:
        """规范化文件名（移除非法字符）"""
        filename = re.sub(r'[<>:"/\\|?*]', '', filename)
        filename = filename.strip('. ')
        return filename or 'unnamed'
    
    def sanitize_folder_name(self, name: str) -> str:
        """清理文件夹名称"""
        return self.normalize_filename(name)
    
    @abstractmethod
    def get_galleries(self, page: int = 1) -> Iterator[GalleryItem]:
        """
        获取图集列表（子类必须实现）
        
        Args:
            page: 页码
        
        Yields:
            GalleryItem: 图集项
        """
        pass
    
    @abstractmethod
    def get_images(self, gallery: GalleryItem) -> Iterator[ImageItem]:
        """
        获取图集中的图片（子类必须实现）
        
        Args:
            gallery: 图集项
        
        Yields:
            ImageItem: 图片项
        """
        pass
    
    def download_image(self, image: ImageItem) -> bool:
        """
        下载单张图片
        
        Args:
            image: 图片项
        
        Returns:
            bool: 是否成功
        """
        folder = self.download_dir / image.folder_name
        result = self.downloader.download_image(image.url, folder, image.filename)
        
        if result:
            self.stats['success'] += 1
        else:
            self.stats['failed'] += 1
        
        return result is not None
    
    def download_gallery(self, gallery: GalleryItem) -> int:
        """
        下载整个图集
        
        Args:
            gallery: 图集项
        
        Returns:
            int: 成功下载的图片数
        """
        logger.info(f"开始下载图集: {gallery.title} ({gallery.image_count}张)")
        
        success_count = 0
        for image in self.get_images(gallery):
            self.stats['total'] += 1
            
            if self.download_image(image):
                success_count += 1
                logger.debug(f"下载成功: {image.filename}")
            else:
                logger.warning(f"下载失败: {image.filename}")
        
        logger.info(f"图集下载完成: {gallery.title} ({success_count}/{gallery.image_count})")
        return success_count
    
    def crawl(self, start_page: int = 1, end_page: Optional[int] = None, max_images: Optional[int] = None):
        """
        开始爬取
        
        Args:
            start_page: 起始页码
            end_page: 结束页码，None表示不限制
            max_images: 最大下载图片数，None表示不限制
        """
        logger.info(f"开始爬取 {self.name}，页码: {start_page} - {end_page or '不限'}, 最多下载 {max_images or '不限'} 张")
        
        page = start_page
        downloaded = 0
        
        while end_page is None or page <= end_page:
            if max_images and downloaded >= max_images:
                break
            
            logger.info(f"正在处理第 {page} 页...")
            
            galleries = list(self.get_galleries(page))
            if not galleries:
                logger.info(f"第 {page} 页无数据，停止爬取")
                break
            
            for gallery in galleries:
                if max_images and downloaded >= max_images:
                    break
                
                for image in self.get_images(gallery):
                    if max_images and downloaded >= max_images:
                        break
                    
                    self.stats['total'] += 1
                    if self.download_image(image):
                        downloaded += 1
                        logger.info(f"已下载: {downloaded}/{max_images or '不限'}")
            
            page += 1
        
        self.print_stats()
        logger.info(f"下载完成，共下载 {downloaded} 张图片")
    
    def print_stats(self):
        """打印统计信息"""
        logger.info("=" * 50)
        logger.info(f"爬取统计 - {self.name}")
        logger.info(f"  总计: {self.stats['total']}")
        logger.info(f"  成功: {self.stats['success']}")
        logger.info(f"  失败: {self.stats['failed']}")
        logger.info(f"  跳过: {self.stats['skipped']}")
        logger.info("=" * 50)
    
    def close(self):
        """清理资源"""
        if self._page:
            self._page.close()
        if self._context:
            self._context.close()
        if self._browser:
            self._browser.close()
        if self._playwright:
            self._playwright.stop()
        self.downloader.close()
        logger.debug("资源已清理")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
