"""
Tuiimg 爬虫
推图网
"""
import logging
from typing import Iterator, Optional
from urllib.parse import urljoin

from base_crawler import BaseCrawler, ImageItem, GalleryItem

logger = logging.getLogger(__name__)


class TuiimgCrawler(BaseCrawler):
    """推图网爬虫"""
    
    def __init__(self):
        super().__init__('tuiimg')
        self.list_url_template = f"{self.base_url}/meinv/"
    
    def get_galleries(self, page: int = 1) -> Iterator[GalleryItem]:
        """获取图集列表"""
        url = self.list_url_template.format(page=page)
        html = self.get_html(url)
        
        if html is None:
            logger.error(f"无法获取页面: {url}")
            return
        
        # 解析图集列表
        items = html.xpath('//ul[@class="img"]//li')
        
        if not items:
            logger.info(f"第 {page} 页没有数据")
            return
        
        for item in items:
            try:
                link_elem = item.xpath('.//a/@href')
                title_elem = item.xpath('.//img/@alt')
                
                if not link_elem:
                    continue
                
                detail_url = urljoin(self.base_url, link_elem[0])
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
        html = self.get_html(gallery.url)
        
        if html is None:
            logger.error(f"无法获取图集页面: {gallery.url}")
            return
        
        # 解析图片
        img_urls = html.xpath('//div[@class="content"]//img/@src')
        
        # 尝试其他XPath
        if not img_urls:
            img_urls = html.xpath('//article//img/@src')
        
        for idx, img_url in enumerate(img_urls, 1):
            if not img_url.startswith('http'):
                img_url = urljoin(self.base_url, img_url)
            
            ext = img_url.split('.')[-1].split('?')[0]
            if ext not in ['jpg', 'jpeg', 'png', 'webp']:
                ext = 'jpg'
            filename = f"{idx:04d}.{ext}"
            
            yield ImageItem(
                url=img_url,
                title=gallery.title,
                folder_name=gallery.title,
                filename=filename,
                meta={'index': idx}
            )
    
    def crawl(self, start_page: int = 1, end_page: Optional[int] = None, max_images: int = 10):
        """爬取，限制下载数量"""
        logger.info(f"开始爬取 {self.name}，最多下载 {max_images} 张")
        
        page = start_page
        downloaded = 0
        
        while downloaded < max_images:
            if end_page and page > end_page:
                break
            
            logger.info(f"正在处理第 {page} 页...")
            galleries = list(self.get_galleries(page))
            
            if not galleries:
                break
            
            for gallery in galleries:
                if downloaded >= max_images:
                    break
                
                for image in self.get_images(gallery):
                    if downloaded >= max_images:
                        break
                    
                    self.stats['total'] += 1
                    if self.download_image(image):
                        downloaded += 1
                        logger.info(f"已下载: {downloaded}/{max_images}")
            
            page += 1
        
        self.print_stats()


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    with TuiimgCrawler() as crawler:
        crawler.crawl(start_page=1, max_images=10)
