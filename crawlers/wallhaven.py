"""
Wallhaven 爬虫
从文本文件读取图片ID并下载
"""
import logging
from pathlib import Path
from typing import Iterator, List, Optional

from base_crawler import BaseCrawler, ImageItem, GalleryItem
from config import DOWNLOAD_ROOT

logger = logging.getLogger(__name__)


class WallhavenCrawler(BaseCrawler):
    """Wallhaven壁纸爬虫"""
    
    def __init__(self, id_file: Optional[str] = None):
        """
        初始化Wallhaven爬虫
        
        Args:
            id_file: 包含图片ID的文本文件路径，每行格式: "id_favcount"
        """
        super().__init__('wallhaven')
        self.id_file = id_file
        self.pic_url_template = "https://w.wallhaven.cc/full/{0}/wallhaven-{1}.jpg"
        self.alt_pic_url_template = "https://w.wallhaven.cc/full/{0}/wallhaven-{1}.png"
    
    def parse_id_file(self, filepath: str) -> List[tuple]:
        """
        解析ID文件
        
        Returns:
            List[tuple]: [(img_id, favcount), ...]
        """
        items = []
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line or '_' not in line:
                        continue
                    parts = line.split('_')
                    img_id = parts[0].strip().split('/')[-1]  # 提取ID
                    favcount = int(parts[1])
                    items.append((img_id, favcount))
        except FileNotFoundError:
            logger.error(f"ID文件不存在: {filepath}")
        except Exception as e:
            logger.error(f"解析ID文件失败: {e}")
        
        return items
    
    def get_folder_by_favcount(self, favcount: int) -> str:
        """
        根据收藏数确定文件夹
        """
        if favcount > 100:
            max_val = (favcount // 100 + 1) * 100
            min_val = max_val - 100
        else:
            max_val = (favcount // 10 + 1) * 10
            min_val = max_val - 10
        
        return f"{min_val}-{max_val}"
    
    def get_galleries(self, page: int = 1) -> Iterator[GalleryItem]:
        """
        Wallhaven使用ID文件而非分页，这里将每个ID作为一个"图集"
        """
        if not self.id_file:
            logger.error("未指定ID文件")
            return
        
        items = self.parse_id_file(self.id_file)
        total = len(items)
        
        for idx, (img_id, favcount) in enumerate(items, 1):
            if idx < page:
                continue
                
            folder = self.get_folder_by_favcount(favcount)
            
            yield GalleryItem(
                url=self.pic_url_template.format(img_id[:2], img_id),
                title=f"wallhaven-{img_id}",
                image_count=1,
                category=folder,
                meta={'id': img_id, 'favcount': favcount, 'index': idx, 'total': total}
            )
    
    def get_images(self, gallery: GalleryItem) -> Iterator[ImageItem]:
        """
        获取图片（Wallhaven每个"图集"只有一张图）
        """
        meta = gallery.meta or {}
        img_id = meta.get('id', '')
        folder = gallery.category
        
        # 尝试jpg格式
        jpg_url = self.pic_url_template.format(img_id[:2], img_id)
        jpg_filename = f"wallhaven-{img_id}.jpg"
        
        yield ImageItem(
            url=jpg_url,
            title=gallery.title,
            folder_name=folder,
            filename=jpg_filename,
            meta={'alt_url': jpg_url.replace('.jpg', '.png')}
        )
    
    def download_image(self, image: ImageItem) -> bool:
        """
        下载图片，支持jpg/png自动切换
        """
        folder = self.download_dir / image.folder_name
        
        # 先尝试jpg
        jpg_path = folder / image.filename
        if jpg_path.exists():
            logger.debug(f"已存在，跳过: {jpg_path}")
            self.stats['skipped'] += 1
            return True
        
        # 检查png是否存在
        png_filename = image.filename.replace('.jpg', '.png')
        png_path = folder / png_filename
        if png_path.exists():
            logger.debug(f"已存在(png)，跳过: {png_path}")
            self.stats['skipped'] += 1
            return True
        
        # 下载jpg
        result = self.downloader.download(image.url, jpg_path)
        
        if result:
            self.stats['success'] += 1
            return True
        
        # jpg失败，尝试png
        alt_url = image.meta.get('alt_url') if image.meta else None
        if alt_url:
            result = self.downloader.download(alt_url, png_path)
            if result:
                self.stats['success'] += 1
                return True
        
        self.stats['failed'] += 1
        return False
    
    def crawl(self, start_page: int = 1, end_page: Optional[int] = None):
        """
        重写爬取方法，支持从指定位置开始
        """
        if not self.id_file:
            logger.error("请提供ID文件路径")
            return
        
        logger.info(f"开始爬取 Wallhaven，从第 {start_page} 条开始")
        
        for gallery in self.get_galleries(start_page):
            meta = gallery.meta or {}
            idx = meta.get('index', 0)
            total = meta.get('total', 0)
            favcount = meta.get('favcount', 0)
            
            logger.info(f"[{idx}/{total}] 下载: {gallery.title} (收藏: {favcount})")
            
            for image in self.get_images(gallery):
                self.stats['total'] += 1
                self.download_image(image)
            
            # 显示进度
            if idx % 100 == 0:
                self.print_stats()
            
            if end_page and idx >= end_page:
                logger.info(f"已达到结束位置 {end_page}")
                break
        
        self.print_stats()


if __name__ == '__main__':
    # 示例用法
    import sys
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    id_file = sys.argv[1] if len(sys.argv) > 1 else None
    
    with WallhavenCrawler(id_file=id_file) as crawler:
        crawler.crawl(start_page=1)
