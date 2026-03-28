"""
Hotgirl 爬虫
"""
import logging
from typing import Iterator, Optional
from urllib.parse import urljoin

from playwright_crawler import PlaywrightCrawler, ImageItem, GalleryItem

logger = logging.getLogger(__name__)


class HotgirlCrawler(PlaywrightCrawler):
    """Hotgirl爬虫"""
    
    def __init__(self):
        super().__init__('hotgirl')
        self.list_url_template = f"{self.base_url}/page/{{page}}/"
    
    def get_galleries(self, page: int = 1) -> Iterator[GalleryItem]:
        """获取图集列表"""
        url = self.list_url_template.format(page=page)
        # 使用更宽松的等待策略
        html = self.get_page_content(url)
        
        if html is None:
            logger.error(f"无法获取页面: {url}")
            return
        
        # 解析图集列表
        articles = html.xpath('//article')
        
        if not articles:
            logger.info(f"第 {page} 页没有数据")
            return
        
        for article in articles:
            try:
                link_elem = article.xpath('.//h2[contains(@class, "entry-title")]/a/@href')
                title_elem = article.xpath('.//h2[contains(@class, "entry-title")]/a/text()')
                
                if not link_elem:
                    continue
                
                detail_url = link_elem[0]
                title = self.sanitize_folder_name(title_elem[0]) if title_elem else "unnamed"
                
                yield GalleryItem(
                    url=detail_url,
                    title=title,
                    image_count=0,
                    meta={'page': page}
                )
                
            except Exception as e:
                logger.warning(f"解析图集项失败: {e}")
                continue
    
    def get_images(self, gallery: GalleryItem) -> Iterator[ImageItem]:
        """获取图集中的图片"""
        html = self.get_page_content(gallery.url)
        
        if html is None:
            logger.error(f"无法获取图集页面: {gallery.url}")
            return
        
        # 解析图片 - 优先使用 data-src（懒加载）
        img_urls = html.xpath('//div[contains(@class, "entry-content")]//img/@data-src')
        if not img_urls:
            img_urls = html.xpath('//div[contains(@class, "entry-content")]//img/@src')
        
        if not img_urls:
            img_urls = html.xpath('//div[@class="content"]//img/@src')
        
        for idx, img_url in enumerate(img_urls, 1):
            # 跳过 data URI 和无效图片
            if img_url.startswith('data:') or '.svg' in img_url:
                continue
            
            if not img_url.startswith('http'):
                img_url = urljoin(self.base_url, img_url)
            
            ext = img_url.split('.')[-1].split('?')[0]
            if ext not in ['jpg', 'jpeg', 'png', 'webp', 'gif']:
                ext = 'jpg'
            filename = f"{idx:04d}.{ext}"
            
            yield ImageItem(
                url=img_url,
                title=gallery.title,
                folder_name=gallery.title,
                filename=filename,
                meta={'index': idx}
            )


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    with HotgirlCrawler() as crawler:
        crawler.crawl(start_page=1, max_images=10)
