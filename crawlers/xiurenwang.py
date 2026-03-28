"""
Xiurenwang 爬虫
秀人网图片爬取
"""
import logging
from typing import Iterator, Optional
from urllib.parse import urljoin

from base_crawler import BaseCrawler, ImageItem, GalleryItem

logger = logging.getLogger(__name__)


class XiurenwangCrawler(BaseCrawler):
    """秀人网爬虫"""
    
    def __init__(self):
        super().__init__('xiurenwang')
        self.list_url_template = f"{self.base_url}/bang/page/{{page}}"
        
        # 特定站点的请求头
        self.headers.update({
            'authority': 'www.xiurenwang.cc',
            'referer': f'{self.base_url}/bang',
        })
        # 更新session的请求头
        self.session.headers.update(self.headers)
        self.downloader.headers = self.headers
    
    def get_galleries(self, page: int = 1) -> Iterator[GalleryItem]:
        """
        获取图集列表
        """
        url = self.list_url_template.format(page=page)
        html = self.get_html(url)
        
        if html is None:
            logger.error(f"无法获取页面: {url}")
            return
        
        # 解析图集列表
        items = html.xpath('//ul[@class="list"]/li')
        
        if not items:
            logger.info(f"第 {page} 页没有数据")
            return
        
        for item in items:
            try:
                link_elem = item.xpath('.//a[@class="img"]/@href')
                if not link_elem:
                    continue
                
                detail_url = urljoin(self.base_url, link_elem[0])
                
                # 获取标题
                title_elem = item.xpath('.//img/@alt')
                title = title_elem[0] if title_elem else "unnamed"
                title = self.sanitize_folder_name(title)
                
                # 获取图片数量（如果有）
                count_elem = item.xpath('.//span[@class="count"]/text()')
                image_count = int(count_elem[0]) if count_elem else 0
                
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
        """
        获取图集中的图片
        """
        html = self.get_html(gallery.url)
        
        if html is None:
            logger.error(f"无法获取图集页面: {gallery.url}")
            return
        
        # 解析图片列表
        img_urls = html.xpath('//div[@id="image"]//a/@href')
        
        if not img_urls:
            # 尝试其他XPath
            img_urls = html.xpath('//div[@class="content"]//img/@src')
        
        for idx, img_url in enumerate(img_urls, 1):
            # 处理相对URL
            if not img_url.startswith('http'):
                img_url = urljoin(self.base_url, img_url)
            
            # 生成文件名
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
    
    def crawl(self, start_page: int = 1, end_page: Optional[int] = None, max_images: int = None):
        """
        爬取指定页码范围
        """
        logger.info(f"开始爬取 {self.name}，页码: {start_page} - {end_page or '不限'}")
        
        page = start_page
        empty_count = 0  # 连续空页计数
        downloaded = 0
        
        while empty_count < 3:  # 连续3页无数据则停止
            if end_page and page > end_page:
                break
            
            if max_images and downloaded >= max_images:
                break
            
            logger.info(f"正在处理第 {page} 页...")
            galleries = list(self.get_galleries(page))
            
            if not galleries:
                empty_count += 1
                logger.info(f"第 {page} 页无数据 (连续空页: {empty_count})")
                page += 1
                continue
            
            empty_count = 0  # 重置空页计数
            
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


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    with XiurenwangCrawler() as crawler:
        crawler.crawl(start_page=1, end_page=5)
