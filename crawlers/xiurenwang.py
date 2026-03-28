"""
Xiurenwang 爬虫
秀人网图片爬取 - 使用 Playwright
"""
import logging
from typing import Iterator, Optional
from urllib.parse import urljoin

from playwright_crawler import PlaywrightCrawler, ImageItem, GalleryItem

logger = logging.getLogger(__name__)


class XiurenwangCrawler(PlaywrightCrawler):
    """秀人网爬虫"""
    
    def __init__(self):
        super().__init__('xiurenwang')
        self.list_url_template = f"{self.base_url}/bang/page/{{page}}"
    
    def get_galleries(self, page: int = 1) -> Iterator[GalleryItem]:
        """获取图集列表"""
        url = self.list_url_template.format(page=page)
        html = self.get_page_content(url)
        
        if html is None:
            logger.error(f"无法获取页面: {url}")
            return
        
        # 解析图集列表 - 使用正确的XPath: ul.loop2 > li
        items = html.xpath('//ul[@class="loop2"]/li')
        
        if not items:
            logger.info(f"第 {page} 页没有数据")
            return
        
        for item in items:
            try:
                link_elem = item.xpath('.//a[@class="img"]/@href')
                if not link_elem:
                    continue
                
                detail_url = urljoin(self.base_url, link_elem[0])
                
                title_elem = item.xpath('.//div[@class="tit"]/a/text()')
                title = title_elem[0] if title_elem else "unnamed"
                title = self.sanitize_folder_name(title)
                
                count_elem = item.xpath('.//i[@class="lip"]/text()')
                image_count = 0
                if count_elem:
                    count_str = count_elem[0].replace('P', '').strip()
                    try:
                        image_count = int(count_str)
                    except ValueError:
                        pass
                
                yield GalleryItem(
                    url=detail_url,
                    title=title,
                    image_count=image_count,
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
        
        # 解析图片列表 - 从 div#image 中获取图片src
        img_urls = html.xpath('//div[@id="image"]//img/@src')
        
        if not img_urls:
            img_urls = html.xpath('//div[@id="image"]//a/@href')
        
        if not img_urls:
            img_urls = html.xpath('//div[@class="content"]//img/@src')
        
        for idx, img_url in enumerate(img_urls, 1):
            if img_url.startswith('//'):
                img_url = 'https:' + img_url
            elif not img_url.startswith('http'):
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
    
    with XiurenwangCrawler() as crawler:
        crawler.crawl(start_page=1, max_images=10)
