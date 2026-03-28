"""
爬虫统一入口
提供命令行界面管理所有爬虫
"""
import os
import sys
import argparse
import logging
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from config import SITE_CONFIGS, LOG_CONFIG, DOWNLOAD_ROOT
from crawlers import (
    WallhavenCrawler, XiurenwangCrawler, EveriaclubCrawler,
    TuiimgCrawler, HotgirlCrawler, KanxiaojiejieCrawler,
    NsfwpicxCrawler, HitxhotCrawler, AsiantolickCrawler
)


def setup_logging(level: str = 'INFO'):
    """配置日志"""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format=LOG_CONFIG['format'],
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(LOG_CONFIG['file'], encoding='utf-8') if LOG_CONFIG['file'] else logging.NullHandler(),
        ]
    )


def list_sites():
    """列出所有可用站点"""
    print("\n可用站点列表:")
    print("-" * 60)
    print(f"{'站点Key':<15} {'站点名称':<20} {'需要代理':<10}")
    print("-" * 60)
    for key, config in SITE_CONFIGS.items():
        proxy = "是" if config.get('proxy') else "否"
        print(f"{key:<15} {config['name']:<20} {proxy:<10}")
    print("-" * 60)


def crawl_site(site: str, start_page: int = 1, end_page: int = None, **kwargs):
    """
    运行指定站点的爬虫
    
    Args:
        site: 站点key
        start_page: 起始页
        end_page: 结束页
        **kwargs: 额外参数
    """
    if site not in SITE_CONFIGS:
        print(f"错误: 未知站点 '{site}'")
        print(f"可用站点: {', '.join(SITE_CONFIGS.keys())}")
        return
    
    config = SITE_CONFIGS[site]
    print(f"\n开始爬取: {config['name']}")
    print(f"下载目录: {DOWNLOAD_ROOT / config['download_dir']}")
    print(f"页码范围: {start_page} - {end_page or '不限'}")
    print("-" * 60)
    
    # 根据站点创建对应的爬虫
    crawler_map = {
        'wallhaven': lambda: WallhavenCrawler(id_file=kwargs.get('id_file')),
        'xiurenwang': XiurenwangCrawler,
        'everiaclub': EveriaclubCrawler,
        'tuiimg': TuiimgCrawler,
        'hotgirl': HotgirlCrawler,
        'kanxiaojiejie': KanxiaojiejieCrawler,
        'nsfwpicx': NsfwpicxCrawler,
        'hitxhot': HitxhotCrawler,
        'asiantolick': AsiantolickCrawler,
    }
    
    if site not in crawler_map:
        print(f"错误: 站点 '{site}' 的爬虫尚未实现")
        return
    
    if site == 'wallhaven' and not kwargs.get('id_file'):
        print("错误: Wallhaven需要提供ID文件路径 (--id-file)")
        return
    
    crawler = crawler_map[site]()
    
    # 运行爬虫
    with crawler:
        crawler.crawl(start_page=start_page, end_page=end_page)
    
    print(f"\n爬取完成: {config['name']}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='图片爬虫工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 列出所有可用站点
  python main.py --list
  
  # 爬取Wallhaven（需要提供ID文件）
  python main.py wallhaven --id-file ids.txt
  
  # 爬取秀人网第1-5页
  python main.py xiurenwang --start-page 1 --end-page 5
  
  # 设置下载目录（环境变量）
  set CRAWLER_DOWNLOAD_PATH=D:/downloads
  set USE_PROXY=true
        """
    )
    
    parser.add_argument('site', nargs='?', help='要爬取的站点key')
    parser.add_argument('--list', '-l', action='store_true', help='列出所有可用站点')
    parser.add_argument('--start-page', '-s', type=int, default=1, help='起始页码 (默认: 1)')
    parser.add_argument('--end-page', '-e', type=int, help='结束页码')
    parser.add_argument('--id-file', '-f', help='ID文件路径（Wallhaven需要）')
    parser.add_argument('--log-level', default='INFO', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'], 
                        help='日志级别 (默认: INFO)')
    
    args = parser.parse_args()
    
    # 设置日志
    setup_logging(args.log_level)
    
    # 处理命令
    if args.list:
        list_sites()
        return
    
    if not args.site:
        parser.print_help()
        print("\n错误: 请指定站点或使用 --list 查看可用站点")
        return
    
    # 运行爬虫
    crawl_site(
        site=args.site,
        start_page=args.start_page,
        end_page=args.end_page,
        id_file=args.id_file
    )


if __name__ == '__main__':
    main()
