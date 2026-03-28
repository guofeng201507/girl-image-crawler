"""
爬虫基类模块
提供所有爬虫的公共功能
"""
import re
import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Dict, Optional, Iterator
from dataclasses import dataclass
from urllib.parse import urljoin

import requests
from lxml import etree

from config import SITE_CONFIGS, DOWNLOAD_ROOT, DEFAULT_HEADERS, PROXY
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


class BaseCrawler(ABC):
    """爬虫基类"""
    
    def __init__(self, site_key: str, headers: Optional[Dict] = None):
        """
        初始化爬虫
        
        Args:
            site_key: 站点配置键名
            headers: 自定义请求头
        """
        self.site_key = site_key
        self.config = SITE_CONFIGS.get(site_key, {})
        if not self.config:
            raise ValueError(f"未知的站点: {site_key}")
        
        self.name = self.config['name']
        self.base_url = self.config['base_url']
        self.download_dir = DOWNLOAD_ROOT / self.config['download_dir']
        
        # 设置请求头
        self.headers = DEFAULT_HEADERS.copy()
        if headers:
            self.headers.update(headers)
        
        # 设置代理
        self.proxy = PROXY if self.config.get('proxy', False) else None
        
        # 创建session
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        
        # 创建下载器
        self.downloader = Downloader(self.headers, self.proxy)
        
        # 统计
        self.stats = {
            'total': 0,
            'success': 0,
            'failed': 0,
            'skipped': 0,
        }
        
        logger.info(f"初始化爬虫: {self.name}")
    
    def get_html(self, url: str, retries: int = 3) -> Optional[etree._Element]:
        """
        获取页面HTML
        
        Args:
            url: 页面URL
            retries: 重试次数
        
        Returns:
            etree._Element: HTML元素，失败返回None
        """
        for attempt in range(retries):
            try:
                response = self.session.get(
                    url, 
                    timeout=30, 
                    proxies=self.proxy
                )
                response.raise_for_status()
                return etree.HTML(response.text)
            except Exception as e:
                logger.warning(f"请求失败 (尝试 {attempt + 1}/{retries}): {url} - {e}")
                if attempt == retries - 1:
                    return None
        return None
    
    def normalize_filename(self, filename: str) -> str:
        """
        规范化文件名（移除非法字符）
        """
        # 移除或替换非法字符
        filename = re.sub(r'[<>:"/\\|?*]', '', filename)
        filename = filename.strip('. ')
        return filename or 'unnamed'
    
    def sanitize_folder_name(self, name: str) -> str:
        """
        清理文件夹名称
        """
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
    
    def crawl(self, start_page: int = 1, end_page: Optional[int] = None):
        """
        开始爬取
        
        Args:
            start_page: 起始页码
            end_page: 结束页码，None表示不限制
        """
        logger.info(f"开始爬取 {self.name}，页码: {start_page} - {end_page or '不限'}")
        
        page = start_page
        while end_page is None or page <= end_page:
            logger.info(f"正在处理第 {page} 页...")
            
            galleries = list(self.get_galleries(page))
            if not galleries:
                logger.info(f"第 {page} 页无数据，停止爬取")
                break
            
            for gallery in galleries:
                self.download_gallery(gallery)
            
            page += 1
        
        self.print_stats()
    
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
        self.session.close()
        self.downloader.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
